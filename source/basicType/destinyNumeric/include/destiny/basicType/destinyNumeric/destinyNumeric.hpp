// create bt deepseek v4 flash 0721
#pragma once
#include <compare>
#include <concepts>
#include <cstddef>
#include <type_traits>

namespace destiny
{
    class Bool;
    class Int8;
    class Int16;
    class Int32;
    class Int64;
    class Uint8;
    class Uint16;
    class Uint32;
    class Uint64;
    class Float32;
    class Float64;
} // namespace destiny

namespace destiny::basicType::destinyNumeric
{
    bool onload() noexcept;
    void unload() noexcept;
} // namespace destiny::basicType::destinyNumeric

namespace destiny::basicType::destinyNumeric::detail
{
    using ::destiny::Bool;
    using ::destiny::Float32;
    using ::destiny::Float64;
    using ::destiny::Int16;
    using ::destiny::Int32;
    using ::destiny::Int64;
    using ::destiny::Int8;
    using ::destiny::Uint16;
    using ::destiny::Uint32;
    using ::destiny::Uint64;
    using ::destiny::Uint8;

    template <typename T, typename... Ts>
    inline constexpr bool IsOneOf = (std::is_same_v<std::remove_cvref_t<T>, Ts> || ...);

    template <typename T>
    concept IntegerType = IsOneOf<T, Int8, Int16, Int32, Int64, Uint8, Uint16, Uint32, Uint64>;

    template <typename T>
    concept FloatingType = IsOneOf<T, Float32, Float64>;

    template <typename T>
    concept BoolType = std::same_as<std::remove_cvref_t<T>, Bool>;

    template <typename T>
    concept NumericType = IntegerType<T> || FloatingType<T> || BoolType<T>;

    template <typename T>
    concept BuiltinInteger = std::is_integral_v<T> && !std::same_as<std::remove_cvref_t<T>, bool>;

    template <typename T>
    concept AnyInteger = IntegerType<T> || BuiltinInteger<T>;

    template <NumericType T> constexpr auto toValue(const T& v) noexcept
    {
        return v.value();
    }

    template <typename T>
        requires(!NumericType<T>) && (std::is_integral_v<T> || std::is_floating_point_v<T>)
    constexpr T toValue(T v) noexcept
    {
        return v;
    }

    template <typename T> struct NumericTraits;

    template <> struct NumericTraits<Int8>
    {
        using Underlying = signed char;
        static constexpr int Width = 8;
        static constexpr bool Signed = true;
        static constexpr bool Float = false;
    };

    template <> struct NumericTraits<Int16>
    {
        using Underlying = signed short;
        static constexpr int Width = 16;
        static constexpr bool Signed = true;
        static constexpr bool Float = false;
    };

    template <> struct NumericTraits<Int32>
    {
        using Underlying = signed int;
        static constexpr int Width = 32;
        static constexpr bool Signed = true;
        static constexpr bool Float = false;
    };

    template <> struct NumericTraits<Int64>
    {
        using Underlying = signed long long;
        static constexpr int Width = 64;
        static constexpr bool Signed = true;
        static constexpr bool Float = false;
    };

    template <> struct NumericTraits<Uint8>
    {
        using Underlying = unsigned char;
        static constexpr int Width = 8;
        static constexpr bool Signed = false;
        static constexpr bool Float = false;
    };

    template <> struct NumericTraits<Uint16>
    {
        using Underlying = unsigned short;
        static constexpr int Width = 16;
        static constexpr bool Signed = false;
        static constexpr bool Float = false;
    };

    template <> struct NumericTraits<Uint32>
    {
        using Underlying = unsigned int;
        static constexpr int Width = 32;
        static constexpr bool Signed = false;
        static constexpr bool Float = false;
    };

    template <> struct NumericTraits<Uint64>
    {
        using Underlying = unsigned long long;
        static constexpr int Width = 64;
        static constexpr bool Signed = false;
        static constexpr bool Float = false;
    };

    template <> struct NumericTraits<Float32>
    {
        using Underlying = float;
        static constexpr int Width = 32;
        static constexpr bool Signed = true;
        static constexpr bool Float = true;
    };

    template <> struct NumericTraits<Float64>
    {
        using Underlying = double;
        static constexpr int Width = 64;
        static constexpr bool Signed = true;
        static constexpr bool Float = true;
    };

    template <> struct NumericTraits<Bool>
    {
        using Underlying = bool;
        static constexpr int Width = 0;
        static constexpr bool Signed = true;
        static constexpr bool Float = false;
    };

    template <int Width, bool Signed> struct IntegerOf;

