#include "destiny/basicType/time/time.hpp"
#include <iostream>

using destiny::Day;
using destiny::Duration;
using destiny::Hour;
using destiny::Minute;
using destiny::Second;

int main()
{
    const destiny::YearMonthDay ymd{2026, 8, 29};
    std::cout << "Year:" << ymd.year().value() << " Month:" << ymd.month().value() << " Day:" << ymd.day().value()
              << std::endl;
    return 0;
}