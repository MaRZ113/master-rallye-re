#pragma once
#include "atmosphere_scene.hpp"
#include <map>
#include <string>
namespace gfx2::atmosphere {
// Explicit diagnostic capture only. Never controls the camera or game clocks.
struct CourseCapture {
    bool enabled=false,key_down=false,original_world=false,seen=false,ambiguous=false,overflow=false;
    unsigned stage=0;uint64_t start=0,last_boundary=UINT64_MAX,seen_frame=UINT64_MAX,race=0,owner=0;
    D3DVIEWPORT8 viewport{},reference_viewport{};float reference_sky_scale=1;
    D3DMATRIX view{},projection{},reference_view{},reference_projection{};Lighting reference_lighting;
    std::string course,metadata_sha;uint64_t metadata_reload=0;std::filesystem::path directory;std::vector<std::string> ledger;
    static constexpr size_t max_rows=8192;
    void observe(uint64_t frame,const D3DMATRIX& v,const D3DMATRIX& p)noexcept{
        if(seen_frame!=frame){seen_frame=frame;seen=false;ambiguous=false;}
        if(seen&&(std::memcmp(&view,&v,64)||std::memcmp(&projection,&p,64)))ambiguous=true;
        for(const auto& row:v.m)for(float x:row)if(!std::isfinite(x))ambiguous=true;
        for(const auto& row:p.m)for(float x:row)if(!std::isfinite(x))ambiguous=true;
        view=v;projection=p;seen=true;
    }
    bool same_camera(uint64_t frame)const noexcept{return seen&&seen_frame==frame&&!ambiguous&&!std::memcmp(&view,&reference_view,64)&&!std::memcmp(&projection,&reference_projection,64)&&!std::memcmp(&viewport,&reference_viewport,sizeof(viewport));}
    static bool same_lighting(const Lighting& a,const Lighting& b)noexcept{
        return a.mode==b.mode&&a.strength==b.strength&&a.exposure==b.exposure&&a.world_brightness==b.world_brightness&&
            a.ambient==b.ambient&&a.sun==b.sun&&a.direction==b.direction&&a.ambient_strength==b.ambient_strength&&a.sun_strength==b.sun_strength&&
            a.fog_enabled==b.fog_enabled&&a.fog==b.fog&&a.fog_strength==b.fog_strength&&a.prelight_contrast==b.prelight_contrast&&a.prelight_visibility==b.prelight_visibility&&a.surface_tone==b.surface_tone&&a.tone_contrast==b.tone_contrast&&a.tone_shoulder==b.tone_shoulder&&a.rim==b.rim&&a.rim_strength==b.rim_strength&&a.rim_power==b.rim_power;
    }
    void append(std::string line){if(ledger.size()==max_rows){overflow=true;return;}ledger.push_back(std::move(line));}
    void cancel(bool& world)noexcept{if(stage)world=original_world;stage=0;ledger.clear();overflow=false;}
};
// P0.1 coverage ledger (Atmosphere.ini CoverageLedger=1, diagnostic, off by
// default). Every course-loop draw seen by observe() is aggregated by
// course/texture/FVF/verdict for the whole session, including draws a
// replacement (ForestFix, PS2 water) took before the atmosphere path. The
// ledger never changes rendering; it is flushed to coverage-<pid>.json.
struct CoverageRow {std::string course,texture,material,verdict,reason;uint32_t fvf=0,category=0;uint64_t draws=0,triangles=0,frames=0,last_frame=UINT64_MAX;};
struct CourseCoverage {
    bool enabled=false,pending=false,reached=false,overflow=false,dirty=false;
    std::string texture;uint32_t fvf=0;uint64_t frame=0,triangles=0,last_flush=0;
    std::map<std::string,CoverageRow> rows;static constexpr size_t max_rows=16384;
    void add(const std::string& course,const std::string& material,const std::string& verdict,const std::string& reason,uint32_t category){
        const std::string key=course+"|"+texture+"|"+std::to_string(fvf)+"|"+verdict+"|"+reason;
        auto it=rows.find(key);
        if(it==rows.end()){if(rows.size()>=max_rows){overflow=true;return;}
            it=rows.emplace(key,CoverageRow{course,texture,material,verdict,reason,fvf,category}).first;}
        auto& r=it->second;++r.draws;r.triangles+=triangles;if(r.last_frame!=frame){r.last_frame=frame;++r.frames;}
        if(r.material.empty())r.material=material;dirty=true;
    }
    static std::string json(const std::string& s){std::string o="\"";for(char c:s){if(c=='"'||c=='\\')o+='\\';if(static_cast<unsigned char>(c)>=32)o+=c;}return o+"\"";}
    std::string serialize(uint64_t frame_now)const{
        std::string o="{\"type\":\"atmosphere_coverage_ledger\",\"schema\":1,\"frame\":"+std::to_string(frame_now)+",\"overflow\":"+(overflow?"true":"false")+",\"rows\":[";
        bool first=true;for(const auto& [k,r]:rows){if(!first)o+=",";first=false;
            o+="{\"course\":"+json(r.course)+",\"texture_sha256\":"+json(r.texture)+",\"material\":"+json(r.material)+",\"verdict\":"+json(r.verdict)+
               ",\"reason\":"+json(r.reason)+",\"fvf\":"+std::to_string(r.fvf)+",\"category\":"+std::to_string(r.category)+",\"draws\":"+std::to_string(r.draws)+
               ",\"triangles\":"+std::to_string(r.triangles)+",\"frames\":"+std::to_string(r.frames)+"}";}
        return o+"]}";
    }
};
} // namespace gfx2::atmosphere
