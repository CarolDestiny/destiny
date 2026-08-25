#include <gtest/gtest.h>

#include <limits>

#include "destiny/basicType/destinyNumeric/destinyNumeric.hpp"

using namespace destiny;
namespace d = basicType::destinyNumeric::detail;

// 为避免 gtest TYPED_TEST 宏在部分工具链上的运行时问题，用宏对 4 个 Uint 类型参数化。

#define DESTINY_UINT_ACCESS_BODY(T, U, W)                                                                              \
    {                                                                                                                  \
        /* bit/setBit 往返：置位读回，全置后 = max，全清后 = 0 */                                                      \
        T v(static_cast<U>(0));                                                                                        \
        for (int i = 0; i < (W); ++i) {                                                                                \
            const auto idx = static_cast<std::size_t>(i);                                                              \
            v.setBit(Bool(true), idx);                                                                                 \
            Bool b;                                                                                                    \
            v.bit(b, idx);                                                                                             \
            EXPECT_TRUE(b.value()) << "bit " << i;                                                                     \
        }                                                                                                              \
        EXPECT_EQ(v.value(), std::numeric_limits<U>::max());                                                           \
        for (int i = 0; i < (W); ++i) {                                                                                \
            const auto idx = static_cast<std::size_t>(i);                                                              \
            v.setBit(Bool(false), idx);                                                                                \
            Bool b;                                                                                                    \
            v.bit(b, idx);                                                                                             \
            EXPECT_FALSE(b.value()) << "bit " << i;                                                                    \
        }                                                                                                              \
        EXPECT_EQ(v.value(), static_cast<U>(0));                                                                       \
    }                                                                                                                  \
    {                                                                                                                  \
        /* setBit 只影响目标位 */                                                                                      \
        T v(static_cast<U>(0));                                                                                        \
        const auto target = static_cast<std::size_t>((W) / 2);                                                         \
        v.setBit(Bool(true), target);                                                                                  \
        for (int i = 0; i < (W); ++i) {                                                                                \
            const auto idx = static_cast<std::size_t>(i);                                                              \
            Bool b;                                                                                                    \
            v.bit(b, idx);                                                                                             \
            EXPECT_EQ(b.value(), idx == target) << "bit " << i;                                                        \
        }                                                                                                              \
    }

// Uint8 只有 bit 接口；piece/byte 仅对更宽类型
#define DESTINY_UINT_ACCESS_BODY_WIDE(T, U, W)                                                                         \
    DESTINY_UINT_ACCESS_BODY(T, U, W)                                                                                  \
    {                                                                                                                  \
        /* piece(Uint8) 往返，LSB-first 约定 */                                                                        \
        T v(static_cast<U>(0));                                                                                        \
        v.setPiece(Uint8(0xAB), 0);                                                                                    \
        v.setPiece(Uint8(0xCD), 1);                                                                                    \
        Uint8 lo, hi;                                                                                                  \
        v.piece(lo, 0);                                                                                                \
        v.piece(hi, 1);                                                                                                \
        EXPECT_EQ(lo.value(), 0xAB);                                                                                   \
        EXPECT_EQ(hi.value(), 0xCD);                                                                                   \
        EXPECT_EQ(v.value(), static_cast<U>(0xCDAB));                                                                  \
        T w(static_cast<U>(0x1234));                                                                                   \
        Uint8 wlo, whi;                                                                                                \
        w.piece(wlo, 0);                                                                                               \
        w.piece(whi, 1);                                                                                               \
        EXPECT_EQ(wlo.value(), 0x34);                                                                                  \
        EXPECT_EQ(whi.value(), 0x12);                                                                                  \
    }                                                                                                                  \
    {                                                                                                                  \
        /* byte/setByte 内存视图（小端平台断言） */                                                                    \
        T v(static_cast<U>(0x1234));                                                                                   \
        Uint8 b0, b1;                                                                                                  \
        v.byte(b0, 0);                                                                                                 \
        v.byte(b1, 1);                                                                                                 \
        EXPECT_EQ(b0.value(), 0x34);                                                                                   \
        EXPECT_EQ(b1.value(), 0x12);                                                                                   \
        v.setByte(Uint8(0x78), 0);                                                                                     \
        Uint8 read;                                                                                                    \
        v.byte(read, 0);                                                                                               \
        EXPECT_EQ(read.value(), 0x78);                                                                                 \
    }

#define DESTINY_UINT_ACCESS_TEST(T, U, W)                                                                              \
    TEST(UintAccessTest, T)                                                                                            \
    {                                                                                                                  \
        DESTINY_UINT_ACCESS_BODY_WIDE(T, U, W)                                                                         \
    }

#define DESTINY_UINT_BIT_ONLY_TEST(T, U, W)                                                                            \
    TEST(UintAccessTest, T)                                                                                            \
    {                                                                                                                  \
        DESTINY_UINT_ACCESS_BODY(T, U, W)                                                                              \
    }

DESTINY_UINT_BIT_ONLY_TEST(Uint8, unsigned char, 8)
DESTINY_UINT_ACCESS_TEST(Uint16, unsigned short, 16)
DESTINY_UINT_ACCESS_TEST(Uint32, unsigned int, 32)
DESTINY_UINT_ACCESS_TEST(Uint64, unsigned long long, 64)
