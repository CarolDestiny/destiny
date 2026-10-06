#include "./share.hpp"
#include "destiny/core/cpuAlloc/best_efficiency_cpu_core.hpp"

bool destiny::core::cpu_alloc::alloc(BestEfficiencyCpuCore& bestEfficiencyCpuCore) noexcept {
    bestEfficiencyCpuCore.cpuCore_ = (void*)(&(detail::cpuCore_buffer[0]));
    return true;
}

void destiny::core::cpu_alloc::dealloc(BestEfficiencyCpuCore& bestEfficiencyCpuCore) noexcept {
    // TODO: safe function
    return;
}

void destiny::core::cpu_alloc::BestEfficiencyCpuCore::function_set(void (*function)()) noexcept {
    const auto cpuCore = (detail::CpuCore*)cpuCore_;
    cpuCore->function_set(function);
    return;
}