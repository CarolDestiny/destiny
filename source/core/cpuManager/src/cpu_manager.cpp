#include "destiny/core/cpuManager/cpu_manager.hpp"
#include "./share.hpp"

uint32_t destiny::core::cpu_manager::id() noexcept
{
        return detail::thread_id;
}

destiny::core::cpu_manager::CoroutineManager& destiny::core::cpu_manager::coroutineManager() noexcept
{
        return detail::threadLocalBuffer[detail::thread_id].coroutineManager;
}

destiny::core::cpu_manager::CoroutineManager& destiny::core::cpu_manager::coroutineManager(uint32_t thread_id) noexcept
{
        return detail::threadLocalBuffer[thread_id].coroutineManager;
}