    template <> struct IntegerOf<8, true>
    {
        using Type = Int8;
    };
    template <> struct IntegerOf<16, true>
    {
        using Type = Int16;
    };
    template <> struct IntegerOf<32, true>
    {
        using Type = Int32;
    };
    template <> struct IntegerOf<64, true>
    {
        using Type = Int64;
    };
    template <> struct IntegerOf<8, false>
    {
        using Type = Uint8;
    };
    template <> struct IntegerOf<16, false>
    {
        using Type = Uint16;
    };
    template <> struct IntegerOf<32, false>
    {
        using Type = Uint32;
    };
    template <> struct IntegerOf<64, false>
    {
        using Type = Uint64;
    };

    template <typename T> struct Classify
    {
        using Type = std::remove_cvref_t<T>;
    };

    template <std::integral T>
        requires(!std::same_as<T, bool>) && (!IsOneOf<T, char, wchar_t, char8_t, char16_t, char32_t>)
    struct Classify<T>
    {
        using Type = typename IntegerOf<static_cast<int>(sizeof(T) * 8), std::is_signed_v<T>>::Type;
    };

    template <std::floating_point T>
        requires(!std::same_as<T, long double>)
    struct Classify<T>
    {
        using Type = std::conditional_t<std::is_same_v<T, float>, Float32, Float64>;
    };

    template <> struct Classify<bool>
    {
        using Type = Bool;
    };

    template <typename T> using Classify_t = typename Classify<std::remove_cvref_t<T>>::Type;

    template <typename T> using Underlying_t = typename NumericTraits<Classify_t<T>>::Underlying;

    // 异符号同宽时取有符号一方加宽一级；64 位已达上限，落到 Uint64
    template <typename T> struct WidenSigned
    {
        static constexpr int W = NumericTraits<T>::Width;
        static constexpr int Next = (W < 16) ? 16 : (W < 32) ? 32 : (W < 64) ? 64 : 64;
        using Type = std::conditional_t<W >= 64, Uint64, typename IntegerOf<Next, true>::Type>;
    };

    // 整数提升：同符号取宽；异符号同宽取有符号并加宽一级；异符号异宽取宽者
    template <typename A, typename B> struct CommonInteger
    {
        static constexpr bool ASigned = NumericTraits<A>::Signed;
        static constexpr bool BSigned = NumericTraits<B>::Signed;
        static constexpr int AWidth = NumericTraits<A>::Width;
        static constexpr int BWidth = NumericTraits<B>::Width;

        using Type = std::conditional_t<
            ASigned == BSigned, typename IntegerOf<(AWidth > BWidth ? AWidth : BWidth), ASigned>::Type,
            std::conditional_t<
                AWidth == BWidth, typename WidenSigned<std::conditional_t<ASigned, A, B>>::Type,
                typename IntegerOf<(AWidth > BWidth ? AWidth : BWidth), (AWidth > BWidth ? ASigned : BSigned)>::Type>>;
    };

    // Bool 参与算术时按 cstdint 语义提升为 Int32
    template <typename T> struct LiftBool
    {
        using Type = T;
    };

    template <> struct LiftBool<Bool>
    {
        using Type = Int32;
    };

    template <typename A, typename B> struct CommonImpl;

    template <IntegerType A, IntegerType B> struct CommonImpl<A, B>
    {
        using Type = typename CommonInteger<A, B>::Type;
    };

    template <FloatingType A, FloatingType B> struct CommonImpl<A, B>
    {
        using Type = std::conditional_t<NumericTraits<A>::Width >= NumericTraits<B>::Width, A, B>;
    };

    template <IntegerType A, FloatingType B> struct CommonImpl<A, B>
    {
        using Type = Float64;
    };

    template <FloatingType A, IntegerType B> struct CommonImpl<A, B>
    {
        using Type = Float64;
    };

    // 结果类型：内建先归入族类型，Bool 提升为 Int32，再按类别规则
    template <typename L, typename R> struct Common
    {
        using A = typename LiftBool<Classify_t<L>>::Type;
        using B = typename LiftBool<Classify_t<R>>::Type;
        using Type = typename CommonImpl<A, B>::Type;
    };

    template <typename L, typename R> using Common_t = typename Common<L, R>::Type;
} // namespace destiny::basicType::destinyNumeric::detail

class destiny::Bool
{
public:
    Bool() noexcept;
    Bool(bool value) noexcept;
    Bool(const Bool& other) noexcept;
    Bool& operator=(const Bool& other) noexcept;
    bool value() const noexcept;
    operator bool() const noexcept;
    template <typename U>
        requires basicType::destinyNumeric::detail::NumericType<U> && (!std::same_as<std::remove_cvref_t<U>, Bool>)
    Bool(const U& other) noexcept;

private:
    bool data_;
};

