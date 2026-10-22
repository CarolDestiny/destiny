#pragma once

#include "./best_efficiency_cpu_core.hpp"
#include "./best_performance_cpu_core.hpp"
#include "./coroutine_manager.hpp"

namespace destiny::core::cpu_manager {
        bool onload() noexcept;
        void unload() noexcept;

        uint32_t id() noexcept; // get thread local id
        CoroutineManager& coroutineManager() noexcept; // get thread local CoroutineManager
        CoroutineManager& coroutineManager(uint32_t thread_id) noexcept; // get thread ${thread_id} CoroutineManager
}

namespace destiny::this_thread {
        using ::destiny::core::cpu_manager::id;
        using ::destiny::core::cpu_manager::coroutineManager;

        using ::destiny::core::cpu_manager::alloc;
        using ::destiny::core::cpu_manager::dealloc;
}

namespace destiny {

}
