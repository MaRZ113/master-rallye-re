#pragma once
#include "atmosphere_scene.hpp"
#include <map>
#include <tuple>
#include <set>
namespace gfx2::atmosphere {
// Cars retain a sky-lit diffuse floor. World exposure is deliberately weaker
// here: the track's baked visibility is not a second body shadow term.
inline Lighting body_lighting(const Lighting& lighting) {
    auto s=lighting;
    s.world_brightness=.85f+.15f*std::clamp(lighting.world_brightness,0.f,1.f);
    // The day floor keeps bodies from going coal-black under low-ambient day
    // presets. Below AmbientStrength .5 (night/dark diagnostic) it fades out
    // so cars darken with the world; .5 and above is unchanged.
    const float day=std::clamp((lighting.ambient_strength-.2f)/.3f,0.f,1.f);
    s.ambient_strength=std::max(s.ambient_strength,.95f*day+lighting.ambient_strength*(1-day));
    for(unsigned i=0;i<3;++i){const float floor=std::array<float,3>{.62f,.70f,.88f}[i];s.ambient[i]=std::max(s.ambient[i],floor*day+s.ambient[i]*(1-day));}
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

enum BodySurfaceRole : uint32_t {Paint=1,OpaqueTrim=2,OpaquePanel=3,OpaqueCover=4,OpaqueHelmet=5,OpaqueFlat=6,OpaqueInterior=7,OpaquePilot=8,WheelRubber=9,WheelMetal=10,OpaqueGlazing=11};
inline const char* body_role_name(uint32_t role)noexcept{switch(role){case Paint:return "paint";case OpaqueTrim:return "opaque_trim";case OpaquePanel:return "opaque_panel";case OpaqueCover:return "opaque_cover";case OpaqueHelmet:return "opaque_helmet";case OpaqueFlat:return "opaque_flat";case OpaqueInterior:return "interior";case OpaquePilot:return "pilot";case WheelRubber:return "wheel_rubber";case WheelMetal:return "wheel_metal";case OpaqueGlazing:return "opaque_glazing";default:return "unsupported";}}
// PERF-ATMO2: the per-role body lighting of vehicle_surface_color, built once per draw.
inline Lighting vehicle_surface_lighting(const Lighting& lighting,uint32_t role){
    auto s=body_lighting(lighting);
    if(role==OpaqueFlat||role==OpaqueInterior||role==OpaqueGlazing)s.sun_strength=0;
    else if(role==OpaquePilot||role==WheelRubber)s.sun_strength*=.35f;
    return s;
}
inline uint32_t vehicle_surface_color(uint32_t original,const std::array<float,3>& normal,const ScenePre& k,bool prepared){
    if(!k.active)return original;const auto base=prepared?(original&0xff000000u)|0x00666666u:original;return scene_color(base,normal,k);
}
inline uint32_t vehicle_surface_color(uint32_t original,const std::array<float,3>& normal,const Lighting& lighting,bool prepared,uint32_t role){
    if(!lighting.active())return original;auto s=body_lighting(lighting);
    if(role==OpaqueFlat||role==OpaqueInterior||role==OpaqueGlazing)s.sun_strength=0;
    else if(role==OpaquePilot||role==WheelRubber)s.sun_strength*=.35f;
    const auto base=prepared?(original&0xff000000u)|0x00666666u:original;
    return scene_color(base,normal,s);
}
struct BodyCapability {std::string family,primary,secondary,ps2_texture;uint32_t role=Paint;std::string resource="car",ps2_secondary_texture;};
class BodyMaterials {
    std::vector<BodyCapability> rows_;
    using NativeKey=std::tuple<std::string,std::string,std::string,std::string>;
    using PS2Key=std::tuple<std::string,std::string,std::string,std::string>;
    std::map<NativeKey,size_t> native_index_;std::map<PS2Key,size_t> ps2_index_;
    // Families the registry lists (any resource). Their authored decisions are final; only absent families use the
    // naming-convention fallback below. Derived rows are cached with stable addresses.
    std::set<std::string> families_;mutable std::map<NativeKey,BodyCapability> derived_;mutable size_t derived_rejected_=0;
public:
    // Add-on fallback (BodyMaterialsAddons=1): a car family that is not in the registry gets its surface role from the
    // same naming contract that tools/atmosphere_vehicle_lighting.py role_for() applies offline (secondary/env texture
    // whitepaint/silverpaint/perspex/rubber/chrome/glass/null + primary keywords). The caller has already certified an
    // opaque draw (no alpha blend/test), which is the tool's opaque=True case. safe() still has the last word.
    bool auto_addons=true;
    static uint32_t derived_role(const std::string& primary,const std::string& secondary_name,const std::string& part) {
        auto has=[&](const char* t){return primary.find(t)!=std::string::npos;};
        if(has("light")||has("lamp")||has("glow")||has("brake"))return 0;   // tool: native emissive / lamp policy
        for(const char* t:{"light","lamp","glow"})if(secondary_name.find(t)!=std::string::npos)return 0;
        const std::string secondary=env_alias(secondary_name);
        const bool white=secondary=="whitepaint-tga"||secondary=="silverpaint-tga";
        if(secondary=="glass-tga")return safe(primary,secondary,OpaqueGlazing)?uint32_t(OpaqueGlazing):0u;
        if(has("glass")||has("window")||has("windscreen"))return 0;
        uint32_t role=0;
        if(part=="wheel")role=secondary=="rubber-tga"?WheelRubber:secondary=="chrome-tga"?WheelMetal:0;
        else if(secondary=="rubber-tga")role=WheelRubber;
        else if(secondary=="chrome-tga")role=WheelMetal;
        else if(has("wheelcover")&&secondary=="perspex-tga")role=OpaqueCover;
        else if(has("sticker")&&(white||secondary=="perspex-tga"))role=OpaquePanel;
        else if(has("helmet"))role=white?OpaqueHelmet:OpaquePilot;
        else if(has("driver")||has("pilot"))role=OpaquePilot;
        else if(white)role=Paint;
        else if(has("chair")||has("seat")||has("interior")||has("dash")||has("cockpit")||has("steer"))role=OpaqueInterior;
        else if(secondary=="perspex-tga")role=OpaqueTrim;
        else if(secondary=="null")role=OpaqueFlat;
        return role&&safe(primary,secondary,role)?role:0u;
    }
    bool registered(const std::string& family)const noexcept{return families_.count(family)!=0;}
    size_t derived_count()const noexcept{return derived_.size();}
    bool attempted=false,ready=false,extended=false;const char* reason="not_loaded";std::string payload_sha;
    // Importer env textures (GT4/classic converters: gt4-env-<hash>, classic-rubber-env-<hash>, ...) -> the retail contract
    // name with the same meaning; retail names pass through. Mirrors env_alias() in tools/atmosphere_vehicle_lighting.py.
    static std::string env_alias(const std::string& s) {
        for(const char* retail:{"whitepaint-tga","silverpaint-tga","perspex-tga","rubber-tga","chrome-tga","glass-tga","null"})if(s==retail)return s;
        auto has=[&](const char* t){return s.find(t)!=std::string::npos;};
        if(has("rubber")||has("tyre")||has("tire"))return "rubber-tga";
        if(has("glass"))return "glass-tga";
        if(has("chrome")||has("metal"))return "chrome-tga";
        if(has("perspex")||has("plastic"))return "perspex-tga";
        if(has("-env-")||s.rfind("env-",0)==0||(s.size()>8&&s.compare(s.size()-8,8,"-env-tga")==0))return "whitepaint-tga";
        return s;
    }
    static bool safe(const std::string& primary,const std::string& secondary_name,uint32_t role=Paint) {
        const std::string secondary=env_alias(secondary_name);
        if(role==Paint){if(secondary!="whitepaint-tga"&&secondary!="silverpaint-tga")return false;}
        else if(role==OpaqueTrim){if(secondary!="perspex-tga")return false;}
        else if(role==OpaquePanel){if(secondary!="whitepaint-tga"&&secondary!="silverpaint-tga"&&secondary!="perspex-tga")return false;}
        else if(role==OpaqueCover){if(secondary!="perspex-tga"||(primary.find("wheelcover-tga")==std::string::npos&&primary.find("wheelcoverside-tga")==std::string::npos))return false;}
        else if(role==OpaqueHelmet){if((secondary!="whitepaint-tga"&&secondary!="silverpaint-tga")||primary.find("helmet")==std::string::npos)return false;}
        else if(role==OpaqueFlat){if(secondary!="null")return false;}
        else if(role==OpaqueInterior){if(secondary!="null"&&secondary!="perspex-tga")return false;}
        else if(role==OpaquePilot){if(secondary!="null"&&secondary!="whitepaint-tga"&&secondary!="silverpaint-tga")return false;}
        else if(role==WheelRubber){if(secondary!="rubber-tga")return false;}
        else if(role==OpaqueGlazing){if(secondary!="glass-tga")return false;}
        else if(role==WheelMetal){if(secondary!="chrome-tga")return false;}
        else return false;
        // A primary's name is not its surface role: original Patrol paint
        // fenders use logowhite64/logoblue64. Only an explicit capability can
        // qualify them; separate sticker/lamp/glass/wheel passes remain native.
        for(const char* excluded:{"glass","window","windscreen","windshield","emissive","wheel","tread","tyre","tire","light","lamp","glow","brake","helmet","sticker","driver"})
            if(primary.find(excluded)!=std::string::npos){
                if(role==OpaqueGlazing&&(!std::strcmp(excluded,"glass")||!std::strcmp(excluded,"window")))continue;
                if(role==OpaquePanel&&!std::strcmp(excluded,"sticker"))continue;
                if(role==OpaqueCover&&!std::strcmp(excluded,"wheel"))continue;
                if(role==OpaqueHelmet&&!std::strcmp(excluded,"helmet"))continue;
                if(role==OpaquePilot&&(!std::strcmp(excluded,"helmet")||!std::strcmp(excluded,"driver")))continue;
                if((role==WheelRubber||role==WheelMetal)&&(!std::strcmp(excluded,"wheel")||!std::strcmp(excluded,"tread")||!std::strcmp(excluded,"tyre")||!std::strcmp(excluded,"tire")))continue;
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
            const bool typed=!std::memcmp(b.data(),"BLM2",4)&&version==2;extended=!std::memcmp(b.data(),"BLM3",4)&&version==3;const size_t size=32+96+96+65+((typed||extended)?4:0)+(extended?97:0);
            if((!legacy&&!typed&&!extended)||count>2048||b.size()!=76+uint64_t(count)*size){reason="body_metadata_header";return false;}
            const auto sha=sha256_bytes(b.data()+76,b.size()-76);if(sha.size()!=64||std::memcmp(sha.data(),b.data()+12,64)){reason="body_metadata_checksum";return false;}
            std::vector<BodyCapability> rows;
            for(unsigned i=0;i<count;++i){const auto* p=b.data()+76+i*size;BodyCapability r;
                auto text=[&](unsigned n,std::string& out){const auto* end=static_cast<const uint8_t*>(std::memchr(p,0,n));if(!end)return false;out.assign(reinterpret_cast<const char*>(p),end-p);p+=n;
                    return !out.empty()&&std::all_of(out.begin(),out.end(),[](char c){return (c>='a'&&c<='z')||(c>='0'&&c<='9')||c=='_'||c=='-';});};
                if(!text(32,r.family)||(extended&&!text(32,r.resource))||!text(96,r.primary)||!text(96,r.secondary)||!text(65,r.ps2_texture)||r.ps2_texture.size()!=64||r.ps2_texture.find_first_not_of("0123456789abcdef")!=std::string::npos){reason="body_metadata_unsafe_capability";return false;}
                if(extended&&(!text(65,r.ps2_secondary_texture)||r.ps2_secondary_texture.size()!=64||r.ps2_secondary_texture.find_first_not_of("0123456789abcdef")!=std::string::npos)){reason="body_metadata_secondary_identity";return false;}
                if(typed||extended)std::memcpy(&r.role,p,4);
                if(!safe(r.primary,r.secondary,r.role)||(!extended&&r.role>OpaqueFlat)||(r.resource!="car"&&r.resource!="wheel")||(r.resource=="wheel"&&r.role!=WheelRubber&&r.role!=WheelMetal)){reason="body_metadata_unsafe_surface_role";return false;}
                rows.push_back(std::move(r));
            }
            std::map<NativeKey,size_t> ni;std::map<PS2Key,size_t> pi;std::set<PS2Key> ambiguous;
            for(size_t i=0;i<rows.size();++i){const auto& r=rows[i];const NativeKey key{r.family,r.resource,r.primary,r.secondary};auto n=ni.emplace(key,i);
                if(!n.second&&rows[n.first->second].role!=r.role){reason="body_metadata_conflicting_native_roles";return false;}
                if(r.ps2_texture==std::string(64,'0'))continue;const PS2Key pk{r.family,r.resource,r.ps2_texture,r.ps2_secondary_texture};if(ambiguous.count(pk))continue;
                auto p=pi.emplace(pk,i);if(!p.second){const auto& before=rows[p.first->second];if(before.role!=r.role||(!extended&&(before.primary!=r.primary||before.secondary!=r.secondary))){pi.erase(pk);ambiguous.insert(pk);}}}
            families_.clear();for(const auto& r:rows)families_.insert(r.family);rows_=std::move(rows);native_index_=std::move(ni);ps2_index_=std::move(pi);payload_sha=sha;ready=true;reason="body_material_capabilities_ready";return true;
        }catch(...){reason="body_metadata_exception";return false;}
    }
    const BodyCapability* native_capability(const std::string& family,const std::string& primary,const std::string& secondary,const std::string& resource="car")const {
        if(!ready)return nullptr;const auto it=native_index_.find({family,resource,primary,secondary});if(it!=native_index_.end())return &rows_[it->second];
        // Registered families keep their authored decisions, except importer env names the registry builder could not read.
        if(!auto_addons||family.empty()||(families_.count(family)&&env_alias(secondary)==secondary))return nullptr;
        const NativeKey key{family,resource,primary,secondary};const auto d=derived_.find(key);if(d!=derived_.end())return d->second.role?&d->second:nullptr;
        if(derived_.size()>=4096)return nullptr;
        BodyCapability c;c.family=family;c.resource=resource;c.primary=primary;c.secondary=secondary;c.ps2_texture=std::string(64,'0');c.ps2_secondary_texture=c.ps2_texture;
        c.role=(resource=="car"||resource=="wheel")?derived_role(primary,secondary,resource):0u;if(!c.role)++derived_rejected_;
        const auto& stored=derived_.emplace(key,std::move(c)).first->second;return stored.role?&stored:nullptr;
    }
    bool native(const std::string& family,const std::string& primary,const std::string& secondary)const {
        return native_capability(family,primary,secondary)!=nullptr;
    }
    const BodyCapability* ps2_capability(const std::string& family,const std::string& texture,const std::string& resource="car",const std::string& secondary="")const {
        if(!ready)return nullptr;const auto it=ps2_index_.find({family,resource,texture,extended?secondary:std::string{}});return it==ps2_index_.end()?nullptr:&rows_[it->second];
    }
    bool ps2(const std::string& family,const std::string& texture)const {return ps2_capability(family,texture)!=nullptr;}
    size_t size()const noexcept{return rows_.size();}
};
}
