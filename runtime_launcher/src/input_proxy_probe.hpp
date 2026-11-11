#pragma once

// Read-only PE32 export/ABI probe for an explicitly enabled SDK-binding
// candidate. It is not a hash allowlist or a general dinput8 compatibility test.
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <string_view>
#include <vector>

inline bool HasSdkBindingAbi(const std::vector<std::uint8_t>& b) {
    auto within = [&](std::size_t at, std::size_t n) { return at <= b.size() && n <= b.size()-at; };
    auto u16 = [&](std::size_t at) -> std::uint16_t {
        return within(at,2) ? static_cast<std::uint16_t>(b[at] | (unsigned(b[at+1])<<8)) : 0;
    };
    auto u32 = [&](std::size_t at) -> std::uint32_t {
        return within(at,4) ? std::uint32_t(b[at]) | (std::uint32_t(b[at+1])<<8) |
                              (std::uint32_t(b[at+2])<<16) | (std::uint32_t(b[at+3])<<24) : 0;
    };
    if (b.size()<0x100 || b.size()>32u*1024u*1024u || b[0]!='M' || b[1]!='Z') return false;
    const auto pe=u32(0x3c);
    if (!within(pe,24) || std::memcmp(b.data()+pe,"PE\0\0",4) || u16(pe+4)!=0x14c ||
        !(u16(pe+22)&0x2000)) return false;
    const auto count=u16(pe+6), optsize=u16(pe+20);
    const std::size_t opt=std::size_t(pe)+24, table=opt+optsize;
    if (!count || count>96 || optsize<104 || !within(table,std::size_t(count)*40) || u16(opt)!=0x10b) return false;
    auto offset = [&](std::uint32_t rva, std::size_t length) -> std::size_t {
        std::size_t found=b.size(); unsigned matches=0;
        for (unsigned i=0;i<count;++i) {
            const auto s=table+i*40;
            const auto va=u32(s+12), rawsize=u32(s+16), raw=u32(s+20);
            if (rva>=va && std::uint64_t(rva-va)+length<=rawsize && within(raw,std::size_t(rawsize))) {
                found=std::size_t(raw)+(rva-va); ++matches;
            }
        }
        return matches==1 ? found : b.size();
    };
    auto executable = [&](std::uint32_t rva) {
        for (unsigned i=0;i<count;++i) {
            const auto s=table+i*40;
            const auto va=u32(s+12), rawsize=u32(s+16), flags=u32(s+36);
            if (rva>=va && std::uint64_t(rva-va)<rawsize && (flags&0x20000000u)) return true;
        }
        return false;
    };
    const auto export_rva=u32(opt+96), export_size=u32(opt+100);
    const auto dir=offset(export_rva,40);
    if (dir==b.size() || export_size<40) return false;
    const auto base=u32(dir+16), functions=u32(dir+20), names=u32(dir+24);
    if (base!=1 || functions<7 || functions>64 || names<7 || names>64) return false;
    const auto ft=offset(u32(dir+28),std::size_t(functions)*4);
    const auto nt=offset(u32(dir+32),std::size_t(names)*4);
    const auto ot=offset(u32(dir+36),std::size_t(names)*2);
    if (ft==b.size() || nt==b.size() || ot==b.size()) return false;
    constexpr std::array<std::string_view,7> required={{"DirectInput8Create","DllCanUnloadNow", "DllGetClassObject", "DllRegisterServer", "DllUnregisterServer", "GetdfDIJoystick", "MRExtraSdkBindingAbi"}};
    std::array<bool,7> found{};
    for (unsigned i=0;i<names;++i) {
        const auto name_at=offset(u32(nt+i*4),1); const auto ordinal=u16(ot+i*2);
        if (name_at==b.size() || ordinal>=functions) return false;
        auto end=name_at; while (end<b.size() && end-name_at<128 && b[end]) ++end;
        if (end==b.size() || end-name_at==128) return false;
        const std::string_view name(reinterpret_cast<const char*>(b.data()+name_at),end-name_at);
        for (std::size_t n=0;n<required.size();++n) if (name==required[n]) {
            if (found[n] || ordinal!=n) return false;
            found[n]=true;
            const auto address=u32(ft+ordinal*4);
            if (!address || offset(address,1)==b.size() || !executable(address) ||
                (address>=export_rva && std::uint64_t(address)<std::uint64_t(export_rva)+export_size)) return false;
            if (n==6) {
                const auto at=offset(address,6); constexpr std::array<std::uint8_t,6> code={{0xb8,0x01,0x31,0x58,0x45,0xc3}};
                if (at==b.size() || !std::equal(code.begin(),code.end(),b.begin()+at)) return false;
            }
        }
    }
    return std::all_of(found.begin(),found.end(),[](bool value){return value;});
}
