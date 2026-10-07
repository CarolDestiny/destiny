#pragma once

#include "destiny/define/platform/platform.hpp"

#if DESTINY_DEFINE_PLATFORM_WINDOWS == true

#include <windows.h>
#include <atomic>

namespace destiny::core::cpu_manager::detail {
    class CpuCore {
    public:
        CpuCore() noexcept = default;
        ~CpuCore() noexcept = default;

        CpuCore(const CpuCore&) = delete;
        CpuCore& operator=(const CpuCore&) = delete;
        CpuCore(CpuCore&&) = delete;
        CpuCore& operator=(CpuCore&&) = delete;

        inline bool create() noexcept;
        inline void stop_set() noexcept;
        inline bool wait(unsigned int time_ms) noexcept;
        inline void destroy() noexcept;

        inline void function_set(void (*function)()) noexcept;
    private:
        static DWORD WINAPI win_thread_function_(LPVOID lpParameter);
        std::atomic<void (*)()> function_{nullptr};
        std::atomic<bool> can_stop_{false};
        HANDLE hThread_;
    };
}

inline bool destiny::core::cpu_manager::detail::CpuCore::create() noexcept {
    hThread_ = CreateThread(
        NULL,
        0,
        win_thread_function_,
        this,
        0,
        NULL
    );
    if (hThread_ == NULL) {
        return false;
    }
    return true;
}

inline void destiny::core::cpu_manager::detail::CpuCore::stop_set() noexcept {
    can_stop_.store(true,std::memory_order_release);
    return;
}

inline bool destiny::core::cpu_manager::detail::CpuCore::wait(unsigned int time_ms) noexcept {
    const DWORD result = WaitForSingleObject(hThread_,time_ms);
    if (result == WAIT_OBJECT_0) {
        return true;
    }
    return false;
}

inline void destiny::core::cpu_manager::detail::CpuCore::destroy() noexcept {
    CloseHandle(hThread_);
    hThread_ = NULL;
}

inline void destiny::core::cpu_manager::detail::CpuCore::function_set(void (*function)()) noexcept {
    function_.store(function,std::memory_order_release);
    function_.notify_one();
    return;
}

inline DWORD destiny::core::cpu_manager::detail::CpuCore::win_thread_function_(LPVOID lpParameter) {
    const CpuCore* that = (CpuCore*)lpParameter;
    void (*function)(void) = nullptr;
    while (true) {
        while (true) {
            that->function_.wait(function,std::memory_order_acquire);
            void (*function_cache)(void) = that->function_.load(std::memory_order_acquire);
            if (function_cache != function) {
                function = function_cache;
                break;
            }
        }

        if (that->can_stop_.load(std::memory_order_acquire) == true) {
            break;
        }

        function();
    }
    return 0;
}

#endif
