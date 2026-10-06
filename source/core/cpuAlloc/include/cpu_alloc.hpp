#pragma once

#include "./best_efficiency_cpu_core.hpp"
#include "./best_performance_cpu_core.hpp"

namespace destiny::core::cpu_alloc {
    bool onload() noexcept;
    void unload() noexcept;
}

namespace destiny {

}