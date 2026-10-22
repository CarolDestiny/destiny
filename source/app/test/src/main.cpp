#include "destiny/core/cpuManager/cpu_manager.hpp"

#include <iostream>

#include <windows.h>

using namespace std;

static void function1(destiny::core::cpu_manager::CoroutineBase& coroutineBase) noexcept
{
        static int a = 0;
        printf("this is function one: %d\n", a++);

        coroutineBase.set_estimate_next_cycle(10);

        if (a > 10)
        {
                coroutineBase.set_is_finish();
        }
        return;
}

int main()
{
        destiny::core::cpu_manager::onload();

        destiny::core::cpu_manager::BestEfficiencyCpuCore cpuCore;
        destiny::core::cpu_manager::alloc(cpuCore);

        {
                destiny::core::cpu_manager::CoroutinePeriodic coroutinePeriodic;
                coroutinePeriodic.set_next_function(function1);
                coroutinePeriodic.set_estimate_next_cycle(10);
                coroutinePeriodic.set_duration(100);
                destiny::this_thread::coroutineManager().add(coroutinePeriodic);
        }

        destiny::this_thread::coroutineManager().exec();
        Sleep(10000);
        destiny::core::cpu_manager::dealloc(cpuCore);
        destiny::core::cpu_manager::unload();

        return 0;
}
