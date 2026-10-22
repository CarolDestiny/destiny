#pragma once

#include "destiny/core/cpuManager/coroutine_manager.hpp"

#include "destiny/define/access/access.hpp"

#include <cstdint>
#include <string>

namespace destiny::core::cpu_manager::detail {
        class ThreadLocalBuffer;
}

class destiny::core::cpu_manager::detail::ThreadLocalBuffer {
public:
        ThreadLocalBuffer() noexcept  = default;
        ~ThreadLocalBuffer() noexcept = default;

        void* slot0{nullptr}; // cpu core info
        CoroutineManager coroutineManager; // CoroutineManager
};
