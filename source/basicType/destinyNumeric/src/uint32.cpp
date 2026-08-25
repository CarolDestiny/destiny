#include "destiny/basicType/destinyNumeric/destinyNumeric.hpp"
using namespace destiny;

Uint32::Uint32() noexcept
{
    data_ = 0;
    return;
}

Uint32::~Uint32() noexcept
{
    return;
}

Uint32::Uint32(unsigned int value) noexcept
{
    data_ = value;
    return;
}
Uint32::Uint32(const Uint32& other) noexcept
{
    data_ = other.data_;
    return;
}

Uint32::Uint32(Uint32&& other) noexcept
{
    data_ = other.data_;
    return;
}

Uint32& Uint32::operator=(const Uint32& other) noexcept
{
    data_ = other.data_;
    return *this;
}

Uint32& Uint32::operator=(Uint32&& other) noexcept
{
    data_ = other.data_;
    return *this;
}

unsigned int Uint32::value() const noexcept
{
    return data_;
}

Uint32& Uint32::operator+=(const Uint32& other) noexcept
{
    data_ += other.data_;
    return *this;
}

Uint32& Uint32::operator-=(const Uint32& other) noexcept
{
    data_ -= other.data_;
    return *this;
}

Uint32& Uint32::operator*=(const Uint32& other) noexcept
{
    data_ *= other.data_;
    return *this;
}

Uint32& Uint32::operator/=(const Uint32& other) noexcept
{
    data_ /= other.data_;
    return *this;
}

Uint32& Uint32::operator%=(const Uint32& other) noexcept
{
    data_ %= other.data_;
    return *this;
}

Uint32& Uint32::operator&=(const Uint32& other) noexcept
{
    data_ &= other.data_;
    return *this;
}

Uint32& Uint32::operator|=(const Uint32& other) noexcept
{
    data_ |= other.data_;
    return *this;
}

Uint32& Uint32::operator^=(const Uint32& other) noexcept
{
    data_ ^= other.data_;
    return *this;
}

Uint32& Uint32::operator<<=(const Uint32& other) noexcept
{
    data_ <<= other.data_;
    return *this;
}

Uint32& Uint32::operator>>=(const Uint32& other) noexcept
{
    data_ >>= other.data_;
    return *this;
}

Uint32& Uint32::operator++() noexcept
{
    ++data_;
    return *this;
}

Uint32 Uint32::operator++(int) noexcept
{
    Uint32 tmp(*this);
    ++data_;
    return tmp;
}

Uint32& Uint32::operator--() noexcept
{
    --data_;
    return *this;
}

Uint32 Uint32::operator--(int) noexcept
{
    Uint32 tmp(*this);
    --data_;
    return tmp;
}

void Uint32::piece(Uint8& out, std::size_t i) const noexcept
{
    out = Uint8(static_cast<unsigned char>((data_ >> (i * 8u)) & 0xFFu));
    return;
}

void Uint32::setPiece(Uint8 v, std::size_t i) noexcept
{
    const unsigned int shift = static_cast<unsigned int>(i) * 8u;
    data_ = (data_ & ~(0xFFu << shift)) | (static_cast<unsigned int>(v.value()) << shift);
    return;
}

void Uint32::piece(Uint16& out, std::size_t i) const noexcept
{
    out = Uint16(static_cast<unsigned short>((data_ >> (i * 16u)) & 0xFFFFu));
    return;
}

void Uint32::setPiece(Uint16 v, std::size_t i) noexcept
{
    const unsigned int shift = static_cast<unsigned int>(i) * 16u;
    data_ = (data_ & ~(0xFFFFu << shift)) | (static_cast<unsigned int>(v.value()) << shift);
    return;
}

void Uint32::byte(Uint8& out, std::size_t i) const noexcept
{
    out = Uint8(*(reinterpret_cast<const unsigned char*>(&data_) + i));
    return;
}

void Uint32::setByte(Uint8 v, std::size_t i) noexcept
{
    *(reinterpret_cast<unsigned char*>(&data_) + i) = v.value();
    return;
}

void Uint32::bit(Bool& out, std::size_t i) const noexcept
{
    out = Bool(static_cast<bool>((data_ >> i) & 1u));
    return;
}

void Uint32::setBit(Bool v, std::size_t i) noexcept
{
    if (v.value()) {
        data_ = data_ | (1u << i);
    }
    else {
        data_ = data_ & ~(1u << i);
    }
    return;
}
