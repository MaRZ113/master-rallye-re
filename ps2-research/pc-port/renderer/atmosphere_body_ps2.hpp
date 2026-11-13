#pragma once
#include "atmosphere_body_common.hpp"
namespace gfx2::atmospherebody {
// Called ONLY inside the existing fully certified fleet private submission,
// after reflection capture, deformation transfer and final owner recheck.
inline bool fleet_vertices(Device8& d,const ps2port::FrontendModel& model,const char* family,const char* asset_identity,unsigned mesh,const D3DMATRIX& world,
                           const std::vector<ps2port::FrontendVertex>& source,std::vector<ps2port::FrontendVertex>& output,const char* resource="car",
                           const atmosphere::BodyCapability** used=nullptr) {   // used: G2.1 grime (role and texture name of the mesh)
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
    output.resize(source.size());std::memcpy(output.data(),copy.data(),copy.size());p->body_vertices+=changed;if(used)*used=capability;
    if(p->first_reason(("body_ps2_"+canonical+resource+"_"+std::to_string(mesh)).c_str()))session().write("{\"type\":\"atmosphere_body_material\",\"route\":\"certified_ps2_fleet\",\"family\":"+quote(canonical)+",\"primary\":"+quote(capability->primary)+",\"resource\":"+quote(std::string(resource))+",\"metadata_payload_sha256\":"+quote(p->body_capabilities.payload_sha)+",\"surface_role\":"+quote(std::string(atmosphere::body_role_name(capability->role)))+",\"mesh_index\":"+std::to_string(mesh)+",\"prepared_normal_y_replaced\":"+(model.ps2_lighting()?"true":"false")+",\"reflection_uv_changed\":false,\"environment_exposure_requested\":false,\"shared_buffer_mutated\":false,\"changed_vertices\":"+std::to_string(changed)+",\"frame\":"+std::to_string(d.trace.frame_number())+"}");
    return true;
}
// VEHICLE-FIX2: the PS2 fleet submission replaces the native body draws, so the
// native body observer (atmosphere_body_general) never sees these cars. Called
// once per certified private submission: car pose (headlight projectors) and
// the car's offline lamp rig, chosen by family (rig car == fleet family; the
// PC lens draw that normally matches a rig is suppressed with the body).
inline void fleet_observe(Device8& d,uintptr_t instance,const D3DMATRIX& w,const char* family)noexcept{
    auto* p=atmosphereintegration::pilot(d);if(!p||!p->enabled()||!instance||!family)return;
    try{
        const auto frame=d.trace.frame_number();atmosphere::Mat4 pose{};std::memcpy(pose.data(),&w,64);for(float x:pose)if(!std::isfinite(x))return;
        p->observe_car(instance,pose,frame);
        if(!p->glint_style.enabled||!p->lamp_rigs.loaded||!p->lighting.active()||p->lighting.ambient_strength>=.5f)return;
        bool single=false;const auto cert=courseintegration::certificate(d,single);if(!single||!cert.valid)return;
        if(p->rig_race!=cert.race_generation){for(auto& owner:p->rig_owners)owner={};p->rig_race=cert.race_generation;}
        auto* o=p->rig_owner(instance,frame,true);if(!o)return;
        if(o->rig<0||_stricmp(p->lamp_rigs.rigs[size_t(o->rig)].car.c_str(),family)){
            int r=-1;for(size_t i=0;i<p->lamp_rigs.rigs.size();++i)if(!_stricmp(p->lamp_rigs.rigs[i].car.c_str(),family)){r=int(i);break;}
            if(r<0)return;o->rig=r;o->surfaces.clear();++p->rig_matches;
            session().write("{\"type\":\"atmosphere_lamp_rig_match\",\"frame\":"+std::to_string(frame)+",\"car\":"+quote(p->lamp_rigs.rigs[size_t(r)].car)+",\"route\":\"ps2_fleet_family\"}");}
        if(o->emitted==frame)return;o->emitted=frame;
        if(p->lamp_points_frame!=frame){p->lamp_points.clear();p->lamp_points_frame=frame;}
        const bool braking=o->braking!=UINT64_MAX&&o->braking+2>=frame;const auto forward=atmosphere::normalized({w._31,w._32,w._33});
        const auto& rig=p->lamp_rigs.rigs[size_t(o->rig)];
        for(size_t i=0;i<rig.points.size()&&p->lamp_points.size()<128;++i){const auto& q=rig.points[i];
            const bool front=q.kind==0||q.kind==4;uint8_t kind=q.kind==4?0:q.kind;if(q.kind==2){if(braking)kind=2;else if(q.tail)kind=1;else continue;}
            atmosphere::Pilot::LampPoint lp;lp.instance=instance;lp.front=front;lp.kind=kind;lp.size=q.kind==4?q.size*.8f:q.size;lp.rig_point=i;
            // PS2 lenses are not the PC lens surface: 3 cm outwards keeps the sprite centre in front of the PS2 shell.
            for(unsigned k=0;k<3;++k){lp.axis[k]=front?forward[k]:-forward[k];
                lp.world[k]=q.pos[0]*(&w._11)[k]+q.pos[1]*(&w._11)[4+k]+q.pos[2]*(&w._11)[8+k]+(&w._11)[12+k]+lp.axis[k]*.03f;}
            p->lamp_points.push_back(lp);++p->rig_points;}
    }catch(...){}
}
// Night only (AmbientStrength < .5): XRGB factor for PS2 fleet passes the body
// relight does not cover (glass, env layers); 0 = leave the PS2 material as is.
inline DWORD fleet_night_factor(Device8& d)noexcept{
    auto* p=atmosphereintegration::pilot(d);if(!p||!p->enabled()||!p->lighting.active()||p->lighting.ambient_strength>=.5f)return 0;
    return 0xff000000u|(atmosphere::flat_body_color(0xffffffffu,p->lighting)&0x00ffffffu);
}
inline void fleet_night_vertices(DWORD factor,const std::vector<ps2port::FrontendVertex>& source,std::vector<ps2port::FrontendVertex>& output){
    output=source;const unsigned f[3]{(factor>>16)&255,(factor>>8)&255,factor&255};
    for(auto& v:output){DWORD c=v.color&0xff000000u;for(unsigned k=0;k<3;++k){const unsigned shift=(2-k)*8;c|=DWORD(((v.color>>shift)&255)*f[k]/255)<<shift;}v.color=c;}
}
}
