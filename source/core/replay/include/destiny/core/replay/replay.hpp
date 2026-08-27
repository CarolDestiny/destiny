#pragma once

#ifdef DEBUG
#define DESTINY_CORE_REPLAY_ON
#endif

namespace destiny::core::replay
{
    bool onload() noexcept;
    void unload() noexcept;
}

namespace destiny::core::replay
{
#define DESTINY_CORE_REPLAY_REGISTER_FUNCTION (functionName) \
    ()
#define DESTINY_CORE_REPLAY_REGISTER_CLASS (classType) \
    ()
}