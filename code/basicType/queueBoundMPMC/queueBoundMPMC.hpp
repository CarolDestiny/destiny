#pragma once
#include <cstddef>
#include <type_traits>
#include <atomic>
#include <bit>
#include <thread>

namespace destiny {
    template<typename T, size_t SIZE = 256>
        requires std::is_pointer_v<T>
    class QueueBoundMPMC;
}

template<typename T, size_t SIZE>
    requires std::is_pointer_v<T>
class destiny::QueueBoundMPMC {
public:
    inline QueueBoundMPMC() noexcept;
    inline ~QueueBoundMPMC() noexcept;

    inline bool empty() noexcept;
    inline size_t size() noexcept;

    inline void push(const T value) noexcept;
    inline T pop() noexcept;
private:
    static constexpr size_t CAPACITY = std::bit_ceil(SIZE);
    static constexpr size_t MASK = CAPACITY - 1;
    struct Slot;

    struct alignas(64) Slot {
        std::atomic<size_t> sequence;
        T data;
    };

    alignas(64) Slot buffer_[CAPACITY];
    alignas(64) std::atomic<size_t> producerIndex_{0};
    alignas(64) std::atomic<size_t> consumerIndex_{0};
};

template<typename T, size_t SIZE> requires std::is_pointer_v<T>
destiny::QueueBoundMPMC<T, SIZE>::QueueBoundMPMC() noexcept {
    for (size_t i = 0; i < CAPACITY; ++ i) {
        buffer_[i].sequence = i;
    }
    return;
}

template<typename T, size_t SIZE> requires std::is_pointer_v<T>
destiny::QueueBoundMPMC<T, SIZE>::~QueueBoundMPMC() noexcept {
    return;
}

template<typename T, size_t SIZE> requires std::is_pointer_v<T>
bool destiny::QueueBoundMPMC<T, SIZE>::empty() noexcept {
    const size_t producerIndex = producerIndex_.load(std::memory_order_acquire);
    const size_t consumerIndex = consumerIndex_.load(std::memory_order_acquire);
    return producerIndex == consumerIndex;
}

template<typename T, size_t SIZE> requires std::is_pointer_v<T>
size_t destiny::QueueBoundMPMC<T, SIZE>::size() noexcept {
    const size_t producerIndex = producerIndex_.load(std::memory_order_acquire);
    const size_t consumerIndex = consumerIndex_.load(std::memory_order_acquire);
    if (producerIndex < consumerIndex) {
        return 0;
    }
    const size_t n = producerIndex - consumerIndex;
    return n <= CAPACITY ? n : CAPACITY;
}


template<typename T, size_t SIZE> requires std::is_pointer_v<T>
void destiny::QueueBoundMPMC<T, SIZE>::push(const T value) noexcept {
    const size_t index = producerIndex_.fetch_add(1, std::memory_order_relaxed);
    Slot& slot = buffer_[index & MASK];
    size_t waitTime = 0;
    while (true) {
        const size_t seq = slot.sequence.load((std::memory_order_relaxed));
        if (index == seq) {
            break;
        }
        // wait
        if (waitTime > 20) {
            slot.sequence.wait(seq, std::memory_order_relaxed);
        }
        else if (waitTime > 10) {
            std::this_thread::yield();
        }
        ++ waitTime;
    }
    std::atomic_thread_fence(std::memory_order_acquire);
    slot.data = value;
    slot.sequence.store(index+1,std::memory_order_release);
    slot.sequence.notify_all();
    return;
}

template<typename T, size_t SIZE> requires std::is_pointer_v<T>
T destiny::QueueBoundMPMC<T, SIZE>::pop() noexcept {
    const size_t index = consumerIndex_.fetch_add(1,std::memory_order_relaxed);
    Slot& slot = buffer_[index & MASK];
    size_t waitTime = 0;
    while (true) {
        const size_t seq = slot.sequence.load(std::memory_order_relaxed);
        if (seq == index + 1) {
            break;
        }
        // wait
        if (waitTime > 20) {
            slot.sequence.wait(seq, std::memory_order_relaxed);
        }
        else if (waitTime > 10) {
            std::this_thread::yield();
        }
        ++ waitTime;
    }
    std::atomic_thread_fence(std::memory_order_acquire);
    const T value = slot.data;
    slot.sequence.store(index + CAPACITY,std::memory_order_release);
    slot.sequence.notify_all();
    return value;
}

