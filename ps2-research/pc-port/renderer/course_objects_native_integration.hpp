#pragma once
#include "wrappers.hpp"
#include "ps2_race_certificate.hpp"
#include "ps2_perf_timing.hpp"
#include "ps2_port_extension.hpp"
#include "course_objects.hpp"
#include "ps2_water_pilot.hpp"
#include "camera_probe.hpp"
#include "provenance.hpp"
#include <cmath>
#include <cstring>

namespace gfx2::courseintegration {
template<class T>struct Ref{T* p=nullptr;~Ref(){if(p)p->Release();}};
inline ps2port::CourseObjectsPilot* pilot(Device8& d)noexcept{return d.ps2_port()?d.ps2_port()->course_objects():nullptr;}
inline RaceCertificate certificate(bool& single,bool& split)noexcept {
    ps2port::perf::Timer timer(ps2port::perf::Certificate);single=split=false;const uintptr_t image=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    // HUD context rejects frontend/no-owner scenes before resolving missing
    // race keys. The camera certificate remains mandatory after this gate.
    const auto hud=ps2port::ps2_race_hud_context();
    if(!hud.valid)return {};
    uintptr_t manager=0,camera=0;uint32_t cameras=0;
    if(image==0x400000&&safe_copy(&manager,reinterpret_cast<const void*>(image+CAMERA_MANAGER_RVA),4)&&manager&&
       safe_copy(&cameras,reinterpret_cast<const void*>(manager+16),4)&&cameras==1&&
       safe_copy(&camera,reinterpret_cast<const void*>(manager),4)&&camera){single=true;return ps2port::ps2_race_certificate(camera);}
    // PS2SplitScreen=1: two active cameras; the certificate is for the renderer's current camera (this pass).
    uintptr_t holder=0,current=0;
    if(image==0x400000&&ps2port::ps2_race_certifier().split_screen()&&manager&&cameras==2&&
       safe_copy(&holder,reinterpret_cast<const void*>(image+RENDERER_HOLDER_RVA),4)&&holder&&
       safe_copy(&holder,reinterpret_cast<const void*>(holder+0x38),4)&&holder&&safe_copy(&current,reinterpret_cast<const void*>(holder+4),4)&&current){
        const auto race=ps2port::ps2_race_certificate(current);
        if(race.valid&&race.mode==ps2port::Ps2RaceMode::SplitScreen){single=split=true;return race;}
    }
    return {};
}
// PERF2.1 (docs/perf2): one race certificate per device / reset generation / frame / renderer current camera for
// every PS2 path. The certificate is a race-level proof (owner registry, lifecycle, course, context, camera); the
// game's main loop (0x5AFE30) runs its update before the frame scheduler (0x653080) draws every camera, so it cannot
// change during one camera's traversal. Runtime PERF2 timing: 90 uncached calls per split-screen frame cost ~5.3 ms.
// Each draw still proves its own owner, buffers, tokens and transforms.
// `split` (SPLIT-GRASS1) reports that the certificate is the PS2SplitScreen=1 certificate of the current pass.
inline RaceCertificate certificate(Device8& d,bool& single,bool& split)noexcept {
    struct Cache{uint64_t device=UINT64_MAX,reset=UINT64_MAX,frame=UINT64_MAX;uintptr_t camera=0;bool single=false,split=false;RaceCertificate value{};};
    static thread_local Cache cache;
    const uintptr_t image=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));uintptr_t holder=0,camera=0;
    if(image==0x400000&&safe_copy(&holder,reinterpret_cast<const void*>(image+RENDERER_HOLDER_RVA),4)&&holder&&
       safe_copy(&holder,reinterpret_cast<const void*>(holder+0x38),4)&&holder)safe_copy(&camera,reinterpret_cast<const void*>(holder+4),4);
    const uint64_t device=d.trace.device_id(),reset=d.ps2_port()?d.ps2_port()->reset_generation():0,frame=d.trace.frame_number();
    if(cache.device!=device||cache.reset!=reset||cache.frame!=frame||cache.camera!=camera){
        cache.device=device;cache.reset=reset;cache.frame=frame;cache.camera=camera;cache.value=certificate(cache.single,cache.split);}
    single=cache.single;split=cache.split;return cache.value;
}
inline RaceCertificate certificate(Device8& d,bool& single)noexcept {bool split=false;return certificate(d,single,split);}
inline bool same_identity(IUnknown* a,IUnknown* b)noexcept {
    if(!a||!b)return false;Ref<IUnknown>x,y;
    return SUCCEEDED(a->QueryInterface(IID_IUnknown,reinterpret_cast<void**>(&x.p)))&&
        SUCCEEDED(b->QueryInterface(IID_IUnknown,reinterpret_cast<void**>(&y.p)))&&x.p&&x.p==y.p;
}
inline bool finite_matrix(const D3DMATRIX& m)noexcept {for(const auto& row:m.m)for(float value:row)if(!std::isfinite(value))return false;return true;}
inline bool perspective(const D3DMATRIX& p)noexcept{return finite_matrix(p)&&p._11>0&&p._22>0&&p._33>1&&p._43<0&&p._34==1&&p._44==0;}
inline void after_setter(Device8& d,uint32_t slot,const Args& args,HRESULT hr)noexcept {
    d.trace.after(slot,args,static_cast<uint32_t>(hr),0,&args,256,false,true);
}
inline HRESULT repair(Device8& d)noexcept {
    auto* p=pilot(d);if(!p)return S_OK;if(p->blocked())return D3DERR_DEVICELOST;
    if(!p->transaction.has_pending())return S_OK;
    return p->transaction.restore(*d.native(),[&](uint32_t slot,const Args& args,HRESULT hr)noexcept{after_setter(d,slot,args,hr);});
}
inline void observe_transform(Device8& d,D3DTRANSFORMSTATETYPE type,bool exe,uint32_t rva,HRESULT hr)noexcept {
    auto* p=pilot(d);if(!p||!p->active()||!exe)return;
    const bool is_view=type==D3DTS_VIEW&&rva==GAMEPLAY_VIEW_RETURN_RVA;
    const bool is_projection=type==D3DTS_PROJECTION&&rva==GAMEPLAY_PROJECTION_RETURN_RVA;
    if(!is_view&&!is_projection)return;
    p->proof.invalidate_depth();
    if(is_view)p->proof.view_site=false;if(is_projection)p->proof.projection_site=false;
    if(FAILED(hr)||!d.trace.scene_active||GetCurrentThreadId()!=d.trace.render_thread_id())return;
    bool single=false;const auto cert=certificate(d,single);
    if(!single||!cert.valid||!ps2port::turkey3_course(cert.course_id.data())){p->proof.clear();return;}
    auto& proof=p->proof;const auto frame=d.trace.frame_number();const auto reset=d.ps2_port()->reset_generation();
    if(proof.frame!=frame||proof.device!=d.trace.device_id()||proof.reset!=reset||
       proof.race!=cert.race_generation||proof.owner!=cert.owner_lifetime||proof.camera!=cert.camera){
        proof.clear();proof.frame=frame;proof.device=d.trace.device_id();proof.reset=reset;
        proof.race=cert.race_generation;proof.owner=cert.owner_lifetime;proof.camera=cert.camera;
    }
    const auto& tracked=d.trace.effective_shadow.matrices[type];D3DMATRIX native{};
    if(!tracked.known||FAILED(d.native()->GetTransform(type,&native))||std::memcmp(&native,&tracked.value,64)||!finite_matrix(native))return;
    // Every verified camera submission needs a subsequent native world draw.
    // A second camera update in this frame cannot reuse the earlier depth proof.
    proof.invalidate_depth();
    if(is_view){proof.view=native;proof.view_site=true;}
    if(is_projection&&perspective(native)){proof.projection=native;proof.projection_site=true;}
}
inline bool native_dependencies(IDirect3DDevice8& n)noexcept {
    DWORD blend=0,vertex=0,indexed=0,result=0,fill=0,clipping=0,bias=0,wrap=0;
    return SUCCEEDED(n.GetRenderState(D3DRS_BLENDOP,&blend))&&blend==D3DBLENDOP_ADD&&
        SUCCEEDED(n.GetRenderState(D3DRS_VERTEXBLEND,&vertex))&&vertex==D3DVBF_DISABLE&&
        SUCCEEDED(n.GetRenderState(D3DRS_INDEXEDVERTEXBLENDENABLE,&indexed))&&!indexed&&
        SUCCEEDED(n.GetTextureStageState(0,D3DTSS_RESULTARG,&result))&&result==D3DTA_CURRENT&&
        SUCCEEDED(n.GetRenderState(D3DRS_FILLMODE,&fill))&&fill==D3DFILL_SOLID&&
        SUCCEEDED(n.GetRenderState(D3DRS_CLIPPING,&clipping))&&clipping&&
        SUCCEEDED(n.GetRenderState(D3DRS_ZBIAS,&bias))&&!bias&&
        SUCCEEDED(n.GetRenderState(D3DRS_WRAP0,&wrap))&&!wrap;
}
inline void observe_world_draw(Device8& d,HRESULT hr)noexcept {
    auto* p=pilot(d);if(!p||!p->active()||FAILED(hr)||!d.trace.scene_active)return;
    auto& proof=p->proof;if(proof.world_draw||proof.frame!=d.trace.frame_number()||!proof.view_site||!proof.projection_site)return;
    D3DMATRIX view{},projection{};DWORD z=0,func=0;
    auto& n=*d.native();
    if(FAILED(n.GetTransform(D3DTS_VIEW,&view))||FAILED(n.GetTransform(D3DTS_PROJECTION,&projection))||
       std::memcmp(&view,&proof.view,64)||std::memcmp(&projection,&proof.projection,64)||
       FAILED(n.GetRenderState(D3DRS_ZENABLE,&z))||z!=D3DZB_TRUE||
       FAILED(n.GetRenderState(D3DRS_ZFUNC,&func))||func!=D3DCMP_LESSEQUAL)return;
    Ref<IDirect3DSurface8> target,back,depth;
    D3DVIEWPORT8 viewport{};D3DSURFACE_DESC desc{};
    if(FAILED(n.GetRenderTarget(&target.p))||FAILED(n.GetBackBuffer(0,D3DBACKBUFFER_TYPE_MONO,&back.p))||
       !same_identity(target.p,back.p)||FAILED(n.GetDepthStencilSurface(&depth.p))||!depth.p||
       FAILED(n.GetViewport(&viewport))||FAILED(target.p->GetDesc(&desc))||viewport.X||viewport.Y||
       viewport.Width!=desc.Width||viewport.Height!=desc.Height||viewport.MinZ!=0||viewport.MaxZ!=1)return;
    proof.viewport=viewport;proof.target=target.p;target.p=nullptr;proof.depth=depth.p;depth.p=nullptr;proof.world_draw=true;
}
inline HRESULT before_ui(Device8& d,bool ui_callsite,bool ui_consumer)noexcept {
    auto* p=pilot(d);if(!p||!p->active()||!ui_callsite)return S_OK;
    const ps2port::CourseBoundaryContext boundary{d.trace.frame_number(),d.trace.device_id(),
        d.ps2_port()->reset_generation(),GetCurrentThreadId()==d.trace.render_thread_id(),
        d.trace.scene_active,ui_consumer,d.trace.shadow.recording||d.trace.effective_shadow.recording};
    if(!ps2port::course_world_preflight(p->proof,boundary)||
       p->boundary_consumed(boundary.frame,p->proof.race,boundary.reset))return S_OK;
    auto& proof=p->proof;auto& n=*d.native();bool single=false;const auto cert=certificate(d,single);
    // COURSE-WATER1: when PS2Water draws this course's water in this race, the static puddle preview would be a second
    // copy of the same surfaces (one rendering path per surface).
    if(auto* water=d.ps2_port()->water();water&&cert.valid&&water->owns(cert.course_id.data(),cert.race_generation)){
        if(p->claim_log(false))try{session().write("{\"type\":\"ps2_course_objects_gate\",\"reason\":\"superseded_by_ps2_water\",\"course\":"+quote(std::string(cert.course_id.data()))+"}");}catch(...){}
        return S_OK;
    }
    Ref<IDirect3DSurface8> target,depth;D3DVIEWPORT8 viewport{};
    ps2port::CourseAdmission a;
    a.supported_build=session().target;a.render_thread=GetCurrentThreadId()==d.trace.render_thread_id();
    a.scene_active=d.trace.scene_active;a.asset_ready=p->active();a.ui_callsite=ui_callsite;a.ui_consumer=ui_consumer;
    a.state_block_recording=d.trace.shadow.recording||d.trace.effective_shadow.recording;
    a.camera_single=single;a.race_valid=cert.valid;a.course=cert.course_id.data();
    a.frame=d.trace.frame_number();a.proof_frame=proof.frame;a.device=d.trace.device_id();a.proof_device=proof.device;
    a.reset=d.ps2_port()->reset_generation();a.proof_reset=proof.reset;a.race=cert.race_generation;a.proof_race=proof.race;
    a.owner=cert.owner_lifetime;a.proof_owner=proof.owner;a.camera=cert.camera;a.proof_camera=proof.camera;
    a.view_site=proof.view_site;a.projection_site=proof.projection_site;a.world_draw=proof.world_draw;
    a.target_matches=SUCCEEDED(n.GetRenderTarget(&target.p))&&same_identity(target.p,proof.target);
    a.depth_matches=SUCCEEDED(n.GetDepthStencilSurface(&depth.p))&&same_identity(depth.p,proof.depth);
    a.viewport_matches=SUCCEEDED(n.GetViewport(&viewport))&&!std::memcmp(&viewport,&proof.viewport,sizeof(viewport));
    a.pc_depth_convention=perspective(proof.projection);a.native_dependency_states=native_dependencies(n);
    const char* reason=ps2port::course_object_admission(a);
    if(std::strcmp(reason,"eligible")){
        if(p->claim_log(false))try{session().write("{\"type\":\"ps2_course_objects_gate\",\"reason\":"+quote(reason)+
            ",\"course\":"+quote(std::string(a.course))+",\"frame\":"+std::to_string(a.frame)+"}");}catch(...){}
        return S_OK;
    }
    if(!p->consume_boundary(a.frame,a.race,a.reset))return S_OK;
    const auto writer=[&](uint32_t slot,const Args& args,HRESULT hr)noexcept{after_setter(d,slot,args,hr);};
    HRESULT captured=p->transaction.capture(n),applied=E_PENDING,draw=E_PENDING,restored=S_OK;
    if(SUCCEEDED(captured))applied=p->transaction.apply(n,p->texture(),proof.view,proof.projection,writer);
    if(SUCCEEDED(applied)){
        p->transaction.mark_up_stream_changed();
        // Private source draw: do not feed this into the application's pending_draw/classifier.
        draw=n.DrawPrimitiveUP(D3DPT_TRIANGLELIST,745,p->asset().vertices.data(),sizeof(ps2port::ObjectVertex));
        if(FAILED(draw))p->disable("native_object_preview_draw_failed");
    }
    if(p->transaction.has_pending())restored=p->transaction.restore(n,writer);
    if(FAILED(restored))p->disable("native_object_state_restore_failed");
    else p->transaction.release();
    if(p->claim_log(true)||FAILED(restored))try{session().write("{\"type\":\"ps2_course_objects_draw\",\"mode\":1,\"material\":\"SOURCE_GEOMETRY_STATIC_MATERIAL_PREVIEW\""+
        std::string(",\"course\":\"RaceTest/Turkey3\",\"frame\":")+std::to_string(a.frame)+
        ",\"device\":"+std::to_string(a.device)+",\"race_generation\":"+std::to_string(a.race)+
        ",\"owner_lifetime\":"+std::to_string(a.owner)+",\"camera\":"+std::to_string(a.camera)+
        ",\"source_meshes\":17,\"source_triangles\":745,\"additional_native_draws\":"+(draw==E_PENDING?"0":"1")+
        std::string(",\"capture_hresult\":")+std::to_string(static_cast<uint32_t>(captured))+
        ",\"apply_hresult\":"+std::to_string(static_cast<uint32_t>(applied))+
        ",\"draw_hresult\":"+std::to_string(static_cast<uint32_t>(draw))+
        ",\"restore_hresult\":"+std::to_string(static_cast<uint32_t>(restored))+
        ",\"artifact_sha256\":"+quote(ps2port::kTurkey3ObjectArtifactSha)+",\"runtime_visibility\":\"PENDING_USER\"}");}catch(...){}
    return FAILED(restored)?restored:S_OK;
}
} // namespace gfx2::courseintegration
