#pragma once

#include "destiny/define/cpu/_python.hpp"

namespace destiny::define::cpu {
    static constexpr unsigned int logical_core_number = DESTINY_PYTHON_DEFINE_CPU_LOGICAL_CORE_NUMBER;
    static constexpr unsigned int cacheline = DESTINY_PYTHON_DEFINE_CPU_CACHELINE;
}

#define DESTINY_DEFINE_CPU_LOGICAL_CORE_NUMBER DESTINY_PYTHON_DEFINE_CPU_LOGICAL_CORE_NUMBER
#define DESTINY_DEFINE_CPU_CACHELINE DESTINY_PYTHON_DEFINE_CPU_CACHELINE