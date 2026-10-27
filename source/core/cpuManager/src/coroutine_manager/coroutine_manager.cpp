#include "destiny/core/cpuManager/coroutine_manager.hpp"
#include "../share.hpp"

#include <chrono>


void destiny::core::cpu_manager::CoroutineManager::function_maintain(CoroutineBase& coroutineBase) noexcept
{

}

bool destiny::core::cpu_manager::CoroutineManager::exec() noexcept
{

        // add maintain function
        {
                CoroutineRegular coroutineRegular;
                coroutineRegular.set_next_function(function_maintain);
                coroutineRegular.set_estimate_next_cycle(1);
                coroutineRegular.slot0() = this;
                coroutineRegular.set_priority(CoroutineRegular::Priority::high);
                // add(coroutineRegular);
        }

        //
        while (true)
        {
                
        }
        return true;
}

