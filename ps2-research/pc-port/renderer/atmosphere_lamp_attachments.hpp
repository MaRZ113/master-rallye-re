#pragma once
#include "atmosphere_lamp_surface.hpp"
#include "atmosphere_headlights.hpp"
#include "provenance.hpp"
#include <filesystem>
#include <fstream>
#include <sstream>

namespace gfx2::atmosphere {
// A source-authored attachment is independent of vertex positions, draw-local
// vertex numbering, node ownership and the switch's current OFF/ON state.
struct LampAttachment {
    int rig=-1;std::string texture,uv;unsigned expanded_vertices=0;
    LampSurfaceAnchor anchor;
};
struct LampAttachments {
    std::vector<LampAttachment> rows;std::string sha;bool ready=false;const char* reason="not_loaded";
    bool manages(int rig,size_t point)const noexcept {if(!ready)return false;for(const auto& r:rows)if(r.rig==rig&&r.anchor.point==point)return true;return false;}
    bool texture_known(const std::string& texture)const noexcept {if(!ready)return false;for(const auto& r:rows)if(r.texture==texture)return true;return false;}
    bool signature_known(const std::string& texture,const std::string& uv,unsigned vertices)const noexcept {
        if(!ready)return false;for(const auto& r:rows)if(r.texture==texture&&r.uv==uv&&r.expanded_vertices==vertices)return true;return false;
    }
    bool load(const std::filesystem::path& file,const LampRigs& rigs)noexcept {
        *this=LampAttachments{};
        try {
            std::ifstream input(file,std::ios::binary|std::ios::ate);
            if(!input||input.tellg()<135||input.tellg()>2*1024*1024){reason="attachment_file_missing_or_size";return false;}
            std::string bytes(size_t(input.tellg()),'\0');input.seekg(0);if(!input.read(bytes.data(),bytes.size()))return false;
            const auto end=bytes.find('\n');if(end==std::string::npos)return false;
            std::istringstream header(bytes.substr(0,end));std::string magic,rig_sha,payload_sha,extra;
            if(!(header>>magic>>rig_sha>>payload_sha)||magic!="LPA1"||(header>>extra)){reason="attachment_header_invalid";return false;}
            if(rig_sha!=rigs.sha||rig_sha.size()!=64){reason="attachment_rig_hash_mismatch";return false;}
            const auto payload=bytes.substr(end+1);sha=sha256_bytes(payload.data(),payload.size());
            if(sha!=payload_sha){reason="attachment_payload_hash_mismatch";return false;}
            auto digest=[](const std::string& s){return s.size()==64&&std::all_of(s.begin(),s.end(),[](char c){return (c>='0'&&c<='9')||(c>='a'&&c<='f');});};
            std::istringstream lines(payload);std::string line;
            while(std::getline(lines,line)){
                if(line.empty())continue;std::istringstream in(line);LampAttachment row;std::string car;unsigned triangle=0;
                if(!(in>>car>>row.anchor.point>>row.texture>>row.uv>>row.expanded_vertices>>triangle>>row.anchor.weights[0]>>row.anchor.weights[1]>>row.anchor.weights[2]>>row.anchor.offset>>row.anchor.sign>>row.anchor.distance)||(in>>extra)){
                    reason="attachment_row_invalid";return false;}
                for(size_t i=0;i<rigs.rigs.size();++i)if(rigs.rigs[i].car==car){row.rig=int(i);break;}
                const auto& a=row.anchor;
                if(row.rig<0||a.point>=rigs.rigs[size_t(row.rig)].points.size()||!digest(row.texture)||!digest(row.uv)||
                   !row.expanded_vertices||row.expanded_vertices>98304||row.expanded_vertices%3||triangle>=row.expanded_vertices/3||
                   !std::isfinite(a.offset)||a.offset<0||a.offset>.06f||!std::isfinite(a.distance)||a.distance<0||a.distance>.0625f||
                   (a.sign!=1&&a.sign!=-1)||!std::all_of(a.weights.begin(),a.weights.end(),[](float x){return std::isfinite(x)&&x>=-1e-5f&&x<=1.00001f;})||
                   std::abs(a.weights[0]+a.weights[1]+a.weights[2]-1)>1e-4f||rows.size()>=2048){reason="attachment_contract_invalid";return false;}
                row.anchor.vertices={triangle*3,triangle*3+1,triangle*3+2};rows.push_back(std::move(row));
            }
            if(rows.empty()){reason="attachment_rows_empty";return false;}
            ready=true;reason="source_lamp_attachments_ready";return true;
        }catch(...){rows.clear();reason="attachment_exception";return false;}
    }
};
// LPA1 uses the parser's source-DX corner order. The native PC compiler swaps
// the first two corners of every triangle (also proved by the fleet source
// certificates). Undo that swap for BOTH positions and UVs: weights and normal
// orientation must refer to the same source corners as the authored anchor.
inline bool lamp_attachment_geometry(const std::vector<uint8_t>& bytes,unsigned stride,const std::vector<uint32_t>& indices,
                                     std::vector<LampVec>& positions,std::string& uv_sha){
    positions.clear();uv_sha.clear();if((stride!=24&&stride!=36)||bytes.size()%stride||indices.empty()||indices.size()%3||indices.size()>98304)return false;
    std::vector<float> uv;uv.reserve(indices.size()*2);positions.reserve(indices.size());
    for(size_t corner=0;corner<indices.size();++corner){
        const auto source_corner=corner%3==0?corner+1:corner%3==1?corner-1:corner;
        const auto i=indices[source_corner];if(i>=bytes.size()/stride)return false;const auto* v=bytes.data()+size_t(i)*stride;
        LampVec p{};float t[2]{};std::memcpy(p.data(),v,12);std::memcpy(t,v+stride-8,8);
        for(float x:p)if(!std::isfinite(x))return false;for(auto& x:t){if(!std::isfinite(x))return false;if(x==0)x=0;uv.push_back(x);}positions.push_back(p);}
    uv_sha=sha256_bytes(uv.data(),uv.size()*sizeof(float));return true;
}
struct LampAttachmentDraw {std::string texture,uv;Mat4 world{};uintptr_t owner=0;std::vector<LampVec> positions;};
struct LampAttachmentQueue {
    std::vector<LampAttachmentDraw> draws;uint64_t frame=UINT64_MAX,race=UINT64_MAX,reset=UINT64_MAX,resolved=UINT64_MAX;
    size_t vertices=0;uint64_t candidates=0,signature_misses=0,owner_misses=0,points=0;
    void clear()noexcept{draws.clear();vertices=0;frame=race=reset=resolved=UINT64_MAX;}
    void begin(uint64_t f,uint64_t r,uint64_t s){if(frame!=f||race!=r||reset!=s){clear();frame=f;race=r;reset=s;}}
    bool push(LampAttachmentDraw draw){if(draws.size()>=64||draw.positions.size()>65536-vertices)return false;vertices+=draw.positions.size();draws.push_back(std::move(draw));return true;}
};
template<class Poses> inline uintptr_t lamp_attachment_owner(const LampAttachmentDraw& draw,const Poses& poses,uint64_t frame)noexcept {
    uintptr_t owner=0;
    for(const auto& pose:poses)if(pose.instance&&pose.frame==frame&&pose.m==draw.world){
        if(owner&&owner!=pose.instance)return 0;owner=pose.instance;}
    return draw.owner&&owner!=draw.owner?0:owner;
}
}
