#pragma once

#include "destiny/define/platform/platform.hpp"

#if DESTINY_DEFINE_PLATFORM_WINDOWS == true

#include <atomic>
#include <windows.h>

namespace destiny::core::detail {
        class NativeThread {
        public:
                NativeThread() noexcept  = default;
                ~NativeThread() noexcept = default;

                NativeThread(const NativeThread&)            = delete;
                NativeThread& operator=(const NativeThread&) = delete;
                NativeThread(NativeThread&&)                 = delete;
                NativeThread& operator=(NativeThread&&)      = delete;

                [[nodiscard]] inline bool constructor() noexcept;
                inline void set_can_stop() noexcept;
                [[nodiscard]] inline bool wait(unsigned int time_ms) noexcept;
                [[nodiscard]] inline bool is_ready() noexcept;
                [[nodiscard]] inline bool destructor() noexcept;

                using Function = int (*)(int argc,char* argv[]) noexcept;
                [[nodiscard]] inline bool function_set(Function function,int argc,char* argv[]) noexcept;

        private:
                static DWORD WINAPI     win_thread_function_(LPVOID lpParameter);
                std::atomic<Function> function_{nullptr};
                std::atomic<int> argc_{0};
                std::atomic<char**> argv_{nullptr};
                std::atomic<bool>       can_stop_{false};
                std::atomic<bool> is_ready_{false};
                HANDLE                  hThread_{nullptr};
        };
}

inline bool destiny::core::detail::NativeThread::constructor() noexcept
{
        hThread_ = CreateThread(
                NULL,
                0,
                win_thread_function_,
                this,
                0,
                NULL
        );
        if (hThread_ == NULL)
        {
                return false;
        }
        is_ready_.store(true, std::memory_order_release);
        return true;
}

inline void destiny::core::detail::NativeThread::set_can_stop() noexcept
{
        can_stop_.store(true, std::memory_order_release);
        return;
}

inline bool destiny::core::detail::NativeThread::wait(unsigned int time_ms) noexcept
{
        const DWORD result = WaitForSingleObject(hThread_, time_ms);
        if (result == WAIT_OBJECT_0)
        {
                return true;
        }
        return false;
}

inline bool destiny::core::detail::NativeThread::is_ready() noexcept
{
        return is_ready_.load(std::memory_order_acquire);
}

inline bool destiny::core::detail::NativeThread::destructor() noexcept
{
        if (hThread_ == nullptr) [[unlikely]]
        {
                return true;
        }

        const DWORD res = WaitForSingleObject(hThread_,0);
        if (res != WAIT_OBJECT_0)
        {
                return false;
        }

        if (CloseHandle(hThread_) == FALSE)
        {
                return false;
        }
        hThread_ = nullptr;
        return true;
}

inline bool destiny::core::detail::NativeThread::function_set(Function function,int argc,char* argv[]) noexcept
{
        if (function == nullptr) [[unlikely]]
        {
                return false;
        }

        bool expected = true;
        const bool res = is_ready_.compare_exchange_strong(expected,false,std::memory_order_acquire,std::memory_order_relaxed);
        if (res == false) [[unlikely]]
        {
                return false;
        }
        argc_.store(argc,std::memory_order_relaxed);
        argv_.store(argv,std::memory_order_relaxed);
        function_.store(function,std::memory_order_release);
        function_.notify_one();
        return true;

}

inline DWORD destiny::core::detail::NativeThread::win_thread_function_(LPVOID lpParameter)
{
        NativeThread* that    = (NativeThread*)lpParameter;
        // exec until can_stop_ == true
        while (true)
        {
                // Wait until the reserved task has been published.
                that->function_.wait(nullptr,std::memory_order_acquire);

                // exec function
                const Function function = that->function_.load(std::memory_order_acquire);
                const int argc = that->argc_.load(std::memory_order_relaxed);
                char** argv = that->argv_.load(std::memory_order_relaxed);
                function(argc,argv);
                that->function_.store(nullptr,std::memory_order_relaxed);

                if (that->can_stop_.load(std::memory_order::acquire) == true) [[unlikely]]
                {
                        break;
                }

                that->is_ready_.store(true,std::memory_order_release);
        }
        return 0;
}

#endif
