#pragma once

namespace destiny::core::cpu_alloc {
    class BestPerformanceCpuCore;

    bool alloc(BestPerformanceCpuCore& bestPerformanceCpuCore) noexcept;
    void dealloc(BestPerformanceCpuCore& bestPerformanceCpuCore) noexcept;
};