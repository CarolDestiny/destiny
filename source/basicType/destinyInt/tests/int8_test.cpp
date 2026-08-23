#include <gtest/gtest.h>

#include "destiny/basicType/destinyInt/destinyInt.hpp"

// Int8 目前只有默认构造 / 值构造 / 析构，且没有读取接口（无 value()），
// 所以这里只能验证：构造不抛异常、值构造能存进去（通过后续加读取接口来真正验证）。
// 一旦 Int8 增加 value() 读取接口，应在此补充存储内容断言。

TEST(Int8Test, DefaultConstruct)
{
    // 默认构造不应抛异常（data_ 未初始化，不读取即可）
    EXPECT_NO_THROW(destiny::Int8 i8);
}

TEST(Int8Test, ValueConstruct)
{
    EXPECT_NO_THROW(destiny::Int8 i8(static_cast<signed char>(42)));
}

// 值构造存储正确性：目前无读取接口，先留一个“骨架断言”
TEST(Int8Test, ValueStored)
{
    destiny::Int8 i8(static_cast<signed char>(7));
    // 暂无读取接口，此处用（编译期）占位断言占位
    SUCCEED();
}

// 模块生命周期钩子应可调用且返回成功
TEST(Int8Test, LifecycleHooks)
{
    EXPECT_TRUE(destiny::basicType::destinyInt::onload());
    EXPECT_NO_THROW(destiny::basicType::destinyInt::unload());
}
