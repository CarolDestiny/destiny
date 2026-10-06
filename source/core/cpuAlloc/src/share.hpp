#pragma once

#include "destiny/core/cpuAlloc/cpu_alloc.hpp"

#include "./cpuCore/cpu_core.hpp"

#include "destiny/define/cpu/cpu.hpp"

namespace destiny::core::cpu_alloc::detail {
    inline CpuCore cpuCore_buffer[destiny::define::cpu::logical_core_number];
    inline void* cpuCore_local_data[destiny::define::cpu::logical_core_number][8];
}