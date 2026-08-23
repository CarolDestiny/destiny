#include <gtest/gtest.h>

#include "destiny/basicType/destinyNumeric/destinyNumeric.hpp"

using namespace destiny;

// ===== 同类型整数算术 =====

TEST(Operators, SameTypeIntArithmetic)
{
    Int8 a(10), b(3);
    EXPECT_EQ((a + b).value(), 13);
    EXPECT_EQ((a - b).value(), 7);
    EXPECT_EQ((a * b).value(), 30);
    EXPECT_EQ((a / b).value(), 3);
    EXPECT_EQ((a % b).value(), 1);
}

TEST(Operators, CrossWidthInt)
{
    Int8 a(100);
    Int16 b(200);
    auto r = a + b; // Int8 + Int16 -> Int16
    static_assert(std::is_same_v<decltype(r), Int16>);
    EXPECT_EQ(r.value(), 300);
}

TEST(Operators, MixedSignedness)
{
    // Int16 + Uint16 -> Int32（用户决策 1）
    Int16 a(20000);
    Uint16 b(30000);
    auto r = a + b;
    static_assert(std::is_same_v<decltype(r), Int32>);
    EXPECT_EQ(r.value(), 50000);

    // 结果 Int32 允许截断赋值回 Int16
    Int16 s = a + Uint16(20000); // 40000 -> 截断
    EXPECT_EQ(s.value(), static_cast<signed short>(40000));
}

TEST(Operators, BuiltinLift)
{
    // 内建混合：提升（决策 3），Int8 + 2000 -> Int32
    Int8 a(8);
    auto r = a + 2000;
    static_assert(std::is_same_v<decltype(r), Int32>);
    EXPECT_EQ(r.value(), 2008);

    // 内建在左
    auto r2 = 3 + Uint16(4); // int -> Int32, Uint16 -> Int32
    static_assert(std::is_same_v<decltype(r2), Int32>);
    EXPECT_EQ(r2.value(), 7);

    // 内建 unsigned
    auto r3 = a + 4000000000u; // Uint32
    static_assert(std::is_same_v<decltype(r3), Uint32>);
    EXPECT_EQ(r3.value(), 4000000008u);
}

TEST(Operators, IntFloat)
{
    // 整数 + 浮点 -> Float64（决策 2）
    Int32 a(5);
    Float32 f(2.5f);
    auto r = a + f;
    static_assert(std::is_same_v<decltype(r), Float64>);
    EXPECT_DOUBLE_EQ(r.value(), 7.5);

    // Float64 允许截断赋值回 Float32
    Float32 g = f + a;
    EXPECT_FLOAT_EQ(g.value(), 7.5f);
}

TEST(Operators, FloatFloat)
{
    Float32 a(1.5f);
    Float64 b(2.5);
    auto r = a + b;
    static_assert(std::is_same_v<decltype(r), Float64>);
    EXPECT_DOUBLE_EQ(r.value(), 4.0);
}

TEST(Operators, BoolArithmetic)
{
    // Bool 参与算术（决策 4），提升为 Int32
    Bool t(true);
    Int32 a(5);
    auto r = t + a;
    static_assert(std::is_same_v<decltype(r), Int32>);
    EXPECT_EQ(r.value(), 6);

    auto r2 = t + Float32(1.5f);
    static_assert(std::is_same_v<decltype(r2), Float64>);
    EXPECT_DOUBLE_EQ(r2.value(), 2.5);
}

// ===== 比较 =====

TEST(Operators, Comparison)
{
    EXPECT_TRUE(Int8(5) == Int8(5));
    EXPECT_TRUE(Int8(5) < Int16(6));
    EXPECT_TRUE(Uint16(3) <= 3);
    EXPECT_TRUE(Int8(2) != 3);
    // 跨符号：提升到 Int16 比较，-1 < 1
    EXPECT_TRUE(Int8(-1) < Uint8(1));
    EXPECT_TRUE(Float64(1.5) > Int32(1));
    EXPECT_TRUE(Bool(true) == true);
    EXPECT_TRUE(Int8(5) >= Int8(5));
    EXPECT_TRUE(Float32(0.1f) < Float64(0.2));
}

// ===== 位运算 =====

