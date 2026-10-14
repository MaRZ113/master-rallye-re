#include "vehicle_partition.hpp"
#include "vehicle_partition_registry.hpp"
#include "foliage_probe.hpp"
#include "provenance.hpp"
#include <algorithm>
#include <cstring>

namespace gfx2::ps2port {
bool vehicle_partition_layout(uint32_t t,uint32_t v) noexcept {
    for(const auto& m:kVehiclePartitionMaterials)if(m.triangles==t&&m.vertices==v)return true;
    return false;
}
std::vector<std::string> vehicle_face_hashes(const DrawSnapshot& s) {
    if(!s.complete_mirror_coverage || s.primitive_type!=D3DPT_TRIANGLELIST ||
       !s.primitive_count || s.primitive_count>8192 || !s.vertex_count ||
       (s.fvf!=0x152 && s.fvf!=0x142) || s.stride!=(s.fvf==0x152?36u:24u) ||
       !s.vertex_resource || !s.index_resource || !s.vertex_generation || !s.index_generation ||
       !s.vertex_revision || !s.index_revision)return {};
    const uint32_t size=s.index_format==D3DFMT_INDEX16?2u:s.index_format==D3DFMT_INDEX32?4u:0;
    const uint64_t begin=(uint64_t(s.base_vertex)+s.min_index)*s.stride;
    if(!size || s.index_bytes.size()!=uint64_t(s.primitive_count)*3*size || begin<s.vertex_byte_offset)return {};
    const uint64_t relative=begin-s.vertex_byte_offset;
    if(relative>s.vertex_bytes.size() || uint64_t(s.vertex_count)*s.stride>s.vertex_bytes.size()-relative)return {};
    std::vector<std::string> faces;faces.reserve(s.primitive_count);
    for(uint32_t f=0;f<s.primitive_count;++f) {
        float xyz[9]{};
        for(uint32_t k=0;k<3;++k) {
            uint32_t i=0;std::memcpy(&i,s.index_bytes.data()+(f*3u+k)*size,size);
            if(i<s.min_index || i-s.min_index>=s.vertex_count)return {};
            std::memcpy(xyz+k*3,s.vertex_bytes.data()+relative+uint64_t(i-s.min_index)*s.stride,12);
        }
        auto h=foliage_face_hash(xyz);if(h.empty())return {};
        faces.push_back(std::move(h));
    }
    return faces;
}
PartitionPlan partition_ordered_faces(const std::vector<std::string>& faces,const PartitionMaterial& m) {
    PartitionPlan p;p.material=&m;
    if(faces.size()!=m.triangles || !m.face_count || m.face_count>8192){p.reason="face_count_mismatch";return p;}
    std::vector<uint32_t> counts(m.face_count);
    for(uint32_t n=0;n<faces.size();++n) {
        const auto* at=std::lower_bound(m.faces,m.faces+m.face_count,faces[n],
            [](const PartitionFace& a,const std::string& b){return std::string_view(a.hash)<b;});
        if(at==m.faces+m.face_count || faces[n]!=at->hash){p.reason="unknown_current_face";p.runs.clear();return p;}
        const auto i=static_cast<size_t>(at-m.faces);
        if(++counts[i]>at->multiplicity){p.reason="face_multiplicity_mismatch";p.runs.clear();return p;}
        if(p.runs.empty() || p.runs.back().shiny!=at->shiny)p.runs.push_back({n,1,at->shiny});
        else ++p.runs.back().count;
    }
    std::string joined;
    for(size_t i=0;i<m.face_count;++i) {
        if(counts[i]!=m.faces[i].multiplicity){p.reason="face_multiplicity_mismatch";p.runs.clear();return p;}
        for(uint32_t n=0;n<counts[i];++n)joined+=m.faces[i].hash;
    }
    if(sha256_bytes(joined.data(),joined.size())!=m.geometry_sha){p.reason="full_geometry_mismatch";p.runs.clear();return p;}
    p.accepted=true;p.reason="exact_current_geometry_verified_material_partition";return p;
}
bool partition_context_valid(const ReflectionSnapshot& s,uint64_t generation) noexcept {
    const auto* g=s.geometry;
    return g && g->supported_build && g->device_id && g->reset_generation==generation &&
        g->complete_mirror_coverage && g->vertex_resource && g->index_resource &&
        g->vertex_generation && g->index_generation && g->vertex_revision && g->index_revision &&
        g->primitive_type==D3DPT_TRIANGLELIST && g->fvf==0x152 && g->stride==36 &&
        s.requested_mode==4 && s.live_race_verified && s.race_generation && s.owner_lifetime &&
        (s.vehicle_body_verified || s.source_material_context_verified) && s.stock_coordinate_policy &&
        s.native_states_complete && s.native_matches_effective && s.texture_matrix_known &&
        s.textures_are_2d && s.textures[0] && s.textures[1] && s.texture_generations[0] && s.texture_generations[1] &&
        s.render_states==std::array<DWORD,4>{FALSE,FALSE,TRUE,FALSE} &&
        s.stages[0]==std::array<DWORD,8>{D3DTOP_MODULATE,D3DTA_TEXTURE,D3DTA_DIFFUSE,
            D3DTOP_MODULATE,D3DTA_TEXTURE,D3DTA_DIFFUSE,0,0} &&
        s.stages[1]==std::array<DWORD,8>{D3DTOP_MODULATEALPHA_ADDCOLOR,D3DTA_CURRENT,D3DTA_TEXTURE,
            D3DTOP_MODULATE,D3DTA_CURRENT,D3DTA_TEXTURE,D3DTSS_TCI_CAMERASPACENORMAL,D3DTTFF_COUNT2};
}
VehiclePartitionPilot::VehiclePartitionPilot(bool supported,const std::wstring& ini) noexcept {
    wchar_t mode[32]{},version[32]{};
    GetPrivateProfileStringW(L"PS2Port",L"RaceModelMode",L"0",mode,32,ini.c_str());
    GetPrivateProfileStringW(L"PS2Port",L"VehicleModelConfigVersion",L"1",version,32,ini.c_str());
    requested_=vehicle_partition_opt_in(mode,version,supported);
    diagnostics_=GetPrivateProfileIntW(L"PS2Port",L"VehicleModelDiagnostics",0,ini.c_str())==1;
}
PartitionPlan VehiclePartitionPilot::classify(const ReflectionSnapshot& s,uint64_t generation) noexcept {
    try {
        if(!requested_ || !partition_context_valid(s,generation)){PartitionPlan p;p.reason="stock_or_unverified_current_context";return p;}
        const auto& g=*s.geometry;
        const std::array<uint64_t,15> key={g.device_id,g.reset_generation,g.vertex_resource,g.index_resource,
            g.vertex_generation,g.index_generation,g.vertex_revision,g.index_revision,g.start_index,
            g.base_vertex,g.min_index,g.vertex_count,g.index_format,g.vertex_byte_offset,g.primitive_count};
        for(const auto& e:cache_)if(e.valid&&e.key==key)return e.plan;
        PartitionPlan p;p.reason="not_in_source_registry";
        const auto faces=vehicle_face_hashes(g);
        for(const auto& m:kVehiclePartitionMaterials)if(m.triangles==g.primitive_count&&m.vertices==g.vertex_count) {
            p=partition_ordered_faces(faces,m);if(p.accepted)break;
        }
        auto& e=cache_[next_++%cache_.size()];e={key,p,true};return p;
    }catch(...){PartitionPlan p;p.reason="partition_evaluation_failed_stock";return p;}
}
bool VehiclePartitionPilot::claim_diagnostic(const PartitionMaterial* m) noexcept {
    if(!diagnostics_)return false;
    for(size_t i=0;i<logged_.size();++i)if(m==&kVehiclePartitionMaterials[i]) {
        if(logged_[i])return false;logged_[i]=true;return true;
    }
    return false;
}
} // namespace gfx2::ps2port