class destiny::Int8
{
public:
    Int8() noexcept;
    ~Int8() noexcept;
    Int8(signed char value) noexcept;
    Int8(const Int8& other) noexcept;
    Int8(Int8&& other) noexcept;
    template <typename U>
        requires basicType::destinyNumeric::detail::NumericType<U> && (!std::same_as<std::remove_cvref_t<U>, Int8>)
    Int8(const U& other) noexcept;
    Int8& operator=(const Int8& other) noexcept;
    Int8& operator=(Int8&& other) noexcept;
    signed char value() const noexcept;
    Int8& operator+=(const Int8& other) noexcept;
    Int8& operator-=(const Int8& other) noexcept;
    Int8& operator*=(const Int8& other) noexcept;
    Int8& operator/=(const Int8& other) noexcept;
    Int8& operator%=(const Int8& other) noexcept;
    Int8& operator&=(const Int8& other) noexcept;
    Int8& operator|=(const Int8& other) noexcept;
    Int8& operator^=(const Int8& other) noexcept;
    Int8& operator<<=(const Int8& other) noexcept;
    Int8& operator>>=(const Int8& other) noexcept;
    Int8& operator++() noexcept;
    Int8 operator++(int) noexcept;
    Int8& operator--() noexcept;
    Int8 operator--(int) noexcept;

private:
    signed char data_;
};

class destiny::Int16
{
public:
    Int16() noexcept;
    ~Int16() noexcept;
    Int16(signed short value) noexcept;
    Int16(const Int16& other) noexcept;
    Int16(Int16&& other) noexcept;
    template <typename U>
        requires basicType::destinyNumeric::detail::NumericType<U> && (!std::same_as<std::remove_cvref_t<U>, Int16>)
    Int16(const U& other) noexcept;
    Int16& operator=(const Int16& other) noexcept;
    Int16& operator=(Int16&& other) noexcept;
    signed short value() const noexcept;
    Int16& operator+=(const Int16& other) noexcept;
    Int16& operator-=(const Int16& other) noexcept;
    Int16& operator*=(const Int16& other) noexcept;
    Int16& operator/=(const Int16& other) noexcept;
    Int16& operator%=(const Int16& other) noexcept;
    Int16& operator&=(const Int16& other) noexcept;
    Int16& operator|=(const Int16& other) noexcept;
    Int16& operator^=(const Int16& other) noexcept;
    Int16& operator<<=(const Int16& other) noexcept;
    Int16& operator>>=(const Int16& other) noexcept;
    Int16& operator++() noexcept;
    Int16 operator++(int) noexcept;
    Int16& operator--() noexcept;
    Int16 operator--(int) noexcept;

private:
    signed short data_;
};

class destiny::Int32
{
public:
    Int32() noexcept;
    ~Int32() noexcept;
    Int32(signed int value) noexcept;
    Int32(const Int32& other) noexcept;
    Int32(Int32&& other) noexcept;
    template <typename U>
        requires basicType::destinyNumeric::detail::NumericType<U> && (!std::same_as<std::remove_cvref_t<U>, Int32>)
    Int32(const U& other) noexcept;
    Int32& operator=(const Int32& other) noexcept;
    Int32& operator=(Int32&& other) noexcept;
    signed int value() const noexcept;
    Int32& operator+=(const Int32& other) noexcept;
    Int32& operator-=(const Int32& other) noexcept;
    Int32& operator*=(const Int32& other) noexcept;
    Int32& operator/=(const Int32& other) noexcept;
    Int32& operator%=(const Int32& other) noexcept;
    Int32& operator&=(const Int32& other) noexcept;
    Int32& operator|=(const Int32& other) noexcept;
    Int32& operator^=(const Int32& other) noexcept;
    Int32& operator<<=(const Int32& other) noexcept;
    Int32& operator>>=(const Int32& other) noexcept;
    Int32& operator++() noexcept;
    Int32 operator++(int) noexcept;
    Int32& operator--() noexcept;
    Int32 operator--(int) noexcept;

private:
    signed int data_;
};

