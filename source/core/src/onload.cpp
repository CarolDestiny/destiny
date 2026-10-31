#include "destiny/core/core.hpp"
#include "./share.hpp"

bool destiny::core::onload() noexcept
{
        for (int64_t i = 0;i < DESTINY_PYTHON_DEFINE_CPU_LOGICAL_CORE_NUMBER;i++)
        {
                const bool res = detail::threadLocalBuffer[i].constructor();
                if (res == false) [[unlikely]]
                {
                        unload();
                        return false;
                }
        }
        return true;
}


