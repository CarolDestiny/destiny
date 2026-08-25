#include <gtest/gtest.h>

#include "destiny/basicType/destinyNumeric/destinyNumeric.hpp"

using namespace destiny;

// 默认构造必须为 false
TEST(BoolTest, DefaultCtorIsFalse)
{
    Bool b;
    EXPECT_FALSE(b.value());
}

// 值构造存储底层值
TEST(BoolTest, ValueCtor)
{
    EXPECT_TRUE(Bool(true).value());
    EXPECT_FALSE(Bool(false).value());
}

// 拷贝构造与赋值
TEST(BoolTest, CopyAndAssignment)
{
    Bool a(true);
    Bool b(a);
    EXPECT_TRUE(b.value());
    Bool c;
    c = a;
    EXPECT_TRUE(c.value());
    c = Bool(false);
    EXPECT_FALSE(c.value());
}

// value() 与 operator bool 一致
TEST(BoolTest, ValueAndConversion)
{
    Bool t(true), f(false);
    EXPECT_TRUE(static_cast<bool>(t));
    EXPECT_FALSE(static_cast<bool>(f));
    EXPECT_EQ(t.value(), static_cast<bool>(t));
}

// 逻辑与/或/非：走内建短路，结果可转 bool
TEST(BoolTest, LogicalAndOrNot)
{
    Bool t(true), f(false);
    EXPECT_TRUE(t && t);
    EXPECT_FALSE(t && f);
    EXPECT_FALSE(f && t);
    EXPECT_TRUE(t || f);
    EXPECT_TRUE(f || t);
    EXPECT_FALSE(f || f);
    EXPECT_FALSE(!t);
    EXPECT_TRUE(!f);
}

// 短路语义：右侧不被求值（通过可观察副作用验证）
TEST(BoolTest, ShortCircuitEvaluation)
{
    Bool t(true), f(false);
    int evalCount = 0;
    auto sideEffect = [&evalCount](Bool) -> Bool {
        ++evalCount;
        return Bool(true);
    };
    // false && (副作用) 短路，不执行
    (void)(f && sideEffect(Bool(true)));
    EXPECT_EQ(evalCount, 0);
    // true || (副作用) 短路，不执行
    (void)(t || sideEffect(Bool(true)));
    EXPECT_EQ(evalCount, 0);
}

// Bool 参与算术：按 cstdint 语义提升为 Int32
TEST(BoolTest, ArithmeticPromotesToInt32)
{
    auto r1 = Bool(true) + Int32(5);
    static_assert(std::is_same_v<decltype(r1), Int32>);
    EXPECT_EQ(r1.value(), 6);

    auto r2 = Bool(false) + Int32(5);
    EXPECT_EQ(r2.value(), 5);
}

// Bool 参与比较：与 Bool、与内建 bool、与整数
TEST(BoolTest, Comparison)
{
    EXPECT_TRUE(Bool(true) == Bool(true));
    EXPECT_TRUE(Bool(true) != Bool(false));
    EXPECT_TRUE(Bool(true) == true);
    EXPECT_TRUE(Bool(false) == false);
    EXPECT_TRUE(Bool(true) > Bool(false));
    // 提升为 Int32 后与整数比较：true == 1，false == 0
    EXPECT_TRUE(Bool(true) == Int32(1));
    EXPECT_TRUE(Bool(false) == Int32(0));
}
