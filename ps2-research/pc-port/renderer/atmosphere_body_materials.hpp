#pragma once
#include "atmosphere_scene.hpp"
#include <map>
#include <tuple>
namespace gfx2::atmosphere {
// Cars retain a sky-lit diffuse floor. World exposure is deliberately weaker
// here: the track's baked visibility is not a second body shadow term.
inline Lighting body_lighting(const Lighting& lighting) {
    auto s=lighting;
    s.world_brightness=.85f+.15f*std::clamp(lighting.world_brightness,0.f,1.f);
    s.ambient_strength=std::max(s.ambient_strength,.95f);
    for(unsigned i=0;i<3;++i)s.ambient[i]=std::max(s.ambient[i],std::array<float,3>{.62f,.70f,.88f}[i]);
    s.sun_strength*=.65f;
    s.prelight_contrast=1;s.prelight_visibility=0;
    return s;
}
inline uint32_t body_color(uint32_t original,const std::array<float,3>& world_normal,const Lighting& lighting,bool replace_ps2_prepared) {
    if(!lighting.active())return original;
    const auto base=replace_ps2_prepared?(original&0xff000000u)|0x00666666u:original;
    return scene_color(base,world_normal,body_lighting(lighting));
}
inline uint32_t flat_body_color(uint32_t original,const Lighting& lighting) {
    auto ambient=body_lighting(lighting);ambient.sun_strength=0;return scene_color(original,{0,1,0},ambient);
}

enum BodySurfaceRole : uint32_t {Paint=1,OpaqueTrim=2,OpaquePanel=3,OpaqueCover=4,OpaqueHelmet=5,OpaqueFlat=6};
struct BodyCapability {std::string family,primary,secondary,ps2_texture;uint32_t role=Paint;};
class BodyMaterials {
    std::vector<BodyCapability> rows_;
public:
    bool attempted=false,ready=false;const char* reason="not_loaded";
    static bool safe(const std::string& primary,const std::string& secondary,uint32_t role=Paint) {
        if(role==Paint){if(secondary!="whitepaint-tga"&&secondary!="silverpaint-tga")return false;}
        else if(role==OpaqueTrim){if(secondary!="perspex-tga")return false;}
        else if(role==OpaquePanel){if(secondary!="whitepaint-tga"&&secondary!="silverpaint-tga"&&secondary!="perspex-tga")return false;}
        else if(role==OpaqueCover){if(secondary!="perspex-tga"||(primary.find("wheelcover-tga")==std::string::npos&&primary.find("wheelcoverside-tga")==std::string::npos))return false;}
        else if(role==OpaqueHelmet){if((secondary!="whitepaint-tga"&&secondary!="silverpaint-tga")||primary.find("helmet")==std::string::npos)return false;}
        else if(role==OpaqueFlat){if(secondary!="null")return false;}
        else return false;
        // A primary's name is not its surface role: original Patrol paint
        // fenders use logowhite64/logoblue64. Only an explicit capability can
        // qualify them; separate sticker/lamp/glass/wheel passes remain native.
        for(const char* excluded:{"glass","wheel","tread","tyre","tire","light","lamp","glow","brake","helmet","sticker","driver"})
            if(primary.find(excluded)!=std::string::npos){
                if(role==OpaquePanel&&!std::strcmp(excluded,"sticker"))continue;
                if(role==OpaqueCover&&!std::strcmp(excluded,"wheel"))continue;
                if(role==OpaqueHelmet&&!std::strcmp(excluded,"helmet"))continue;
                return false;
            }
        return true;
    }
    bool load(const std::filesystem::path& path)noexcept {
        if(attempted)return ready;attempted=true;
        try {
            std::ifstream f(path,std::ios::binary|std::ios::ate);if(!f||f.tellg()<76||f.tellg()>1024*1024){reason="body_metadata_missing_or_size";return false;}
            std::vector<uint8_t> b(size_t(f.tellg()));f.seekg(0);if(!f.read(reinterpret_cast<char*>(b.data()),b.size()))return false;
            uint32_t version=0,count=0;std::memcpy(&version,b.data()+4,4);std::memcpy(&count,b.data()+8,4);
            const bool legacy=!std::memcmp(b.data(),"BLM1",4)&&version==1;
            const bool typed=!std::memcmp(b.data(),"BLM2",4)&&version==2;const size_t size=32+96+96+65+(typed?4:0);
            if((!legacy&&!typed)||count>2048||b.size()!=76+uint64_t(count)*size){reason="body_metadata_header";return false;}
            const auto sha=sha256_bytes(b.data()+76,b.size()-76);if(std::memcmp(sha.data(),b.data()+12,64)){reason="body_metadata_checksum";return false;}
            std::vector<BodyCapability> rows;
            for(unsigned i=0;i<count;++i){const auto* p=b.data()+76+i*size;BodyCapability r;
                auto text=[&](unsigned n,std::string& out){const auto* end=static_cast<const uint8_t*>(std::memchr(p,0,n));if(!end)return false;out.assign(reinterpret_cast<const char*>(p),end-p);p+=n;
                    return !out.empty()&&std::all_of(out.begin(),out.end(),[](char c){return (c>='a'&&c<='z')||(c>='0'&&c<='9')||c=='_'||c=='-';});};
                if(!text(32,r.family)||!text(96,r.primary)||!text(96,r.secondary)||!text(65,r.ps2_texture)||r.ps2_texture.size()!=64){reason="body_metadata_unsafe_capability";return false;}
                if(typed)std::memcpy(&r.role,p,4);
                if(!safe(r.primary,r.secondary,r.role)){reason="body_metadata_unsafe_surface_role";return false;}
                rows.push_back(std::move(r));
            }
            rows_=std::move(rows);ready=true;reason="body_material_capabilities_ready";return true;
        }catch(...){reason="body_metadata_exception";return false;}
    }
    const BodyCapability* native_capability(const std::string& family,const std::string& primary,const std::string& secondary)const {
        if(!ready)return nullptr;for(const auto& r:rows_)if(r.family==family&&r.primary==primary&&r.secondary==secondary&&safe(r.primary,r.secondary,r.role))return &r;return nullptr;
    }
    bool native(const std::string& family,const std::string& primary,const std::string& secondary)const {
        return ready&&std::any_of(rows_.begin(),rows_.end(),[&](const auto& r){return r.family==family&&r.primary==primary&&r.secondary==secondary&&safe(r.primary,r.secondary,r.role);});
    }
    const BodyCapability* ps2_capability(const std::string& family,const std::string& texture)const {
        if(!ready)return nullptr;for(const auto& r:rows_)if(r.family==family&&r.ps2_texture==texture)return &r;return nullptr;
    }
    bool ps2(const std::string& family,const std::string& texture)const {return ps2_capability(family,texture)!=nullptr;}
    size_t size()const noexcept{return rows_.size();}
};
}
