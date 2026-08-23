#include <gtest/gtest.h>

#include "destiny/define/define.hpp"

TEST(DefineTest, VersionMacros)
{
    EXPECT_EQ(DESTINY_VERSION_MAJOR, 0);
    EXPECT_EQ(DESTINY_VERSION_MINOR, 1);
}

TEST(DefineTest, DebugMacro)
{
    // Assert DESTINY_DEBUG is a valid macro (1 in Debug, 0 in Release)
    EXPECT_TRUE(DESTINY_DEBUG == 0 || DESTINY_DEBUG == 1);
}
