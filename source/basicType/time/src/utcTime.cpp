#include "destiny/basicType/time/time.hpp"
#include <chrono>

using namespace destiny;

UtcTime UtcTime::now() noexcept
{
    UtcTime res;
    ; // clang-format off
    res.value_ = static_cast<std::uint64_t>(
        std::chrono::duration_cast<std::chrono::seconds>(
            std::chrono::system_clock::now().time_since_epoch()
            ).count()
        );
    ; // clang-format on
    return res;
}

std::uint64_t UtcTime::value() const noexcept
{
    return value_;
}

