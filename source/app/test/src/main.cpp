#include <iostream>
#include <windows.h>

#include "destiny/core/cpuManager/cpu_manager.hpp"
#include "destiny/core/cpuManager/best_efficiency_cpu_core.hpp"

using namespace std;

static void function1() noexcept {
    printf("Hello destiny more thread\n");
    return;
}

int main() {
    destiny::core::cpu_manager::onload();
    destiny::core::cpu_manager::BestEfficiencyCpuCore cpuCore;
    destiny::core::cpu_manager::alloc(cpuCore);
    cpuCore.function_set(function1);
    Sleep(1000);
    destiny::core::cpu_manager::dealloc(cpuCore);
    destiny::core::cpu_manager::unload();
    return 0;
}