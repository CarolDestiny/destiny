#include "destiny/basicType/time/time.hpp"
#include <chrono>

using namespace destiny;

bool LocalZone::setZone(const std::string& zoneName) noexcept
{
    try {
        const auto* tz = std::chrono::locate_zone(zoneName);
        const auto now = std::chrono::system_clock::now();
        offset_ = static_cast<std::int32_t>(tz->get_info(now).offset.count());
        return true;
    } catch (const std::runtime_error&) {
        offset_ = 0;
        return false;
    }
}