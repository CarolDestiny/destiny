#include "destiny/basicType/destinyNumeric/destinyNumeric.hpp"
using namespace destiny;

Int32::Int32() noexcept
{
    data_ = 0;
    return;
}

Int32::~Int32() noexcept
{
    return;
}

Int32::Int32(signed int value) noexcept
{
    data_ = value;
    return;
}
Int32::Int32(const Int32& other) noexcept
{
    data_ = other.data_;
    return;
}

Int32::Int32(Int32&& other) noexcept
{
    data_ = other.data_;
    return;
}

Int32& Int32::operator=(const Int32& other) noexcept
{
    data_ = other.data_;
    return *this;
}

Int32& Int32::operator=(Int32&& other) noexcept
{
    data_ = other.data_;
    return *this;
}

signed int Int32::value() const noexcept
{
    return data_;
}

Int32& Int32::operator+=(const Int32& other) noexcept
{
    data_ += other.data_;
    return *this;
}

Int32& Int32::operator-=(const Int32& other) noexcept
{
    data_ -= other.data_;
    return *this;
}

Int32& Int32::operator*=(const Int32& other) noexcept
{
    data_ *= other.data_;
    return *this;
}

Int32& Int32::operator/=(const Int32& other) noexcept
{
    data_ /= other.data_;
    return *this;
}

Int32& Int32::operator%=(const Int32& other) noexcept
{
    data_ %= other.data_;
    return *this;
}

Int32& Int32::operator&=(const Int32& other) noexcept
{
    data_ &= other.data_;
    return *this;
}

Int32& Int32::operator|=(const Int32& other) noexcept
{
    data_ |= other.data_;
    return *this;
}

Int32& Int32::operator^=(const Int32& other) noexcept
{
    data_ ^= other.data_;
    return *this;
}

Int32& Int32::operator<<=(const Int32& other) noexcept
{
    data_ <<= other.data_;
    return *this;
}

Int32& Int32::operator>>=(const Int32& other) noexcept
{
    data_ >>= other.data_;
    return *this;
}

Int32& Int32::operator++() noexcept
{
    ++data_;
    return *this;
}

Int32 Int32::operator++(int) noexcept
{
    Int32 tmp(*this);
    ++data_;
    return tmp;
}

Int32& Int32::operator--() noexcept
{
    --data_;
    return *this;
}

Int32 Int32::operator--(int) noexcept
{
    Int32 tmp(*this);
    --data_;
    return tmp;
}
