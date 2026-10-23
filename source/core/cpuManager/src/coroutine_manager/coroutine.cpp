#include "destiny/core/cpuManager/coroutine_manager.hpp"

void destiny::core::cpu_manager::CoroutineBase::set_is_finish() noexcept
{
        is_finish_ = true;
        return;
}

bool destiny::core::cpu_manager::CoroutineBase::is_finish() const noexcept
{
        return is_finish_;
}

void destiny::core::cpu_manager::CoroutineBase::set_next_function(CoroutineFunctionType function) noexcept
{
        next_function_ = function;
        return;
}

void destiny::core::cpu_manager::CoroutineBase::call_next_function() noexcept
{
        next_function_(*this);
}

void destiny::core::cpu_manager::CoroutineBase::set_estimate_next_cycle(uint32_t estimate_next_cycle) noexcept
{
        estimate_next_cycle_ = estimate_next_cycle;
        return;
}

uint32_t destiny::core::cpu_manager::CoroutineBase::get_estimate_next_cycle() const noexcept
{
        return estimate_next_cycle_;
}

destiny::core::cpu_manager::CoroutineBase::Priority destiny::core::cpu_manager::CoroutineBase::get_priority() const noexcept
{
        return priority_;
}

void*& destiny::core::cpu_manager::CoroutineBase::slot0() noexcept
{
        return slots_[0];
}

void*& destiny::core::cpu_manager::CoroutineBase::slot1() noexcept
{
        return slots_[1];
}
void*& destiny::core::cpu_manager::CoroutineBase::slot2() noexcept
{
        return slots_[2];
}

void*& destiny::core::cpu_manager::CoroutineBase::slot3() noexcept
{
        return slots_[3];
}

void destiny::core::cpu_manager::CoroutineUrgent::set_priority(Priority priority) noexcept
{
        priority_ = (CoroutineBase::Priority)priority;
        return;
}

void destiny::core::cpu_manager::CoroutinePeriodic::set_priority(Priority priority) noexcept
{
        priority_ = (CoroutineBase::Priority)priority;
        return;
}

void destiny::core::cpu_manager::CoroutinePeriodic::set_duration(uint32_t duration) noexcept
{
        duration_ = duration;
        return;
}

uint32_t destiny::core::cpu_manager::CoroutinePeriodic::get_duration() const noexcept
{
        return duration_;
}


void destiny::core::cpu_manager::CoroutineRegular::set_priority(Priority priority) noexcept
{
        priority_ = (CoroutineBase::Priority)priority;
        return;
}
