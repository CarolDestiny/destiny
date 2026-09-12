#include "destiny/basicType/time/time.hpp"

using namespace destiny;

YearMonthDay::YearMonthDay(std::uint64_t year, std::uint8_t month, std::uint8_t day) noexcept
{
    year_ = year;
    month_ = month;
    day_ = day;
    return;
}

Year YearMonthDay::year() const noexcept
{
    return Year(year_);
}

Month YearMonthDay::month() const noexcept
{
    return Month(month_);
}

Day YearMonthDay::day() const noexcept
{
    return Day(day_);
}

YearMonthDay& YearMonthDay::operator+(const Duration<Year>& other) noexcept
{
    year_ += other.value();
    return *this;
}

YearMonthDay& YearMonthDay::operator+(const Duration<Month>& other) noexcept
{
    const std::int64_t cache = other.value() + month_;
    year_ += cache / 12;
    month_ = cache % 12;
    return *this;
}

YearMonthDay& YearMonthDay::operator+(const Duration<Day>& other) noexcept
{

}

YearMonthDay& YearMonthDay::operator-(const Duration<Year>& other) noexcept
{
    year_ -= other.value();
    return *this;
}

YearMonthDay& YearMonthDay::operator-(const Duration<Month>& other) noexcept
{

}

