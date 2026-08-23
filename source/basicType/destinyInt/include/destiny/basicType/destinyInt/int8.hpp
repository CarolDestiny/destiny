#pragma once

namespace destiny
{
    class Int8;
}

class destiny::Int8
{
public:
    Int8() noexcept;
    ~Int8() noexcept;
    Int8(signed char value) noexcept;

private:
    signed char data_;
};
