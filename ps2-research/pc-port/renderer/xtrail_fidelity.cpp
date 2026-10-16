#include "xtrail_fidelity.hpp"
#include "ps2_config.hpp"
#include "xtrail_decal_registry.hpp"
#include "xtrail_glass.hpp"
#include "brake_glow.hpp"
#include "provenance.hpp"
#include <algorithm>
#include <cstring>
namespace gfx2::ps2port {
std::vector<XtrailDecalVertex> prepare_decal_vertices(const DrawSnapshot& g,std::string_view expected,
    const XtrailDecalNormal* normals,size_t entries){
    if(!normals||entries!=20)return {};
    if(!g.supported_build||!g.device_id||g.fvf!=0x142||g.stride!=24||g.vertex_count!=20||g.primitive_count!=14)return {};
    auto faces=vehicle_face_hashes(g);if(faces.size()!=14)return {};
    std::sort(faces.begin(),faces.end());std::string joined;for(const auto& f:faces)joined+=f;
    if(sha256_bytes(joined.data(),joined.size())!=expected)return {};
    const size_t relative=static_cast<size_t>((uint64_t(g.base_vertex)+g.min_index)*24-g.vertex_byte_offset);
    std::array<XtrailDecalVertex,20> vertices{};
    for(uint32_t i=0;i<20;++i){
        const uint8_t* source=g.vertex_bytes.data()+relative+i*24;
        float xyz[3]{};std::memcpy(xyz,source,12);
        for(float& value:xyz)if(value==0)value=0; // same source signed-zero identity rule
        const auto hash=sha256_bytes(xyz,12);
        const auto* entry=std::lower_bound(normals,normals+entries,hash,
            [](const XtrailDecalNormal& a,const std::string& b){return std::string_view(a.position_sha)<b;});
        if(entry==normals+entries||hash!=entry->position_sha||
           std::memcmp(source+16,entry->uv_bits.data(),8))return {};
        DWORD color=0;std::memcpy(&color,source+12,4);if(color!=entry->diffuse)return {};
        auto& v=vertices[i];std::memcpy(v.xyz,source,12);std::memcpy(v.normal,entry->normal_bits.data(),12);
        v.diffuse=color;std::memcpy(v.uv,source+16,8);
    }
    const uint32_t size=g.index_format==D3DFMT_INDEX16?2u:4u;
    std::vector<XtrailDecalVertex> result;result.reserve(42);
    for(uint32_t i=0;i<42;++i){uint32_t index=0;std::memcpy(&index,g.index_bytes.data()+i*size,size);result.push_back(vertices[index-g.min_index]);}
    return result;
}
std::vector<XtrailDecalVertex> prepare_xtrail_decal(const DrawSnapshot& g){
    return prepare_decal_vertices(g,kXtrailDecalGeometrySha,kXtrailDecalNormals,std::size(kXtrailDecalNormals));
}
void XtrailTransaction::release() noexcept {
    if(texture_)texture_->Release();if(stream_)stream_->Release();if(indices_)indices_->Release();
    texture_=nullptr;stream_=nullptr;indices_=nullptr;pending_=0;captured_=false;
}
HRESULT XtrailTransaction::capture(IDirect3DDevice8& n) noexcept {
    if(pending_)return D3DERR_INVALIDCALL;release();
    for(size_t i=0;i<stages_.size();++i){auto hr=n.GetTextureStageState(1,kReflectionStageStates[i],&stages_[i]);if(FAILED(hr))return hr;}
    auto hr=n.GetTexture(1,&texture_);
    if(SUCCEEDED(hr))hr=n.GetVertexShader(&fvf_);
    if(SUCCEEDED(hr))hr=n.GetStreamSource(0,&stream_,&stride_);
    if(SUCCEEDED(hr))hr=n.GetIndices(&indices_,&base_);
    if(FAILED(hr)||!stream_||!indices_){release();return FAILED(hr)?hr:E_POINTER;}
    captured_=true;return S_OK;
}
XtrailFidelity::XtrailFidelity(bool supported,const std::wstring& ini) noexcept {
    try{glass_=std::make_unique<XtrailGlass>(supported,ini);}catch(...){}
    try{brake_=std::make_unique<BrakeGlow>(supported,ini);}catch(...){}
    wchar_t mode[32]{},version[32]{};
    ::gfx2::ps2port::config::read_string(L"XtrailFidelityMode",L"0",mode,32,ini.c_str());
    ::gfx2::ps2port::config::read_string(L"XtrailFidelityVersion",L"1",version,32,ini.c_str());
    requested_=xtrail_fidelity_opt_in(mode,version,supported);
    diagnostics_=::gfx2::ps2port::config::read_int(L"XtrailFidelityDiagnostics",0,ini.c_str())==1;
}
XtrailFidelity::~XtrailFidelity()=default;
bool XtrailFidelity::glass_pending()const noexcept{return (glass_&&(glass_->blocked()||glass_->transaction.pending()))||(brake_&&(brake_->blocked()||brake_->transaction.pending()));}
void XtrailFidelity::before_reset()noexcept{if(transaction.pending())blocked_=true;transaction.release();for(auto& c:cache_)c={};next_=0;if(glass_)glass_->before_reset();if(brake_)brake_->before_reset();}
void XtrailFidelity::after_reset(bool called,bool successful)noexcept{if(called&&successful){blocked_=false;logged_=0;}if(glass_)glass_->after_reset(called,successful);if(brake_)brake_->after_reset(called,successful);}
const std::vector<XtrailDecalVertex>* XtrailFidelity::prepare(const DrawSnapshot& g) noexcept {
    try{
        if(!g.supported_build||!g.complete_mirror_coverage||!g.device_id||!g.vertex_generation||!g.index_generation||
           !g.vertex_revision||!g.index_revision||g.fvf!=0x142||g.stride!=24||g.vertex_count!=20||g.primitive_count!=14)return nullptr;
        const std::array<uint64_t,15> key={g.device_id,g.reset_generation,g.vertex_resource,g.index_resource,
            g.vertex_generation,g.index_generation,g.vertex_revision,g.index_revision,g.start_index,
            g.base_vertex,g.min_index,g.vertex_count,g.index_format,g.vertex_byte_offset,g.primitive_count};
        for(auto& c:cache_)if(c.valid&&c.key==key)return c.vertices.empty()?nullptr:&c.vertices;
        auto& c=cache_[next_++%cache_.size()];c={key,prepare_xtrail_decal(g),true};return c.vertices.empty()?nullptr:&c.vertices;
    }catch(...){return nullptr;}
}
} // namespace gfx2::ps2port
