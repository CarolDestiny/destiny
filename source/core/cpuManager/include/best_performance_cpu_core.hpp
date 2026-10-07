#pragma once

namespace destiny::core::cpu_manager {
    class BestPerformanceCpuCore;

    bool alloc(BestPerformanceCpuCore& bestPerformanceCpuCore) noexcept;
    void dealloc(BestPerformanceCpuCore& bestPerformanceCpuCore) noexcept;
};