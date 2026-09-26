#include <cpuid.h>
#include <cstdio>

int main() {
    unsigned a=0,b=0,c=0,d=0;
    const unsigned maximum=__get_cpuid_max(0,nullptr);
    if (maximum==0) return 2;
    __cpuid(0,a,b,c,d);
    const unsigned vendor_b=b,vendor_c=c,vendor_d=d;
    unsigned leaf1=0,leaf7=0,xcr0_low=0;
    if (maximum>=1) {
        __cpuid(1,a,b,c,d);
        leaf1=c;
        // XGETBV is valid only when XSAVE and OSXSAVE are both advertised.
        if ((c & (1u<<26)) && (c & (1u<<27))) {
            unsigned high;
            __asm__ volatile ("xgetbv" : "=a"(xcr0_low), "=d"(high) : "c"(0));
        }
    }
    if (maximum>=7) {
        __cpuid_count(7,0,a,b,c,d);
        leaf7=b;
    }
    std::printf("{\"vendor\":[%u,%u,%u],\"leaf1_ecx\":%u,\"leaf7_ebx\":%u,\"xcr0_low\":%u,\"target_bits\":%u}\n",
                vendor_b,vendor_d,vendor_c,leaf1,leaf7,xcr0_low,static_cast<unsigned>(sizeof(void*)*8));
}
