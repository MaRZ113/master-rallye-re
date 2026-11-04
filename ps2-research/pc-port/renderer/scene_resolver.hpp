#pragma once
#include "atmosphere_scene.hpp"
#include "atmosphere_normals.hpp"
#include "atmosphere_body_materials.hpp"
#include <map>
#include <limits>
#include <cctype>

namespace gfx2::atmosphere {
enum MaterialFlags : uint32_t {Noise=1,Plain=2,AlphaTest=4,TwoSided=8,Deny=16,Environment=32,EnvironmentTexture=64};
struct SceneMaterial {std::string course,name,texture;uint32_t category=0,flags=0;int32_t winding=-1;};
// On a certified unblended, non-alpha-tested pass, texture alpha is unused
// coverage data (often zero in opaque course assets). A known material role
// can prove opacity from that pass. Unknown automatic ground retains its
// conservative all-255 texture requirement; no shader exclusion is bypassed.
inline bool source_opaque_pass(const SceneMaterial* m,bool texture_opaque,bool blended,bool alpha_test)noexcept{
    return !blended&&(texture_opaque||(m&&m->category>=1&&m->category<=4&&!(m->flags&Deny)&&
        (!alpha_test||(m->category==4&&(m->flags&AlphaTest)&&!(m->flags&Environment)))));
}
// Optional external material capabilities, never object/triangle identities.
// Integrity is self-contained (not a DLL-compiled allowlist). Authoring an LSM1
// file cannot bypass current race, pass, buffer, geometry or shader proofs.
class LightingMetadata {
    std::map<std::pair<std::string,std::string>,SceneMaterial> materials_;
public:
    bool attempted=false,ready=false,present=false;std::string sha;const char* reason="not_loaded";
    bool load(const std::filesystem::path& path)noexcept {
        if(attempted)return ready;attempted=true;
        try{
            present=std::filesystem::exists(path);
            std::ifstream f(path,std::ios::binary|std::ios::ate);if(!f||f.tellg()<76||f.tellg()>4*1024*1024){reason="metadata_missing_or_size";return false;}
            std::vector<uint8_t> b(size_t(f.tellg()));f.seekg(0);if(!f.read(reinterpret_cast<char*>(b.data()),b.size()))return false;
            uint32_t version=0,count=0;std::memcpy(&version,b.data()+4,4);std::memcpy(&count,b.data()+8,4);
            constexpr size_t row=64+96+65+12;
            if(std::memcmp(b.data(),"LSM1",4)||version!=1||count>16384||b.size()!=76+uint64_t(count)*row){reason="metadata_header_invalid";return false;}
            sha=sha256_bytes(b.data()+76,b.size()-76);
            if(std::memcmp(sha.data(),b.data()+12,64)){reason="metadata_checksum_mismatch";return false;}
            std::map<std::pair<std::string,std::string>,SceneMaterial> parsed;
            for(size_t i=0;i<count;++i){const auto* p=b.data()+76+i*row;SceneMaterial m;
                auto text=[&](size_t n,std::string& out){const auto* end=static_cast<const uint8_t*>(std::memchr(p,0,n));if(!end)return false;out.assign(reinterpret_cast<const char*>(p),end-p);p+=n;
                    return std::all_of(out.begin(),out.end(),[](unsigned char c){return c>=32&&c<127;});};
                if(!text(64,m.course)||m.course.empty()||!std::all_of(m.course.begin(),m.course.end(),[](char c){return std::isalnum(static_cast<unsigned char>(c))||c=='_'||c=='-';})||
                   !text(96,m.name)||m.name.empty()||!text(65,m.texture)||m.texture.size()!=64||!std::all_of(m.texture.begin(),m.texture.end(),[](char c){return (c>='0'&&c<='9')||(c>='a'&&c<='f');})){reason="metadata_text_invalid";return false;}
                std::memcpy(&m.category,p,4);std::memcpy(&m.flags,p+4,4);std::memcpy(&m.winding,p+8,4);
                if(m.category>4||(m.flags&~127u)||(m.winding!=1&&m.winding!=-1)||(!m.category&&!(m.flags&Deny))||
                   ((m.flags&Environment)&&(m.category!=4||(m.flags&Deny)))||
                   ((m.flags&EnvironmentTexture)&&(m.category!=0||m.flags!=(Deny|EnvironmentTexture)||(m.name!="aluminium-tga"&&m.name!="whitepaint-tga"&&m.name!="silverpaint-tga")))||
                   ((m.flags&AlphaTest)&&m.category!=3&&(m.category!=4||(m.flags&Environment)))||((m.flags&TwoSided)&&m.category!=3)||
                   (!(m.flags&Deny)&&!(m.flags&(Noise|Plain)))){reason="metadata_capability_invalid";return false;}
                auto key=std::make_pair(m.course,m.texture);auto old=parsed.find(key);
                if(old!=parsed.end()&&(old->second.category!=m.category||old->second.flags!=m.flags||old->second.winding!=m.winding)){reason="metadata_ambiguous_texture";return false;}
                parsed[key]=std::move(m);
            }
            materials_=std::move(parsed);ready=true;reason="material_metadata_ready";return true;
        }catch(...){present=true;reason="metadata_exception";return false;}
    }
    const SceneMaterial* find(const char* course,const std::string& texture)const {
        auto i=materials_.find({course,texture});return i==materials_.end()?nullptr:&i->second;
    }
    size_t size()const noexcept{return materials_.size();}
};

inline bool transformed_normal(const std::array<float,3>& n,const std::array<float,16>& m,std::array<float,3>& out)noexcept {
    // Row-vector D3D world: normal * inverse-transpose(world3x3).
    const float a=m[0],b=m[1],c=m[2],d=m[4],e=m[5],f=m[6],g=m[8],h=m[9],i=m[10];
    const std::array<float,9> co{e*i-f*h,f*g-d*i,d*h-e*g,c*h-b*i,a*i-c*g,b*g-a*h,b*f-c*e,c*d-a*f,a*e-b*d};
    const float det=a*co[0]+b*co[1]+c*co[2];if(!std::isfinite(det)||std::abs(det)<1e-8f)return false;
    for(unsigned k=0;k<3;++k){out[k]=(n[0]*co[k]+n[1]*co[3+k]+n[2]*co[6+k])/det;if(!std::isfinite(out[k]))return false;}
    const float length=std::sqrt(out[0]*out[0]+out[1]*out[1]+out[2]*out[2]);if(length<1e-8f)return false;
    for(auto& x:out)x/=length;return true;
}
struct ResolvedGeometry {
    std::vector<uint8_t> original,index_bytes,lit;
    uint64_t vertex_revision=0,index_revision=0,changed=0,last_frame=0;
    std::vector<std::array<float,3>> geometric_normals,effective_normals;std::vector<uint8_t> used;uint64_t hinted=0,duplicate_faces=0,opposite_faces=0;
    uint32_t category=0;bool accepted=false;const char* reason="unclassified";
    bool same_source(const uint8_t* v,size_t vn,const uint8_t* i,size_t in,uint64_t vr,uint64_t ir,bool& compared)const noexcept {
        compared=false;if(original.size()!=vn||index_bytes.size()!=in||!v||!i)return false;
        if(vertex_revision==vr&&index_revision==ir)return true;
        compared=true;return !std::memcmp(original.data(),v,vn)&&!std::memcmp(index_bytes.data(),i,in);
    }
    size_t storage()const noexcept{return original.size()+index_bytes.size()+lit.size()+(geometric_normals.size()+effective_normals.size())*12+used.size();}
};
// Resource generations + exact draw range/state/material; no geometry hash.
using ResolverKey=std::array<uint64_t,12>;
struct ResolverKeyHash {size_t operator()(const ResolverKey& key)const noexcept {size_t h=0;for(auto x:key)h^=std::hash<uint64_t>{}(x)+0x9e3779b9+(h<<6)+(h>>2);return h;}};
class SceneResolver {
public:
    std::unordered_map<ResolverKey,ResolvedGeometry,ResolverKeyHash> entries;
    uint64_t hits=0,misses=0,rebuilds=0,content_checks=0,skipped=0,accepted=0,cache_resets=0;
    size_t bytes=0;static constexpr size_t max_bytes=48*1024*1024,max_entries=2048;
    void clear()noexcept{entries.clear();bytes=0;++cache_resets;}
    bool room(size_t wanted)const noexcept{return entries.size()<max_entries&&wanted<=max_bytes-bytes;}
    std::array<uint64_t,5> classified_ranges()const noexcept {
        std::array<uint64_t,5> counts{};for(const auto& pair:entries){const auto& entry=pair.second;
            ++counts[entry.accepted&&entry.category<=4?entry.category:0];}return counts;
    }
};

// Geometric normals are reconstructed once per changed vertex/index range.
// They do not pretend to be the original authored smoothing normals. Index
// winding is checked by source metadata; the proven native base_noise fallback
// uses MR's CW front-face convention. Invalid/degenerate inputs fail closed.
inline bool light_geometry(ResolvedGeometry& entry,unsigned stride,unsigned min,unsigned vertices,unsigned width,
                           const SceneMaterial* material,bool noise,bool opaque,bool alpha_test,
                           bool auto_ground,const Lighting& settings,NormalHints* hints=nullptr,const char* course="",const std::string& texture="",bool environment=false) {
    entry.accepted=false;entry.category=0;entry.changed=0;entry.lit.clear();entry.geometric_normals.clear();entry.effective_normals.clear();entry.used.clear();entry.hinted=0;entry.duplicate_faces=entry.opposite_faces=0;
    auto reject=[&](const char* why){entry.reason=why;return false;};
    if(!vertices||vertices>32768||(stride!=24&&stride!=32&&stride!=36)||(width!=2&&width!=4)||
       entry.original.size()!=uint64_t(vertices)*stride||entry.index_bytes.empty()||entry.index_bytes.size()%(width*3))return reject("resolver_geometry_layout");
    if(material&&(material->flags&Deny))return reject("material_explicitly_excluded");
    if(environment!=bool(stride==36)|| (environment&&(!material||!(material->flags&Environment)||material->category!=4||noise||!opaque||alpha_test)))return reject("environment_material_contract");
    const bool automatic=!material;
    if(automatic&&(!auto_ground||!noise||!opaque||alpha_test))return reject("ambiguous_material_no_ground_contract");
    if(material&&(!(material->flags&(noise?Noise:Plain))||(alpha_test&&!(material->flags&AlphaTest))||(!opaque&&material->category!=3)))return reject("metadata_live_shader_mismatch");
    const unsigned category=material?material->category:2;const float sign=material?float(material->winding):-1.f;
    std::vector<std::array<float,3>> positions(vertices);std::vector<std::array<double,3>> normals(vertices);std::vector<uint8_t> used(vertices);
    for(unsigned i=0;i<vertices;++i){const auto* v=entry.original.data()+i*stride;std::memcpy(positions[i].data(),v,12);
        for(float x:positions[i])if(!std::isfinite(x)||std::abs(x)>1e7f)return reject("resolver_nonfinite_position");
        float uv[2]{};std::memcpy(uv,v+(environment?28:16),8);for(float x:uv)if(!std::isfinite(x)||std::abs(x)>1e7f)return reject("resolver_nonfinite_uv");}
    // PS2 course buffers contain front/back triangles sharing the SAME vertex
    // indices. Summing both cancels normals and amplifies float residue. Dedup
    // only for shading; the submitted index stream and culling stay untouched.
    std::unordered_map<uint64_t,bool> seen;std::vector<std::array<uint32_t,3>> triangles;
    for(size_t offset=0;offset<entry.index_bytes.size();offset+=width*3){std::array<uint32_t,3> ix{};
        for(unsigned k=0;k<3;++k){std::memcpy(&ix[k],entry.index_bytes.data()+offset+k*width,width);if(ix[k]<min||uint64_t(ix[k])>=uint64_t(min)+vertices)return reject("resolver_index_out_of_range");ix[k]-=min;}
        auto sorted=ix;std::sort(sorted.begin(),sorted.end());
        const uint64_t key=uint64_t(sorted[0])|(uint64_t(sorted[1])<<15)|(uint64_t(sorted[2])<<30);
        const bool parity=(unsigned(ix[0]>ix[1])+unsigned(ix[0]>ix[2])+unsigned(ix[1]>ix[2]))%2!=0;
        auto old=seen.emplace(key,parity);if(!old.second){++entry.duplicate_faces;if(old.first->second!=parity)++entry.opposite_faces;continue;}
        triangles.push_back(ix);
    }
    uint64_t positive=0,faces=0;
    for(const auto& ix:triangles){
        const auto& a=positions[ix[0]];const auto& b=positions[ix[1]];const auto& c=positions[ix[2]];
        const std::array<double,3> u{double(b[0])-a[0],double(b[1])-a[1],double(b[2])-a[2]},v{double(c[0])-a[0],double(c[1])-a[1],double(c[2])-a[2]};
        std::array<double,3> n{sign*(u[1]*v[2]-u[2]*v[1]),sign*(u[2]*v[0]-u[0]*v[2]),sign*(u[0]*v[1]-u[1]*v[0])};
        const double norm=std::sqrt(n[0]*n[0]+n[1]*n[1]+n[2]*n[2]);if(!std::isfinite(norm))return reject("resolver_normal_overflow");if(norm<1e-10)continue;
        ++faces;if(n[1]/norm>.2)++positive;
        for(unsigned k=0;k<3;++k){auto& sum=normals[ix[k]];double alignment=0;for(unsigned j=0;j<3;++j)alignment+=sum[j]*n[j];
            const double face_sign=((material&&(material->flags&TwoSided))||entry.opposite_faces)&&alignment<0?-1.:1.;
            used[ix[k]]=1;for(unsigned j=0;j<3;++j)sum[j]+=n[j]*face_sign;}
    }
    if(!faces)return reject("resolver_degenerate_geometry");
    if(automatic&&positive*4<faces*3)return reject("ambiguous_non_ground_geometry");
    entry.lit=entry.original;entry.geometric_normals.assign(vertices,{});entry.effective_normals.assign(vertices,{});entry.used=used;entry.hinted=0;
    for(unsigned i=0;i<vertices;++i)if(used[i]){const auto& sum=normals[i];const double length=std::sqrt(sum[0]*sum[0]+sum[1]*sum[1]+sum[2]*sum[2]);
        if(!std::isfinite(length)||length<1e-10){entry.lit.clear();return reject("resolver_cancelled_vertex_normal");}
        std::array<float,3> n{};for(unsigned k=0;k<3;++k)n[k]=float(sum[k]/length);
        if(environment){std::memcpy(n.data(),entry.original.data()+i*stride+12,12);float norm=0;for(float x:n){if(!std::isfinite(x))return reject("environment_nonfinite_normal");norm+=x*x;}if(!std::isfinite(norm)||norm<1e-8f)return reject("environment_invalid_normal");for(float& x:n)x/=std::sqrt(norm);}
        entry.geometric_normals[i]=n;bool hinted=false;
        if(hints&&category!=3&&!environment){hinted=hints->resolve(course,texture,positions[i],n,n);
            // Paired front/back topology has no intrinsic signed orientation.
            // Authored hints may choose either side; admission is unchanged.
            if(!hinted&&entry.opposite_faces){auto opposite=n;for(auto& x:opposite)x=-x;hinted=hints->resolve(course,texture,positions[i],opposite,n);}
            if(hinted)++entry.hinted;}
        entry.effective_normals[i]=n;
        if(!environment&&((material&&(material->flags&TwoSided))||(entry.opposite_faces&&!hinted))){float dot=0;for(unsigned j=0;j<3;++j)dot+=n[j]*settings.direction[j];if(dot<0)for(float& x:n)x=-x;}
        const unsigned color_offset=environment?24:12;
        uint32_t original=0;std::memcpy(&original,entry.original.data()+i*stride+color_offset,4);const auto color=scene_color(original,n,settings);
        std::memcpy(entry.lit.data()+i*stride+color_offset,&color,4);entry.changed+=color!=original;
    }
    entry.category=category;entry.accepted=true;entry.reason=automatic?"native_opaque_base_noise_ground":"material_capability_and_live_geometry";return true;
}
} // namespace gfx2::atmosphere
