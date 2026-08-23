#include <gtest/gtest.h>

#include "destiny/define/define.hpp"

TEST(DefineTest, VersionMacros)
{
    EXPECT_EQ(DESTINY_VERSION_MAJOR, 0);
    EXPECT_EQ(DESTINY_VERSION_MINOR, 1);
}

TEST(DefineTest, DebugMacro)
{
    // 断言 DESTINY_DEBUG 是合法宏（Debug 下为 1，Release 下为 0）
    EXPECT_TRUE(DESTINY_DEBUG == 0 || DESTINY_DEBUG == 1);
}
