#include <bit>

#include "destiny/basicType/destinyNumeric/destinyNumeric.hpp"
using namespace destiny;

Float32::Float32() noexcept
{
    data_ = 0.0f;
    return;
}

Float32::Float32(float value) noexcept
{
    data_ = value;
    return;
}

Float32::Float32(const Float32& other) noexcept
{
    data_ = other.data_;
    return;
}

Float32::Float32(Float32&& other) noexcept
{
    data_ = other.data_;
    return;
}

Float32& Float32::operator=(const Float32& other) noexcept
{
    data_ = other.data_;
    return *this;
}

Float32& Float32::operator=(Float32&& other) noexcept
{
    data_ = other.data_;
    return *this;
}

float Float32::value() const noexcept
{
    return data_;
}

Float32& Float32::operator+=(const Float32& other) noexcept
{
    data_ += other.data_;
    return *this;
}

Float32& Float32::operator-=(const Float32& other) noexcept
{
    data_ -= other.data_;
    return *this;
}

Float32& Float32::operator*=(const Float32& other) noexcept
{
    data_ *= other.data_;
    return *this;
}

Float32& Float32::operator/=(const Float32& other) noexcept
{
    data_ /= other.data_;
    return *this;
}

Float32& Float32::operator++() noexcept
{
    data_ += 1.0f;
    return *this;
}

Float32 Float32::operator++(int) noexcept
{
    Float32 tmp(*this);
    data_ += 1.0f;
    return tmp;
}

Float32& Float32::operator--() noexcept
{
    data_ -= 1.0f;
    return *this;
}

Float32 Float32::operator--(int) noexcept
{
    Float32 tmp(*this);
    data_ -= 1.0f;
    return tmp;
}

Uint32 Float32::bits() const noexcept
{
    return Uint32(std::bit_cast<unsigned int>(data_));
}

Float32 Float32::fromBits(Uint32 b) noexcept
{
    return Float32(std::bit_cast<float>(b.value()));
}
