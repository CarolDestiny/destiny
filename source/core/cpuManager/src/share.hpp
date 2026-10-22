#pragma once

#include "destiny/core/cpuManager/cpu_manager.hpp"
#include "./thread_local_buffer/thread_local_buffer.hpp"
#include "./cpu_core/cpu_core.hpp"
#include "destiny/define/cpu/cpu.hpp"

namespace destiny::core::cpu_manager::detail {
        inline CpuCore cpuCores[destiny::define::cpu::logical_core_number];
        inline bool cpuCore_status[destiny::define::cpu::logical_core_number];
        // true means can be used

        inline thread_local uint32_t thread_id;
        inline ThreadLocalBuffer threadLocalBuffer[destiny::define::cpu::logical_core_number];
}
