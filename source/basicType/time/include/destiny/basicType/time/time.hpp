#pragma once
#include "time.hpp"
#include <cstdint>
#include <string>
#include <type_traits>

namespace destiny {
    class UtcTime;
    class LocalZone;
    class ZoneTime;
    class Year;
    class Month;
    class Day;
    class Hour;
    class Minute;
    class Second;
    class YearMonthDay;
    class YearMonthDayHourMinuteSecond;
    class HourMinuteSecond;
    namespace basicType::time::detail {
        ; // clang-format off
        template <typename T>
        concept DurationType =
            std::is_same_v<T, Year> ||
            std::is_same_v<T, Month> ||
            std::is_same_v<T, Day> ||
            std::is_same_v<T, Hour> ||
            std::is_same_v<T, Minute> ||
            std::is_same_v<T, Second>;

        template <typename T>
        concept AutoConvertDurationType =
            std::is_same_v<T, Day> ||
            std::is_same_v<T, Hour> ||
            std::is_same_v<T, Minute> ||
            std::is_same_v<T, Second>;

        template <typename T> struct scale;
        template <> struct scale<Day> { static constexpr std::int64_t value = 86'400; };
        template <> struct scale<Hour> {  static constexpr std::int64_t value = 3'600; };
        template <> struct scale<Minute> { static constexpr std::int64_t value = 60; };
        template <> struct scale<Second> { static constexpr std::int64_t value = 1; };

        ; // clang-format on
    }

    template <basicType::time::detail::DurationType T>
    class Duration;
}

class destiny::UtcTime {
public:
    UtcTime() noexcept = default;
    ~UtcTime() noexcept = default;
    UtcTime(const UtcTime&) noexcept = default;
    UtcTime& operator=(const UtcTime&) noexcept = default;
    static UtcTime now() noexcept;
    std::uint64_t value() const noexcept;

private:
    std::uint64_t value_{0};
};

class destiny::LocalZone {
public:
    friend class ZoneTime;
    LocalZone() noexcept = default;
    ~LocalZone() noexcept = default;
    LocalZone(const LocalZone&) noexcept = default;
    LocalZone& operator=(const LocalZone&) noexcept = default;
    bool setZone(const std::string& zoneName) noexcept;

private:
    std::int32_t offset_{0};
};

class destiny::ZoneTime {
public:
    ZoneTime() noexcept = default;
    ~ZoneTime() noexcept = default;
    ZoneTime(const ZoneTime&) noexcept = default;
    ZoneTime(const UtcTime& utcTime, const LocalZone& localZone = LocalZone()) noexcept;
    ZoneTime& operator=(const ZoneTime&) noexcept = default;
    std::uint64_t value() const noexcept;

private:
    std::uint64_t value_{0};
};

#define DESTINY_BASICTYPE_TIME_AUTO_CLASS(NAME) \
    class destiny::NAME {\
    public:\
        NAME() noexcept = default;\
        ~NAME() noexcept = default;\
        NAME(const NAME&) noexcept = default;\
        NAME& operator=(const NAME&) noexcept = default;\
        std::uint64_t value() const noexcept { return value_; };\
    private:\
        std::uint64_t value_{0};\
    }
DESTINY_BASICTYPE_TIME_AUTO_CLASS(Year);
DESTINY_BASICTYPE_TIME_AUTO_CLASS(Month);
DESTINY_BASICTYPE_TIME_AUTO_CLASS(Day);
DESTINY_BASICTYPE_TIME_AUTO_CLASS(Hour);
DESTINY_BASICTYPE_TIME_AUTO_CLASS(Minute);
DESTINY_BASICTYPE_TIME_AUTO_CLASS(Second);
#undef DESTINY_BASICTYPE_TIME_AUTO_CLASS

template <destiny::basicType::time::detail::DurationType T>
class destiny::Duration {
    
};