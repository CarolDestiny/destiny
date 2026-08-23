#include "destiny/basicType/destinyInt/int8.hpp"

destiny::Int8::Int8() noexcept
{
    data_ = 0;
    return;
}

destiny::Int8::~Int8() noexcept
{
    return;
}

destiny::Int8::Int8(signed char value) noexcept
{
    data_ = value;
    return;
}
