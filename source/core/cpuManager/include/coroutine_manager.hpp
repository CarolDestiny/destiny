#pragma once

#include "./promise_local.hpp"
#include "destiny/define/access/access.hpp"

#include <atomic>
#include <cstdint>
#include <deque>

namespace destiny::core::cpu_manager {
        class CoroutineBase;
        using CoroutineFunctionType = void (*)(CoroutineBase& coroutineBase) noexcept;
        class CoroutineUrgent;
        class CoroutinePeriodic;
        class CoroutineRegular;
        class CoroutineManager;
}

class destiny::core::cpu_manager::CoroutineBase {
        friend CoroutineManager;

        DESTINY_DEFINE_ACCESS_PUBLIC CoroutineBase() noexcept  = default;
        DESTINY_DEFINE_ACCESS_PUBLIC ~CoroutineBase() noexcept = default;

        DESTINY_DEFINE_ACCESS_PRIVATE bool   is_finish_{false};
        DESTINY_DEFINE_ACCESS_PUBLIC void    set_is_finish() noexcept;
        DESTINY_DEFINE_ACCESS_PROTECTED bool is_finish() const noexcept;

        DESTINY_DEFINE_ACCESS_PRIVATE CoroutineFunctionType next_function_{nullptr};
        DESTINY_DEFINE_ACCESS_PUBLIC void                   set_next_function(CoroutineFunctionType function) noexcept;
        DESTINY_DEFINE_ACCESS_PROTECTED void                call_next_function() noexcept;

        DESTINY_DEFINE_ACCESS_PRIVATE uint32_t   estimate_next_cycle_{0};
        DESTINY_DEFINE_ACCESS_PUBLIC void        set_estimate_next_cycle(uint32_t estimate_next_cycle) noexcept;
        DESTINY_DEFINE_ACCESS_PROTECTED uint32_t get_estimate_next_cycle() const noexcept;

        DESTINY_DEFINE_ACCESS_PRIVATE void* promiseLocalGet_;
        DESTINY_DEFINE_ACCESS_PUBLIC template<typename T> bool set_res(T value) noexcept;

        DESTINY_DEFINE_ACCESS_PRIVATE void* slots_[4];
        DESTINY_DEFINE_ACCESS_PUBLIC void*& slot0() noexcept;
        DESTINY_DEFINE_ACCESS_PUBLIC void*& slot1() noexcept;
        DESTINY_DEFINE_ACCESS_PUBLIC void*& slot2() noexcept;
        DESTINY_DEFINE_ACCESS_PUBLIC void*& slot3() noexcept;
};

class destiny::core::cpu_manager::CoroutineUrgent : public CoroutineBase {
        DESTINY_DEFINE_ACCESS_PUBLIC CoroutineUrgent() noexcept  = default;
        DESTINY_DEFINE_ACCESS_PUBLIC ~CoroutineUrgent() noexcept = default;

        DESTINY_DEFINE_ACCESS_PUBLIC enum class Priority : bool
        {
                block,
                normal
        };
        DESTINY_DEFINE_ACCESS_PRIVATE Priority   priority_{Priority::normal};
        DESTINY_DEFINE_ACCESS_PUBLIC void        set_priority(Priority priority) noexcept;
        DESTINY_DEFINE_ACCESS_PROTECTED Priority get_priority() const noexcept;
};

class destiny::core::cpu_manager::CoroutinePeriodic : public CoroutineBase {
        friend CoroutineManager;

        DESTINY_DEFINE_ACCESS_PUBLIC CoroutinePeriodic() noexcept  = default;
        DESTINY_DEFINE_ACCESS_PUBLIC ~CoroutinePeriodic() noexcept = default;

        DESTINY_DEFINE_ACCESS_PUBLIC enum class Priority : uint8_t
        {
                protected_catchUp,
                protected_skip,
                fixed_catchUp,
                fixed_skip,
                bounded_catchUp,
                bounded_skip
        };
        DESTINY_DEFINE_ACCESS_PRIVATE Priority   priority_{Priority::fixed_catchUp};
        DESTINY_DEFINE_ACCESS_PUBLIC void        set_priority(Priority priority) noexcept;
        DESTINY_DEFINE_ACCESS_PROTECTED Priority get_priority() const noexcept;

        DESTINY_DEFINE_ACCESS_PRIVATE uint32_t   duration_{UINT32_MAX};
        DESTINY_DEFINE_ACCESS_PUBLIC void        set_duration(uint32_t duration) noexcept;
        DESTINY_DEFINE_ACCESS_PROTECTED uint32_t get_duration() const noexcept;
        DESTINY_DEFINE_ACCESS_PROTECTED uint64_t last_time_{0};
        DESTINY_DEFINE_ACCESS_PROTECTED uint64_t next_time_{0};
};

class destiny::core::cpu_manager::CoroutineRegular : public CoroutineBase {
        DESTINY_DEFINE_ACCESS_PUBLIC CoroutineRegular() noexcept  = default;
        DESTINY_DEFINE_ACCESS_PUBLIC ~CoroutineRegular() noexcept = default;

        DESTINY_DEFINE_ACCESS_PUBLIC enum class Priority : uint8_t
        {
                high,
                normal,
                low,
                background
        };
        DESTINY_DEFINE_ACCESS_PRIVATE Priority   priority_{Priority::normal};
        DESTINY_DEFINE_ACCESS_PUBLIC void        set_priority(Priority priority) noexcept;
        DESTINY_DEFINE_ACCESS_PROTECTED Priority get_priority() const noexcept;
};

class destiny::core::cpu_manager::CoroutineManager {
        DESTINY_DEFINE_ACCESS_PUBLIC CoroutineManager() noexcept  = default;
        DESTINY_DEFINE_ACCESS_PUBLIC ~CoroutineManager() noexcept = default;

        DESTINY_DEFINE_ACCESS_PRIVATE std::deque<CoroutineBase*> coroutineList_;

        DESTINY_DEFINE_ACCESS_PUBLIC bool add(CoroutineUrgent coroutineUrgent) noexcept;
        DESTINY_DEFINE_ACCESS_PUBLIC bool add(CoroutineRegular coroutineRegular) noexcept;

        DESTINY_DEFINE_ACCESS_PRIVATE CoroutinePeriodic* nearly_coroutinePeriodic_{nullptr};
        DESTINY_DEFINE_ACCESS_PUBLIC bool                add(CoroutinePeriodic coroutinePeriodic) noexcept;

        DESTINY_DEFINE_ACCESS_PUBLIC static void function_maintain(CoroutineBase& coroutineBase) noexcept;

        DESTINY_DEFINE_ACCESS_PUBLIC bool exec() noexcept;
};

template <typename T>
bool destiny::core::cpu_manager::CoroutineBase::set_res(T value) noexcept
{
        return PromiseLocalSet(promiseLocalGet_).set_res(value);
}
