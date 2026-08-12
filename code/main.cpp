#include <iostream>
#include <chrono>
#include "basicType/queueBoundMPMC/queueBoundMPMC.hpp"

int main() {
    using namespace std::chrono;

    constexpr size_t producerNumber = 1;
    constexpr size_t consumerNumber = 1;
    constexpr size_t len = 100000000;
    destiny::QueueBoundMPMC<void*> queue;

    std::thread thProducer[producerNumber];
    std::thread thConsumer[consumerNumber];

    const auto start = high_resolution_clock::now();

    for (auto& value: thProducer) {
        value = std::thread([&] {
            for (int j = 1; j < len; j++) {
                queue.push((void*) (j));
            }
            return;
        });
    }

    for (auto& value: thConsumer) {
        value = std::thread([&] {
            while (queue.pop() != nullptr);
            return;
        });
    }

    for (auto& value: thProducer) {
        value.join();
    }

    for (auto& value: thConsumer) {
        queue.push(nullptr);
    }

    for (auto& value: thConsumer) {
        value.join();
    }

    const auto end = high_resolution_clock::now();
    const auto duration = duration_cast<microseconds>(end - start);

    std::cout << len * producerNumber * 1000 * 1000  / (size_t)duration.count() << std::endl;
    return 0;
}