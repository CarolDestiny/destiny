#pragma once
#include <atomic>
#include <cstdint>

namespace destiny::core::replay::detail
{
    class BoundMPSC;
}

class destiny::core::replay::detail::BoundMPSC
{
public:
    inline BoundMPSC() noexcept = default;
    inline ~BoundMPSC() noexcept = default;
    inline bool push(void* ptr) noexcept;
    inline bool pop(void*& ptr) noexcept;

private:
    static constexpr std::uint32_t capacity_ = UINT16_MAX + 1u;
    static constexpr std::uint32_t pushRetryLimit_ = 512u;
    static constexpr std::uint32_t popRetryLimit_ = 2u * capacity_;

    static constexpr std::uint16_t indexFromTicket(std::uint16_t ticket) noexcept
    {
        return static_cast<std::uint16_t>(((ticket & 0xffu) << 8u) | (ticket >> 8u));
    }

    alignas(64) std::atomic<std::uint16_t> ticket_{0};
    // MPSC means that only one consumer may mutate this cursor.
    alignas(64) std::uint16_t head_{0};
    alignas(64) std::atomic<void*> buffer_[capacity_]{nullptr};
    inline bool push_try(void* ptr) noexcept;
    inline bool pop_try(void*& ptr) noexcept;
};

bool destiny::core::replay::detail::BoundMPSC::push_try(void* ptr) noexcept
{
    if (ptr == nullptr) [[unlikely]] {
        return false;
    }

    const auto ticket = ticket_.fetch_add(1, std::memory_order_relaxed);
    const auto index = indexFromTicket(ticket);
    void* expected = nullptr;
    return buffer_[index].compare_exchange_strong(expected, ptr, std::memory_order_release, std::memory_order_relaxed);
}

bool destiny::core::replay::detail::BoundMPSC::pop_try(void*& ptr) noexcept
{
    const std::uint16_t index = head_++;
    ptr = buffer_[index].load(std::memory_order_acquire);
    if (ptr == nullptr) {
        return false;
    }
    buffer_[index].store(nullptr, std::memory_order_relaxed);
    return true;
}

bool destiny::core::replay::detail::BoundMPSC::push(void* ptr) noexcept
{
    if (ptr == nullptr) [[unlikely]] {
        return false;
    }
    std::uint32_t retries = 0;
    while (true) {
        if (push_try(ptr)) {
            return true;
        }
        if (++retries > pushRetryLimit_) {
            return false;
        }
    }
}

bool destiny::core::replay::detail::BoundMPSC::pop(void*& ptr) noexcept
{
    std::uint32_t retries = 0;
    while (true) {
        if (pop_try(ptr)) {
            return true;
        }
        if (++retries > popRetryLimit_) {
            return false;
        }
    }
}
