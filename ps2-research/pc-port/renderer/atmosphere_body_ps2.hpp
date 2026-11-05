#pragma once
#include "atmosphere_body_common.hpp"
namespace gfx2::atmospherebody {
// Called ONLY inside the existing fully certified fleet private submission,
// after reflection capture, deformation transfer and final owner recheck.
inline bool fleet_vertices(Device8& d,const ps2port::FrontendModel& model,const char* family,const char* asset_identity,unsigned mesh,const D3DMATRIX& world,
                           const std::vector<ps2port::FrontendVertex>& source,std::vector<ps2port::FrontendVertex>& output,const char* resource="car") {
    auto* p=atmosphereintegration::pilot(d);if(!p||!p->enabled()||!p->body_materials||!p->lighting.active())return false;
    Timing timer(*p);p->body_capabilities.load(p->body_path);
    if(!p->body_capabilities.ready||mesh>=model.asset().meshes.size()||d.trace.shadow.recording||d.trace.effective_shadow.recording||GetCurrentThreadId()!=d.trace.render_thread_id())return false;
    courseintegration::Ref<IDirect3DSurface8> target,back;auto& n=*d.native();
    if(FAILED(n.GetRenderTarget(&target.p))||FAILED(n.GetBackBuffer(0,D3DBACKBUFFER_TYPE_MONO,&back.p))||!courseintegration::same_identity(target.p,back.p))return false;
    const auto& m=model.asset().meshes[mesh];if((m.mode!=1&&m.mode!=3)||m.texture[0]>=model.asset().textures.size())return false;
    auto key=std::make_pair(std::string(model.content_fix()?model.content_fix()->sha:asset_identity),m.texture[0]);auto found=p->body_texture_cache.find(key);
    if(found==p->body_texture_cache.end()){
        if(p->body_texture_cache.size()>=1024)return false;const auto& texture=model.asset().textures[m.texture[0]];
        found=p->body_texture_cache.emplace(key,sha256_bytes(texture.pixels.data(),texture.pixels.size()*4)).first;
    }
    std::string canonical=family;for(auto& c:canonical)c=char(std::tolower(static_cast<unsigned char>(c)));
    std::string secondary(64,'0');if(p->body_capabilities.extended&&m.mode==3){if(m.texture[1]>=model.asset().textures.size())return false;
        const auto skey=std::make_pair(key.first,m.texture[1]);auto second=p->body_texture_cache.find(skey);if(second==p->body_texture_cache.end()){
            if(p->body_texture_cache.size()>=1024)return false;const auto& t=model.asset().textures[m.texture[1]];second=p->body_texture_cache.emplace(skey,sha256_bytes(t.pixels.data(),t.pixels.size()*4)).first;}secondary=second->second;}
    const auto* capability=p->body_capabilities.ps2_capability(canonical,found->second,resource,secondary);if(!capability||(!p->body_capabilities.extended&&m.mode!=3))return false;
    std::vector<uint8_t> copy(source.size()*sizeof(source[0]));std::memcpy(copy.data(),source.data(),copy.size());uint64_t changed=0;
    D3DMATRIX view{};const bool have_view=p->lighting.rim&&SUCCEEDED(n.GetTransform(D3DTS_VIEW,&view));
    if(!shade(copy,36,24,12,world,p->lighting,model.ps2_lighting(),changed,capability->role,have_view?&view:nullptr))return false;
    debug_sample(d,*p,"certified_ps2_fleet",canonical,source.data(),copy.data(),source.size(),world);
    output.resize(source.size());std::memcpy(output.data(),copy.data(),copy.size());p->body_vertices+=changed;
    if(p->first_reason(("body_ps2_"+canonical+resource+"_"+std::to_string(mesh)).c_str()))session().write("{\"type\":\"atmosphere_body_material\",\"route\":\"certified_ps2_fleet\",\"family\":"+quote(canonical)+",\"primary\":"+quote(capability->primary)+",\"resource\":"+quote(std::string(resource))+",\"metadata_payload_sha256\":"+quote(p->body_capabilities.payload_sha)+",\"surface_role\":"+quote(std::string(atmosphere::body_role_name(capability->role)))+",\"mesh_index\":"+std::to_string(mesh)+",\"prepared_normal_y_replaced\":"+(model.ps2_lighting()?"true":"false")+",\"reflection_uv_changed\":false,\"environment_exposure_requested\":false,\"shared_buffer_mutated\":false,\"changed_vertices\":"+std::to_string(changed)+",\"frame\":"+std::to_string(d.trace.frame_number())+"}");
    return true;
}
}
