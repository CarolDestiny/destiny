#pragma once

#include <cstdint>

namespace destiny::core {
        [[nodiscard]] bool onload() noexcept;
        void               unload() noexcept;

        class CpuCore;
        
}

namespace destiny::this_thread {
        [[nodiscard]] uint64_t id() noexcept;
}

namespace destiny {

}

class destiny::core::CpuCore {
public:
        CpuCore() noexcept  = default;
        ~CpuCore() noexcept = default;

        using Function = int (*)(int argc, char* argv[]) noexcept;
        [[nodiscard]] bool set_function(Function function, int argc, char* argv[]) noexcept;

private:
        uint32_t thread_id_{0};
};
