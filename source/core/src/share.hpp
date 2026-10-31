#pragma once

#include "./native_thread/native_thread.hpp"
#include "./thread_local_buffer.hpp"
#include "destiny/define/cpu/cpu.hpp"

#include <cstdint>


namespace destiny::core::detail {
        inline thread_local uint32_t thread_id = 0;
        inline NativeThread          nativeThread[DESTINY_PYTHON_DEFINE_CPU_LOGICAL_CORE_NUMBER];
        inline std::atomic<bool>     nativeThread_status[DESTINY_PYTHON_DEFINE_CPU_LOGICAL_CORE_NUMBER]{};

        inline ThreadLocalBuffer threadLocalBuffer[DESTINY_DEFINE_CPU_LOGICAL_CORE_NUMBER];
}
