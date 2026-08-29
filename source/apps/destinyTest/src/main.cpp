#include "destiny/basicType/time/time.hpp"
#include <iostream>

using destiny::Day;
using destiny::Duration;
using destiny::Hour;
using destiny::Minute;
using destiny::Second;

int main() {
    const auto r1 = Hour{14} + Duration<Hour>{3};              // 同单位 T+Duration -> Hour
    const auto r2 = Hour{14} + Duration<Minute>{30};           // T+Duration 跨单位 -> Minute
    const auto r3 = Duration<Hour>{3} + Minute{30};            // Duration+T 跨单位 -> Minute
    const auto r4 = Duration<Day>{1} + Duration<Hour>{3};      // Duration+Duration 跨 -> Hour
    const auto r5 = Duration<Hour>{3} - Duration<Minute>{30};  // Duration-Duration 跨 -> Minute
    const auto r6 = Duration<Day>{1} - Duration<Hour>{2};      // Duration-Duration 跨 -> Hour

    std::cout << r1.value() << ' ' << r2.value() << ' ' << r3.value() << ' '
              << r4.value() << ' ' << r5.value() << ' ' << r6.value() << '\n';
    return 0;
}