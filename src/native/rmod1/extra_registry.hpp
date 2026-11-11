#pragma once
#include "vehicle_registry_abi.hpp"
#include <climits>
#include <cstring>
#include <cstdint>

namespace extra_registry {
// Transport: decimal or 0x-prefixed address in the child process environment.
// The launcher publishes it only after installing the immutable MRVC allocation.
inline bool address(const wchar_t* text, std::uint32_t& result) {
    if (!text || !*text) return false;
    unsigned base=10;
    if (text[0]==L'0' && (text[1]==L'x'||text[1]==L'X')) {base=16;text+=2;}
    std::uint32_t value=0;bool any=false;
    for (;*text;++text) {
        unsigned digit=99;
        if (*text>=L'0'&&*text<=L'9') digit=unsigned(*text-L'0');
        else if (*text>=L'a'&&*text<=L'f') digit=unsigned(*text-L'a')+10;
        else if (*text>=L'A'&&*text<=L'F') digit=unsigned(*text-L'A')+10;
        if (digit>=base || value>(UINT32_MAX-digit)/base) return false;
        value=value*base+digit;any=true;
    }
    result=value;return any&&value!=0;
}
inline bool span(std::uint32_t start,std::uint32_t count,std::uint32_t stride) {
    return start && std::uint64_t(start)+std::uint64_t(count)*stride<=UINT64_C(0x100000000);
}
inline bool descriptor(const mr_vehicle_registry::DescriptorV1& d) {
    return !std::memcmp(d.magic,"MRVC",4) && d.abi_version==1 && d.struct_size==sizeof(d)
        && d.record_count>=26 && d.record_count<=INT_MAX && d.record_stride==52 && d.class_count==3
        && d.registry_getter_va==0x45a3c0
        && span(d.class_counts_va,3,4) && span(d.class_tables_va,3,4)
        && span(d.reverse_classes_va,d.record_count,4) && span(d.reverse_locals_va,d.record_count,4)
        && std::uint64_t(d.record_count)*52+4+39*44<=INT_MAX;
}
inline bool native_count(std::uint32_t allocation,std::uint32_t& count) {
    constexpr unsigned tail=4+39*44;
    if (allocation<tail+26*52 || allocation>INT_MAX || (allocation-tail)%52) return false;
    count=(allocation-tail)/52;return true;
}
}
