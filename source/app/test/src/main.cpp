#include <iostream>
#include <windows.h>

#include "destiny/core/cpuAlloc/best_efficiency_cpu_core.hpp"

using namespace std;

void function1() noexcept {
    printf("Hello destiny more thread\n");
    return;
}

int main() {
    destiny::core::cpu_alloc::BestEfficiencyCpuCore cpuCore;
    destiny::core::cpu_alloc::alloc(cpuCore);
    cpuCore.function_set(function1);
    Sleep(1000);
    destiny::core::cpu_alloc::dealloc(cpuCore);
    return 0;
}