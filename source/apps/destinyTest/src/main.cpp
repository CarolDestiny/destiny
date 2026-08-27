#include "destiny/basicType/time/time.hpp"
#include <iostream>
using namespace destiny;
int main()
{
    LocalZone localZone;
    bool a = localZone.setZone("Asia/Shanghai");
    std::cout << ZoneTime(UtcTime::now(),localZone).value()<< std::endl;
    return 0;
}