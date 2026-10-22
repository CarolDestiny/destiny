#pragma once

namespace destiny::core::cpu_manager {
        template <typename T>
        class PromiseLocalGet;
        class PromiseLocalSet;
}


template <typename T>
class destiny::core::cpu_manager::PromiseLocalGet {
public:
        PromiseLocalGet() noexcept  = default;
        ~PromiseLocalGet() noexcept = default;
        bool is_finish() const noexcept;
        bool get_res(T& value) const noexcept;

protected:
        bool is_finish_{false};
        T    data_{};
        friend class PromiseLocalSet;
};

class destiny::core::cpu_manager::PromiseLocalSet {
public:
        inline PromiseLocalSet(void* promiseLocalGet) noexcept;
        ~PromiseLocalSet() noexcept = default;
        template <typename T>
        bool set_res(T value) noexcept;

protected:
        void* promiseLocalGet_;
};

template <typename T>
bool destiny::core::cpu_manager::PromiseLocalGet<T>::is_finish() const noexcept
{
        return is_finish_;
}

template <typename T>
bool destiny::core::cpu_manager::PromiseLocalGet<T>::get_res(T& value) const noexcept
{
        value = data_;
        return is_finish_;
}

inline destiny::core::cpu_manager::PromiseLocalSet::PromiseLocalSet(void* promiseLocalGet) noexcept
{
        promiseLocalGet_ = promiseLocalGet;
        return;
}

template <typename T>
bool destiny::core::cpu_manager::PromiseLocalSet::set_res(T value) noexcept
{
        if (promiseLocalGet_ == nullptr) [[unlikely]]
        {
                return false;
        }
        // TODO: if error return false
        ((PromiseLocalGet<T>*)promiseLocalGet_)->data_      = value;
        ((PromiseLocalGet<T>*)promiseLocalGet_)->is_finish_ = true;
        return true;
}
