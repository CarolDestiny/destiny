#include "destiny/core/cpuManager/best_efficiency_cpu_core.hpp"

#include "./share.hpp"

bool destiny::core::cpu_manager::alloc(BestEfficiencyCpuCore& bestEfficiencyCpuCore) noexcept
{
        int index = -1;
        for (int i = 0; i < destiny::define::cpu::logical_core_number; i++)
        {
                if (detail::cpuCore_status[i] == true)
                {
                        index = i;
                        break;
                }
        }
        if (index == -1)
        {
                return false;
        }
        detail::cpuCore_status[index]  = false;
        bestEfficiencyCpuCore.cpuCore_ = (void*)(&detail::cpuCores[index]);
        return true;
}

void destiny::core::cpu_manager::dealloc(BestEfficiencyCpuCore& bestEfficiencyCpuCore) noexcept
{
        int index = -1;
        for (int i = 0; i < destiny::define::cpu::logical_core_number; i++)
        {
                if (bestEfficiencyCpuCore.cpuCore_ == (void*)(&detail::cpuCores[i]))
                {
                        index = i;
                }
        }
        detail::cpuCore_status[index] = true;
        // TODO: safe function
        return;
}

void destiny::core::cpu_manager::BestEfficiencyCpuCore::function_set(void (*function)()) noexcept
{
        const auto cpuCore = (detail::CpuCore*)cpuCore_;
        cpuCore->function_set(function);
        return;
}
