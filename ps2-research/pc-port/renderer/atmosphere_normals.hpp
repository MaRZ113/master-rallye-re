#pragma once
#include "atmosphere_scene.hpp"
#include <map>
#include <tuple>
namespace gfx2::atmosphere {
// Optional authoring data, NOT admission. Spatially indexed original normals
// survive draw splits, vertex reordering and UV/prelight edits. Missing hints
// leave the independent material resolver and geometric fallback operational.
class NormalHints {
    using Key=std::tuple<std::string,std::string,int32_t,int32_t,int32_t>;
    std::map<Key,std::vector<std::array<float,3>>> rows_;
public:
    bool attempted=false,ready=false;const char* reason="not_loaded";
    uint64_t matched=0,fallback=0;size_t records=0;
    static int32_t cell(float x)noexcept{return int32_t(std::lround(double(x)*1000));}
    bool load(const std::filesystem::path& path)noexcept {
        if(attempted)return ready;attempted=true;
        try {
            std::ifstream f(path,std::ios::binary|std::ios::ate);
            if(!f||f.tellg()<76||f.tellg()>64*1024*1024){reason="normal_hints_missing_or_size";return false;}
            std::vector<uint8_t> b(size_t(f.tellg()));f.seekg(0);if(!f.read(reinterpret_cast<char*>(b.data()),b.size()))return false;
            uint32_t version=0,count=0;std::memcpy(&version,b.data()+4,4);std::memcpy(&count,b.data()+8,4);
            constexpr size_t size=64+65+24;
            if(std::memcmp(b.data(),"LNH1",4)||version!=1||count>400000||b.size()!=76+uint64_t(count)*size){reason="normal_hints_header";return false;}
            const auto sha=sha256_bytes(b.data()+76,b.size()-76);if(std::memcmp(sha.data(),b.data()+12,64)){reason="normal_hints_checksum";return false;}
            std::map<Key,std::vector<std::array<float,3>>> parsed;
            for(unsigned j=0;j<count;++j){const auto* r=b.data()+76+j*size;
                if(!std::memchr(r,0,64)||!std::memchr(r+64,0,65)){reason="normal_hints_text";return false;}
                const std::string course(reinterpret_cast<const char*>(r)),texture(reinterpret_cast<const char*>(r+64));
                if(canonical_course(course).empty()||texture.size()!=64){reason="normal_hints_identity";return false;}
                std::array<float,3> p{},n{};std::memcpy(p.data(),r+129,12);std::memcpy(n.data(),r+141,12);
                for(float x:p)if(!std::isfinite(x)||std::abs(x)>1e6f){reason="normal_hints_position";return false;}
                float length=0;for(float x:n){if(!std::isfinite(x)){reason="normal_hints_normal";return false;}length+=x*x;}
                if(length<.99f||length>1.01f){reason="normal_hints_unit_normal";return false;}
                auto& candidates=parsed[{canonical_course(course),texture,cell(p[0]),cell(p[1]),cell(p[2])}];
                if(std::any_of(candidates.begin(),candidates.end(),[&](const auto& other){float dot=0;for(unsigned k=0;k<3;++k)dot+=other[k]*n[k];return dot>.9999f;}))continue;
                if(candidates.size()==16){reason="normal_hints_ambiguous_capacity";return false;}candidates.push_back(n);
            }
            rows_=std::move(parsed);records=count;ready=true;reason="authored_spatial_normals_ready";return true;
        }catch(...){reason="normal_hints_exception";return false;}
    }
    bool only_course(const std::string& course)const{const auto key=canonical_course(course);return !key.empty()&&std::all_of(rows_.begin(),rows_.end(),[&](const auto& r){return std::get<0>(r.first)==key;});}
    bool resolve(const std::string& course,const std::string& texture,const std::array<float,3>& p,const std::array<float,3>& geometric,std::array<float,3>& result) {
        // A changed layout at the same position cannot borrow an unrelated
        // normal: require facing agreement. At authored hard edges choose the
        // best aligned original cluster; a near tie retains geometric shading.
        if(!ready||std::any_of(p.begin(),p.end(),[](float x){return !std::isfinite(x)||std::abs(x)>1e6f;})){++fallback;return false;}
        const auto it=rows_.find({canonical_course(course),texture,cell(p[0]),cell(p[1]),cell(p[2])});
        if(it==rows_.end()){++fallback;return false;}
        float best=.5f,second=-1;std::array<float,3> chosen{};
        for(const auto& n:it->second){float dot=0;for(unsigned k=0;k<3;++k)dot+=n[k]*geometric[k];
            if(dot>best){second=best;best=dot;chosen=n;}else if(dot>second)second=dot;}
        if(best<=.5f||(second>.5f&&best-second<.02f)){++fallback;return false;}
        result=chosen;++matched;return true;
    }
};
}
