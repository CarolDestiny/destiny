#include <gtest/gtest.h>

#include <atomic>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <memory>
#include <thread>
#include <vector>

#include "../src/boundMPSC.hpp"

namespace
{

    using BoundMPSC = destiny::core::replay::detail::BoundMPSC;

    constexpr std::size_t kCapacity = static_cast<std::size_t>(std::numeric_limits<std::uint16_t>::max()) + 1u;

    struct Event
    {
        std::uint64_t id = 0;
    };

    std::size_t eventIndex(void* pointer, const std::vector<Event>& events) noexcept
    {
        const auto base = reinterpret_cast<std::uintptr_t>(events.data());
        const auto address = reinterpret_cast<std::uintptr_t>(pointer);
        const auto bytes = events.size() * sizeof(Event);
        if (address < base || address - base >= bytes) {
            return events.size();
        }

        const auto offset = address - base;
        if (offset % sizeof(Event) != 0) {
            return events.size();
        }
        return static_cast<std::size_t>(offset / sizeof(Event));
    }

    bool consumeUnique(BoundMPSC& queue, const std::vector<Event>& events, std::vector<std::uint8_t>& seen)
    {
        void* pointer = nullptr;
        if (!queue.pop(pointer)) {
            return false;
        }

        const auto index = eventIndex(pointer, events);
        if (index >= events.size() || events[index].id != index || seen[index] != 0) {
            return false;
        }
        seen[index] = 1;
        return true;
    }

    TEST(BoundMPSC, PushAndPopRoundTrip)
    {
        BoundMPSC queue;
        Event event{42};
        void* result = nullptr;

        ASSERT_TRUE(queue.push(&event));
        ASSERT_TRUE(queue.pop(result));
        EXPECT_EQ(result, static_cast<void*>(&event));
    }

    TEST(BoundMPSC, NullPointerIsRejectedAndEmptyPopClearsOutput)
    {
        BoundMPSC queue;
        void* result = reinterpret_cast<void*>(static_cast<std::uintptr_t>(1));

        EXPECT_FALSE(queue.push(nullptr));
        EXPECT_FALSE(queue.pop(result));
        EXPECT_EQ(result, nullptr);
    }

    TEST(BoundMPSC, FullQueueCanBeDrainedWithoutDuplicates)
    {
        BoundMPSC queue;
        std::vector<Event> events(kCapacity);
        std::vector<std::uint8_t> seen(kCapacity, 0);
        for (std::size_t index = 0; index < events.size(); ++index) {
            events[index].id = index;
            ASSERT_TRUE(queue.push(&events[index]));
        }

        for (std::size_t index = 0; index < events.size(); ++index) {
            ASSERT_TRUE(consumeUnique(queue, events, seen)) << "failed at element " << index;
        }

        for (const auto value : seen) {
            EXPECT_EQ(value, 1);
        }

        void* result = reinterpret_cast<void*>(static_cast<std::uintptr_t>(1));
        EXPECT_FALSE(queue.pop(result));
        EXPECT_EQ(result, nullptr);
    }

    TEST(BoundMPSC, FullQueueRejectsOverflowWithoutDiscardingPublishedEvents)
    {
        BoundMPSC queue;
        std::vector<Event> events(kCapacity + 1u);
        std::vector<std::uint8_t> seen(kCapacity, 0);
        for (std::size_t index = 0; index < kCapacity; ++index) {
            events[index].id = index;
            ASSERT_TRUE(queue.push(&events[index]));
        }

        events.back().id = kCapacity;
        EXPECT_FALSE(queue.push(&events.back()));

        for (std::size_t index = 0; index < kCapacity; ++index) {
            ASSERT_TRUE(consumeUnique(queue, events, seen)) << "failed at element " << index;
        }
        for (const auto value : seen) {
            EXPECT_EQ(value, 1);
        }

        void* result = nullptr;
        ASSERT_TRUE(queue.push(&events.back()));
        ASSERT_TRUE(queue.pop(result));
        EXPECT_EQ(result, static_cast<void*>(&events.back()));
        EXPECT_FALSE(queue.pop(result));
        EXPECT_EQ(result, nullptr);
    }

    TEST(BoundMPSC, QueueReusesEverySlotAcrossTicketAndCursorWrap)
    {
        BoundMPSC queue;
        std::vector<Event> events(2u * kCapacity);
        std::vector<std::uint8_t> seen(events.size(), 0);

        for (std::size_t cycle = 0; cycle < 2; ++cycle) {
            const auto begin = cycle * kCapacity;
            for (std::size_t offset = 0; offset < kCapacity; ++offset) {
                events[begin + offset].id = begin + offset;
                ASSERT_TRUE(queue.push(&events[begin + offset]));
            }

            for (std::size_t offset = 0; offset < kCapacity; ++offset) {
                ASSERT_TRUE(consumeUnique(queue, events, seen))
                    << "failed at cycle " << cycle << ", element " << offset;
            }
        }

        for (const auto value : seen) {
            EXPECT_EQ(value, 1);
        }
    }

