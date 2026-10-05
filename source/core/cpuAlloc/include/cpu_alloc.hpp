#pragma once

#include "./best_efficiency_cpu_core.hpp"
#include "./best_performance_cpu_core.hpp"

namespace destiny::core::cpu_alloc {
    bool onload() noexcept;
    void unload() noexcept;
}

namespace destiny {
    using core::cpu_alloc::BestPerformanceCpuCore;
    using core::cpu_alloc::BestEfficiencyCpuCore;
    using core::cpu_alloc::alloc;
    using core::cpu_alloc::dealloc;
}