class destiny::Int64
{
public:
    Int64() noexcept;
    ~Int64() noexcept;
    Int64(signed long long value) noexcept;
    Int64(const Int64& other) noexcept;
    Int64(Int64&& other) noexcept;
    template <typename U>
        requires basicType::destinyNumeric::detail::NumericType<U> && (!std::same_as<std::remove_cvref_t<U>, Int64>)
    Int64(const U& other) noexcept;
    Int64& operator=(const Int64& other) noexcept;
    Int64& operator=(Int64&& other) noexcept;
    signed long long value() const noexcept;
    Int64& operator+=(const Int64& other) noexcept;
    Int64& operator-=(const Int64& other) noexcept;
    Int64& operator*=(const Int64& other) noexcept;
    Int64& operator/=(const Int64& other) noexcept;
    Int64& operator%=(const Int64& other) noexcept;
    Int64& operator&=(const Int64& other) noexcept;
    Int64& operator|=(const Int64& other) noexcept;
    Int64& operator^=(const Int64& other) noexcept;
    Int64& operator<<=(const Int64& other) noexcept;
    Int64& operator>>=(const Int64& other) noexcept;
    Int64& operator++() noexcept;
    Int64 operator++(int) noexcept;
    Int64& operator--() noexcept;
    Int64 operator--(int) noexcept;

private:
    signed long long data_;
};

class destiny::Uint8
{
public:
    Uint8() noexcept;
    ~Uint8() noexcept;
    Uint8(unsigned char value) noexcept;
    Uint8(const Uint8& other) noexcept;
    Uint8(Uint8&& other) noexcept;
    template <typename U>
        requires basicType::destinyNumeric::detail::NumericType<U> && (!std::same_as<std::remove_cvref_t<U>, Uint8>)
    Uint8(const U& other) noexcept;
    Uint8& operator=(const Uint8& other) noexcept;
    Uint8& operator=(Uint8&& other) noexcept;
    unsigned char value() const noexcept;
    void bit(Bool& out, std::size_t i) const noexcept;
    void setBit(Bool v, std::size_t i) noexcept;
    Uint8& operator+=(const Uint8& other) noexcept;
    Uint8& operator-=(const Uint8& other) noexcept;
    Uint8& operator*=(const Uint8& other) noexcept;
    Uint8& operator/=(const Uint8& other) noexcept;
    Uint8& operator%=(const Uint8& other) noexcept;
    Uint8& operator&=(const Uint8& other) noexcept;
    Uint8& operator|=(const Uint8& other) noexcept;
    Uint8& operator^=(const Uint8& other) noexcept;
    Uint8& operator<<=(const Uint8& other) noexcept;
    Uint8& operator>>=(const Uint8& other) noexcept;
    Uint8& operator++() noexcept;
    Uint8 operator++(int) noexcept;
    Uint8& operator--() noexcept;
    Uint8 operator--(int) noexcept;

private:
    unsigned char data_;
};

class destiny::Uint16
{
public:
    Uint16() noexcept;
    ~Uint16() noexcept;
    Uint16(unsigned short value) noexcept;
    Uint16(const Uint16& other) noexcept;
    Uint16(Uint16&& other) noexcept;
    template <typename U>
        requires basicType::destinyNumeric::detail::NumericType<U> && (!std::same_as<std::remove_cvref_t<U>, Uint16>)
    Uint16(const U& other) noexcept;
    Uint16& operator=(const Uint16& other) noexcept;
    Uint16& operator=(Uint16&& other) noexcept;
    unsigned short value() const noexcept;
    void piece(Uint8& out, std::size_t i) const noexcept;
    void setPiece(Uint8 v, std::size_t i) noexcept;
    void byte(Uint8& out, std::size_t i) const noexcept;
    void setByte(Uint8 v, std::size_t i) noexcept;
    void bit(Bool& out, std::size_t i) const noexcept;
    void setBit(Bool v, std::size_t i) noexcept;
    Uint16& operator+=(const Uint16& other) noexcept;
    Uint16& operator-=(const Uint16& other) noexcept;
    Uint16& operator*=(const Uint16& other) noexcept;
    Uint16& operator/=(const Uint16& other) noexcept;
    Uint16& operator%=(const Uint16& other) noexcept;
    Uint16& operator&=(const Uint16& other) noexcept;
    Uint16& operator|=(const Uint16& other) noexcept;
    Uint16& operator^=(const Uint16& other) noexcept;
    Uint16& operator<<=(const Uint16& other) noexcept;
    Uint16& operator>>=(const Uint16& other) noexcept;
    Uint16& operator++() noexcept;
    Uint16 operator++(int) noexcept;
    Uint16& operator--() noexcept;
    Uint16 operator--(int) noexcept;

private:
    unsigned short data_;
};