TEST(Operators, Bitwise)
{
    Uint8 a(0b1010);
    EXPECT_EQ((a & Uint8(0b1100)).value(), 0b1000);
    EXPECT_EQ((a | Uint8(0b0101)).value(), 0b1111);
    EXPECT_EQ((a ^ Uint8(0b1111)).value(), 0b0101);
    EXPECT_EQ((Uint16(0x00FF) << 8).value(), 0xFF00u);
    EXPECT_EQ((Uint16(0xFF00) >> 8).value(), 0xFFu);
    // 与内建混合：结果提升到 Int32
    auto r = Int8(0x0F) & 0x0F;
    static_assert(std::is_same_v<decltype(r), Int32>);
    EXPECT_EQ(r.value(), 0x0F);
    EXPECT_EQ((Int8(5) & Int8(3)).value(), 1);
}

// ===== 一元 =====

TEST(Operators, Unary)
{
    EXPECT_EQ((-Int8(5)).value(), -5);
    EXPECT_EQ((-Uint8(1)).value(), 255);
    EXPECT_EQ((~Uint8(0)).value(), 255);
    EXPECT_EQ((+Int8(3)).value(), 3);
    EXPECT_DOUBLE_EQ((-Float64(2.5)).value(), -2.5);
    EXPECT_FLOAT_EQ((-Float32(1.0f)).value(), -1.0f);
}

// ===== Bool 逻辑（走内建短路）=====

TEST(Operators, BoolLogic)
{
    // && || ! 走内建短路（operator bool），结果是 bool
    Bool t(true), f(false);
    EXPECT_TRUE(t && t);
    EXPECT_FALSE(t && f);
    EXPECT_TRUE(t || f);
    EXPECT_FALSE(!t);
    EXPECT_TRUE(!f);
}

// ===== 截断构造 =====

TEST(Operators, TruncatingConversion)
{
    Int16 s(30000);
    Int8 b = s; // Int16 -> Int8 截断
    EXPECT_EQ(b.value(), static_cast<signed char>(30000));

    Uint64 big(0x0123456789ABCDEFULL);
    Uint32 low = big; // 截断到低 32 位
    EXPECT_EQ(low.value(), 0x89ABCDEFu);

    Float32 f32 = Float64(3.14159265358979); // double -> float 截断
    EXPECT_FLOAT_EQ(f32.value(), 3.1415927f);

    Bool b2 = Int32(7); // 非零 -> true
    EXPECT_TRUE(b2.value());
    Bool b3 = Int32(0);
    EXPECT_FALSE(b3.value());
}

// ===== 提升规则：编译期断言结果类型 =====

TEST(Operators, PromotionRules)
{
    namespace d = basicType::destinyNumeric::detail;

    // 同符号：取宽者
    static_assert(std::is_same_v<d::Common_t<Int8, Int16>, Int16>);
    static_assert(std::is_same_v<d::Common_t<Uint16, Uint64>, Uint64>);
    // 异符号同宽：取有符号并加宽一级（Int16 + Uint16 -> Int32）
    static_assert(std::is_same_v<d::Common_t<Int16, Uint16>, Int32>);
    static_assert(std::is_same_v<d::Common_t<Int8, Uint8>, Int16>);
    // 异符号异宽：取宽者
    static_assert(std::is_same_v<d::Common_t<Int8, Uint32>, Uint32>);
    static_assert(std::is_same_v<d::Common_t<Int64, Uint16>, Int64>);
    // 整数 + 浮点：一律 Float64
    static_assert(std::is_same_v<d::Common_t<Int32, Float32>, Float64>);
    static_assert(std::is_same_v<d::Common_t<Uint64, Float32>, Float64>);
    // 浮点相遇：取宽者
    static_assert(std::is_same_v<d::Common_t<Float32, Float64>, Float64>);
    // Bool 参与：提升为 Int32
    static_assert(std::is_same_v<d::Common_t<Bool, Int32>, Int32>);
    static_assert(std::is_same_v<d::Common_t<Bool, Float32>, Float64>);
    // 内建类型归类
    static_assert(std::is_same_v<d::Common_t<Int8, int>, Int32>);
    static_assert(std::is_same_v<d::Common_t<Uint16, unsigned int>, Uint32>);
    static_assert(std::is_same_v<d::Common_t<Int8, double>, Float64>);
}
