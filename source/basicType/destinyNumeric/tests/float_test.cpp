#include <gtest/gtest.h>

#include <typeinfo>

#include "destiny/basicType/destinyNumeric/destinyNumeric.hpp"

using namespace destiny;
namespace d = basicType::destinyNumeric::detail;

// 为避免 gtest TYPED_TEST 宏在部分工具链上的运行时问题，用宏对 Float32/64 参数化。

#define DESTINY_FLOAT_TEST_BODY(T, U, B, ONEBITS, ZEROBITS, NANBITS, INFBITS)                                          \
    {                                                                                                                  \
        T v;                                                                                                           \
        EXPECT_DOUBLE_EQ(v.value(), 0.0); /* 默认构造为 0.0 */                                                         \
    }                                                                                                                  \
    {                                                                                                                  \
        T v(static_cast<U>(3.5));                                                                                      \
        EXPECT_DOUBLE_EQ(v.value(), 3.5);                                                                              \
    }                                                                                                                  \
    {                                                                                                                  \
        T a(static_cast<U>(2.5));                                                                                      \
        T b(a);                                                                                                        \
        EXPECT_DOUBLE_EQ(b.value(), 2.5);                                                                              \
        T c(std::move(b));                                                                                             \
        EXPECT_DOUBLE_EQ(c.value(), 2.5);                                                                              \
        T d;                                                                                                           \
        d = c;                                                                                                         \
        EXPECT_DOUBLE_EQ(d.value(), 2.5);                                                                              \
    }                                                                                                                  \
    {                                                                                                                  \
        T v(static_cast<U>(10.0));                                                                                     \
        v += T(static_cast<U>(2.0));                                                                                   \
        EXPECT_DOUBLE_EQ(v.value(), 12.0);                                                                             \
        v -= T(static_cast<U>(3.0));                                                                                   \
        EXPECT_DOUBLE_EQ(v.value(), 9.0);                                                                              \
        v *= T(static_cast<U>(2.0));                                                                                   \
        EXPECT_DOUBLE_EQ(v.value(), 18.0);                                                                             \
        v /= T(static_cast<U>(4.0));                                                                                   \
        EXPECT_DOUBLE_EQ(v.value(), 4.5);                                                                              \
    }                                                                                                                  \
    {                                                                                                                  \
        T v(static_cast<U>(1.5));                                                                                      \
        EXPECT_DOUBLE_EQ((++v).value(), 2.5);                                                                          \
        EXPECT_DOUBLE_EQ((v++).value(), 2.5);                                                                          \
        EXPECT_DOUBLE_EQ(v.value(), 3.5);                                                                              \
        EXPECT_DOUBLE_EQ((--v).value(), 2.5);                                                                          \
        EXPECT_DOUBLE_EQ((v--).value(), 2.5);                                                                          \
        EXPECT_DOUBLE_EQ(v.value(), 1.5);                                                                              \
    }                                                                                                                  \
    {                                                                                                                  \
        T v(static_cast<U>(-123.456));                                                                                 \
        T round = T::fromBits(v.bits());                                                                               \
        EXPECT_DOUBLE_EQ(round.value(), v.value());                                                                    \
    }                                                                                                                  \
    {                                                                                                                  \
        EXPECT_EQ(T(static_cast<U>(1.0)).bits().value(), (ONEBITS));                                                   \
        EXPECT_EQ(T(static_cast<U>(0.0)).bits().value(), (ZEROBITS));                                                  \
        EXPECT_DOUBLE_EQ(T::fromBits(B(ONEBITS)).value(), 1.0);                                                        \
    }                                                                                                                  \
    {                                                                                                                  \
        /* NaN：IEEE 语义，NaN != NaN，所有比较 false */                                                               \
        T nan = T::fromBits(B(NANBITS));                                                                               \
        const double nv = static_cast<double>(nan.value());                                                            \
        EXPECT_FALSE(nv == nv);                                                                                        \
        EXPECT_TRUE(nv != nv);                                                                                         \
        EXPECT_FALSE(nv < nv);                                                                                         \
        EXPECT_FALSE(nv > nv);                                                                                         \
        EXPECT_FALSE(nv <= nv);                                                                                        \
        EXPECT_FALSE(nv >= nv);                                                                                        \
    }                                                                                                                  \
    {                                                                                                                  \
        /* 正无穷 */                                                                                                   \
        T inf = T::fromBits(B(INFBITS));                                                                               \
        EXPECT_TRUE(static_cast<double>(inf.value()) > 0.0);                                                           \
    }

#define DESTINY_FLOAT_TEST(T, U, B, ONEBITS, ZEROBITS, NANBITS, INFBITS)                                               \
    TEST(FloatTest, T)                                                                                                 \
    {                                                                                                                  \
        DESTINY_FLOAT_TEST_BODY(T, U, B, ONEBITS, ZEROBITS, NANBITS, INFBITS)                                          \
    }

DESTINY_FLOAT_TEST(Float32, float, Uint32, 0x3F800000u, 0u, 0x7FC00000u, 0x7F800000u)
DESTINY_FLOAT_TEST(Float64, double, Uint64, 0x3FF0000000000000ULL, 0ULL, 0x7FF8000000000000ULL, 0x7FF0000000000000ULL)