class destiny::Uint32
{
public:
    Uint32() noexcept;
    ~Uint32() noexcept;
    Uint32(unsigned int value) noexcept;
    Uint32(const Uint32& other) noexcept;
    Uint32(Uint32&& other) noexcept;
    template <typename U>
        requires basicType::destinyNumeric::detail::NumericType<U> && (!std::same_as<std::remove_cvref_t<U>, Uint32>)
    Uint32(const U& other) noexcept;
    Uint32& operator=(const Uint32& other) noexcept;
    Uint32& operator=(Uint32&& other) noexcept;
    unsigned int value() const noexcept;
    void piece(Uint8& out, std::size_t i) const noexcept;
    void setPiece(Uint8 v, std::size_t i) noexcept;
    void piece(Uint16& out, std::size_t i) const noexcept;
    void setPiece(Uint16 v, std::size_t i) noexcept;
    void byte(Uint8& out, std::size_t i) const noexcept;
    void setByte(Uint8 v, std::size_t i) noexcept;
    void bit(Bool& out, std::size_t i) const noexcept;
    void setBit(Bool v, std::size_t i) noexcept;
    Uint32& operator+=(const Uint32& other) noexcept;
    Uint32& operator-=(const Uint32& other) noexcept;
    Uint32& operator*=(const Uint32& other) noexcept;
    Uint32& operator/=(const Uint32& other) noexcept;
    Uint32& operator%=(const Uint32& other) noexcept;
    Uint32& operator&=(const Uint32& other) noexcept;
    Uint32& operator|=(const Uint32& other) noexcept;
    Uint32& operator^=(const Uint32& other) noexcept;
    Uint32& operator<<=(const Uint32& other) noexcept;
    Uint32& operator>>=(const Uint32& other) noexcept;
    Uint32& operator++() noexcept;
    Uint32 operator++(int) noexcept;
    Uint32& operator--() noexcept;
    Uint32 operator--(int) noexcept;

private:
    unsigned int data_;
};

class destiny::Uint64
{
public:
    Uint64() noexcept;
    ~Uint64() noexcept;
    Uint64(unsigned long long value) noexcept;
    Uint64(const Uint64& other) noexcept;
    Uint64(Uint64&& other) noexcept;
    template <typename U>
        requires basicType::destinyNumeric::detail::NumericType<U> && (!std::same_as<std::remove_cvref_t<U>, Uint64>)
    Uint64(const U& other) noexcept;
    Uint64& operator=(const Uint64& other) noexcept;
    Uint64& operator=(Uint64&& other) noexcept;
    unsigned long long value() const noexcept;
    void piece(Uint8& out, std::size_t i) const noexcept;
    void setPiece(Uint8 v, std::size_t i) noexcept;
    void piece(Uint16& out, std::size_t i) const noexcept;
    void setPiece(Uint16 v, std::size_t i) noexcept;
    void piece(Uint32& out, std::size_t i) const noexcept;
    void setPiece(Uint32 v, std::size_t i) noexcept;
    void byte(Uint8& out, std::size_t i) const noexcept;
    void setByte(Uint8 v, std::size_t i) noexcept;
    void bit(Bool& out, std::size_t i) const noexcept;
    void setBit(Bool v, std::size_t i) noexcept;
    Uint64& operator+=(const Uint64& other) noexcept;
    Uint64& operator-=(const Uint64& other) noexcept;
    Uint64& operator*=(const Uint64& other) noexcept;
    Uint64& operator/=(const Uint64& other) noexcept;
    Uint64& operator%=(const Uint64& other) noexcept;
    Uint64& operator&=(const Uint64& other) noexcept;
    Uint64& operator|=(const Uint64& other) noexcept;
    Uint64& operator^=(const Uint64& other) noexcept;
    Uint64& operator<<=(const Uint64& other) noexcept;
    Uint64& operator>>=(const Uint64& other) noexcept;
    Uint64& operator++() noexcept;
    Uint64 operator++(int) noexcept;
    Uint64& operator--() noexcept;
    Uint64 operator--(int) noexcept;

private:
    unsigned long long data_;
};

class destiny::Float32
{
public:
    Float32() noexcept;
    Float32(float value) noexcept;
    Float32(const Float32& other) noexcept;
    Float32(Float32&& other) noexcept;
    template <typename U>
        requires basicType::destinyNumeric::detail::NumericType<U> && (!std::same_as<std::remove_cvref_t<U>, Float32>)
    Float32(const U& other) noexcept;
    Float32& operator=(const Float32& other) noexcept;
    Float32& operator=(Float32&& other) noexcept;
    float value() const noexcept;

    Float32& operator+=(const Float32& other) noexcept;
    Float32& operator-=(const Float32& other) noexcept;
    Float32& operator*=(const Float32& other) noexcept;
    Float32& operator/=(const Float32& other) noexcept;

    Float32& operator++() noexcept;
    Float32 operator++(int) noexcept;
    Float32& operator--() noexcept;
    Float32 operator--(int) noexcept;

    Uint32 bits() const noexcept;
    static Float32 fromBits(Uint32 b) noexcept;

private:
    float data_;
};

