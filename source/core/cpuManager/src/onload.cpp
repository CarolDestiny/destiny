#include "./share.hpp"

bool destiny::core::cpu_manager::onload() noexcept {
    for (int i = 0;i < destiny::define::cpu::logical_core_number; i++) {
        const bool res = detail::cpuCore_buffer[i].create();
        // TODO: more good error deal
        if (res == false) {
            return false;
        }
    }

    return true;
}