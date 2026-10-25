#pragma once
// Source-derived ground detail preview. Admission and proof helpers are shared
// with the existing object layer; grass owns independent proof and resources.
#include "course_objects_native_integration.hpp"
#include "grass_pilot.hpp"
#include "grass_split_native.hpp"
#include <vector>

namespace gfx2::grassintegration {
inline ps2port::GrassPilot* pilot(Device8& d) noexcept {
    return d.ps2_port() ? d.ps2_port()->grass() : nullptr;
}
inline HRESULT repair_one(Device8& d,ps2port::GrassPilot* p) noexcept {
    if(!p)return S_OK;
    if(p->blocked())return D3DERR_DEVICELOST;
    if(!p->transaction.has_pending())return S_OK;
    return p->transaction.restore(*d.native(),[&](uint32_t slot,const Args& args,HRESULT hr) noexcept {
        courseintegration::after_setter(d,slot,args,hr);
    });
}
inline void observe_transform_one(Device8& d,ps2port::GrassPilot* p,D3DTRANSFORMSTATETYPE type,bool exe,uint32_t rva,HRESULT hr) noexcept {
    if(grasssplit::observe_transform(d,p,type,exe,rva,hr))return; // SPLIT-GRASS1: PS2SplitScreen=1 passes only.
    if(!p||!p->active()||!exe)return;
    const bool is_view=type==D3DTS_VIEW&&rva==GAMEPLAY_VIEW_RETURN_RVA;
    const bool is_projection=type==D3DTS_PROJECTION&&rva==GAMEPLAY_PROJECTION_RETURN_RVA;
    if(!is_view&&!is_projection)return;
    p->proof.invalidate_depth();
    if(is_view)p->proof.view_site=false;
    if(is_projection)p->proof.projection_site=false;
    if(FAILED(hr)||!d.trace.scene_active||GetCurrentThreadId()!=d.trace.render_thread_id())return;
    bool single=false; const auto cert=courseintegration::certificate(d,single);
    if(!single||!cert.valid||!p->select_course(cert.course_id.data(),*d.native())){p->proof.clear();return;}
    auto& proof=p->proof; const auto frame=d.trace.frame_number(); const auto reset=d.ps2_port()->reset_generation();
    if(proof.frame!=frame||proof.device!=d.trace.device_id()||proof.reset!=reset||
       proof.race!=cert.race_generation||proof.owner!=cert.owner_lifetime||proof.camera!=cert.camera){
        proof.clear(); proof.frame=frame;proof.device=d.trace.device_id();proof.reset=reset;
        proof.race=cert.race_generation;proof.owner=cert.owner_lifetime;proof.camera=cert.camera;
    }
    const auto& tracked=d.trace.effective_shadow.matrices[type];D3DMATRIX native{};
    if(!tracked.known||FAILED(d.native()->GetTransform(type,&native))||
       std::memcmp(&native,&tracked.value,64)||!courseintegration::finite_matrix(native))return;
    // A later camera submission cannot reuse an earlier world/depth proof.
    proof.invalidate_depth();
    if(is_view){proof.view=native;proof.view_site=true;}
    if(is_projection&&courseintegration::perspective(native)){proof.projection=native;proof.projection_site=true;}
}
inline void observe_world_draw_one(Device8& d,ps2port::GrassPilot* p,HRESULT hr) noexcept {
    if(!p||!p->active()||FAILED(hr)||!d.trace.scene_active||
        GetCurrentThreadId()!=d.trace.render_thread_id())return;
    if(grasssplit::observe_world_draw(d,p))return;
    auto& proof=p->proof;
    if(proof.world_draw||proof.frame!=d.trace.frame_number()||!proof.view_site||!proof.projection_site)return;
    auto& n=*d.native();D3DMATRIX view{},projection{};DWORD z=0,func=0;
    if(FAILED(n.GetTransform(D3DTS_VIEW,&view))||FAILED(n.GetTransform(D3DTS_PROJECTION,&projection))||
       std::memcmp(&view,&proof.view,64)||std::memcmp(&projection,&proof.projection,64)||
       FAILED(n.GetRenderState(D3DRS_ZENABLE,&z))||z!=D3DZB_TRUE||
       FAILED(n.GetRenderState(D3DRS_ZFUNC,&func))||func!=D3DCMP_LESSEQUAL)return;
    courseintegration::Ref<IDirect3DSurface8> target,back,depth;
    D3DVIEWPORT8 viewport{};D3DSURFACE_DESC desc{};
    if(FAILED(n.GetRenderTarget(&target.p))||FAILED(n.GetBackBuffer(0,D3DBACKBUFFER_TYPE_MONO,&back.p))||
       !courseintegration::same_identity(target.p,back.p)||FAILED(n.GetDepthStencilSurface(&depth.p))||!depth.p||
       FAILED(n.GetViewport(&viewport))||FAILED(target.p->GetDesc(&desc))||viewport.X||viewport.Y||
       viewport.Width!=desc.Width||viewport.Height!=desc.Height||viewport.MinZ!=0||viewport.MaxZ!=1)return;
    proof.viewport=viewport;proof.target=target.p;target.p=nullptr;
    proof.depth=depth.p;depth.p=nullptr;proof.world_draw=true;
}
inline HRESULT before_ui_one(Device8& d,ps2port::GrassPilot* p,bool ui_callsite,bool ui_consumer) noexcept {
    if(!p||!p->active()||!ui_callsite)return S_OK;
    if(p->proof.split.count)return grasssplit::before_ui(d,p,ui_callsite,ui_consumer);
    const ps2port::CourseBoundaryContext boundary{d.trace.frame_number(),d.trace.device_id(),
        d.ps2_port()->reset_generation(),GetCurrentThreadId()==d.trace.render_thread_id(),
        d.trace.scene_active,ui_consumer,d.trace.shadow.recording||d.trace.effective_shadow.recording};
    if(!ps2port::course_world_preflight(p->proof,boundary)||
       p->boundary_consumed(boundary.frame,p->proof.race,boundary.reset))return S_OK;
    auto& proof=p->proof;auto& n=*d.native();bool single=false;
    const auto cert=courseintegration::certificate(d,single);
    const auto effect=std::strcmp(p->category(),"shrubs")?ps2diag::Effect::Grass:ps2diag::Effect::Shrubs;
    if(cert.valid&&!p->supports_course(cert.course_id.data())){if(auto* x=d.ps2_port())x->note(effect,"course_has_no_asset");return S_OK;}
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
    const char* reason=ps2port::course_object_admission(a,p->course());
    if(std::strcmp(reason,"eligible")){
        if(auto* x=d.ps2_port())x->note(effect,reason);
        if(p->claim_log(false))try{session().write("{\"type\":\"ps2_grass_gate\",\"reason\":"+quote(reason)+
            ",\"course\":"+quote(std::string(a.course))+",\"frame\":"+std::to_string(a.frame)+"}");}catch(...){}
        return S_OK;
    }
    if(!p->consume_boundary(a.frame,a.race,a.reset))return S_OK;
    std::vector<ps2port::ObjectVertex> vertices;
    const bool built=p->build_vertices(proof.view,vertices);
    if(p->claim_build_log())try{session().write("{\"type\":\"ps2_grass_build\",\"frame\":"+
        std::to_string(a.frame)+",\"course\":"+quote(p->course())+",\"success\":"+(built?"true":"false")+
        ",\"sprite_candidates\":"+std::to_string(vertices.size()/6)+",\"reason\":"+quote(p->reason())+",\"detail_category\":"+quote(p->category())+"}");}catch(...){}
    if(!built){
        // COURSE-RENDER-FIX1: a frame whose camera or point set cannot be built is skipped and counted; it must not latch the
        // detail layer off for the rest of the session (the next frame, race or course starts from a clean proof).
        const char* failure=p->reason();
        if(auto* x=d.ps2_port())x->note(effect,failure);
        if(p->claim_log(false))try{session().write("{\"type\":\"ps2_grass_gate\",\"reason\":"+quote(failure)+
            ",\"phase\":\"build_preview_vertices\",\"frame\":"+std::to_string(a.frame)+"}");}catch(...){}
        p->proof.clear();
        return S_OK;
    }
    if(vertices.empty()){if(auto* x=d.ps2_port())x->note(effect,"no_points_in_range");return S_OK;}
    const auto writer=[&](uint32_t slot,const Args& args,HRESULT hr) noexcept {
        courseintegration::after_setter(d,slot,args,hr);
    };
    D3DMATRIX identity{};identity._11=identity._22=identity._33=identity._44=1.f;
    HRESULT captured=p->transaction.capture(n),applied=E_PENDING,draw=E_PENDING,restored=S_OK;
    if(SUCCEEDED(captured))applied=p->transaction.apply(n,p->texture(),identity,proof.projection,writer,
        ps2port::CourseObjectMaterialState{FALSE,D3DTADDRESS_CLAMP,D3DTADDRESS_CLAMP});
    if(SUCCEEDED(applied)){
        p->transaction.mark_up_stream_changed();
        // Only the private sprite batch. Never submit it to application's draw tracker.
        draw=n.DrawPrimitiveUP(D3DPT_TRIANGLELIST,static_cast<UINT>(vertices.size()/3),vertices.data(),sizeof(ps2port::ObjectVertex));
        if(FAILED(draw))p->disable("native_grass_preview_draw_failed");
    }
    if(p->transaction.has_pending())restored=p->transaction.restore(n,writer);
    if(FAILED(restored))p->disable("native_grass_state_restore_failed");
    else p->transaction.release();
    if(auto* x=d.ps2_port())x->note(effect,FAILED(draw)?"draw_failed":FAILED(restored)?"restore_failed":FAILED(applied)?"apply_failed":FAILED(captured)?"capture_failed":"drawn");
    if(p->claim_log(true)||FAILED(restored))try{session().write("{\"type\":\"ps2_grass_draw\",\"course\":"+quote(p->course())+
        std::string(",\"frame\":")+std::to_string(a.frame)+",\"device\":"+std::to_string(a.device)+
        ",\"race_generation\":"+std::to_string(a.race)+",\"owner_lifetime\":"+std::to_string(a.owner)+
        ",\"camera\":"+std::to_string(a.camera)+",\"source_points\":"+std::to_string(p->asset().points.size())+
        ",\"sprite_candidates\":"+std::to_string(vertices.size()/6)+",\"source_kind\":\"PS2_SPATIAL_DETAIL_SOURCE\""+
        ",\"generation_policy\":\"SYNTHETIC_FULL_TRIANGLE_ACTIVATION\",\"original_incremental_clip\":\"UNKNOWN\""+
        ",\"pc_sprite_half_size\":"+std::to_string(p->sprite_half_size())+
        ",\"additional_native_draws\":"+(draw==E_PENDING?"0":"1")+
        std::string(",\"capture_hresult\":")+std::to_string(static_cast<uint32_t>(captured))+
        ",\"apply_hresult\":"+std::to_string(static_cast<uint32_t>(applied))+
        ",\"draw_hresult\":"+std::to_string(static_cast<uint32_t>(draw))+
        ",\"restore_hresult\":"+std::to_string(static_cast<uint32_t>(restored))+
        ",\"artifact_sha256\":"+quote(p->artifact_sha())+",\"detail_category\":"+quote(p->category())+",\"runtime_visibility\":\"PENDING_USER\"}");}catch(...){}
    // A fully restored failed private preview cannot replace original UI HRESULT.
    // Unresolved restoration blocks that native submission with the real failure.
    return FAILED(restored)?restored:S_OK;
}
// Independent categories retain their own proof, texture, per-frame boundary
// and pending transaction. Neither category may reuse the other's admission.
inline std::array<ps2port::GrassPilot*,2> detail_pilots(Device8& d) noexcept {
    return d.ps2_port()?d.ps2_port()->ground_details():std::array<ps2port::GrassPilot*,2>{nullptr,nullptr};
}
inline HRESULT repair(Device8& d) noexcept {
    for(auto* p:detail_pilots(d)){const auto hr=repair_one(d,p);if(FAILED(hr))return hr;}return S_OK;
}
inline void observe_transform(Device8& d,D3DTRANSFORMSTATETYPE type,bool exe,uint32_t rva,HRESULT hr) noexcept {
    for(auto* p:detail_pilots(d))observe_transform_one(d,p,type,exe,rva,hr);
}
inline void observe_world_draw(Device8& d,HRESULT hr) noexcept {
    for(auto* p:detail_pilots(d))observe_world_draw_one(d,p,hr);
}
inline HRESULT before_ui(Device8& d,bool ui_callsite,bool ui_consumer) noexcept {
    for(auto* p:detail_pilots(d)){const auto hr=before_ui_one(d,p,ui_callsite,ui_consumer);if(FAILED(hr))return hr;}return S_OK;
}
} // namespace gfx2::grassintegration