class destiny::Float64
{
public:
    Float64() noexcept;
    Float64(double value) noexcept;
    Float64(const Float64& other) noexcept;
    Float64(Float64&& other) noexcept;
    template <typename U>
        requires basicType::destinyNumeric::detail::NumericType<U> && (!std::same_as<std::remove_cvref_t<U>, Float64>)
    Float64(const U& other) noexcept;
    Float64& operator=(const Float64& other) noexcept;
    Float64& operator=(Float64&& other) noexcept;
    double value() const noexcept;

    Float64& operator+=(const Float64& other) noexcept;
    Float64& operator-=(const Float64& other) noexcept;
    Float64& operator*=(const Float64& other) noexcept;
    Float64& operator/=(const Float64& other) noexcept;

    Float64& operator++() noexcept;
    Float64 operator++(int) noexcept;
    Float64& operator--() noexcept;
    Float64 operator--(int) noexcept;

    Uint64 bits() const noexcept;
    static Float64 fromBits(Uint64 b) noexcept;

private:
    double data_;
};

// ======================= 跨类型截断构造（模板成员，须内联于头文件）=======================

namespace destiny
{
    template <typename U>
        requires basicType::destinyNumeric::detail::NumericType<U> && (!std::same_as<std::remove_cvref_t<U>, Bool>)
    Bool::Bool(const U& other) noexcept
    {
        data_ = static_cast<bool>(other.value());
        return;
    }

    template <typename U>
        requires basicType::destinyNumeric::detail::NumericType<U> && (!std::same_as<std::remove_cvref_t<U>, Int8>)
    Int8::Int8(const U& other) noexcept
    {
        data_ = static_cast<signed char>(other.value());
        return;
    }

    template <typename U>
        requires basicType::destinyNumeric::detail::NumericType<U> && (!std::same_as<std::remove_cvref_t<U>, Int16>)
    Int16::Int16(const U& other) noexcept
    {
        data_ = static_cast<signed short>(other.value());
        return;
    }

    template <typename U>
        requires basicType::destinyNumeric::detail::NumericType<U> && (!std::same_as<std::remove_cvref_t<U>, Int32>)
    Int32::Int32(const U& other) noexcept
    {
        data_ = static_cast<signed int>(other.value());
        return;
    }

    template <typename U>
        requires basicType::destinyNumeric::detail::NumericType<U> && (!std::same_as<std::remove_cvref_t<U>, Int64>)
    Int64::Int64(const U& other) noexcept
    {
        data_ = static_cast<signed long long>(other.value());
        return;
    }

    template <typename U>
        requires basicType::destinyNumeric::detail::NumericType<U> && (!std::same_as<std::remove_cvref_t<U>, Uint8>)
    Uint8::Uint8(const U& other) noexcept
    {
        data_ = static_cast<unsigned char>(other.value());
        return;
    }

    template <typename U>
        requires basicType::destinyNumeric::detail::NumericType<U> && (!std::same_as<std::remove_cvref_t<U>, Uint16>)
    Uint16::Uint16(const U& other) noexcept
    {
        data_ = static_cast<unsigned short>(other.value());
        return;
    }

    template <typename U>
        requires basicType::destinyNumeric::detail::NumericType<U> && (!std::same_as<std::remove_cvref_t<U>, Uint32>)
    Uint32::Uint32(const U& other) noexcept
    {
        data_ = static_cast<unsigned int>(other.value());
        return;
    }

    template <typename U>
        requires basicType::destinyNumeric::detail::NumericType<U> && (!std::same_as<std::remove_cvref_t<U>, Uint64>)
    Uint64::Uint64(const U& other) noexcept
    {
        data_ = static_cast<unsigned long long>(other.value());
        return;
    }

    template <typename U>
        requires basicType::destinyNumeric::detail::NumericType<U> && (!std::same_as<std::remove_cvref_t<U>, Float32>)
    Float32::Float32(const U& other) noexcept
    {
        data_ = static_cast<float>(other.value());
        return;
    }

    template <typename U>
        requires basicType::destinyNumeric::detail::NumericType<U> && (!std::same_as<std::remove_cvref_t<U>, Float64>)
    Float64::Float64(const U& other) noexcept
    {
        data_ = static_cast<double>(other.value());
        return;
    }

    template <typename L, typename R>
        requires(basicType::destinyNumeric::detail::NumericType<L> || basicType::destinyNumeric::detail::NumericType<R>)
    auto operator+(const L& l, const R& r) noexcept -> basicType::destinyNumeric::detail::Common_t<L, R>
    {
        using C = basicType::destinyNumeric::detail::Common_t<L, R>;
        using U = basicType::destinyNumeric::detail::Underlying_t<C>;
        const auto vl = basicType::destinyNumeric::detail::toValue(l);
        const auto vr = basicType::destinyNumeric::detail::toValue(r);
        return C(static_cast<U>(vl) + static_cast<U>(vr));
    }

