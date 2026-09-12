#pragma once
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
        template <AutoConvertDurationType T, AutoConvertDurationType U>
        using ResType = std::conditional_t<(scale<T>::value < scale<U>::value), T, U>;
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

#define DESTINY_BASICTYPE_TIME_AUTO_CLASS(NAME)                                                                        \
    class destiny::NAME {                                                                                              \
    public:                                                                                                            \
        NAME() noexcept = default;                                                                                     \
        ~NAME() noexcept = default;                                                                                    \
        NAME(const NAME&) noexcept = default;                                                                          \
        NAME& operator=(const NAME&) noexcept = default;                                                               \
        NAME(std::uint64_t value) noexcept : value_{value} {}                                                          \
        std::uint64_t value() const noexcept { return value_; };                                                       \
                                                                                                                       \
    private:                                                                                                           \
        std::uint64_t value_{0};                                                                                       \
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
public:
    Duration() noexcept = default;
    ~Duration() noexcept = default;
    Duration(const Duration&) noexcept = default;
    Duration(std::int64_t value) noexcept { value_ = value; }
    Duration& operator=(const Duration&) noexcept = default;
    std::int64_t value() const noexcept { return value_; }
    Duration<Second> toSecond() const noexcept
        requires destiny::basicType::time::detail::AutoConvertDurationType<T>
    {
        return Duration<Second>(value_ * destiny::basicType::time::detail::scale<T>::value);
    }

private:
    std::int64_t value_{0};
};

template <destiny::basicType::time::detail::DurationType T>
inline T operator+(const T& a, const destiny::Duration<T>& b) noexcept
{
    return T(a.value() + b.value());
}

template <destiny::basicType::time::detail::DurationType T>
inline T operator+(const destiny::Duration<T>& a, const T& b) noexcept
{
    return T(a.value() + b.value());
}

template <destiny::basicType::time::detail::DurationType T>
inline destiny::Duration<T> operator+(const destiny::Duration<T>& a, const destiny::Duration<T>& b) noexcept
{
    return destiny::Duration<T>(a.value() + b.value());
}

template <destiny::basicType::time::detail::DurationType T>
inline T operator-(const T& a, const destiny::Duration<T>& b) noexcept
{
    return T(a.value() - b.value());
}

template <destiny::basicType::time::detail::DurationType T>
inline T operator-(const destiny::Duration<T>& a, const T& b) noexcept
{
    return T(a.value() - b.value());
}

template <destiny::basicType::time::detail::DurationType T>
inline destiny::Duration<T> operator-(const destiny::Duration<T>& a, const destiny::Duration<T>& b) noexcept
{
    return destiny::Duration<T>(a.value() - b.value());
}

template <destiny::basicType::time::detail::AutoConvertDurationType T,
          destiny::basicType::time::detail::AutoConvertDurationType U>
    requires(!std::is_same_v<T, U>)
inline destiny::basicType::time::detail::ResType<T, U> operator+(const T& a, const destiny::Duration<U>& b) noexcept
{
    using resType = destiny::basicType::time::detail::ResType<T, U>;
    const auto total =
        static_cast<std::int64_t>(a.value()) * destiny::basicType::time::detail::scale<T>::value + b.toSecond().value();
    return resType(total / destiny::basicType::time::detail::scale<resType>::value);
}

; // clang-format off
template <destiny::basicType::time::detail::AutoConvertDurationType T,
          destiny::basicType::time::detail::AutoConvertDurationType U>
    requires(!std::is_same_v<T, U>)
inline destiny::basicType::time::detail::ResType<T, U>
operator+(const destiny::Duration<T>& a, const U& b) noexcept
{
    using resType = destiny::basicType::time::detail::ResType<T, U>;
    const auto total =
        a.toSecond().value() + static_cast<std::int64_t>(b.value()) * destiny::basicType::time::detail::scale<U>::value;
    return resType(total / destiny::basicType::time::detail::scale<resType>::value);
}
; // clang-format on

template <destiny::basicType::time::detail::AutoConvertDurationType T,
          destiny::basicType::time::detail::AutoConvertDurationType U>
    requires(!std::is_same_v<T, U>)
inline destiny::Duration<destiny::basicType::time::detail::ResType<T, U>>
operator+(const destiny::Duration<T>& a, const destiny::Duration<U>& b) noexcept
{
    using resType = destiny::basicType::time::detail::ResType<T, U>;
    const auto total = a.toSecond().value() + b.toSecond().value();
    return destiny::Duration<resType>{total / destiny::basicType::time::detail::scale<resType>::value};
}

template <destiny::basicType::time::detail::AutoConvertDurationType T,
          destiny::basicType::time::detail::AutoConvertDurationType U>
    requires(!std::is_same_v<T, U>)
inline destiny::basicType::time::detail::ResType<T, U> operator-(const T& a, const destiny::Duration<U>& b) noexcept
{
    using resType = destiny::basicType::time::detail::ResType<T, U>;
    const auto total =
        static_cast<std::int64_t>(a.value()) * destiny::basicType::time::detail::scale<T>::value - b.toSecond().value();
    return resType(total / destiny::basicType::time::detail::scale<resType>::value);
}

template <destiny::basicType::time::detail::AutoConvertDurationType T,
          destiny::basicType::time::detail::AutoConvertDurationType U>
    requires(!std::is_same_v<T, U>)
inline destiny::basicType::time::detail::ResType<T, U> operator-(const destiny::Duration<T>& a, const U& b) noexcept
{
    using resType = destiny::basicType::time::detail::ResType<T, U>;
    const auto total =
        a.toSecond().value() - static_cast<std::int64_t>(b.value()) * destiny::basicType::time::detail::scale<U>::value;
    return resType(total / destiny::basicType::time::detail::scale<resType>::value);
}

template <destiny::basicType::time::detail::AutoConvertDurationType T,
          destiny::basicType::time::detail::AutoConvertDurationType U>
    requires(!std::is_same_v<T, U>)
inline destiny::Duration<destiny::basicType::time::detail::ResType<T, U>>
operator-(const destiny::Duration<T>& a, const destiny::Duration<U>& b) noexcept
{
    using resType = destiny::basicType::time::detail::ResType<T, U>;
    const auto total = a.toSecond().value() - b.toSecond().value();
    return destiny::Duration<resType>{total / destiny::basicType::time::detail::scale<resType>::value};
}

class destiny::YearMonthDay {
public:
    YearMonthDay() noexcept = default;
    ~YearMonthDay() noexcept = default;
    YearMonthDay(const YearMonthDay&) noexcept = default;
    YearMonthDay& operator=(const YearMonthDay&) noexcept = default;
    YearMonthDay(std::uint64_t year, std::uint8_t month, std::uint8_t day) noexcept;
    Year year() const noexcept;
    Month month() const noexcept;
    Day day() const noexcept;

    YearMonthDay& operator+(const Duration<Year>& other) noexcept;
    YearMonthDay& operator+(const Duration<Month>& other) noexcept;
    YearMonthDay& operator+(const Duration<Day>& other) noexcept;
    YearMonthDay& operator-(const Duration<Year>& other) noexcept;
    YearMonthDay& operator-(const Duration<Month>& other) noexcept;
    YearMonthDay& operator-(const Duration<Day>& other) noexcept;

private:
    std::uint64_t year_{0};
    std::uint8_t month_{0};
    std::uint8_t day_{0};
};