/* edit bt AI */
#pragma once

#include "destiny/define/platform/platform.hpp"

#if DESTINY_DEFINE_PLATFORM_LINUX == true

#include <atomic>
#include <limits>

#include <pthread.h>
#include <time.h>

namespace destiny::core::cpu_manager::detail {
        class CpuCore {
        public:
                CpuCore() noexcept  = default;
                ~CpuCore() noexcept = default;

                CpuCore(const CpuCore&)            = delete;
                CpuCore& operator=(const CpuCore&) = delete;
                CpuCore(CpuCore&&)                 = delete;
                CpuCore& operator=(CpuCore&&)      = delete;

                inline bool create() noexcept;
                inline void stop_set() noexcept;
                inline bool wait(unsigned int time_ms) noexcept;
                inline void destroy() noexcept;

                inline void function_set(void (*function)()) noexcept;

        private:
                static void*            linux_thread_function_(void* lpParameter);
                std::atomic<void (*)()> function_{nullptr};
                std::atomic<bool>       can_stop_{false};
                pthread_t               thread_{};
                bool                    is_created_{false};
                bool                    is_joined_{false};
        };
}

inline bool destiny::core::cpu_manager::detail::CpuCore::create() noexcept
{
        if (is_created_ == true)
        {
                return false;
        }

        function_.store(nullptr, std::memory_order_relaxed);
        can_stop_.store(false, std::memory_order_relaxed);
        is_joined_ = false;

        const int result = pthread_create(
                &thread_,
                nullptr,
                linux_thread_function_,
                this
        );
        if (result != 0)
        {
                return false;
        }
        is_created_ = true;
        return true;
}

inline void destiny::core::cpu_manager::detail::CpuCore::stop_set() noexcept
{
        can_stop_.store(true, std::memory_order_release);
        return;
}

inline bool destiny::core::cpu_manager::detail::CpuCore::wait(unsigned int time_ms) noexcept
{
        if (is_created_ == false)
        {
                return false;
        }
        if (is_joined_ == true)
        {
                return true;
        }

        int result;
        if (time_ms == std::numeric_limits<unsigned int>::max())
        {
                result = pthread_join(thread_, nullptr);
        }
        else if (time_ms == 0)
        {
                result = pthread_tryjoin_np(thread_, nullptr);
        }
        else
        {
                timespec timeout;
                if (clock_gettime(CLOCK_REALTIME, &timeout) != 0)
                {
                        return false;
                }
                timeout.tv_sec += time_ms / 1000;
                timeout.tv_nsec += (time_ms % 1000) * 1000000L;
                if (timeout.tv_nsec >= 1000000000L)
                {
                        timeout.tv_sec++;
                        timeout.tv_nsec -= 1000000000L;
                }
                result = pthread_timedjoin_np(thread_, nullptr, &timeout);
        }

        if (result == 0)
        {
                is_joined_ = true;
                return true;
        }
        return false;
}

inline void destiny::core::cpu_manager::detail::CpuCore::destroy() noexcept
{
        if (is_created_ == false)
        {
                return;
        }
        if (is_joined_ == false)
        {
                pthread_detach(thread_);
        }
        thread_     = {};
        is_created_ = false;
        is_joined_  = false;
        return;
}

inline void destiny::core::cpu_manager::detail::CpuCore::function_set(void (*function)()) noexcept
{
        function_.store(function, std::memory_order_release);
        function_.notify_one();
        return;
}

inline void* destiny::core::cpu_manager::detail::CpuCore::linux_thread_function_(void* lpParameter)
{
        const CpuCore* that    = (CpuCore*)lpParameter;
        void (*function)(void) = nullptr;
        while (true)
        {
                while (true)
                {
                        that->function_.wait(function, std::memory_order_acquire);
                        void (*function_cache)(void) = that->function_.load(std::memory_order_acquire);
                        if (function_cache != function)
                        {
                                function = function_cache;
                                break;
                        }
                }

                if (that->can_stop_.load(std::memory_order_acquire) == true)
                {
                        break;
                }

                if (function != nullptr)
                {
                        function();
                }
        }
        return nullptr;
}

#endif
