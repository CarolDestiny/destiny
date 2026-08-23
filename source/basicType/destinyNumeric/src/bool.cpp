#include "destiny/basicType/destinyNumeric/destinyNumeric.hpp"
using namespace destiny;

Bool::Bool() noexcept
{
    data_ = false;
    return;
}

Bool::Bool(bool value) noexcept
{
    data_ = value;
    return;
}

Bool::Bool(const Bool& other) noexcept
{
    data_ = other.data_;
    return;
}

Bool& Bool::operator=(const Bool& other) noexcept
{
    data_ = other.data_;
    return *this;
}

bool Bool::value() const noexcept
{
    return data_;
}

Bool::operator bool() const noexcept
{
    return data_;
}
