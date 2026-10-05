#include "./share.hpp"
#include "destiny/core/cpuAlloc/best_efficiency_cpu_core.hpp"

bool destiny::core::cpu_alloc::alloc(BestEfficiencyCpuCore& bestEfficiencyCpuCore) noexcept {
    bestEfficiencyCpuCore.cpuCore_ = new detail::CpuCore();
    const auto cpuCore = (detail::CpuCore*)bestEfficiencyCpuCore.cpuCore_;
    cpuCore->create();
    return true;
}

void destiny::core::cpu_alloc::dealloc(BestEfficiencyCpuCore& bestEfficiencyCpuCore) noexcept {
    const auto cpuCore = (detail::CpuCore*)bestEfficiencyCpuCore.cpuCore_;
    cpuCore->stop_set();
    cpuCore->function_set(nullptr);
    cpuCore->wait(10000);
    cpuCore->destroy();
    return;
}

void destiny::core::cpu_alloc::BestEfficiencyCpuCore::function_set(void (*function)()) noexcept {
    const auto cpuCore = (detail::CpuCore*)cpuCore_;
    cpuCore->function_set(function);
    return;
}