    template <typename L, typename R>
        requires(basicType::destinyNumeric::detail::NumericType<L> || basicType::destinyNumeric::detail::NumericType<R>)
    auto operator-(const L& l, const R& r) noexcept -> basicType::destinyNumeric::detail::Common_t<L, R>
    {
        using C = basicType::destinyNumeric::detail::Common_t<L, R>;
        using U = basicType::destinyNumeric::detail::Underlying_t<C>;
        const auto vl = basicType::destinyNumeric::detail::toValue(l);
        const auto vr = basicType::destinyNumeric::detail::toValue(r);
        return C(static_cast<U>(vl) - static_cast<U>(vr));
    }

    template <typename L, typename R>
        requires(basicType::destinyNumeric::detail::NumericType<L> || basicType::destinyNumeric::detail::NumericType<R>)
    auto operator*(const L& l, const R& r) noexcept -> basicType::destinyNumeric::detail::Common_t<L, R>
    {
        using C = basicType::destinyNumeric::detail::Common_t<L, R>;
        using U = basicType::destinyNumeric::detail::Underlying_t<C>;
        const auto vl = basicType::destinyNumeric::detail::toValue(l);
        const auto vr = basicType::destinyNumeric::detail::toValue(r);
        return C(static_cast<U>(vl) * static_cast<U>(vr));
    }

    template <typename L, typename R>
        requires(basicType::destinyNumeric::detail::NumericType<L> || basicType::destinyNumeric::detail::NumericType<R>)
    auto operator/(const L& l, const R& r) noexcept -> basicType::destinyNumeric::detail::Common_t<L, R>
    {
        using C = basicType::destinyNumeric::detail::Common_t<L, R>;
        using U = basicType::destinyNumeric::detail::Underlying_t<C>;
        const auto vl = basicType::destinyNumeric::detail::toValue(l);
        const auto vr = basicType::destinyNumeric::detail::toValue(r);
        return C(static_cast<U>(vl) / static_cast<U>(vr));
    }

    template <typename L, typename R>
        requires basicType::destinyNumeric::detail::AnyInteger<L> && basicType::destinyNumeric::detail::AnyInteger<R>
                 && (basicType::destinyNumeric::detail::IntegerType<L>
                     || basicType::destinyNumeric::detail::IntegerType<R>)
    auto operator%(const L& l, const R& r) noexcept -> basicType::destinyNumeric::detail::Common_t<L, R>
    {
        using C = basicType::destinyNumeric::detail::Common_t<L, R>;
        using U = basicType::destinyNumeric::detail::Underlying_t<C>;
        const auto vl = basicType::destinyNumeric::detail::toValue(l);
        const auto vr = basicType::destinyNumeric::detail::toValue(r);
        return C(static_cast<U>(vl) % static_cast<U>(vr));
    }

    template <typename L, typename R>
        requires basicType::destinyNumeric::detail::AnyInteger<L> && basicType::destinyNumeric::detail::AnyInteger<R>
                 && (basicType::destinyNumeric::detail::IntegerType<L>
                     || basicType::destinyNumeric::detail::IntegerType<R>)
    auto operator&(const L& l, const R& r) noexcept -> basicType::destinyNumeric::detail::Common_t<L, R>
    {
        using C = basicType::destinyNumeric::detail::Common_t<L, R>;
        using U = basicType::destinyNumeric::detail::Underlying_t<C>;
        const auto vl = basicType::destinyNumeric::detail::toValue(l);
        const auto vr = basicType::destinyNumeric::detail::toValue(r);
        return C(static_cast<U>(vl) & static_cast<U>(vr));
    }

    template <typename L, typename R>
        requires basicType::destinyNumeric::detail::AnyInteger<L> && basicType::destinyNumeric::detail::AnyInteger<R>
                 && (basicType::destinyNumeric::detail::IntegerType<L>
                     || basicType::destinyNumeric::detail::IntegerType<R>)
    auto operator|(const L& l, const R& r) noexcept -> basicType::destinyNumeric::detail::Common_t<L, R>
    {
        using C = basicType::destinyNumeric::detail::Common_t<L, R>;
        using U = basicType::destinyNumeric::detail::Underlying_t<C>;
        const auto vl = basicType::destinyNumeric::detail::toValue(l);
        const auto vr = basicType::destinyNumeric::detail::toValue(r);
        return C(static_cast<U>(vl) | static_cast<U>(vr));
    }

