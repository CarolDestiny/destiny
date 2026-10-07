#include "./share.hpp"
#include "destiny/core/cpuManager/best_efficiency_cpu_core.hpp"

bool destiny::core::cpu_manager::alloc(BestEfficiencyCpuCore& bestEfficiencyCpuCore) noexcept {
    bestEfficiencyCpuCore.cpuCore_ = (void*)(&(detail::cpuCore_buffer[0]));
    return true;
}

void destiny::core::cpu_manager::dealloc(BestEfficiencyCpuCore& bestEfficiencyCpuCore) noexcept {
    // TODO: safe function
    return;
}

void destiny::core::cpu_manager::BestEfficiencyCpuCore::function_set(void (*function)()) noexcept {
    const auto cpuCore = (detail::CpuCore*)cpuCore_;
    cpuCore->function_set(function);
    return;
}