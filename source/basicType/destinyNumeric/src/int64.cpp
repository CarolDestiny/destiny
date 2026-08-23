#include "destiny/basicType/destinyNumeric/destinyNumeric.hpp"
using namespace destiny;

Int64::Int64() noexcept
{
    data_ = 0;
    return;
}

Int64::~Int64() noexcept
{
    return;
}

Int64::Int64(signed long long value) noexcept
{
    data_ = value;
    return;
}
Int64::Int64(const Int64& other) noexcept
{
    data_ = other.data_;
    return;
}

Int64::Int64(Int64&& other) noexcept
{
    data_ = other.data_;
    return;
}

Int64& Int64::operator=(const Int64& other) noexcept
{
    data_ = other.data_;
    return *this;
}

Int64& Int64::operator=(Int64&& other) noexcept
{
    data_ = other.data_;
    return *this;
}

signed long long Int64::value() const noexcept
{
    return data_;
}

Int64& Int64::operator+=(const Int64& other) noexcept
{
    data_ += other.data_;
    return *this;
}

Int64& Int64::operator-=(const Int64& other) noexcept
{
    data_ -= other.data_;
    return *this;
}

Int64& Int64::operator*=(const Int64& other) noexcept
{
    data_ *= other.data_;
    return *this;
}

Int64& Int64::operator/=(const Int64& other) noexcept
{
    data_ /= other.data_;
    return *this;
}

Int64& Int64::operator%=(const Int64& other) noexcept
{
    data_ %= other.data_;
    return *this;
}

Int64& Int64::operator&=(const Int64& other) noexcept
{
    data_ &= other.data_;
    return *this;
}

Int64& Int64::operator|=(const Int64& other) noexcept
{
    data_ |= other.data_;
    return *this;
}

Int64& Int64::operator^=(const Int64& other) noexcept
{
    data_ ^= other.data_;
    return *this;
}

Int64& Int64::operator<<=(const Int64& other) noexcept
{
    data_ <<= other.data_;
    return *this;
}

Int64& Int64::operator>>=(const Int64& other) noexcept
{
    data_ >>= other.data_;
    return *this;
}

Int64& Int64::operator++() noexcept
{
    ++data_;
    return *this;
}

Int64 Int64::operator++(int) noexcept
{
    Int64 tmp(*this);
    ++data_;
    return tmp;
}

Int64& Int64::operator--() noexcept
{
    --data_;
    return *this;
}

Int64 Int64::operator--(int) noexcept
{
    Int64 tmp(*this);
    --data_;
    return tmp;
}
