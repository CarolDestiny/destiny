#pragma once
#include "boundMPSC.hpp"
#include <fstream>
#include <thread>

namespace destiny::core::replay::detail
{
    inline BoundMPSC boundMPSC;
    inline std::thread thMainTain;
    void thFunction() noexcept;

    inline std::fstream fileSession;
} // namespace destiny::core::replay::detail