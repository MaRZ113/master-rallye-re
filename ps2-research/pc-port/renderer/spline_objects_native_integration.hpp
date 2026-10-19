#pragma once
// COURSE-ALIVE1 native side: the moving PS2 spline objects are one private draw per texture at the typed pre-UI
// boundary, with the same world proof (gameplay VIEW/PROJECTION sites, a later native world draw, unchanged target,
// depth and viewport) and the same fixed state transaction as the course objects and grass. Single camera only.
#include "course_objects_native_integration.hpp"
#include "spline_objects.hpp"
#include "ps2_hud_damage_feed.hpp"
#include <cstdio>
#include <vector>

namespace gfx2::splineintegration {
inline ps2port::SplineObjectsPilot* pilot(Device8& d) noexcept {return d.ps2_port()?d.ps2_port()->spline_objects():nullptr;}

// PS2 tick observer: Broker "Car0" -> gaVehicleOutputData (tag 10, type name) -> vehicle position +0xec/+0xf0/+0xf4
// (PC GPS 4a57a0 and ps2_hud_damage_feed.hpp read the same fields). The PS2 owner uses the literal Car0 as well.
class SplineObserverReader {
    uint64_t generation_=0;bool id_ok_=false;uint32_t car0_=0;
public:
    bool read(RaceReadMemory& m,uint32_t base,uint64_t race,ps2spline::Vec3& out,const char*& reason) noexcept {
        reason="not_read";
        if(!race){reason="no_race_generation";return false;}
        if(race!=generation_){generation_=race;id_ok_=m.resolve_id(base,"Car0",car0_);}
        if(!id_ok_){reason="car0_key_missing";return false;}
        uint32_t manager=0,begin=0,end=0,native=0,payload=0,tag=0,type=0,vehicle=0;
        auto word=[&](uint32_t a,uint32_t& v){return !(a&3)&&m.read(a,&v,4);};
        auto pointer=[&](uint32_t a,uint32_t& v){return word(a,v)&&v>=0x10000&&v<=0x7ffffffc&&!(v&3);};
        if(!pointer(base+ps2port::kHudBrokerRva,manager)||!pointer(manager+4,begin)||!word(manager+8,end)||end<begin||(end-begin)%0x1c||
           car0_>=(end-begin)/0x1c){reason="broker_unreadable";return false;}
        const uint32_t record=begin+car0_*0x1c;char name[32]{};
        if(!word(record,native)||native!=car0_||!word(record+8,tag)||tag!=ps2port::kHudBrokerObjectTag||!pointer(record+4,payload)||
           !word(payload+4,type)||!race_pool_text(m,base,type,name,sizeof(name))||std::strcmp(name,"gaVehicleOutputData")||
           !pointer(payload+8,vehicle)){reason="car0_not_vehicle_output";return false;}
        for(int i=0;i<3;++i)if(!m.read(vehicle+0xec+4*i,&out[size_t(i)],4)||!std::isfinite(out[size_t(i)])){reason="car0_position_unreadable";return false;}
        reason="car0_vehicle_output";return true;
    }
};
inline SplineObserverReader& observer_reader() noexcept {static SplineObserverReader r;return r;}

inline HRESULT repair(Device8& d) noexcept {
    auto* p=pilot(d);if(!p)return S_OK;if(p->blocked())return D3DERR_DEVICELOST;
    if(!p->transaction.has_pending())return S_OK;
    return p->transaction.restore(*d.native(),[&](uint32_t slot,const Args& args,HRESULT hr) noexcept {courseintegration::after_setter(d,slot,args,hr);});
}
inline void observe_transform(Device8& d,D3DTRANSFORMSTATETYPE type,bool exe,uint32_t rva,HRESULT hr) noexcept {
    auto* p=pilot(d);if(!p||!p->active()||!exe)return;
    const bool is_view=type==D3DTS_VIEW&&rva==GAMEPLAY_VIEW_RETURN_RVA;
    const bool is_projection=type==D3DTS_PROJECTION&&rva==GAMEPLAY_PROJECTION_RETURN_RVA;
    if(!is_view&&!is_projection)return;
    p->proof.invalidate_depth();
    if(is_view)p->proof.view_site=false;
    if(is_projection)p->proof.projection_site=false;
    if(FAILED(hr)||!d.trace.scene_active||GetCurrentThreadId()!=d.trace.render_thread_id())return;
    bool single=false;const auto cert=courseintegration::certificate(d,single);
    const bool selected=single&&cert.valid&&p->select_course(cert.course_id.data(),cert.race_generation);
    if(p->take_course_log()&&p->diagnostics())try{session().write("{\"type\":\"ps2_spline_objects_course\",\"course\":"+quote(std::string(cert.course_id.data()))+
        ",\"race_generation\":"+std::to_string(cert.race_generation)+",\"selected\":"+(selected?"true":"false")+
        ",\"course_guard\":"+quote(p->guard_reason())+",\"objects\":"+std::to_string(selected?p->runtime().controllers().size():0)+"}");}catch(...){}
    if(!selected){p->proof.clear();return;}
    auto& proof=p->proof;const auto frame=d.trace.frame_number();const auto reset=d.ps2_port()->reset_generation();
    if(proof.frame!=frame||proof.device!=d.trace.device_id()||proof.reset!=reset||
       proof.race!=cert.race_generation||proof.owner!=cert.owner_lifetime||proof.camera!=cert.camera){
        proof.clear();proof.frame=frame;proof.device=d.trace.device_id();proof.reset=reset;
        proof.race=cert.race_generation;proof.owner=cert.owner_lifetime;proof.camera=cert.camera;
    }
    const auto& tracked=d.trace.effective_shadow.matrices[type];D3DMATRIX native{};
    if(!tracked.known||FAILED(d.native()->GetTransform(type,&native))||std::memcmp(&native,&tracked.value,64)||!courseintegration::finite_matrix(native))return;
    proof.invalidate_depth();
    if(is_view){proof.view=native;proof.view_site=true;}
    if(is_projection&&courseintegration::perspective(native)){proof.projection=native;proof.projection_site=true;}
}
inline void observe_world_draw(Device8& d,HRESULT hr) noexcept {
    auto* p=pilot(d);if(!p||!p->active()||FAILED(hr)||!d.trace.scene_active||GetCurrentThreadId()!=d.trace.render_thread_id())return;
    auto& proof=p->proof;
    if(proof.world_draw||proof.frame!=d.trace.frame_number()||!proof.view_site||!proof.projection_site)return;
    auto& n=*d.native();D3DMATRIX view{},projection{};DWORD z=0,func=0;
    if(FAILED(n.GetTransform(D3DTS_VIEW,&view))||FAILED(n.GetTransform(D3DTS_PROJECTION,&projection))||
       std::memcmp(&view,&proof.view,64)||std::memcmp(&projection,&proof.projection,64)||
       FAILED(n.GetRenderState(D3DRS_ZENABLE,&z))||z!=D3DZB_TRUE||FAILED(n.GetRenderState(D3DRS_ZFUNC,&func))||func!=D3DCMP_LESSEQUAL)return;
    courseintegration::Ref<IDirect3DSurface8> target,back,depth;D3DVIEWPORT8 viewport{};D3DSURFACE_DESC desc{};
    if(FAILED(n.GetRenderTarget(&target.p))||FAILED(n.GetBackBuffer(0,D3DBACKBUFFER_TYPE_MONO,&back.p))||
       !courseintegration::same_identity(target.p,back.p)||FAILED(n.GetDepthStencilSurface(&depth.p))||!depth.p||
       FAILED(n.GetViewport(&viewport))||FAILED(target.p->GetDesc(&desc))||viewport.X||viewport.Y||
       viewport.Width!=desc.Width||viewport.Height!=desc.Height||viewport.MinZ!=0||viewport.MaxZ!=1)return;
    proof.viewport=viewport;proof.target=target.p;target.p=nullptr;proof.depth=depth.p;depth.p=nullptr;proof.world_draw=true;
}
// Native course fog as the game left it after the world: linear vertex fog, no table fog, finite 0 <= start < end.
inline bool native_course_fog(IDirect3DDevice8& n) noexcept {
    DWORD vertex=0,table=0,start=0,end=0;float s=0,e=0;
    if(FAILED(n.GetRenderState(D3DRS_FOGVERTEXMODE,&vertex))||FAILED(n.GetRenderState(D3DRS_FOGTABLEMODE,&table))||
       FAILED(n.GetRenderState(D3DRS_FOGSTART,&start))||FAILED(n.GetRenderState(D3DRS_FOGEND,&end)))return false;
    std::memcpy(&s,&start,4);std::memcpy(&e,&end,4);
    return vertex==D3DFOG_LINEAR&&table==D3DFOG_NONE&&std::isfinite(s)&&std::isfinite(e)&&s>=0.f&&s<e;
}
inline std::string pose_record(const ps2port::SplineObjectsPilot& p,uint64_t frame,const char* observer) {
    const auto& rt=p.runtime();const auto& a=p.asset();const auto& c=a.courses[rt.course()];
    std::string s="{\"type\":\"ps2_spline_objects_pose\",\"course\":"+quote(c.id)+",\"frame\":"+std::to_string(frame)+
        ",\"race_generation\":"+std::to_string(rt.race())+",\"invocations\":"+std::to_string(rt.ticks())+",\"observer\":"+quote(observer)+",\"objects\":[";
    for(size_t i=0;i<rt.controllers().size();++i){const auto& k=rt.controllers()[i];const auto pose=k.pose();char buf[256];
        std::snprintf(buf,sizeof(buf),"%s{\"egg\":\"%s\",\"active\":%s,\"time\":%.6g,\"position\":[%.4f,%.4f,%.4f],\"forward\":[%.5f,%.5f,%.5f],\"up\":[%.5f,%.5f,%.5f]}",
            i?",":"",a.objects[c.first+i].egg.c_str(),k.active()?"true":"false",double(k.time()),double(pose.position[0]),double(pose.position[1]),double(pose.position[2]),
            double(pose.forward[0]),double(pose.forward[1]),double(pose.forward[2]),double(pose.up[0]),double(pose.up[1]),double(pose.up[2]));s+=buf;}
    return s+"]}";
}
inline HRESULT before_ui(Device8& d,bool ui_callsite,bool ui_consumer) noexcept {
    auto* p=pilot(d);if(!p||!p->active()||!ui_callsite)return S_OK;
    const ps2port::CourseBoundaryContext boundary{d.trace.frame_number(),d.trace.device_id(),
        d.ps2_port()->reset_generation(),GetCurrentThreadId()==d.trace.render_thread_id(),
        d.trace.scene_active,ui_consumer,d.trace.shadow.recording||d.trace.effective_shadow.recording};
    if(!ps2port::course_world_preflight(p->proof,boundary)||p->boundary_consumed(boundary.frame,p->proof.race,boundary.reset))return S_OK;
    auto& proof=p->proof;auto& n=*d.native();bool single=false;
    const auto cert=courseintegration::certificate(d,single);
    if(!single||!cert.valid||!p->select_course(cert.course_id.data(),cert.race_generation))return S_OK;
    // Motion first, once per frame: it must not depend on whether this frame's draw is admitted.
    const char* observer_reason="not_read";ps2spline::Vec3 observer{};
    ps2port::HudLiveMemory memory;
    const bool have_observer=observer_reader().read(memory,0x400000,cert.race_generation,observer,observer_reason);
    const auto pause=read_pause_menu_state_readonly();
    const bool paused=pause.present&&pause.tag==0&&pause.value!=0;
    p->advance_frame(boundary.frame,paused,have_observer?&observer:nullptr);
    if(p->claim_pose_log())try{session().write(pose_record(*p,boundary.frame,observer_reason));}catch(...){}
    courseintegration::Ref<IDirect3DSurface8> target,depth;D3DVIEWPORT8 viewport{};
    ps2port::CourseAdmission a;
    a.supported_build=session().target;a.render_thread=GetCurrentThreadId()==d.trace.render_thread_id();
    a.scene_active=d.trace.scene_active;a.asset_ready=p->active();a.ui_callsite=ui_callsite;a.ui_consumer=ui_consumer;
    a.state_block_recording=d.trace.shadow.recording||d.trace.effective_shadow.recording;
    a.camera_single=single;a.race_valid=cert.valid;a.course=cert.course_id.data();
    a.frame=d.trace.frame_number();a.proof_frame=proof.frame;a.device=d.trace.device_id();a.proof_device=proof.device;
    a.reset=d.ps2_port()->reset_generation();a.proof_reset=proof.reset;
    a.race=cert.race_generation;a.proof_race=proof.race;a.owner=cert.owner_lifetime;a.proof_owner=proof.owner;
    a.camera=cert.camera;a.proof_camera=proof.camera;a.view_site=proof.view_site;
    a.projection_site=proof.projection_site;a.world_draw=proof.world_draw;
    a.target_matches=SUCCEEDED(n.GetRenderTarget(&target.p))&&courseintegration::same_identity(target.p,proof.target);
    a.depth_matches=SUCCEEDED(n.GetDepthStencilSurface(&depth.p))&&courseintegration::same_identity(depth.p,proof.depth);
    a.viewport_matches=SUCCEEDED(n.GetViewport(&viewport))&&!std::memcmp(&viewport,&proof.viewport,sizeof(viewport));
    a.pc_depth_convention=courseintegration::perspective(proof.projection);
    a.native_dependency_states=courseintegration::native_dependencies(n);
    const auto& course=p->asset().courses[p->runtime().course()];
    const char* reason=ps2port::course_object_admission(a,course.id);
    if(std::strcmp(reason,"eligible")){
        if(p->claim_log(false))try{session().write("{\"type\":\"ps2_spline_objects_gate\",\"reason\":"+quote(reason)+
            ",\"course\":"+quote(std::string(a.course))+",\"frame\":"+std::to_string(a.frame)+"}");}catch(...){}
        return S_OK;
    }
    if(!p->consume_boundary(a.frame,a.race,a.reset))return S_OK;
    std::vector<ps2port::SplineBatch> batches;
    if(!p->runtime().build(batches)){p->disable("spline_world_vertices_nonfinite");return S_OK;}
    const bool fog=native_course_fog(n);
    const auto writer=[&](uint32_t slot,const Args& args,HRESULT hr) noexcept {courseintegration::after_setter(d,slot,args,hr);};
    HRESULT captured=S_OK,applied=S_OK,draw=E_PENDING,restored=S_OK;UINT triangles=0,draws=0;
    for(const auto& batch:batches){
        if(batch.vertices.empty())continue;
        captured=p->transaction.capture(n);if(FAILED(captured))break;
        // World identity (vertices are already world space), the verified gameplay view and projection.
        applied=p->transaction.apply(n,p->texture(batch.texture),proof.view,proof.projection,writer,
            ps2port::CourseObjectMaterialState{TRUE,D3DTADDRESS_WRAP,D3DTADDRESS_WRAP,FALSE,static_cast<DWORD>(fog?TRUE:FALSE)});
        if(SUCCEEDED(applied)){
            p->transaction.mark_up_stream_changed();
            // Private draw only; never fed into the application's draw tracker or classifier.
            draw=n.DrawPrimitiveUP(D3DPT_TRIANGLELIST,static_cast<UINT>(batch.vertices.size()/3),batch.vertices.data(),sizeof(ps2port::ObjectVertex));
            if(FAILED(draw))p->disable("native_spline_objects_draw_failed");
            else{triangles+=static_cast<UINT>(batch.vertices.size()/3);++draws;}
        }
        if(p->transaction.has_pending())restored=p->transaction.restore(n,writer);
        if(FAILED(restored)){p->disable("native_spline_objects_state_restore_failed");break;}
        p->transaction.release();
        if(FAILED(applied)||FAILED(draw))break;
    }
    if(p->claim_log(true)||FAILED(restored))try{session().write("{\"type\":\"ps2_spline_objects_draw\",\"course\":"+quote(course.id)+
        ",\"frame\":"+std::to_string(a.frame)+",\"race_generation\":"+std::to_string(a.race)+",\"camera\":"+std::to_string(a.camera)+
        ",\"objects\":"+std::to_string(p->runtime().controllers().size())+",\"draws\":"+std::to_string(draws)+",\"triangles\":"+std::to_string(triangles)+
        ",\"fog\":"+(fog?"true":"false")+",\"course_guard\":"+quote(p->guard_reason())+",\"observer\":"+quote(observer_reason)+
        ",\"capture_hresult\":"+std::to_string(static_cast<uint32_t>(captured))+",\"apply_hresult\":"+std::to_string(static_cast<uint32_t>(applied))+
        ",\"draw_hresult\":"+std::to_string(static_cast<uint32_t>(draw))+",\"restore_hresult\":"+std::to_string(static_cast<uint32_t>(restored))+
        ",\"artifact_sha256\":"+quote(ps2port::kSplineObjectsArtifactSha)+",\"runtime_visibility\":\"PENDING_USER\"}");}catch(...){}
    return FAILED(restored)?restored:S_OK;
}
} // namespace gfx2::splineintegration
