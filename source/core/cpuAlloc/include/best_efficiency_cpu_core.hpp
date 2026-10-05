#pragma once

namespace destiny::core::cpu_alloc {
    class BestEfficiencyCpuCore;

    bool alloc(BestEfficiencyCpuCore& bestEfficiencyCpuCore) noexcept;
    void dealloc(BestEfficiencyCpuCore& bestEfficiencyCpuCore) noexcept;
};

class destiny::core::cpu_alloc::BestEfficiencyCpuCore {
public:
    BestEfficiencyCpuCore() noexcept = default;
    ~BestEfficiencyCpuCore() noexcept = default;

    BestEfficiencyCpuCore(const BestEfficiencyCpuCore&) noexcept = delete;
    BestEfficiencyCpuCore& operator=(const BestEfficiencyCpuCore&) noexcept = delete;

    BestEfficiencyCpuCore(BestEfficiencyCpuCore&&) noexcept = delete;
    BestEfficiencyCpuCore& operator=(BestEfficiencyCpuCore&&) noexcept = delete;

    void function_set(void (*function)()) noexcept;

private:
    void* cpuCore_;

    friend bool alloc(BestEfficiencyCpuCore& bestEfficiencyCpuCore) noexcept;
    friend void dealloc(BestEfficiencyCpuCore& bestEfficiencyCpuCore) noexcept;
};