    template <typename L, typename R>
        requires basicType::destinyNumeric::detail::AnyInteger<L> && basicType::destinyNumeric::detail::AnyInteger<R>
                 && (basicType::destinyNumeric::detail::IntegerType<L>
                     || basicType::destinyNumeric::detail::IntegerType<R>)
    auto operator^(const L& l, const R& r) noexcept -> basicType::destinyNumeric::detail::Common_t<L, R>
    {
        using C = basicType::destinyNumeric::detail::Common_t<L, R>;
        using U = basicType::destinyNumeric::detail::Underlying_t<C>;
        const auto vl = basicType::destinyNumeric::detail::toValue(l);
        const auto vr = basicType::destinyNumeric::detail::toValue(r);
        return C(static_cast<U>(vl) ^ static_cast<U>(vr));
    }

    // 移位：结果类型跟随左操作数（内建则先归类），右操作数是移位数
    template <typename L, typename R>
        requires basicType::destinyNumeric::detail::AnyInteger<L> && basicType::destinyNumeric::detail::AnyInteger<R>
                 && (basicType::destinyNumeric::detail::IntegerType<L>
                     || basicType::destinyNumeric::detail::IntegerType<R>)
    auto operator<<(const L& l, const R& r) noexcept -> basicType::destinyNumeric::detail::Classify_t<L>
    {
        using T = basicType::destinyNumeric::detail::Classify_t<L>;
        using U = basicType::destinyNumeric::detail::Underlying_t<T>;
        const auto vl = basicType::destinyNumeric::detail::toValue(l);
        const auto vr = basicType::destinyNumeric::detail::toValue(r);
        return T(static_cast<U>(static_cast<U>(vl) << vr));
    }

    template <typename L, typename R>
        requires basicType::destinyNumeric::detail::AnyInteger<L> && basicType::destinyNumeric::detail::AnyInteger<R>
                 && (basicType::destinyNumeric::detail::IntegerType<L>
                     || basicType::destinyNumeric::detail::IntegerType<R>)
    auto operator>>(const L& l, const R& r) noexcept -> basicType::destinyNumeric::detail::Classify_t<L>
    {
        using T = basicType::destinyNumeric::detail::Classify_t<L>;
        using U = basicType::destinyNumeric::detail::Underlying_t<T>;
        const auto vl = basicType::destinyNumeric::detail::toValue(l);
        const auto vr = basicType::destinyNumeric::detail::toValue(r);
        return T(static_cast<U>(static_cast<U>(vl) >> vr));
    }

    // 一元：负号/正号/取反（`~` 仅整数）
    template <basicType::destinyNumeric::detail::IntegerType T> auto operator-(const T& v) noexcept -> T
    {
        return T(-v.value());
    }

    template <basicType::destinyNumeric::detail::FloatingType T> auto operator-(const T& v) noexcept -> T
    {
        return T(-v.value());
    }

    template <basicType::destinyNumeric::detail::IntegerType T> auto operator+(const T& v) noexcept -> T
    {
        return T(+v.value());
    }

    template <basicType::destinyNumeric::detail::FloatingType T> auto operator+(const T& v) noexcept -> T
    {
        return T(+v.value());
    }

    template <basicType::destinyNumeric::detail::IntegerType T> auto operator~(const T& v) noexcept -> T
    {
        return T(~v.value());
    }

    // 比较：整数产生 strong_ordering，浮点产生 partial_ordering
    template <typename L, typename R>
        requires(basicType::destinyNumeric::detail::NumericType<L> || basicType::destinyNumeric::detail::NumericType<R>)
    auto operator==(const L& l, const R& r) noexcept -> bool
    {
        using C = basicType::destinyNumeric::detail::Common_t<L, R>;
        using U = basicType::destinyNumeric::detail::Underlying_t<C>;
        const auto vl = basicType::destinyNumeric::detail::toValue(l);
        const auto vr = basicType::destinyNumeric::detail::toValue(r);
        return static_cast<U>(vl) == static_cast<U>(vr);
    }

    template <typename L, typename R>
        requires(basicType::destinyNumeric::detail::NumericType<L> || basicType::destinyNumeric::detail::NumericType<R>)
    auto operator<=>(const L& l, const R& r) noexcept
    {
        using C = basicType::destinyNumeric::detail::Common_t<L, R>;
        using U = basicType::destinyNumeric::detail::Underlying_t<C>;
        const auto vl = basicType::destinyNumeric::detail::toValue(l);
        const auto vr = basicType::destinyNumeric::detail::toValue(r);
        return static_cast<U>(vl) <=> static_cast<U>(vr);
    }
} // namespace destiny
