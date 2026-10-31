#pragma once

#include "destiny/define/access/access.hpp"

namespace destiny::core::detail {
        class ThreadLocalBuffer;
}

class destiny::core::detail::ThreadLocalBuffer {
        DESTINY_DEFINE_ACCESS_PUBLIC ThreadLocalBuffer() noexcept = default;
        DESTINY_DEFINE_ACCESS_PUBLIC ~ThreadLocalBuffer() noexcept = default;

        DESTINY_DEFINE_ACCESS_PUBLIC bool constructor() noexcept;
        DESTINY_DEFINE_ACCESS_PUBLIC void destructor() noexcept;

        DESTINY_DEFINE_ACCESS_PRIVATE
};