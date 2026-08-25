#include <gtest/gtest.h>

#include <limits>
#include <typeinfo>

#include "destiny/basicType/destinyNumeric/destinyNumeric.hpp"

using namespace destiny;
namespace d = basicType::destinyNumeric::detail;

// 为避免 gtest TYPED_TEST 宏在部分工具链上的运行时问题，用宏对 8 个整数类型参数化。

#define DESTINY_INT_TEST_BODY(T, U)                                                                                    \
    static_assert(std::is_same_v<d::NumericTraits<T>::Underlying, U>);                                                 \
    {                                                                                                                  \
        T v;                                                                                                           \
        EXPECT_EQ(v.value(), static_cast<U>(0)); /* 默认构造为 0 */                                                    \
    }                                                                                                                  \
    {                                                                                                                  \
        T v(static_cast<U>(42));                                                                                       \
        EXPECT_EQ(v.value(), static_cast<U>(42));                                                                      \
    }                                                                                                                  \
    {                                                                                                                  \
        T a(static_cast<U>(7));                                                                                        \
        T b(a);                                                                                                        \
        EXPECT_EQ(b.value(), static_cast<U>(7));                                                                       \
        T c;                                                                                                           \
        c = a;                                                                                                         \
        EXPECT_EQ(c.value(), static_cast<U>(7));                                                                       \
    }                                                                                                                  \
    {                                                                                                                  \
        T a(static_cast<U>(10));                                                                                       \
        a += T(static_cast<U>(2));                                                                                     \
        EXPECT_EQ(a.value(), static_cast<U>(12));                                                                      \
        a -= T(static_cast<U>(3));                                                                                     \
        EXPECT_EQ(a.value(), static_cast<U>(9));                                                                       \
        a *= T(static_cast<U>(2));                                                                                     \
        EXPECT_EQ(a.value(), static_cast<U>(18));                                                                      \
        a /= T(static_cast<U>(3));                                                                                     \
        EXPECT_EQ(a.value(), static_cast<U>(6));                                                                       \
    }                                                                                                                  \
    {                                                                                                                  \
        T v(static_cast<U>(17));                                                                                       \
        v %= T(static_cast<U>(5));                                                                                     \
        EXPECT_EQ(v.value(), static_cast<U>(2));                                                                       \
    }                                                                                                                  \
    {                                                                                                                  \
        T v(static_cast<U>(1));                                                                                        \
        EXPECT_EQ((++v).value(), static_cast<U>(2));                                                                   \
        EXPECT_EQ((v++).value(), static_cast<U>(2));                                                                   \
        EXPECT_EQ(v.value(), static_cast<U>(3));                                                                       \
        EXPECT_EQ((--v).value(), static_cast<U>(2));                                                                   \
        EXPECT_EQ((v--).value(), static_cast<U>(2));                                                                   \
        EXPECT_EQ(v.value(), static_cast<U>(1));                                                                       \
    }                                                                                                                  \
    {                                                                                                                  \
        T v(static_cast<U>(5));                                                                                        \
        EXPECT_EQ((+v).value(), static_cast<U>(5));                                                                    \
    }                                                                                                                  \
    {                                                                                                                  \
        constexpr bool IsSigned = std::is_signed_v<U>;                                                                 \
        if constexpr (IsSigned) {                                                                                      \
            EXPECT_EQ((-T(static_cast<U>(5))).value(), static_cast<U>(-5));                                            \
        }                                                                                                              \
        else {                                                                                                         \
            EXPECT_EQ((-T(static_cast<U>(1))).value(), std::numeric_limits<U>::max());                                 \
        }                                                                                                              \
    }                                                                                                                  \
    {                                                                                                                  \
        constexpr bool IsSigned = std::is_signed_v<U>;                                                                 \
        if constexpr (IsSigned) {                                                                                      \
            EXPECT_EQ((~T(static_cast<U>(5))).value(), static_cast<U>(~5));                                            \
        }                                                                                                              \
        else {                                                                                                         \
            EXPECT_EQ((~T(static_cast<U>(0))).value(), std::numeric_limits<U>::max());                                 \
        }                                                                                                              \
    }                                                                                                                  \
    {                                                                                                                  \
        T a(static_cast<U>(0b1010));                                                                                   \
        T b(static_cast<U>(0b1100));                                                                                   \
        EXPECT_EQ((a & b).value(), static_cast<U>(0b1000));                                                            \
        EXPECT_EQ((a | b).value(), static_cast<U>(0b1110));                                                            \
        EXPECT_EQ((a ^ b).value(), static_cast<U>(0b0110));                                                            \
    }                                                                                                                  \
    {                                                                                                                  \
        EXPECT_EQ((T(static_cast<U>(1)) << 1).value(), static_cast<U>(2));                                             \
        EXPECT_EQ((T(static_cast<U>(4)) >> 1).value(), static_cast<U>(2));                                             \
    }                                                                                                                  \
    {                                                                                                                  \
        T a(static_cast<U>(5));                                                                                        \
        T b(static_cast<U>(5));                                                                                        \
        T c(static_cast<U>(6));                                                                                        \
        EXPECT_TRUE(a == b);                                                                                           \
        EXPECT_FALSE(a != b);                                                                                          \
        EXPECT_TRUE(a != c);                                                                                           \
        EXPECT_TRUE(a < c);                                                                                            \
        EXPECT_TRUE(c > a);                                                                                            \
        EXPECT_TRUE(a <= b);                                                                                           \
        EXPECT_TRUE(a >= b);                                                                                           \
    }                                                                                                                  \
    {                                                                                                                  \
        EXPECT_EQ(T(static_cast<U>(1)) <=> T(static_cast<U>(2)), std::strong_ordering::less);                          \
        EXPECT_EQ(T(static_cast<U>(2)) <=> T(static_cast<U>(2)), std::strong_ordering::equal);                         \
        EXPECT_EQ(T(static_cast<U>(3)) <=> T(static_cast<U>(2)), std::strong_ordering::greater);                       \
    }                                                                                                                  \
    {                                                                                                                  \
        auto r = T(static_cast<U>(5)) + 2;                                                                             \
        static_assert(std::is_same_v<decltype(r), d::Common_t<T, int>>);                                               \
        EXPECT_EQ(static_cast<long long>(r.value()), 7);                                                               \
    }                                                                                                                  \
    {                                                                                                                  \
        EXPECT_EQ(T(std::numeric_limits<U>::min()).value(), std::numeric_limits<U>::min());                            \
        EXPECT_EQ(T(std::numeric_limits<U>::max()).value(), std::numeric_limits<U>::max());                            \
    }

#define DESTINY_INT_TEST(T, U)                                                                                         \
    TEST(IntegerTest, T)                                                                                               \
    {                                                                                                                  \
        DESTINY_INT_TEST_BODY(T, U)                                                                                    \
    }

DESTINY_INT_TEST(Int8, signed char)
DESTINY_INT_TEST(Int16, signed short)
DESTINY_INT_TEST(Int32, signed int)
DESTINY_INT_TEST(Int64, signed long long)
DESTINY_INT_TEST(Uint8, unsigned char)
DESTINY_INT_TEST(Uint16, unsigned short)
DESTINY_INT_TEST(Uint32, unsigned int)
DESTINY_INT_TEST(Uint64, unsigned long long)

// 模块生命周期钩子
TEST(NumericModule, LifecycleHooks)
{
    EXPECT_TRUE(basicType::destinyNumeric::onload());
    EXPECT_NO_THROW(basicType::destinyNumeric::unload());
}
