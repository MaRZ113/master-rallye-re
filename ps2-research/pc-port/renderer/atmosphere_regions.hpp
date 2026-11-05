#pragma once
#include "atmosphere_scene.hpp"
#include "atmosphere_lifecycle.hpp"
#include <charconv>
#include <map>
#include <sstream>
namespace gfx2::atmosphere {
// Immutable, opt-in authoring data. Never authorizes a material or changes a hook.
struct RegionalPatch {
    std::map<std::string,float> numbers;bool has_fog=false;uint32_t fog=0;int sky=-2;
};
struct RegionalField {const char* name;float Lighting::*member;float low,high;};
inline constexpr RegionalField kRegionalFields[]={
    {"LightingStrength",&Lighting::strength,0,1},{"Exposure",&Lighting::exposure,.25f,2},
    {"WorldBrightness",&Lighting::world_brightness,.1f,1.5f},{"AmbientStrength",&Lighting::ambient_strength,0,2},
    {"SunlightStrength",&Lighting::sun_strength,0,2},{"FogStrength",&Lighting::fog_strength,0,1},
    {"PrelightContrast",&Lighting::prelight_contrast,0,1},{"PrelightVisibility",&Lighting::prelight_visibility,0,1}};
inline std::string regional_scene(const std::string& scene){
    if(scene.size()>9&&_strnicmp(scene.c_str(),"RaceTest/",9)==0)return canonical_course(scene.substr(9));return {};
}
class RegionalCatalog {
    std::map<std::string,RegionalPatch> profiles_,courses_;std::map<std::string,std::string> bindings_;
    static std::string trim(std::string s){const auto a=s.find_first_not_of(" \t\r");if(a==s.npos)return {};return s.substr(a,s.find_last_not_of(" \t\r")-a+1);}
    static bool patch_value(RegionalPatch& p,const std::string& key,const std::string& value){
        if(key=="FogColor"){
            const auto v=value.rfind("0x",0)==0?value.substr(2):value;uint32_t n=0;const auto r=std::from_chars(v.data(),v.data()+v.size(),n,16);
            if(r.ec!=std::errc{}||r.ptr!=v.data()+v.size()||n>0xffffff)return false;p.has_fog=true;p.fog=0xff000000u|n;return true;}
        if(key=="SkyPreset"){
            if(value=="Inherit"){p.sky=-2;return true;}if(value=="Native"){p.sky=-1;return true;}
            if(value.size()!=1||value[0]<'0'||value[0]>'5')return false;p.sky=value[0]-'0';return true;}
        float lo=0,hi=0;bool found=false;
        for(const auto& f:kRegionalFields)if(key==f.name){lo=f.low;hi=f.high;found=true;}
        for(const auto* prefix:{"Ambient","Sunlight","SunDir"})for(char c:std::string(prefix==std::string("SunDir")?"XYZ":"RGB"))if(key==std::string(prefix)+c){lo=prefix==std::string("SunDir")?-1.f:0.f;hi=prefix==std::string("SunDir")?1.f:2.f;found=true;}
        if(key=="FogEnabled"){found=true;lo=0;hi=1;if(value!="0"&&value!="1")return false;}
        float n=0;const auto r=std::from_chars(value.data(),value.data()+value.size(),n);
        if(!found||r.ec!=std::errc{}||r.ptr!=value.data()+value.size()||!std::isfinite(n)||n<lo||n>hi)return false;
        p.numbers[key]=n;return true;
    }
    static bool direction_valid(const RegionalPatch& p){
        unsigned count=0;float length=0;for(const auto* k:{"SunDirX","SunDirY","SunDirZ"}){const auto it=p.numbers.find(k);if(it!=p.numbers.end()){++count;length+=it->second*it->second;}}
        return !count||(count==3&&length>1e-6f);
    }
    static void apply_patch(Lighting& s,const RegionalPatch& p,int& sky){
        for(const auto& f:kRegionalFields){const auto it=p.numbers.find(f.name);if(it!=p.numbers.end())s.*(f.member)=it->second;}
        for(unsigned i=0;i<3;++i)for(unsigned a=0;a<3;++a){const std::string prefix=a==0?"Ambient":a==1?"Sunlight":"SunDir";const auto k=prefix+(a==2?"XYZ":"RGB")[i];const auto it=p.numbers.find(k);if(it!=p.numbers.end())(a==0?s.ambient:a==1?s.sun:s.direction)[i]=it->second;}
        if(const auto it=p.numbers.find("FogEnabled");it!=p.numbers.end())s.fog_enabled=it->second==1;
        if(p.has_fog)s.fog=p.fog;if(p.sky!=-2)sky=p.sky;
    }
public:
    bool ready=false;const char* reason="regional_off";std::string sha;size_t bindings()const noexcept{return bindings_.size();}
    bool parse(const std::string& content){
        *this={};reason="regional_invalid_file";if(content.empty()||content.size()>256*1024)return false;
        RegionalCatalog next;std::istringstream stream(content);std::string line,section;std::map<std::string,bool> seen;unsigned lines=0;
        while(std::getline(stream,line)){
            if(++lines>4096||line.size()>512)return false;line=trim(line);if(line.empty()||line[0]==';'||line[0]=='#')continue;
            if(line.front()=='['&&line.back()==']'){section=line.substr(1,line.size()-2);if(section!="Regions"){if(section.rfind("Region:",0)!=0&&section.rfind("Course:",0)!=0)return false;const auto name=canonical_course(section.substr(7));if(name.empty())return false;section=section.substr(0,7)+name;}continue;}
            const auto at=line.find('=');if(section.empty()||at==line.npos)return false;const auto key=trim(line.substr(0,at)),value=trim(line.substr(at+1));
            if(key.empty()||value.empty()||!seen.emplace(section+"/"+key,true).second)return false;
            if(section=="Regions"){const auto course=canonical_course(key),region=canonical_course(value);if(course.empty()||region.empty()||!next.bindings_.emplace(course,region).second)return false;}
            else {const auto name=canonical_course(section.substr(7));if(name.empty())return false;auto& dest=section.rfind("Region:",0)==0?next.profiles_:next.courses_;if(!patch_value(dest[name],key,value))return false;}
        }
        if(next.profiles_.size()>32||next.courses_.size()>256||next.bindings_.size()>256)return false;
        for(const auto& b:next.bindings_)if(!next.profiles_.count(b.second))return false;
        for(const auto* table:{&next.profiles_,&next.courses_})for(const auto& p:*table)if(!direction_valid(p.second))return false;
        next.ready=true;next.reason="regional_catalog_ready";next.sha=sha256_bytes(reinterpret_cast<const BYTE*>(content.data()),content.size());*this=std::move(next);return true;
    }
    bool load(const std::filesystem::path& path){
        std::ifstream f(path,std::ios::binary|std::ios::ate);if(!f||f.tellg()<0||f.tellg()>256*1024){*this={};reason="regional_missing_or_oversized";return false;}
        std::string s(static_cast<size_t>(f.tellg()),'\0');f.seekg(0);if(!f.read(s.data(),s.size())){*this={};reason="regional_read_failed";return false;}return parse(s);
    }
    std::string apply(const std::string& scene,Lighting& s,int& sky)const{
        sky=-2;if(!ready||!s.active())return {};const auto course=regional_scene(scene);if(course.empty())return {};std::string region;
        if(const auto b=bindings_.find(course);b!=bindings_.end()){region=b->second;apply_patch(s,profiles_.at(region),sky);}
        if(const auto p=courses_.find(course);p!=courses_.end()){apply_patch(s,p->second,sky);if(region.empty())region="course_override";}return region;
    }
};
inline const RegionalCatalog& regional_catalog(const std::wstring& ini){
    // A process snapshot keeps early native CloudNumber and subsequent lighting
    // consistent. Editing regional authoring data requires a new process.
    static const RegionalCatalog catalog=[&](){RegionalCatalog c;wchar_t text[512]{};GetPrivateProfileStringW(L"Atmosphere",L"RegionalAtmospheres",L"",text,512,ini.c_str());
        if(text[0]){std::filesystem::path path(text);if(path.is_relative())path=std::filesystem::path(ini).parent_path()/path;c.load(path);}return c;}();return catalog;
}
inline int regional_sky_request(const std::wstring& ini,const Lifecycle& life,int requested){
    if(!life.installed||!life.same_thread||!life.race||!life.scene)return requested;
    wchar_t mode[32]{};GetPrivateProfileStringW(L"Atmosphere",L"LightingPreset",L"GoldenHour",mode,32,ini.c_str());if(std::wcscmp(mode,L"Original")==0)return requested;
    Lighting s;s.mode=Lighting::Mode::GoldenHour;int sky=-2;regional_catalog(ini).apply(life.scene_name.data(),s,sky);return sky==-2?requested:sky;
}
} // namespace gfx2::atmosphere
