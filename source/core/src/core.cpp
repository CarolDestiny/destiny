#include "destiny/core/core.hpp"
#include "./share.hpp"

uint64_t destiny::this_thread::id() noexcept
{
        return core::detail::thread_id;
}
