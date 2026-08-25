#include "destiny/basicType/destinyNumeric/destinyNumeric.hpp"
using namespace destiny;

Uint64::Uint64() noexcept
{
    data_ = 0;
    return;
}

Uint64::~Uint64() noexcept
{
    return;
}

Uint64::Uint64(unsigned long long value) noexcept
{
    data_ = value;
    return;
}
Uint64::Uint64(const Uint64& other) noexcept
{
    data_ = other.data_;
    return;
}

Uint64::Uint64(Uint64&& other) noexcept
{
    data_ = other.data_;
    return;
}

Uint64& Uint64::operator=(const Uint64& other) noexcept
{
    data_ = other.data_;
    return *this;
}

Uint64& Uint64::operator=(Uint64&& other) noexcept
{
    data_ = other.data_;
    return *this;
}

unsigned long long Uint64::value() const noexcept
{
    return data_;
}

Uint64& Uint64::operator+=(const Uint64& other) noexcept
{
    data_ += other.data_;
    return *this;
}

Uint64& Uint64::operator-=(const Uint64& other) noexcept
{
    data_ -= other.data_;
    return *this;
}

Uint64& Uint64::operator*=(const Uint64& other) noexcept
{
    data_ *= other.data_;
    return *this;
}

Uint64& Uint64::operator/=(const Uint64& other) noexcept
{
    data_ /= other.data_;
    return *this;
}

Uint64& Uint64::operator%=(const Uint64& other) noexcept
{
    data_ %= other.data_;
    return *this;
}

Uint64& Uint64::operator&=(const Uint64& other) noexcept
{
    data_ &= other.data_;
    return *this;
}

Uint64& Uint64::operator|=(const Uint64& other) noexcept
{
    data_ |= other.data_;
    return *this;
}

Uint64& Uint64::operator^=(const Uint64& other) noexcept
{
    data_ ^= other.data_;
    return *this;
}

Uint64& Uint64::operator<<=(const Uint64& other) noexcept
{
    data_ <<= other.data_;
    return *this;
}

Uint64& Uint64::operator>>=(const Uint64& other) noexcept
{
    data_ >>= other.data_;
    return *this;
}

Uint64& Uint64::operator++() noexcept
{
    ++data_;
    return *this;
}

Uint64 Uint64::operator++(int) noexcept
{
    Uint64 tmp(*this);
    ++data_;
    return tmp;
}

Uint64& Uint64::operator--() noexcept
{
    --data_;
    return *this;
}

Uint64 Uint64::operator--(int) noexcept
{
    Uint64 tmp(*this);
    --data_;
    return tmp;
}

void Uint64::piece(Uint8& out, std::size_t i) const noexcept
{
    out = Uint8(static_cast<unsigned char>((data_ >> (i * 8ull)) & 0xFFull));
    return;
}

void Uint64::setPiece(Uint8 v, std::size_t i) noexcept
{
    const unsigned long long shift = static_cast<unsigned long long>(i) * 8ull;
    data_ = (data_ & ~(0xFFull << shift)) | (static_cast<unsigned long long>(v.value()) << shift);
    return;
}

void Uint64::piece(Uint16& out, std::size_t i) const noexcept
{
    out = Uint16(static_cast<unsigned short>((data_ >> (i * 16ull)) & 0xFFFFull));
    return;
}

void Uint64::setPiece(Uint16 v, std::size_t i) noexcept
{
    const unsigned long long shift = static_cast<unsigned long long>(i) * 16ull;
    data_ = (data_ & ~(0xFFFFull << shift)) | (static_cast<unsigned long long>(v.value()) << shift);
    return;
}

void Uint64::piece(Uint32& out, std::size_t i) const noexcept
{
    out = Uint32(static_cast<unsigned int>((data_ >> (i * 32ull)) & 0xFFFFFFFFull));
    return;
}

void Uint64::setPiece(Uint32 v, std::size_t i) noexcept
{
    const unsigned long long shift = static_cast<unsigned long long>(i) * 32ull;
    data_ = (data_ & ~(0xFFFFFFFFull << shift)) | (static_cast<unsigned long long>(v.value()) << shift);
    return;
}

void Uint64::byte(Uint8& out, std::size_t i) const noexcept
{
    out = Uint8(*(reinterpret_cast<const unsigned char*>(&data_) + i));
    return;
}

void Uint64::setByte(Uint8 v, std::size_t i) noexcept
{
    *(reinterpret_cast<unsigned char*>(&data_) + i) = v.value();
    return;
}

void Uint64::bit(Bool& out, std::size_t i) const noexcept
{
    out = Bool(static_cast<bool>((data_ >> i) & 1ull));
    return;
}

void Uint64::setBit(Bool v, std::size_t i) noexcept
{
    if (v.value()) {
        data_ = data_ | (1ull << i);
    }
    else {
        data_ = data_ & ~(1ull << i);
    }
    return;
}
