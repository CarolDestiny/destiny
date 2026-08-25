#include "destiny/basicType/destinyNumeric/destinyNumeric.hpp"
using namespace destiny;

Uint8::Uint8() noexcept
{
    data_ = 0;
    return;
}

Uint8::~Uint8() noexcept
{
    return;
}

Uint8::Uint8(unsigned char value) noexcept
{
    data_ = value;
    return;
}
Uint8::Uint8(const Uint8& other) noexcept
{
    data_ = other.data_;
    return;
}

Uint8::Uint8(Uint8&& other) noexcept
{
    data_ = other.data_;
    return;
}

Uint8& Uint8::operator=(const Uint8& other) noexcept
{
    data_ = other.data_;
    return *this;
}

Uint8& Uint8::operator=(Uint8&& other) noexcept
{
    data_ = other.data_;
    return *this;
}

unsigned char Uint8::value() const noexcept
{
    return data_;
}

Uint8& Uint8::operator+=(const Uint8& other) noexcept
{
    data_ += other.data_;
    return *this;
}

Uint8& Uint8::operator-=(const Uint8& other) noexcept
{
    data_ -= other.data_;
    return *this;
}

Uint8& Uint8::operator*=(const Uint8& other) noexcept
{
    data_ *= other.data_;
    return *this;
}

Uint8& Uint8::operator/=(const Uint8& other) noexcept
{
    data_ /= other.data_;
    return *this;
}

Uint8& Uint8::operator%=(const Uint8& other) noexcept
{
    data_ %= other.data_;
    return *this;
}

Uint8& Uint8::operator&=(const Uint8& other) noexcept
{
    data_ &= other.data_;
    return *this;
}

Uint8& Uint8::operator|=(const Uint8& other) noexcept
{
    data_ |= other.data_;
    return *this;
}

Uint8& Uint8::operator^=(const Uint8& other) noexcept
{
    data_ ^= other.data_;
    return *this;
}

Uint8& Uint8::operator<<=(const Uint8& other) noexcept
{
    data_ <<= other.data_;
    return *this;
}

Uint8& Uint8::operator>>=(const Uint8& other) noexcept
{
    data_ >>= other.data_;
    return *this;
}

Uint8& Uint8::operator++() noexcept
{
    ++data_;
    return *this;
}

Uint8 Uint8::operator++(int) noexcept
{
    Uint8 tmp(*this);
    ++data_;
    return tmp;
}

Uint8& Uint8::operator--() noexcept
{
    --data_;
    return *this;
}

Uint8 Uint8::operator--(int) noexcept
{
    Uint8 tmp(*this);
    --data_;
    return tmp;
}

void Uint8::bit(Bool& out, std::size_t i) const noexcept
{
    out = Bool(static_cast<bool>((data_ >> i) & 1u));
    return;
}

void Uint8::setBit(Bool v, std::size_t i) noexcept
{
    if (v.value()) {
        data_ = static_cast<unsigned char>(data_ | (1u << i));
    }
    else {
        data_ = static_cast<unsigned char>(data_ & ~(1u << i));
    }
    return;
}
