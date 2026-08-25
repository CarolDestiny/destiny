#include "../src/boundMPSC.hpp"

#include <algorithm>
#include <atomic>
#include <cerrno>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <limits>
#include <memory>
#include <string_view>
#include <thread>
#include <vector>

namespace
{

    using Queue = destiny::core::replay::detail::BoundMPSC;
    using Clock = std::chrono::steady_clock;

    constexpr std::uint64_t kDefaultEventsPerProducer = 1'000'000;
    constexpr std::size_t kMaxDefaultProducers = 8;
    constexpr auto kTimeout = std::chrono::seconds(60);

    struct Token
    {
        std::uint64_t id = 0;
    };

    struct ProducerResult
    {
        std::uint64_t published = 0;
        std::uint64_t failedPushReturns = 0;
    };

    struct BenchmarkResult
    {
        std::size_t producerCount = 0;
        std::size_t eventsPerProducer = 0;
        std::size_t expectedEvents = 0;
        std::size_t publishedEvents = 0;
        std::size_t consumedEvents = 0;
        std::size_t failedPushReturns = 0;
        std::size_t failedPopReturns = 0;
        std::size_t invalidPointers = 0;
        std::size_t duplicateEvents = 0;
        std::size_t missingEvents = 0;
        std::uint64_t elapsedNanoseconds = 0;
        bool strictVerification = true;
        bool completed = false;
    };

    bool parsePositive(const char* text, std::uint64_t& value) noexcept
    {
        if (text == nullptr || *text == '\0') {
            return false;
        }

        errno = 0;
        char* end = nullptr;
        const auto parsed = std::strtoull(text, &end, 10);
        if (errno != 0 || end == text || *end != '\0' || parsed == 0) {
            return false;
        }

        value = static_cast<std::uint64_t>(parsed);
        return true;
    }

    std::size_t defaultProducerCount() noexcept
    {
        const auto hardwareThreads = std::thread::hardware_concurrency();
        if (hardwareThreads <= 1) {
            return 1;
        }
        return std::min<std::size_t>(static_cast<std::size_t>(hardwareThreads - 1), kMaxDefaultProducers);
    }

    void yieldAfterContention(const std::uint64_t attempts) noexcept
    {
        if ((attempts & 1023u) == 0u) {
            std::this_thread::yield();
        }
    }

    std::size_t tokenIndex(void* pointer, const std::vector<Token>& tokens) noexcept
    {
        const auto base = reinterpret_cast<std::uintptr_t>(tokens.data());
        const auto address = reinterpret_cast<std::uintptr_t>(pointer);
        const auto bytes = tokens.size() * sizeof(Token);
        if (address < base || address - base >= bytes) {
            return tokens.size();
        }

        const auto offset = address - base;
        if (offset % sizeof(Token) != 0) {
            return tokens.size();
        }
        return static_cast<std::size_t>(offset / sizeof(Token));
    }

    BenchmarkResult runBenchmark(const std::size_t producerCount, const std::size_t eventsPerProducer,
                                 const bool strictVerification)
    {
        BenchmarkResult result;
        result.producerCount = producerCount;
        result.eventsPerProducer = eventsPerProducer;
        result.expectedEvents = producerCount * eventsPerProducer;
        result.strictVerification = strictVerification;

        auto queue = std::make_unique<Queue>();
        std::vector<Token> tokens(result.expectedEvents);
        for (std::size_t index = 0; index < tokens.size(); ++index) {
            tokens[index].id = index;
        }
        std::vector<std::uint8_t> seen(strictVerification ? result.expectedEvents : 0u, 0);

        std::vector<ProducerResult> producerResults(producerCount);
        std::vector<std::thread> producers;
        producers.reserve(producerCount);

        std::atomic<std::size_t> ready{0};
        std::atomic<bool> start{false};
        std::atomic<bool> stop{false};
        std::atomic<std::size_t> invalidPointers{0};
        std::atomic<std::size_t> duplicateEvents{0};
        std::size_t consumed = 0;
        std::size_t failedPopReturns = 0;
        Clock::time_point finishedAt{};
        Clock::time_point deadline{};

        std::thread consumer([&] {
            ready.fetch_add(1, std::memory_order_relaxed);
            while (!start.load(std::memory_order_acquire)) {
                std::this_thread::yield();
            }

            while (consumed < result.expectedEvents && !stop.load(std::memory_order_acquire)) {
                void* pointer = nullptr;
                if (!queue->pop(pointer)) {
                    ++failedPopReturns;
                    yieldAfterContention(failedPopReturns);
                    if ((failedPopReturns & 16383u) == 0u && Clock::now() >= deadline) {
                        stop.store(true, std::memory_order_release);
                        break;
                    }
                    continue;
                }

                if (pointer == nullptr) {
                    invalidPointers.fetch_add(1, std::memory_order_relaxed);
                    stop.store(true, std::memory_order_release);
                    break;
                }

                if (strictVerification) {
                    const auto index = tokenIndex(pointer, tokens);
                    if (index >= tokens.size() || tokens[index].id != index) {
                        invalidPointers.fetch_add(1, std::memory_order_relaxed);
                        stop.store(true, std::memory_order_release);
                        break;
                    }
                    if (seen[index] != 0) {
                        duplicateEvents.fetch_add(1, std::memory_order_relaxed);
                        stop.store(true, std::memory_order_release);
                        break;
                    }
                    seen[index] = 1;
                }
                ++consumed;
            }

            finishedAt = Clock::now();
            if (consumed == result.expectedEvents) {
                stop.store(true, std::memory_order_release);
            }
        });

        for (std::size_t producer = 0; producer < producerCount; ++producer) {
            producers.emplace_back([&, producer] {
                ready.fetch_add(1, std::memory_order_relaxed);
                while (!start.load(std::memory_order_acquire)) {
                    std::this_thread::yield();
                }

                ProducerResult local;
                const auto begin = producer * eventsPerProducer;
                const auto end = begin + eventsPerProducer;
                for (std::size_t index = begin; index < end && !stop.load(std::memory_order_acquire);) {
                    if (queue->push(&tokens[index])) {
                        ++index;
                        ++local.published;
                        continue;
                    }

                    ++local.failedPushReturns;
                    yieldAfterContention(local.failedPushReturns);
                    if ((local.failedPushReturns & 16383u) == 0u && Clock::now() >= deadline) {
                        stop.store(true, std::memory_order_release);
                        break;
                    }
                }
                producerResults[producer] = local;
            });
        }

        while (ready.load(std::memory_order_acquire) != producerCount + 1u) {
            std::this_thread::yield();
        }
        const auto measuredStart = Clock::now();
        deadline = measuredStart + kTimeout;
        start.store(true, std::memory_order_release);

        consumer.join();
        for (auto& producer : producers) {
            producer.join();
        }

        if (finishedAt < measuredStart) {
            finishedAt = Clock::now();
        }

        result.consumedEvents = consumed;
        result.failedPopReturns = failedPopReturns;
        result.invalidPointers = invalidPointers.load(std::memory_order_relaxed);
        result.duplicateEvents = duplicateEvents.load(std::memory_order_relaxed);
        for (const auto& producer : producerResults) {
            result.publishedEvents += static_cast<std::size_t>(producer.published);
            result.failedPushReturns += static_cast<std::size_t>(producer.failedPushReturns);
        }
        if (strictVerification) {
            for (const auto value : seen) {
                result.missingEvents += value == 0 ? 1u : 0u;
            }
        }
        result.elapsedNanoseconds = static_cast<std::uint64_t>(
            std::chrono::duration_cast<std::chrono::nanoseconds>(finishedAt - measuredStart).count());
        result.completed = result.publishedEvents == result.expectedEvents
                           && result.consumedEvents == result.expectedEvents && result.invalidPointers == 0
                           && result.duplicateEvents == 0 && (!strictVerification || result.missingEvents == 0);
        return result;
    }

