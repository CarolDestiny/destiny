#include "destiny/core/core.hpp"
#include "./share.hpp"

void destiny::core::unload() noexcept
{
        for (int64_t i = 0;i < DESTINY_PYTHON_DEFINE_CPU_LOGICAL_CORE_NUMBER;i++)
        {
                detail::threadLocalBuffer[i].destructor();
        }
        return;
}