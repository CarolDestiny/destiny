#pragma once

#include "./promise_local.hpp"
#include "coroutine_manager.hpp"
#include "destiny/define/access/access.hpp"

#include <atomic>
#include <cstdint>
#include <list>
#include <deque>
#include <vector>

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

        DESTINY_DEFINE_ACCESS_PROTECTED enum class Priority : uint8_t
        {
                urgent_block                = 0,
                periodic_protected_catch_up = 1,
                periodic_protected_skip     = 2,
                urgent_normal               = 3,
                periodic_fixed_catch_up     = 4,
                periodic_fixed_skip         = 5,
                regular_high                = 6,
                periodic_bounded_catch_up   = 7,
                periodic_bounded_skip       = 8,
                regular_normal              = 9,
                regular_low                 = 10,
                regular_background          = 11
        };
        DESTINY_DEFINE_ACCESS_PROTECTED Priority priority_;
        DESTINY_DEFINE_ACCESS_PROTECTED Priority get_priority() const noexcept;

        DESTINY_DEFINE_ACCESS_PRIVATE void* promiseLocalGet_;
        DESTINY_DEFINE_ACCESS_PUBLIC template <typename T>
        bool set_res(T value) noexcept;

        DESTINY_DEFINE_ACCESS_PRIVATE void* slots_[4];
        DESTINY_DEFINE_ACCESS_PUBLIC void*& slot0() noexcept;
        DESTINY_DEFINE_ACCESS_PUBLIC void*& slot1() noexcept;
        DESTINY_DEFINE_ACCESS_PUBLIC void*& slot2() noexcept;
        DESTINY_DEFINE_ACCESS_PUBLIC void*& slot3() noexcept;
};

class destiny::core::cpu_manager::CoroutineUrgent : public CoroutineBase {
        DESTINY_DEFINE_ACCESS_PUBLIC CoroutineUrgent() noexcept  = default;
        DESTINY_DEFINE_ACCESS_PUBLIC ~CoroutineUrgent() noexcept = default;

        DESTINY_DEFINE_ACCESS_PUBLIC enum class Priority : uint8_t
        {
                block  = (uint8_t)CoroutineBase::Priority::urgent_block,
                normal = (uint8_t)CoroutineBase::Priority::urgent_normal
        };
        DESTINY_DEFINE_ACCESS_PUBLIC void set_priority(Priority priority) noexcept;
};

class destiny::core::cpu_manager::CoroutinePeriodic : public CoroutineBase {
        friend CoroutineManager;

        DESTINY_DEFINE_ACCESS_PUBLIC CoroutinePeriodic() noexcept  = default;
        DESTINY_DEFINE_ACCESS_PUBLIC ~CoroutinePeriodic() noexcept = default;

        DESTINY_DEFINE_ACCESS_PUBLIC enum class Priority : uint8_t
        {
                protected_catch_up = (uint8_t)CoroutineBase::Priority::periodic_protected_catch_up,
                protected_skip     = (uint8_t)CoroutineBase::Priority::periodic_protected_skip,
                fixed_catch_up     = (uint8_t)CoroutineBase::Priority::periodic_fixed_catch_up,
                fixed_skip         = (uint8_t)CoroutineBase::Priority::periodic_fixed_skip,
                bounded_catch_up   = (uint8_t)CoroutineBase::Priority::periodic_bounded_catch_up,
                bounded_skip       = (uint8_t)CoroutineBase::Priority::periodic_bounded_skip
        };
        DESTINY_DEFINE_ACCESS_PUBLIC void set_priority(Priority priority) noexcept;

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
                high       = (uint8_t)CoroutineBase::Priority::regular_high,
                normal     = (uint8_t)CoroutineBase::Priority::regular_normal,
                low        = (uint8_t)CoroutineBase::Priority::regular_low,
                background = (uint8_t)CoroutineBase::Priority::regular_background
        };
        DESTINY_DEFINE_ACCESS_PUBLIC void set_priority(Priority priority) noexcept;
};

class destiny::core::cpu_manager::CoroutineManager {
        DESTINY_DEFINE_ACCESS_PUBLIC CoroutineManager() noexcept  = default;
        DESTINY_DEFINE_ACCESS_PUBLIC ~CoroutineManager() noexcept = default;

        DESTINY_DEFINE_ACCESS_PRIVATE std::list<std::vector<CoroutineUrgent>> coroutineUrgentBuffer_;
        DESTINY_DEFINE_ACCESS_PRIVATE std::vector<CoroutineUrgent*> coroutineUrgentCache_;
        DESTINY_DEFINE_ACCESS_PUBLIC bool  acquire(CoroutineUrgent*& coroutineUrgent) noexcept;
        DESTINY_DEFINE_ACCESS_PUBLIC bool  cancel(CoroutineUrgent*& coroutineUrgent) noexcept;
        DESTINY_DEFINE_ACCESS_PUBLIC bool  submit(CoroutineUrgent*& coroutineUrgent) noexcept;
        DESTINY_DEFINE_ACCESS_PRIVATE bool release(CoroutineUrgent*& coroutineUrgent) noexcept;

        DESTINY_DEFINE_ACCESS_PUBLIC bool  acquire(CoroutinePeriodic*& coroutinePeriodic) noexcept;
        DESTINY_DEFINE_ACCESS_PUBLIC bool  cancel(CoroutinePeriodic*& coroutinePeriodic) noexcept;
        DESTINY_DEFINE_ACCESS_PUBLIC bool  submit(CoroutinePeriodic*& coroutinePeriodic) noexcept;
        DESTINY_DEFINE_ACCESS_PRIVATE bool release(CoroutinePeriodic*& coroutinePeriodic) noexcept;

        DESTINY_DEFINE_ACCESS_PUBLIC bool  acquire(CoroutineRegular*& coroutineRegular) noexcept;
        DESTINY_DEFINE_ACCESS_PUBLIC bool  cancel(CoroutineRegular*& coroutineRegular) noexcept;
        DESTINY_DEFINE_ACCESS_PUBLIC bool  submit(CoroutineRegular*& coroutineRegular) noexcept;
        DESTINY_DEFINE_ACCESS_PRIVATE bool release(CoroutineRegular*& coroutineRegular) noexcept;

        DESTINY_DEFINE_ACCESS_PUBLIC static void function_maintain(CoroutineBase& coroutineBase) noexcept;

        DESTINY_DEFINE_ACCESS_PUBLIC bool exec() noexcept;
};

template <typename T>
bool destiny::core::cpu_manager::CoroutineBase::set_res(T value) noexcept
{
        return PromiseLocalSet(promiseLocalGet_).set_res(value);
}
