#include "./share.hpp"

static void function_null() {
    return;
}

void destiny::core::cpu_manager::unload() noexcept {
    for (int i=0;i<destiny::define::cpu::logical_core_number;i++) {
        detail::cpuCore_buffer[i].stop_set();
    }
    for (int i=0;i<destiny::define::cpu::logical_core_number;i++) {
        detail::cpuCore_buffer[i].function_set(function_null);
    }
    for (int i=0;i<destiny::define::cpu::logical_core_number;i++) {
        detail::cpuCore_buffer[i].wait(1000);
    }
    for (int i=0;i<destiny::define::cpu::logical_core_number;i++) {
        detail::cpuCore_buffer[i].destroy();
    }
    return;
}