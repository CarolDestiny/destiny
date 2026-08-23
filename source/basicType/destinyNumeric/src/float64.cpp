#include <bit>

#include "destiny/basicType/destinyNumeric/destinyNumeric.hpp"
using namespace destiny;

Float64::Float64() noexcept
{
    data_ = 0.0;
    return;
}

Float64::Float64(double value) noexcept
{
    data_ = value;
    return;
}

Float64::Float64(const Float64& other) noexcept
{
    data_ = other.data_;
    return;
}

Float64::Float64(Float64&& other) noexcept
{
    data_ = other.data_;
    return;
}

Float64& Float64::operator=(const Float64& other) noexcept
{
    data_ = other.data_;
    return *this;
}

Float64& Float64::operator=(Float64&& other) noexcept
{
    data_ = other.data_;
    return *this;
}

double Float64::value() const noexcept
{
    return data_;
}

Float64& Float64::operator+=(const Float64& other) noexcept
{
    data_ += other.data_;
    return *this;
}

Float64& Float64::operator-=(const Float64& other) noexcept
{
    data_ -= other.data_;
    return *this;
}

Float64& Float64::operator*=(const Float64& other) noexcept
{
    data_ *= other.data_;
    return *this;
}

Float64& Float64::operator/=(const Float64& other) noexcept
{
    data_ /= other.data_;
    return *this;
}

Float64& Float64::operator++() noexcept
{
    data_ += 1.0;
    return *this;
}

Float64 Float64::operator++(int) noexcept
{
    Float64 tmp(*this);
    data_ += 1.0;
    return tmp;
}

Float64& Float64::operator--() noexcept
{
    data_ -= 1.0;
    return *this;
}

Float64 Float64::operator--(int) noexcept
{
    Float64 tmp(*this);
    data_ -= 1.0;
    return tmp;
}

Uint64 Float64::bits() const noexcept
{
    return Uint64(std::bit_cast<unsigned long long>(data_));
}

Float64 Float64::fromBits(Uint64 b) noexcept
{
    return Float64(std::bit_cast<double>(b.value()));
}
