#include "destiny/basicType/time/time.hpp"

using namespace  destiny;

ZoneTime::ZoneTime(const UtcTime& utcTime, const LocalZone& localZone) noexcept
{
    value_ = utcTime.value() + localZone.offset_;
    return;
}

std::uint64_t ZoneTime::value() const noexcept
{
    return value_;
}