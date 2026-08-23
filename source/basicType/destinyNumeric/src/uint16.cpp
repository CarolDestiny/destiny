#include "destiny/basicType/destinyNumeric/destinyNumeric.hpp"
using namespace destiny;

Uint16::Uint16() noexcept
{
    data_ = 0;
    return;
}

Uint16::~Uint16() noexcept
{
    return;
}

Uint16::Uint16(unsigned short value) noexcept
{
    data_ = value;
    return;
}
Uint16::Uint16(const Uint16& other) noexcept
{
    data_ = other.data_;
    return;
}

Uint16::Uint16(Uint16&& other) noexcept
{
    data_ = other.data_;
    return;
}

Uint16& Uint16::operator=(const Uint16& other) noexcept
{
    data_ = other.data_;
    return *this;
}

Uint16& Uint16::operator=(Uint16&& other) noexcept
{
    data_ = other.data_;
    return *this;
}

unsigned short Uint16::value() const noexcept
{
    return data_;
}

Uint16& Uint16::operator+=(const Uint16& other) noexcept
{
    data_ += other.data_;
    return *this;
}

Uint16& Uint16::operator-=(const Uint16& other) noexcept
{
    data_ -= other.data_;
    return *this;
}

Uint16& Uint16::operator*=(const Uint16& other) noexcept
{
    data_ *= other.data_;
    return *this;
}

Uint16& Uint16::operator/=(const Uint16& other) noexcept
{
    data_ /= other.data_;
    return *this;
}

Uint16& Uint16::operator%=(const Uint16& other) noexcept
{
    data_ %= other.data_;
    return *this;
}

Uint16& Uint16::operator&=(const Uint16& other) noexcept
{
    data_ &= other.data_;
    return *this;
}

Uint16& Uint16::operator|=(const Uint16& other) noexcept
{
    data_ |= other.data_;
    return *this;
}

Uint16& Uint16::operator^=(const Uint16& other) noexcept
{
    data_ ^= other.data_;
    return *this;
}

Uint16& Uint16::operator<<=(const Uint16& other) noexcept
{
    data_ <<= other.data_;
    return *this;
}

Uint16& Uint16::operator>>=(const Uint16& other) noexcept
{
    data_ >>= other.data_;
    return *this;
}

Uint16& Uint16::operator++() noexcept
{
    ++data_;
    return *this;
}

Uint16 Uint16::operator++(int) noexcept
{
    Uint16 tmp(*this);
    ++data_;
    return tmp;
}

Uint16& Uint16::operator--() noexcept
{
    --data_;
    return *this;
}

Uint16 Uint16::operator--(int) noexcept
{
    Uint16 tmp(*this);
    --data_;
    return tmp;
}

void Uint16::piece(Uint8& out, std::size_t i) const noexcept
{
    out = Uint8(static_cast<unsigned char>((data_ >> (i * 8u)) & 0xFFu));
    return;
}

void Uint16::setPiece(Uint8 v, std::size_t i) noexcept
{
    const unsigned int shift = static_cast<unsigned int>(i) * 8u;
    data_ = static_cast<unsigned short>((data_ & ~(0xFFu << shift)) | (static_cast<unsigned int>(v.value()) << shift));
    return;
}

void Uint16::byte(Uint8& out, std::size_t i) const noexcept
{
    out = Uint8(*(reinterpret_cast<const unsigned char*>(&data_) + i));
    return;
}

void Uint16::setByte(Uint8 v, std::size_t i) noexcept
{
    *(reinterpret_cast<unsigned char*>(&data_) + i) = v.value();
    return;
}

void Uint16::bit(Bool& out, std::size_t i) const noexcept
{
    out = Bool(static_cast<bool>((data_ >> i) & 1u));
    return;
}

void Uint16::setBit(Bool v, std::size_t i) noexcept
{
    if (v.value())
    {
        data_ = static_cast<unsigned short>(data_ | (1u << i));
    }
    else
    {
        data_ = static_cast<unsigned short>(data_ & ~(1u << i));
    }
    return;
}