    void printResult(const BenchmarkResult& result)
    {
        const double seconds = static_cast<double>(result.elapsedNanoseconds) / 1'000'000'000.0;
        const double throughput = seconds > 0.0 ? static_cast<double>(result.consumedEvents) / seconds : 0.0;

        std::cout << "BoundMPSC throughput\n"
                  << "  producers: " << result.producerCount << '\n'
                  << "  events/producer: " << result.eventsPerProducer << '\n'
                  << "  expected events: " << result.expectedEvents << '\n'
                  << "  published events: " << result.publishedEvents << '\n'
                  << "  consumed events: " << result.consumedEvents << '\n'
                  << "  failed push returns: " << result.failedPushReturns << '\n'
                  << "  failed pop returns: " << result.failedPopReturns << '\n'
                  << "  invalid pointers: " << result.invalidPointers << '\n'
                  << "  duplicate events: " << result.duplicateEvents << '\n'
                  << "  missing events: " << result.missingEvents << '\n'
                  << "  verification: " << (result.strictVerification ? "strict" : "disabled") << '\n'
                  << "  elapsed: " << std::fixed << std::setprecision(6) << seconds << " s\n"
                  << "  end-to-end throughput: " << std::setprecision(2) << throughput << " events/s\n"
                  << "  status: " << (result.completed ? "PASS" : "FAIL") << '\n';
    }

    void printUsage()
    {
        std::cerr << "usage: boundMPSC_bench [producers] [events_per_producer] [--verify|--no-verify]\n";
    }

} // namespace

int main(int argc, char** argv)
{
    std::uint64_t producerCountValue = static_cast<std::uint64_t>(defaultProducerCount());
    std::uint64_t eventsPerProducerValue = kDefaultEventsPerProducer;
    bool strictVerification = true;
    std::size_t positionalArguments = 0;

    for (int index = 1; index < argc; ++index) {
        const std::string_view argument = argv[index];
        if (argument == "--verify") {
            strictVerification = true;
            continue;
        }
        if (argument == "--no-verify") {
            strictVerification = false;
            continue;
        }

        std::uint64_t* destination = nullptr;
        if (positionalArguments == 0) {
            destination = &producerCountValue;
        }
        else if (positionalArguments == 1) {
            destination = &eventsPerProducerValue;
        }
        else {
            printUsage();
            return 2;
        }
        if (!parsePositive(argv[index], *destination)) {
            printUsage();
            return 2;
        }
        ++positionalArguments;
    }

    if (producerCountValue > std::numeric_limits<std::size_t>::max()
        || eventsPerProducerValue > std::numeric_limits<std::size_t>::max()) {
        std::cerr << "benchmark size is not representable on this target\n";
        return 2;
    }

    const auto producerCount = static_cast<std::size_t>(producerCountValue);
    const auto eventsPerProducer = static_cast<std::size_t>(eventsPerProducerValue);
    if (eventsPerProducer > std::numeric_limits<std::size_t>::max() / producerCount) {
        std::cerr << "benchmark size overflows size_t\n";
        return 2;
    }

    const auto expectedEvents = producerCount * eventsPerProducer;
    if (expectedEvents > std::numeric_limits<std::size_t>::max() / sizeof(Token)) {
        std::cerr << "benchmark token allocation overflows size_t\n";
        return 2;
    }

    const auto result = runBenchmark(producerCount, eventsPerProducer, strictVerification);
    printResult(result);
    return result.completed ? 0 : 1;
}
