#pragma once
// RETAIL-DERIVATIVE1 (opt-in RetailDerivativeBuilds=1 in PS2Port.ini, docs/collision-debug1): in-place mods of the
// retail MRallye.exe (invitation entries, cooked course builds such as MRallye_cook_spain_extream.exe) keep the file
// size, the image base and the section table and change a few 4 KiB pages (3..11 of 763 in the owner's builds). Such an
// EXE is accepted as RETAIL_DERIVATIVE: the baseline treats it as the retail target (every hook still verifies its own
// bytes and fails closed) and the PS2 extension runs only CollisionDebug unless RetailDerivativeEffects=1.
// A relinked build (MRallye_patched.exe: other section layout) or any other program is rejected.
#include "retail_layout_table.hpp"
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <iterator>
#include <fstream>
#include <string>
#include <vector>

namespace gfx2::ps2port {

inline constexpr uint32_t kMaxChangedRetailPages=64;

struct RetailDerivative {
    bool requested=false,accepted=false;
    const char* reason="not_requested";
    std::vector<uint32_t> changed_pages;   // file offsets of the pages that differ from retail
};
inline RetailDerivative& retail_derivative() noexcept {static RetailDerivative state;return state;}

inline uint64_t retail_fnv1a64(const uint8_t* p,size_t n) noexcept {
    uint64_t h=0xcbf29ce484222325ull;for(size_t i=0;i<n;++i){h^=p[i];h*=0x100000001b3ull;}return h;
}
inline void check_retail_derivative_bytes(const uint8_t* b,size_t n,RetailDerivative& out) {
    out.accepted=false;out.changed_pages.clear();
    auto u16=[&](size_t o){uint16_t v;std::memcpy(&v,b+o,2);return v;};
    auto u32=[&](size_t o){uint32_t v;std::memcpy(&v,b+o,4);return v;};
    if(n!=retail::kFileSize){out.reason="file_size_differs_from_retail";return;}
    if(b[0]!='M'||b[1]!='Z'||u32(0x3c)!=retail::kPeOffset||std::memcmp(b+retail::kPeOffset,"PE\0\0",4)){out.reason="pe_header_differs";return;}
    const size_t pe=retail::kPeOffset;
    if(u16(pe+6)!=retail::kSections.size()||u32(pe+24+28)!=retail::kImageBase){out.reason="image_base_or_section_count_differs";return;}
    const size_t table=pe+24+u16(pe+20);
    if(table+retail::kSections.size()*40>n){out.reason="pe_header_differs";return;}
    for(size_t i=0;i<retail::kSections.size();++i){
        const auto& s=retail::kSections[i];const size_t o=table+i*40;
        if(std::memcmp(b+o,s.name,8)||u32(o+12)!=s.va||u32(o+16)!=s.raw_size||u32(o+20)!=s.raw_ptr||u32(o+36)!=s.characteristics){
            out.reason="section_layout_differs_from_retail";return;}
    }
    for(size_t page=0;page<retail::kPageFnv.size();++page){
        const size_t at=page*retail::kPageSize,len=std::min<size_t>(retail::kPageSize,n-at);
        if(retail_fnv1a64(b+at,len)!=retail::kPageFnv[page])out.changed_pages.push_back(static_cast<uint32_t>(at));
    }
    if(out.changed_pages.empty()){out.reason="identical_to_retail";out.accepted=true;return;}
    if(out.changed_pages.size()>kMaxChangedRetailPages){out.reason="too_many_changed_pages";return;}
    out.reason="retail_derivative";out.accepted=true;
}
inline void check_retail_derivative(const std::wstring& path,RetailDerivative& out) {
    try{
        std::ifstream f(path,std::ios::binary);if(!f){out.reason="exe_unreadable";return;}
        std::vector<uint8_t> b((std::istreambuf_iterator<char>(f)),std::istreambuf_iterator<char>());
        check_retail_derivative_bytes(b.data(),b.size(),out);
    }catch(...){out.accepted=false;out.reason="exe_unreadable";}
}
inline std::string retail_derivative_json(const RetailDerivative& d) {
    std::string s="{\"type\":\"retail_derivative\",\"requested\":"+std::string(d.requested?"true":"false")+",\"accepted\":"+
        (d.accepted?"true":"false")+",\"reason\":\""+d.reason+"\",\"max_changed_pages\":"+std::to_string(kMaxChangedRetailPages)+",\"changed_pages\":[";
    char buf[16];
    for(size_t i=0;i<d.changed_pages.size();++i){std::snprintf(buf,sizeof(buf),"%s\"0x%x\"",i?",":"",d.changed_pages[i]);s+=buf;}
    return s+"]}";
}
} // namespace gfx2::ps2port
