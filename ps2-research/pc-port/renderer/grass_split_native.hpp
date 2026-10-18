#pragma once
// SPLIT-GRASS1 (docs/split-grass1): Grass/Shrubs in two-player split screen, opt-in under PS2SplitScreen=1.
// One world proof per camera pass (CourseSplitProof); at the UI boundary every proven pass is drawn once into
// its own viewport with its own view and projection, and the transaction restores the UI viewport and states.
// Only a SplitScreen certificate of the renderer's current camera reaches this path; the single-camera path in
// grass_native_integration.hpp is unchanged.
#include "course_objects_native_integration.hpp"
#include "grass_pilot.hpp"
#include <array>
#include <string>
#include <vector>

namespace gfx2::grasssplit {
inline void gate_log(ps2port::GrassPilot* p,const char* reason,uint64_t frame) noexcept {
    if(p->claim_log(false))try{session().write("{\"type\":\"ps2_grass_gate\",\"reason\":"+quote(reason)+
        ",\"mode\":\"split_screen\",\"category\":"+quote(p->category())+",\"frame\":"+std::to_string(frame)+"}");}catch(...){}
}
// Gameplay PROJECTION/VIEW site of an active pilot. Returns false (the single path decides, and its
// invalidation also reaches the split passes) unless the current camera holds a split-screen certificate.
inline bool observe_transform(Device8& d,ps2port::GrassPilot* p,D3DTRANSFORMSTATETYPE type,bool exe,uint32_t rva,HRESULT hr) noexcept {
    const bool is_view=type==D3DTS_VIEW&&rva==GAMEPLAY_VIEW_RETURN_RVA;
    const bool is_projection=type==D3DTS_PROJECTION&&rva==GAMEPLAY_PROJECTION_RETURN_RVA;
    if(!p||!p->active()||!exe||(!is_view&&!is_projection)||FAILED(hr)||!d.trace.scene_active||
       GetCurrentThreadId()!=d.trace.render_thread_id())return false;
    bool single=false,split=false;const auto cert=courseintegration::certificate(d,single,split);
    if(!split||!single||!cert.valid)return false;
    auto& proof=p->proof;
    if(!p->select_course(cert.course_id.data(),*d.native())){proof.clear();return true;}
    proof.clear_single();
    auto& passes=proof.split;const auto frame=d.trace.frame_number();
    auto* pass=passes.begin_pass(frame,d.trace.device_id(),d.ps2_port()->reset_generation(),cert.race_generation,cert.owner_lifetime,cert.camera);
    if(!pass){gate_log(p,"split_third_camera_or_unproven_pass",frame);return true;}
    // A later submission of this camera cannot reuse its earlier world/depth proof; the other pass keeps its own.
    pass->invalidate_depth();
    if(is_view)pass->view_site=false;
    if(is_projection){pass->projection_site=false;passes.projection_site=false;}
    const auto& tracked=d.trace.effective_shadow.matrices[type];D3DMATRIX native{};
    if(!tracked.known||FAILED(d.native()->GetTransform(type,&native))||
       std::memcmp(&native,&tracked.value,64)||!courseintegration::finite_matrix(native))return true;
    if(is_projection&&courseintegration::perspective(native)){
        passes.projection=native;passes.projection_site=true;pass->projection=native;pass->projection_site=true;}
    if(is_view){
        pass->view=native;pass->view_site=true;
        // Camera 2 does not re-set PROJECTION. It inherits only the matrix verified at the gameplay projection
        // site in this frame, and only while the device and the effective shadow both still hold it exactly.
        const auto& tracked_projection=d.trace.effective_shadow.matrices[D3DTS_PROJECTION];D3DMATRIX current{};
        if(passes.projection_site&&tracked_projection.known&&SUCCEEDED(d.native()->GetTransform(D3DTS_PROJECTION,&current))&&
           !std::memcmp(&current,&tracked_projection.value,64)&&!std::memcmp(&current,&passes.projection,64)&&
           courseintegration::perspective(current)){pass->projection=current;pass->projection_site=true;}
    }
    return true;
}
// First native world draw of the current pass: the single proof's matrix/depth/target checks, but the viewport
// is the pass half (inside the back buffer) and the draw must still belong to the pass camera. Returns true
// whenever split passes exist in this pilot (the single proof is empty then).
inline bool observe_world_draw(Device8& d,ps2port::GrassPilot* p) noexcept {
    auto& passes=p->proof.split;if(!passes.count)return false;
    auto* pass=passes.current_pass();
    if(!pass||pass->world_draw||passes.frame!=d.trace.frame_number()||!pass->view_site||!pass->projection_site)return true;
    bool single=false,split=false;const auto cert=courseintegration::certificate(d,single,split);
    if(!single||!split||!cert.valid||cert.camera!=pass->camera||cert.race_generation!=passes.race||cert.owner_lifetime!=passes.owner)return true;
    auto& n=*d.native();D3DMATRIX view{},projection{};DWORD z=0,func=0;
    if(FAILED(n.GetTransform(D3DTS_VIEW,&view))||FAILED(n.GetTransform(D3DTS_PROJECTION,&projection))||
       std::memcmp(&view,&pass->view,64)||std::memcmp(&projection,&pass->projection,64)||
       FAILED(n.GetRenderState(D3DRS_ZENABLE,&z))||z!=D3DZB_TRUE||
       FAILED(n.GetRenderState(D3DRS_ZFUNC,&func))||func!=D3DCMP_LESSEQUAL)return true;
    courseintegration::Ref<IDirect3DSurface8> target,back,depth;
    D3DVIEWPORT8 viewport{};D3DSURFACE_DESC desc{};
    if(FAILED(n.GetRenderTarget(&target.p))||FAILED(n.GetBackBuffer(0,D3DBACKBUFFER_TYPE_MONO,&back.p))||
       !courseintegration::same_identity(target.p,back.p)||FAILED(n.GetDepthStencilSurface(&depth.p))||!depth.p||
       FAILED(n.GetViewport(&viewport))||FAILED(target.p->GetDesc(&desc))||
       !ps2port::course_split_viewport(viewport,desc.Width,desc.Height))return true;
    pass->viewport=viewport;pass->target=target.p;target.p=nullptr;
    pass->depth=depth.p;depth.p=nullptr;pass->world_draw=true;
    return true;
}
// UI boundary (frame scheduler 0x653080 rebinds camera slot 0 with the full viewport before the UI).
inline HRESULT before_ui(Device8& d,ps2port::GrassPilot* p,bool ui_callsite,bool ui_consumer) noexcept {
    auto& passes=p->proof.split;
    const auto frame=d.trace.frame_number();const auto device=d.trace.device_id();const auto reset=d.ps2_port()->reset_generation();
    const bool render_thread=GetCurrentThreadId()==d.trace.render_thread_id();
    const bool recording=d.trace.shadow.recording||d.trace.effective_shadow.recording;
    // Cheap rejection before broker or GPU reads; then one full evaluation per frame, whatever its outcome.
    if(!ui_callsite||!render_thread||!d.trace.scene_active||!ui_consumer||recording||!device||passes.frame!=frame||
       passes.device!=device||passes.reset!=reset||p->boundary_consumed(frame,passes.race,reset))return S_OK;
    p->consume_boundary(frame,passes.race,reset);
    auto& n=*d.native();bool single=false,split=false;
    const auto cert=courseintegration::certificate(d,single,split);
    ps2port::CourseSplitAdmission a;
    a.supported_build=session().target;a.render_thread=render_thread;a.scene_active=d.trace.scene_active;
    a.asset_ready=p->active();a.ui_callsite=ui_callsite;a.ui_consumer=ui_consumer;a.state_block_recording=recording;
    a.race_valid=cert.valid;a.split_certificate=single&&split;a.course=cert.course_id.data();
    a.frame=frame;a.device=device;a.reset=reset;a.race=cert.race_generation;a.owner=cert.owner_lifetime;a.camera=cert.camera;
    courseintegration::Ref<IDirect3DSurface8> target,depth;D3DSURFACE_DESC desc{};
    const bool target_known=SUCCEEDED(n.GetRenderTarget(&target.p))&&target.p&&SUCCEEDED(target.p->GetDesc(&desc));
    const bool depth_known=SUCCEEDED(n.GetDepthStencilSurface(&depth.p))&&depth.p;
    a.target_width=desc.Width;a.target_height=desc.Height;
    for(size_t i=0;i<ps2port::kCourseSplitPasses;++i){const auto& pass=passes.passes[i];
        a.target_matches[i]=target_known&&courseintegration::same_identity(target.p,pass.target);
        a.depth_matches[i]=depth_known&&courseintegration::same_identity(depth.p,pass.depth);
        a.pc_depth_convention[i]=courseintegration::perspective(pass.projection);}
    a.native_dependency_states=courseintegration::native_dependencies(n);
    const char* reason=ps2port::course_split_admission(a,passes,p->course());
    if(std::strcmp(reason,"eligible")){gate_log(p,reason,frame);return S_OK;}
    const auto writer=[&](uint32_t slot,const Args& args,HRESULT hr) noexcept {
        courseintegration::after_setter(d,slot,args,hr);
    };
    D3DMATRIX identity{};identity._11=identity._22=identity._33=identity._44=1.f;
    // disable() clears the proof, so the log reads copies taken before drawing.
    const std::array<uint32_t,ps2port::kCourseSplitPasses> cameras{passes.passes[0].camera,passes.passes[1].camera};
    const std::array<D3DVIEWPORT8,ps2port::kCourseSplitPasses> rects{passes.passes[0].viewport,passes.passes[1].viewport};
    std::array<size_t,ps2port::kCourseSplitPasses> sprites{};
    std::array<HRESULT,ps2port::kCourseSplitPasses> captured{E_PENDING,E_PENDING},viewports{E_PENDING,E_PENDING},
        applied{E_PENDING,E_PENDING},draws{E_PENDING,E_PENDING},restores{S_OK,S_OK};
    HRESULT result=S_OK;
    for(size_t i=0;i<ps2port::kCourseSplitPasses&&p->active();++i){
        const auto& pass=passes.passes[i];std::vector<ps2port::ObjectVertex> vertices;
        const bool built=p->build_vertices(pass.view,vertices);
        if(p->claim_build_log())try{session().write("{\"type\":\"ps2_grass_build\",\"frame\":"+
            std::to_string(frame)+",\"mode\":\"split_screen\",\"pass\":"+std::to_string(i)+",\"course\":"+quote(p->course())+
            ",\"success\":"+(built?"true":"false")+",\"sprite_candidates\":"+std::to_string(vertices.size()/6)+
            ",\"reason\":"+quote(p->reason())+",\"detail_category\":"+quote(p->category())+"}");}catch(...){}
        if(!built){const char* failure=p->reason();gate_log(p,failure,frame);p->disable(failure);return S_OK;}
        sprites[i]=vertices.size()/6;
        if(vertices.empty())continue;
        captured[i]=p->transaction.capture(n);
        if(SUCCEEDED(captured[i]))viewports[i]=p->transaction.capture_viewport(n);
        if(SUCCEEDED(viewports[i]))viewports[i]=p->transaction.apply_viewport(n,pass.viewport,writer);
        if(SUCCEEDED(viewports[i]))applied[i]=p->transaction.apply(n,p->texture(),identity,pass.projection,writer,
            ps2port::CourseObjectMaterialState{FALSE,D3DTADDRESS_CLAMP,D3DTADDRESS_CLAMP});
        if(SUCCEEDED(applied[i])){
            p->transaction.mark_up_stream_changed();
            // Only the private sprite batch. Never submit it to application's draw tracker.
            draws[i]=n.DrawPrimitiveUP(D3DPT_TRIANGLELIST,static_cast<UINT>(vertices.size()/3),vertices.data(),sizeof(ps2port::ObjectVertex));
        }
        if(p->transaction.has_pending())restores[i]=p->transaction.restore(n,writer);
        if(FAILED(restores[i])){p->disable("native_grass_split_state_restore_failed");result=restores[i];break;}
        p->transaction.release();
        if(FAILED(captured[i])||FAILED(viewports[i])||FAILED(applied[i])||(draws[i]!=E_PENDING&&FAILED(draws[i]))){
            p->disable("native_grass_split_preview_failed");break;}
    }
    if(p->claim_log(true)||FAILED(result))try{
        std::string list;
        for(size_t i=0;i<ps2port::kCourseSplitPasses;++i){const auto& v=rects[i];
            list+=std::string(i?",":"")+"{\"camera\":"+std::to_string(cameras[i])+",\"viewport\":["+
                std::to_string(v.X)+","+std::to_string(v.Y)+","+std::to_string(v.Width)+","+std::to_string(v.Height)+
                "],\"sprite_candidates\":"+std::to_string(sprites[i])+
                ",\"capture_hresult\":"+std::to_string(static_cast<uint32_t>(captured[i]))+
                ",\"viewport_hresult\":"+std::to_string(static_cast<uint32_t>(viewports[i]))+
                ",\"apply_hresult\":"+std::to_string(static_cast<uint32_t>(applied[i]))+
                ",\"draw_hresult\":"+std::to_string(static_cast<uint32_t>(draws[i]))+
                ",\"restore_hresult\":"+std::to_string(static_cast<uint32_t>(restores[i]))+"}";}
        session().write("{\"type\":\"ps2_grass_draw\",\"mode\":\"split_screen\",\"course\":"+quote(p->course())+
            ",\"frame\":"+std::to_string(frame)+",\"device\":"+std::to_string(device)+
            ",\"race_generation\":"+std::to_string(a.race)+",\"owner_lifetime\":"+std::to_string(a.owner)+
            ",\"ui_camera\":"+std::to_string(a.camera)+",\"source_points\":"+std::to_string(p->asset().points.size())+
            ",\"passes\":["+list+"],\"source_kind\":\"PS2_SPATIAL_DETAIL_SOURCE\""+
            ",\"artifact_sha256\":"+quote(p->artifact_sha())+",\"detail_category\":"+quote(p->category())+
            ",\"runtime_visibility\":\"PENDING_USER\"}");}catch(...){}
    // As in the single path: only an unresolved restoration replaces the original UI HRESULT.
    return result;
}
} // namespace gfx2::grasssplit
