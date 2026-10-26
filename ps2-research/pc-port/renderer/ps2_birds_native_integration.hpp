#pragma once
// COURSE-ALIVE2 native side: the PS2 birds are one private draw per atlas cell at the typed pre-UI boundary, after the
// course, water and spline objects (the PS2 drains its en2d world sprites after the course geometry), with the same
// world proof and fixed state transaction as the course objects, grass and spline objects. Single camera only.
// PS2 mode8 sprite state -> D3D: ABE (Cs-Cd)*As+Cd = SRCALPHA/INVSRCALPHA, ATE 0 = no alpha test, ZTST GEQUAL with PS2
// reversed depth = LESSEQUAL, ZMSK 1 = no depth write, FGE 1 = course fog, TFX MODULATE TCC 1 = texture x white,
// TEX1 linear/linear, REGION_CLAMP = one CLAMP texture per atlas cell.
#include "spline_objects_native_integration.hpp"
#include "ps2_birds_pilot.hpp"
#include <cstdio>
#include <vector>

namespace gfx2::birdsintegration {
inline ps2port::PS2BirdsPilot* pilot(Device8& d) noexcept {return d.ps2_port()?d.ps2_port()->birds():nullptr;}

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
    if(p->take_course_log()&&p->diagnostics())try{
        const size_t c=birds_course_index(p->asset(),cert.course_id.data());
        const bool gate=c!=SIZE_MAX&&p->asset().courses[c].flight_present&&p->asset().courses[c].mill_present;
        session().write("{\"type\":\"ps2_birds_course\",\"course\":"+quote(std::string(cert.course_id.data()))+
        ",\"race_generation\":"+std::to_string(cert.race_generation)+",\"selected\":"+(selected?"true":"false")+
        ",\"course_guard\":"+quote(p->guard_reason())+",\"ps2_update_gate\":"+(gate?"\"open\"":"\"closed_no_local_milllist\"")+
        ",\"ignore_list_gate_diagnostic\":"+(p->ignore_gate()?"true":"false")+",\"flight_points\":"+std::to_string(c!=SIZE_MAX?p->asset().courses[c].count:0)+"}");}catch(...){}
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
inline std::string state_record(const ps2port::PS2BirdsPilot& p,uint64_t frame) {
    const auto& m=p.manager();std::vector<ps2birds::BirdView> v;try{m.snapshot(v);}catch(...){}
    std::string s="{\"type\":\"ps2_birds_state\",\"course\":"+quote(p.asset().courses[p.course()].id)+",\"frame\":"+std::to_string(frame)+
        ",\"race_generation\":"+std::to_string(p.race())+",\"ticks\":"+std::to_string(m.ticks())+",\"flying\":"+std::to_string(m.flying_count())+
        ",\"pending\":"+std::to_string(m.pending_count())+",\"free\":"+std::to_string(m.free_count())+",\"rng_state\":"+std::to_string(m.rng().state())+",\"birds\":[";
    for(size_t i=0;i<v.size();++i){char buf[160];std::snprintf(buf,sizeof(buf),"%s{\"entity\":%u,\"key\":%d,\"position\":[%.3f,%.3f,%.3f]}",i?",":"",
        unsigned(v[i].entity),int(v[i].key),double(v[i].position[0]),double(v[i].position[1]),double(v[i].position[2]));s+=buf;}
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
    if(!single||!cert.valid||!p->select_course(cert.course_id.data(),cert.race_generation)){
        if(auto* x=d.ps2_port())x->note(ps2diag::Effect::Birds,single&&cert.valid?p->guard_reason():"no_single_race_certificate");
        return S_OK;
    }
    // Ticks first, once per frame, with this frame's verified camera (PS2 observer = camera manager entry 0).
    ps2birds::Vec3 camera{},look{},up{};
    if(!ps2port::birds_camera(proof.view,camera,look,up)){if(auto* x=d.ps2_port())x->note(ps2diag::Effect::Birds,"camera_not_orthonormal");return S_OK;}
    const auto pause=read_pause_menu_state_readonly();
    p->advance_frame(boundary.frame,pause.present&&pause.tag==0&&pause.value!=0,camera);
    if(p->claim_state_log())try{session().write(state_record(*p,boundary.frame));}catch(...){}
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
    const auto& course=p->asset().courses[p->course()];
    const char* reason=ps2port::course_object_admission(a,course.id);
    if(std::strcmp(reason,"eligible")){
        if(auto* x=d.ps2_port())x->note(ps2diag::Effect::Birds,reason);
        if(p->claim_log(false))try{session().write("{\"type\":\"ps2_birds_gate\",\"reason\":"+quote(reason)+
            ",\"course\":"+quote(std::string(a.course))+",\"frame\":"+std::to_string(a.frame)+"}");}catch(...){}
        return S_OK;
    }
    if(!p->consume_boundary(a.frame,a.race,a.reset))return S_OK;
    std::vector<ps2birds::BirdView> birds;std::vector<ps2port::BirdBatch> batches;
    try{p->manager().snapshot(birds);}catch(...){birds.clear();}
    if(birds.empty()){if(auto* x=d.ps2_port())x->note(ps2diag::Effect::Birds,p->manager().active()?"no_bird_flying":"ps2_list_gate_closed");return S_OK;}
    if(!ps2port::birds_build(p->asset(),birds,look,up,batches)){if(auto* x=d.ps2_port())x->note(ps2diag::Effect::Birds,"world_vertices_nonfinite");p->proof.clear();return S_OK;}
    const bool fog=splineintegration::native_course_fog(n);
    const auto writer=[&](uint32_t slot,const Args& args,HRESULT hr) noexcept {courseintegration::after_setter(d,slot,args,hr);};
    HRESULT captured=S_OK,applied=S_OK,draw=E_PENDING,restored=S_OK;UINT triangles=0,draws=0;
    for(const auto& batch:batches){
        if(batch.vertices.empty())continue;
        captured=p->transaction.capture(n);if(FAILED(captured))break;
        applied=p->transaction.apply(n,p->texture(batch.cell),proof.view,proof.projection,writer,
            ps2port::CourseObjectMaterialState{FALSE,D3DTADDRESS_CLAMP,D3DTADDRESS_CLAMP,TRUE,static_cast<DWORD>(fog?TRUE:FALSE)});
        if(SUCCEEDED(applied)){
            p->transaction.mark_up_stream_changed();
            draw=n.DrawPrimitiveUP(D3DPT_TRIANGLELIST,static_cast<UINT>(batch.vertices.size()/3),batch.vertices.data(),sizeof(ps2port::ObjectVertex));
            if(FAILED(draw))p->disable("native_birds_draw_failed");
            else{triangles+=static_cast<UINT>(batch.vertices.size()/3);++draws;}
        }
        if(p->transaction.has_pending())restored=p->transaction.restore(n,writer);
        if(FAILED(restored)){p->disable("native_birds_state_restore_failed");break;}
        p->transaction.release();
        if(FAILED(applied)||FAILED(draw))break;
    }
    if(auto* x=d.ps2_port())x->note(ps2diag::Effect::Birds,FAILED(restored)?"restore_failed":FAILED(draw)?"draw_failed":FAILED(applied)?"apply_failed":FAILED(captured)?"capture_failed":draws?"drawn":"nothing_visible");
    if(p->claim_log(true)||FAILED(restored))try{session().write("{\"type\":\"ps2_birds_draw\",\"course\":"+quote(course.id)+
        ",\"frame\":"+std::to_string(a.frame)+",\"race_generation\":"+std::to_string(a.race)+",\"birds\":"+std::to_string(birds.size())+
        ",\"draws\":"+std::to_string(draws)+",\"triangles\":"+std::to_string(triangles)+",\"fog\":"+(fog?"true":"false")+
        ",\"course_guard\":"+quote(p->guard_reason())+
        ",\"capture_hresult\":"+std::to_string(static_cast<uint32_t>(captured))+",\"apply_hresult\":"+std::to_string(static_cast<uint32_t>(applied))+
        ",\"draw_hresult\":"+std::to_string(static_cast<uint32_t>(draw))+",\"restore_hresult\":"+std::to_string(static_cast<uint32_t>(restored))+
        ",\"artifact_sha256\":"+quote(ps2port::kPS2BirdsArtifactSha)+",\"runtime_visibility\":\"PENDING_USER\"}");}catch(...){}
    return FAILED(restored)?restored:S_OK;
}
} // namespace gfx2::birdsintegration