    struct ConcurrentRoundResult
    {
        std::size_t published = 0;
        std::size_t consumed = 0;
        std::size_t duplicateOrInvalid = 0;
        std::size_t missing = 0;
        std::size_t failedPushReturns = 0;
        std::size_t failedPopReturns = 0;
        bool stoppedByDeadline = false;
    };

    ConcurrentRoundResult runConcurrentRound(const std::size_t producerCount, const std::size_t eventsPerProducer)
    {
        const auto total = producerCount * eventsPerProducer;
        auto queue = std::make_unique<BoundMPSC>();
        std::vector<Event> events(total);
        for (std::size_t index = 0; index < total; ++index) {
            events[index].id = index;
        }

        std::vector<std::uint8_t> seen(total, 0);
        std::vector<std::size_t> publishedByProducer(producerCount, 0);
        std::atomic<std::size_t> ready{0};
        std::atomic<bool> start{false};
        std::atomic<bool> stop{false};
        std::atomic<bool> deadlineExpired{false};
        std::atomic<std::size_t> duplicateOrInvalid{0};
        std::chrono::steady_clock::time_point deadline;
        std::size_t consumed = 0;
        std::size_t failedPopReturns = 0;

        std::thread consumer([&] {
            ready.fetch_add(1, std::memory_order_relaxed);
            while (!start.load(std::memory_order_acquire)) {
                std::this_thread::yield();
            }

            while (consumed < total && !stop.load(std::memory_order_acquire)) {
                void* pointer = nullptr;
                if (!queue->pop(pointer)) {
                    ++failedPopReturns;
                    if (std::chrono::steady_clock::now() >= deadline) {
                        deadlineExpired.store(true, std::memory_order_release);
                        stop.store(true, std::memory_order_release);
                        break;
                    }
                    std::this_thread::yield();
                    continue;
                }

                const auto index = eventIndex(pointer, events);
                if (index >= events.size() || events[index].id != index || seen[index] != 0) {
                    duplicateOrInvalid.fetch_add(1, std::memory_order_relaxed);
                    stop.store(true, std::memory_order_release);
                    break;
                }
                seen[index] = 1;
                ++consumed;
            }

            if (consumed == total) {
                stop.store(true, std::memory_order_release);
            }
        });

        std::vector<std::thread> producers;
        producers.reserve(producerCount);
        std::vector<std::size_t> failedPushReturns(producerCount, 0);
        for (std::size_t producer = 0; producer < producerCount; ++producer) {
            producers.emplace_back([&, producer] {
                ready.fetch_add(1, std::memory_order_relaxed);
                while (!start.load(std::memory_order_acquire)) {
                    std::this_thread::yield();
                }

                const auto begin = producer * eventsPerProducer;
                const auto end = begin + eventsPerProducer;
                for (std::size_t index = begin; index < end && !stop.load(std::memory_order_acquire);) {
                    if (queue->push(&events[index])) {
                        ++index;
                        ++publishedByProducer[producer];
                        continue;
                    }

                    ++failedPushReturns[producer];
                    if (std::chrono::steady_clock::now() >= deadline) {
                        deadlineExpired.store(true, std::memory_order_release);
                        stop.store(true, std::memory_order_release);
                        break;
                    }
                    std::this_thread::yield();
                }
            });
        }

        while (ready.load(std::memory_order_acquire) != producerCount + 1u) {
            std::this_thread::yield();
        }
        deadline = std::chrono::steady_clock::now() + std::chrono::seconds(10);
        start.store(true, std::memory_order_release);

        for (auto& producer : producers) {
            producer.join();
        }
        consumer.join();

        ConcurrentRoundResult result;
        result.consumed = consumed;
        result.duplicateOrInvalid = duplicateOrInvalid.load(std::memory_order_relaxed);
        result.failedPopReturns = failedPopReturns;
        for (std::size_t producer = 0; producer < producerCount; ++producer) {
            result.published += publishedByProducer[producer];
            result.failedPushReturns += failedPushReturns[producer];
        }
        for (const auto value : seen) {
            result.missing += value == 0 ? 1u : 0u;
        }
        result.stoppedByDeadline = deadlineExpired.load(std::memory_order_acquire);
        return result;
    }

    TEST(BoundMPSC, ConcurrentProducersAndConsumerPreserveEveryEvent)
    {
        constexpr std::size_t producerCount = 4;
        constexpr std::size_t eventsPerProducer = 20'000;
        constexpr std::size_t rounds = 3;

        for (std::size_t round = 0; round < rounds; ++round) {
            const auto result = runConcurrentRound(producerCount, eventsPerProducer);
            const auto expected = producerCount * eventsPerProducer;
            EXPECT_FALSE(result.stoppedByDeadline) << "round " << round;
            EXPECT_EQ(result.published, expected) << "round " << round;
            EXPECT_EQ(result.consumed, expected) << "round " << round;
            EXPECT_EQ(result.duplicateOrInvalid, 0u) << "round " << round;
            EXPECT_EQ(result.missing, 0u) << "round " << round;
        }
    }

} // namespace
