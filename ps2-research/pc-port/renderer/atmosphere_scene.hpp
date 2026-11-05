#pragma once
#include "provenance.hpp"
#include "atmosphere_scene_registry.hpp"
#include "atmosphere_art.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <string>
#include <unordered_map>
#include <vector>
namespace gfx2::atmosphere {
// Windows course asset identifiers are case-insensitive; keep one safe key.
inline std::string canonical_course(const std::string& id){
    if(id.empty()||id.size()>63)return {};std::string out;out.reserve(id.size());
    for(unsigned char c:id){if(!((c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='_'||c=='-'))return {};
        out.push_back(c>='A'&&c<='Z'?char(c+32):char(c));}return out;
}
struct Lighting {
    enum class Mode {Original,Day,GoldenHour};Mode mode=Mode::Original;
    float strength=1,exposure=1,ambient_strength=.8f,sun_strength=.95f,fog_strength=1,world_brightness=1,prelight_contrast=1,prelight_visibility=0;
    std::array<float,3> ambient{.62f,.70f,.88f},sun{1.4f,1.02f,.64f},direction{-.65f,.45f,.61f};
    bool fog_enabled=false;uint32_t fog=0xff98765d;
    bool surface_tone=false,rim=false;float tone_contrast=1,tone_shoulder=0,rim_strength=0,rim_power=3;
    bool active()const noexcept{return mode!=Mode::Original&&strength>0;}
};
inline uint32_t scene_color(uint32_t color,std::array<float,3> normal,const Lighting& s)noexcept {
    if(!s.active())return color;
    float n2=0,d2=0;for(unsigned i=0;i<3;++i){n2+=normal[i]*normal[i];d2+=s.direction[i]*s.direction[i];}
    float nl=0;if(n2>1e-12f&&d2>1e-12f)for(unsigned i=0;i<3;++i)nl+=normal[i]*s.direction[i]/std::sqrt(n2*d2);
    nl=std::clamp(nl,0.f,1.f);
    const float luminance=(float((color>>16)&255)*.2126f+float((color>>8)&255)*.7152f+float(color&255)*.0722f)/255;
    // Original vertex RGB already encodes visibility AND material compensation.
    // Default gain is independent of RGB, retaining compensation across seams.
    // Legacy luminance masking is explicit opt-in, never a shadow solver.
    const float visibility=1+s.prelight_visibility*(std::clamp((luminance-.08f)/.72f,0.f,1.f)-1);
    // Compress legacy baked directional contrast while retaining hue, black
    // occlusion and alpha. Default 1 is byte-compatible; authored sunset may
    // reduce duplicated prelight at material boundaries. Not a shadow solver.
    const float target=.65f+(luminance-.65f)*s.prelight_contrast;
    const float coverage=std::clamp((luminance-.08f)/.25f,0.f,1.f);
    const float prelight_gain=luminance>1e-6f?1+coverage*(target/luminance-1):1;
    uint32_t result=color&0xff000000;std::array<float,3> rgb{};float illumination=0;
    for(unsigned i=0;i<3;++i){const unsigned shift=(2-i)*8;const float old=float((color>>shift)&255);
        const float gain=(s.ambient[i]*s.ambient_strength+s.sun[i]*s.sun_strength*nl*visibility)*s.exposure*s.world_brightness;
        illumination+=gain*(i==0?.2126f:i==1?.7152f:.0722f);
        rgb[i]=old*(1+s.strength*(prelight_gain*gain-1));}
    // Curve lighting energy, never authored vertex RGB: material/texture
    // compensation must keep the same gain on both sides of a seam.
    if(s.surface_tone&&illumination>1e-6f){float mapped=std::max(0.f,(illumination-.65f)*s.tone_contrast+.65f);
        if(mapped>1)mapped=1+(mapped-1)/(1+s.tone_shoulder*(mapped-1));
        const float ratio=1+s.strength*(mapped/illumination-1);for(auto& c:rgb)c*=ratio;}
    for(unsigned i=0;i<3;++i)result|=uint32_t(std::clamp(std::lround(rgb[i]),0l,255l))<<((2-i)*8);
    return result;
}
inline uint32_t scene_fog(uint32_t original,const Lighting& s)noexcept {
    if(!s.active()||!s.fog_enabled)return original;uint32_t out=original&0xff000000;
    const float a=std::clamp(s.strength*s.fog_strength,0.f,1.f);
    for(unsigned shift:{0u,8u,16u})out|=uint32_t(std::lround(float((original>>shift)&255)*(1-a)+float((s.fog>>shift)&255)*a))<<shift;
    return out;
}
// Static course environment energy follows ambient exposure, with a square
// root response so metallic highlights remain readable. Diffuse gets its own
// directional light; this factor affects only the certified secondary texture.
inline uint32_t world_environment_factor(const Lighting& s)noexcept {
    if(!s.active())return 0xffffffffu;
    auto energy=s;energy.prelight_contrast=1;energy.prelight_visibility=0;energy.surface_tone=false;
    const auto ambient=scene_color(0xffffffffu,{0,0,0},energy);uint32_t out=0xff000000u;
    // Night (AmbientStrength < .5): static reflections fade with the world;
    // .5 and above keeps the accepted sqrt response unchanged.
    const float night=std::clamp(s.ambient_strength/.5f,0.f,1.f);
    for(unsigned shift:{0u,8u,16u})out|=uint32_t(std::lround(255*night*std::sqrt(float((ambient>>shift)&255)/255)))<<shift;
    return out;
}
inline uint32_t environment_texel(uint32_t source,uint32_t factor)noexcept {
    uint32_t out=source&0xff000000u;
    for(unsigned shift:{0u,8u,16u})out|=((((source>>shift)&255)*((factor>>shift)&255)+127)/255)<<shift;
    return out;
}
// CPU results only. The caller must still prove the current geometry/material
// before using this cache. No device/resource pointer survives here.
struct SceneColors {
    std::vector<uint32_t> indices,colors;
    std::vector<uint8_t> used;
    Lighting settings;
    bool ready=false;
    bool matches(const std::vector<uint32_t>& current,size_t vertices,const Lighting& s)const noexcept {
        return ready&&colors.size()==vertices&&indices==current&&settings.mode==s.mode&&
            settings.strength==s.strength&&settings.exposure==s.exposure&&settings.ambient_strength==s.ambient_strength&&
            settings.sun_strength==s.sun_strength&&settings.ambient==s.ambient&&settings.sun==s.sun&&settings.direction==s.direction&&settings.world_brightness==s.world_brightness&&settings.prelight_contrast==s.prelight_contrast&&settings.prelight_visibility==s.prelight_visibility&&settings.surface_tone==s.surface_tone&&settings.tone_contrast==s.tone_contrast&&settings.tone_shoulder==s.tone_shoulder;
    }
    bool bake(const std::vector<std::array<float,3>>& source,const std::vector<uint32_t>& current,
              const std::vector<uint32_t>& original,const Lighting& s) {
        ready=false;if(source.size()!=current.size())return false;
        std::vector<std::array<float,3>> normals(original.size());used.assign(original.size(),0);
        for(size_t j=0;j<current.size();++j){auto i=current[j];if(i>=original.size())return false;used[i]=1;
            for(unsigned k=0;k<3;++k)normals[i][k]+=source[j][k];}
        colors=original;
        for(size_t i=0;i<colors.size();++i)if(used[i])colors[i]=scene_color(original[i],normals[i],s);
        indices=current;settings=s;ready=true;return true;
    }
};
struct SceneRecord {
    std::string course,material,geometry,texture,opaque_texture;uint32_t category=0;
    std::vector<std::array<float,3>> normals;
    mutable SceneColors lighting_cache;
};
class SceneAtlas {
    std::unordered_multimap<std::string,size_t> index_;
    std::vector<SceneRecord> records_;
public:
    bool attempted=false,ready=false;const char* reason="not_loaded";
    bool load(const std::filesystem::path& path)noexcept {
        if(attempted)return ready;attempted=true;
        try{
            std::ifstream f(path,std::ios::binary|std::ios::ate);if(!f||f.tellg()<12||f.tellg()>32*1024*1024){reason="scene_atlas_missing_or_size_invalid";return false;}
            const auto size=static_cast<size_t>(f.tellg());f.seekg(0);std::vector<uint8_t> bytes(size);
            if(!f.read(reinterpret_cast<char*>(bytes.data()),size)||sha256_bytes(bytes.data(),size)!=kSceneAtlasSha){reason="scene_atlas_source_hash_mismatch";return false;}
            size_t position=0;auto read=[&](void* p,size_t n){if(n>bytes.size()-position)return false;std::memcpy(p,bytes.data()+position,n);position+=n;return true;};
            char magic[4]{};uint32_t version=0,count=0;if(!read(magic,4)||std::memcmp(magic,"ATS2",4)||!read(&version,4)||version!=1||!read(&count,4)||count>8192){reason="scene_atlas_header_invalid";return false;}
            std::vector<SceneRecord> parsed;parsed.reserve(count);
            auto text=[&](size_t n,std::string& out){std::array<char,128> b{};if(n>b.size()||!read(b.data(),n)||!std::memchr(b.data(),0,n))return false;out=b.data();return true;};
            for(uint32_t i=0;i<count;++i){SceneRecord r;uint32_t vertices=0;
                if(!text(32,r.course)||!read(&r.category,4)||r.category<1||r.category>4||!read(&vertices,4)||!vertices||vertices>98304||vertices%3||
                    !text(64,r.material)||!text(65,r.geometry)||!text(65,r.texture)||!text(65,r.opaque_texture)||r.geometry.size()!=64||r.texture.size()!=64||r.opaque_texture.size()!=64){reason="scene_atlas_record_invalid";return false;}
                r.normals.resize(vertices);if(!read(r.normals.data(),vertices*12)){reason="scene_atlas_normals_truncated";return false;}
                for(const auto& n:r.normals)for(float c:n)if(!std::isfinite(c)||std::abs(c)>2){reason="scene_atlas_normal_invalid";return false;}
                parsed.push_back(std::move(r));}
            if(position!=bytes.size()){reason="scene_atlas_trailing_bytes";return false;}
            records_=std::move(parsed);for(size_t i=0;i<records_.size();++i)index_.emplace(records_[i].geometry,i);
            ready=true;reason="source_scene_atlas_ready";return true;
        }catch(...){records_.clear();index_.clear();reason="scene_atlas_exception";return false;}
    }
    const SceneRecord* find(const std::string& geometry,const char* course,const std::string& texture)const noexcept {
        auto range=index_.equal_range(geometry);const SceneRecord* result=nullptr;
        for(auto i=range.first;i!=range.second;++i){const auto& r=records_[i->second];
            if(r.course==course&&(r.texture==texture||r.opaque_texture==texture)){if(result)return nullptr;result=&r;}}
        return result;
    }
    size_t size()const noexcept{return records_.size();}
};
} // namespace gfx2::atmosphere
