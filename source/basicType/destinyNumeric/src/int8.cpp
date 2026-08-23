#include "destiny/basicType/destinyNumeric/destinyNumeric.hpp"
using namespace destiny;

Int8::Int8() noexcept
{
    data_ = 0;
    return;
}

Int8::~Int8() noexcept
{
    return;
}

Int8::Int8(signed char value) noexcept
{
    data_ = value;
    return;
}
Int8::Int8(const Int8& other) noexcept
{
    data_ = other.data_;
    return;
}

Int8::Int8(Int8&& other) noexcept
{
    data_ = other.data_;
    return;
}

Int8& Int8::operator=(const Int8& other) noexcept
{
    data_ = other.data_;
    return *this;
}

Int8& Int8::operator=(Int8&& other) noexcept
{
    data_ = other.data_;
    return *this;
}

signed char Int8::value() const noexcept
{
    return data_;
}

Int8& Int8::operator+=(const Int8& other) noexcept
{
    data_ += other.data_;
    return *this;
}

Int8& Int8::operator-=(const Int8& other) noexcept
{
    data_ -= other.data_;
    return *this;
}

Int8& Int8::operator*=(const Int8& other) noexcept
{
    data_ *= other.data_;
    return *this;
}

Int8& Int8::operator/=(const Int8& other) noexcept
{
    data_ /= other.data_;
    return *this;
}

Int8& Int8::operator%=(const Int8& other) noexcept
{
    data_ %= other.data_;
    return *this;
}

Int8& Int8::operator&=(const Int8& other) noexcept
{
    data_ &= other.data_;
    return *this;
}

Int8& Int8::operator|=(const Int8& other) noexcept
{
    data_ |= other.data_;
    return *this;
}

Int8& Int8::operator^=(const Int8& other) noexcept
{
    data_ ^= other.data_;
    return *this;
}

Int8& Int8::operator<<=(const Int8& other) noexcept
{
    data_ <<= other.data_;
    return *this;
}

Int8& Int8::operator>>=(const Int8& other) noexcept
{
    data_ >>= other.data_;
    return *this;
}

Int8& Int8::operator++() noexcept
{
    ++data_;
    return *this;
}

Int8 Int8::operator++(int) noexcept
{
    Int8 tmp(*this);
    ++data_;
    return tmp;
}

Int8& Int8::operator--() noexcept
{
    --data_;
    return *this;
}

Int8 Int8::operator--(int) noexcept
{
    Int8 tmp(*this);
    --data_;
    return tmp;
}
