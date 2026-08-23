#include "destiny/basicType/destinyNumeric/destinyNumeric.hpp"
using namespace destiny;

Int16::Int16() noexcept
{
    data_ = 0;
    return;
}

Int16::~Int16() noexcept
{
    return;
}

Int16::Int16(signed short value) noexcept
{
    data_ = value;
    return;
}
Int16::Int16(const Int16& other) noexcept
{
    data_ = other.data_;
    return;
}

Int16::Int16(Int16&& other) noexcept
{
    data_ = other.data_;
    return;
}

Int16& Int16::operator=(const Int16& other) noexcept
{
    data_ = other.data_;
    return *this;
}

Int16& Int16::operator=(Int16&& other) noexcept
{
    data_ = other.data_;
    return *this;
}

signed short Int16::value() const noexcept
{
    return data_;
}

Int16& Int16::operator+=(const Int16& other) noexcept
{
    data_ += other.data_;
    return *this;
}

Int16& Int16::operator-=(const Int16& other) noexcept
{
    data_ -= other.data_;
    return *this;
}

Int16& Int16::operator*=(const Int16& other) noexcept
{
    data_ *= other.data_;
    return *this;
}

Int16& Int16::operator/=(const Int16& other) noexcept
{
    data_ /= other.data_;
    return *this;
}

Int16& Int16::operator%=(const Int16& other) noexcept
{
    data_ %= other.data_;
    return *this;
}

Int16& Int16::operator&=(const Int16& other) noexcept
{
    data_ &= other.data_;
    return *this;
}

Int16& Int16::operator|=(const Int16& other) noexcept
{
    data_ |= other.data_;
    return *this;
}

Int16& Int16::operator^=(const Int16& other) noexcept
{
    data_ ^= other.data_;
    return *this;
}

Int16& Int16::operator<<=(const Int16& other) noexcept
{
    data_ <<= other.data_;
    return *this;
}

Int16& Int16::operator>>=(const Int16& other) noexcept
{
    data_ >>= other.data_;
    return *this;
}

Int16& Int16::operator++() noexcept
{
    ++data_;
    return *this;
}

Int16 Int16::operator++(int) noexcept
{
    Int16 tmp(*this);
    ++data_;
    return tmp;
}

Int16& Int16::operator--() noexcept
{
    --data_;
    return *this;
}

Int16 Int16::operator--(int) noexcept
{
    Int16 tmp(*this);
    --data_;
    return tmp;
}
