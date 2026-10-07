#pragma once

#include "./best_efficiency_cpu_core.hpp"
#include "./best_performance_cpu_core.hpp"

namespace destiny::core::cpu_manager {
    bool onload() noexcept;
    void unload() noexcept;
}

namespace destiny {

}