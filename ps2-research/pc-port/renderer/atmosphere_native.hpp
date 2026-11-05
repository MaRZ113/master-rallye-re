#pragma once
#include "course_objects_native_integration.hpp"
#include "ground_detail_native.hpp"
#include "atmosphere.hpp"
#include "buffer_provenance.hpp"

namespace gfx2::atmosphereintegration {
inline atmosphere::Pilot* pilot(Device8& d)noexcept{return d.ps2_port()?d.ps2_port()->atmosphere_pilot():nullptr;}
inline void notify(Device8& d,uint32_t slot,const Args& args,HRESULT hr)noexcept{courseintegration::after_setter(d,slot,args,hr);}
inline HRESULT repair(Device8& d) noexcept {
    auto* p=pilot(d);if(!p)return S_OK;
    if(p->sun.transaction.pending()){const auto hr=p->sun.transaction.restore(*d.native());if(FAILED(hr))return hr;}
    return atmosphere::restore_pending(*p,*d.native(),[&](uint32_t slot,const Args& args,HRESULT hr)noexcept{notify(d,slot,args,hr);});
}
} // namespace gfx2::atmosphereintegration
#include "atmosphere_capture_native.hpp"
namespace gfx2::atmosphereintegration {
// Use only native supported vertex/table fog; preserve density/range/modes.
// The enclosing CourseObjectTransaction owns colour application and rollback.
inline void proxy_fog(Device8& d,ps2port::CourseObjectMaterialState& material)noexcept {
    DWORD vertex=0,table=0,start=0,end=0,color=0;auto& n=*d.native();
    if(FAILED(n.GetRenderState(D3DRS_FOGVERTEXMODE,&vertex))||FAILED(n.GetRenderState(D3DRS_FOGTABLEMODE,&table))||
       FAILED(n.GetRenderState(D3DRS_FOGSTART,&start))||FAILED(n.GetRenderState(D3DRS_FOGEND,&end)))return;
    float near_fog=0,far_fog=0;std::memcpy(&near_fog,&start,4);std::memcpy(&far_fog,&end,4);
    const bool valid=(vertex==D3DFOG_LINEAR&&table==D3DFOG_NONE&&std::isfinite(near_fog)&&std::isfinite(far_fog)&&near_fog>=0&&near_fog<far_fog)||
        (table!=D3DFOG_NONE&&table<=D3DFOG_LINEAR);
    auto* p=pilot(d);if(!valid||!p||!p->enabled()||!p->lighting.active()||!p->lighting.fog_enabled)return;
    if(FAILED(n.GetRenderState(D3DRS_FOGCOLOR,&color)))return;
    material.fog=TRUE;material.override_fog_color=true;material.fog_color=atmosphere::scene_fog(color,p->lighting);
    try{if(p->first_reason("proxy_layer_fog"))session().write("{\"type\":\"atmosphere_proxy_fog\",\"original\":"+std::to_string(color)+",\"effective\":"+std::to_string(material.fog_color)+",\"range_modes_unchanged\":true}");}catch(...){}
}
// Spline objects are drawn after the world, when the game has already left
// the course fog state: reuse this frame's course fog snapshot (mode, range and
// the atmosphere fog colour). Without a snapshot the native state is kept.
inline bool course_fog_snapshot(Device8& d,ps2port::CourseObjectMaterialState& material)noexcept {
    auto* p=pilot(d);if(!p||!p->enabled()||p->course_fog.frame!=d.trace.frame_number())return false;
    const auto& f=p->course_fog;material.fog=TRUE;material.override_fog_range=true;
    material.fog_vertex_mode=f.vertex;material.fog_table_mode=f.table;material.fog_start=f.start;material.fog_end=f.end;
    material.override_fog_color=true;material.fog_color=p->lighting.active()&&p->lighting.fog_enabled?atmosphere::scene_fog(f.color,p->lighting):f.color;
    try{if(p->first_reason("proxy_course_fog_snapshot"))session().write("{\"type\":\"atmosphere_proxy_fog_snapshot\",\"vertex_mode\":"+std::to_string(f.vertex)+",\"table_mode\":"+std::to_string(f.table)+",\"color\":"+std::to_string(material.fog_color)+"}");}catch(...){}
    return true;
}
// PS2 layers drawn by the proxy itself (source-point grass, rigid props) never
// pass through the course resolver. Their private vertex copies get the same
// world lighting just before submission. Grass sprites use the ground's up
// normal (they sit on it); props use flat face normals oriented away from the
// batch centre (barrels, bales and tumbleweeds are roughly convex).
inline void light_proxy_layer(Device8& d,std::vector<ps2port::ObjectVertex>& v,bool upright)noexcept {
    auto* p=pilot(d);if(!p||!p->enabled()||!p->world||!p->lighting.active()||v.size()<3)return;
    try{
        const auto& s=p->lighting;
        if(upright){for(auto& x:v)x.color=atmosphere::scene_color(x.color,{0,1,0},s);++p->proxy_layer_draws;return;}
        double c[3]{};for(const auto& x:v){c[0]+=x.x;c[1]+=x.y;c[2]+=x.z;}for(auto& k:c)k/=double(v.size());
        for(size_t i=0;i+2<v.size();i+=3){auto& a=v[i];auto& b=v[i+1];auto& e=v[i+2];
            const float u[3]{b.x-a.x,b.y-a.y,b.z-a.z},w[3]{e.x-a.x,e.y-a.y,e.z-a.z};
            std::array<float,3> n{u[1]*w[2]-u[2]*w[1],u[2]*w[0]-u[0]*w[2],u[0]*w[1]-u[1]*w[0]};
            const float len=std::sqrt(n[0]*n[0]+n[1]*n[1]+n[2]*n[2]);if(!std::isfinite(len)||len<1e-12f)n={0,1,0};else for(auto& k:n)k/=len;
            const float out=(float((a.x+b.x+e.x)/3-c[0]))*n[0]+(float((a.y+b.y+e.y)/3-c[1]))*n[1]+(float((a.z+b.z+e.z)/3-c[2]))*n[2];
            if(out<0)for(auto& k:n)k=-k;
            for(auto* x:{&a,&b,&e})x->color=atmosphere::scene_color(x->color,n,s);}
        ++p->proxy_layer_draws;
    }catch(...){}
}
inline void log(Device8& d,const char* reason)noexcept {
    try{session().write("{\"type\":\"atmosphere_draw\",\"reason\":"+quote(std::string(reason))+",\"frame\":"+std::to_string(d.trace.frame_number())+"}");}catch(...){}
}
inline void sun_transform(Device8& d,D3DTRANSFORMSTATETYPE type,bool exe,uint32_t rva)noexcept{
    if(!exe||!((type==D3DTS_VIEW&&rva==GAMEPLAY_VIEW_RETURN_RVA)||(type==D3DTS_PROJECTION&&rva==GAMEPLAY_PROJECTION_RETURN_RVA)))return;
    auto* p=pilot(d);if(p&&(p->sun_disk||p->sun_halo||p->sun_flare||p->sun_style.vignette>0))p->sun.clear();
}
inline void sun_world(Device8& d,HRESULT hr,uintptr_t pc)noexcept{
    auto* p=pilot(d);if(!p||!p->enabled()||!(p->sun_disk||p->sun_halo||p->sun_flare||p->sun_style.vignette>0)||FAILED(hr)||!d.trace.scene_active||
        pc!=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr))+groundintegration::COURSE_DRAW_RETURN_RVA||
        GetCurrentThreadId()!=d.trace.render_thread_id())return;
    auto& proof=p->sun.proof;const auto frame=d.trace.frame_number();
    const auto& shadow=d.trace.effective_shadow;const auto& shader=shadow.bindings.vertex_shader;
    if(shader.known&&(shader.value==0x142||shader.value==0x242)&&groundintegration::course_world(d)){
        const auto& z=shadow.rs[D3DRS_ZENABLE];const auto& write=shadow.rs[D3DRS_ZWRITEENABLE];
        // A depth-only mask cannot prove occlusion by course cards/opaque
        // surfaces which deliberately omit depth writes. Never guess visibility.
        if(z.known&&z.value==D3DZB_TRUE&&(!write.known||!write.value))p->sun.unsafe_frame=frame;
    }
    if(proof.world&&proof.frame==frame)return;
    proof.clear();bool single=false;const auto cert=courseintegration::certificate(d,single);if(!single||!cert.valid)return;
    auto& n=*d.native();DWORD fvf=0;D3DVIEWPORT8 viewport{};
    if(FAILED(n.GetVertexShader(&fvf))||(fvf!=0x142&&fvf!=0x242&&fvf!=0x152)||
       !groundintegration::render(d,n,D3DRS_ZENABLE,D3DZB_TRUE)||!groundintegration::render(d,n,D3DRS_ZWRITEENABLE,TRUE)||
       !groundintegration::render(d,n,D3DRS_ALPHABLENDENABLE,FALSE))return;
    courseintegration::Ref<IDirect3DSurface8> back;
    if(FAILED(n.GetRenderTarget(&proof.target))||FAILED(n.GetBackBuffer(0,D3DBACKBUFFER_TYPE_MONO,&back.p))||
       !courseintegration::same_identity(proof.target,back.p)||FAILED(n.GetDepthStencilSurface(&proof.depth))||!proof.depth||
       FAILED(n.GetTransform(D3DTS_VIEW,&proof.view))||FAILED(n.GetTransform(D3DTS_PROJECTION,&proof.projection))){proof.clear();return;}
    D3DSURFACE_DESC desc{};if(FAILED(proof.target->GetDesc(&desc))||FAILED(n.GetViewport(&viewport))||viewport.X||viewport.Y||viewport.Width!=desc.Width||viewport.Height!=desc.Height||
       viewport.MinZ!=0||viewport.MaxZ!=1||!courseintegration::perspective(proof.projection)){proof.clear();return;}
    proof.frame=frame;proof.race=cert.race_generation;proof.owner=cert.owner_lifetime;proof.camera=cert.camera;proof.reset=d.ps2_port()->reset_generation();proof.world=true;
}
inline HRESULT sun_before_ui(Device8& d,bool ui)noexcept{
    capture_boundary(d,ui);
    auto* p=pilot(d);if(!ui||!p||!p->enabled()||!(p->sun_disk||p->sun_halo||p->sun_flare||p->sun_style.vignette>0)||!d.trace.scene_active||
       d.trace.shadow.recording||d.trace.effective_shadow.recording||GetCurrentThreadId()!=d.trace.render_thread_id())return S_OK;
    auto& sun=p->sun;const auto frame=d.trace.frame_number();if(sun.drawn_frame==frame)return S_OK;
    auto gate=[&](const char* reason){sun.reason=reason;if(p->first_reason(reason)||(d.trace.control.active&&sun.gate_frame!=frame))try{sun.gate_frame=frame;session().write("{\"type\":\"atmosphere_sun_gate\",\"frame\":"+std::to_string(frame)+",\"reason\":"+quote(std::string(reason))+",\"drawn\":false}");}catch(...){}return S_OK;};
    auto& proof=sun.proof;if(sun.unsafe_frame==frame)return gate("sun_non_depth_writing_course_surface");
    if(!proof.world||proof.frame!=frame)return gate("sun_current_frame_scene_depth_unproven");
    bool single=false;const auto cert=courseintegration::certificate(d,single);
    if(!single||!cert.valid||!proof.world||proof.frame!=frame||proof.race!=cert.race_generation||proof.owner!=cert.owner_lifetime||proof.camera!=cert.camera||proof.reset!=d.ps2_port()->reset_generation())return gate("sun_current_frame_scene_depth_unproven");
    auto& n=*d.native();courseintegration::Ref<IDirect3DSurface8> target,depth;D3DVIEWPORT8 viewport{};D3DSURFACE_DESC desc{};
    if(FAILED(n.GetRenderTarget(&target.p))||FAILED(n.GetDepthStencilSurface(&depth.p))||!courseintegration::same_identity(target.p,proof.target)||!courseintegration::same_identity(depth.p,proof.depth)||
       FAILED(target.p->GetDesc(&desc))||FAILED(n.GetViewport(&viewport))||viewport.X||viewport.Y||viewport.Width!=desc.Width||viewport.Height!=desc.Height||viewport.MinZ!=0||viewport.MaxZ!=1)return gate("sun_depth_or_viewport_changed");
    sun.drawn_frame=frame;
    if(p->sun_style.vignette>0){const auto writer=[](void* context,uint32_t slot,const Args& args,HRESULT hr)noexcept{notify(*static_cast<Device8*>(context),slot,args,hr);};
        const auto vr=sun.vignette(n,desc.Width,desc.Height,p->sun_style.vignette,&d,writer);if(FAILED(vr))return vr;
        if(p->first_reason("art_vignette")||d.trace.control.active)session().write("{\"type\":\"atmosphere_art_overlay\",\"effect\":\"vignette\",\"before_hud\":true,\"requested_triangles\":64,\"new_render_targets\":0,\"hresult\":"+std::to_string(uint32_t(vr))+"}");}
    if(!(p->sun_disk||p->sun_halo||p->sun_flare))return S_OK;
    atmosphere::SunPosition position;if(!atmosphere::sun_position(p->lighting.direction,proof.view,proof.projection,desc.Width,desc.Height,position,p->sun_style.core_degrees))return gate("sun_behind_camera_or_outside_view");
    try{
        const auto writer=[](void* context,uint32_t slot,const Args& args,HRESULT hr)noexcept{notify(*static_cast<Device8*>(context),slot,args,hr);};
        const auto hr=sun.render(n,position,p->sun_disk,p->sun_halo,p->sun_flare,&d,writer,&p->lighting,p->sun_style);LARGE_INTEGER frequency{};QueryPerformanceFrequency(&frequency);
        if(p->first_reason(sun.reason)||d.trace.control.active||frame%120==0)session().write("{\"type\":\"atmosphere_sun_gpu\",\"frame\":"+std::to_string(frame)+",\"reason\":"+quote(std::string(sun.reason))+
            ",\"x\":"+std::to_string(position.x)+",\"y\":"+std::to_string(position.y)+",\"radius\":"+std::to_string(position.radius)+",\"msaa\":"+std::to_string(desc.MultiSampleType)+",\"hresult\":"+std::to_string(uint32_t(sun.last_hr))+
            ",\"attempts\":"+std::to_string(sun.attempts)+",\"masked_submissions\":"+std::to_string(sun.rendered)+",\"cpu_ticks\":"+std::to_string(sun.cpu_ticks)+",\"qpc_frequency\":"+std::to_string(frequency.QuadPart)+",\"cpu_visibility_readback\":false,\"historical_visibility_used\":false,\"depth_writes\":false}");
        return FAILED(hr)?hr:S_OK;
    }catch(...){sun.reason="sun_exception_suppressed";return repair(d);}
}
inline void coverage_commit(Device8& d,atmosphere::Pilot& p)noexcept;
inline void coverage_flush(Device8& d,atmosphere::Pilot& p,bool force)noexcept;
inline void coverage_start(Device8& d,atmosphere::Pilot& p,UINT count)noexcept;
inline void observe(Device8& d,D3DPRIMITIVETYPE type,UINT,UINT vertices,UINT,UINT count,uintptr_t pc)noexcept {
    auto* p=pilot(d);if(!p||!p->enabled()||!count||type!=D3DPT_TRIANGLELIST||!d.trace.scene_active||
        d.trace.shadow.recording||d.trace.effective_shadow.recording||GetCurrentThreadId()!=d.trace.render_thread_id()||
        pc!=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr))+groundintegration::COURSE_DRAW_RETURN_RVA)return;
    try {
        const auto frame=d.trace.frame_number();
        if(p->coverage.enabled){coverage_commit(d,*p);coverage_flush(d,*p,false);coverage_start(d,*p,count);}
        if(p->course_fog.frame!=frame){auto& n=*d.native();DWORD enabled=FALSE,vertex=0,table=0,start=0,end=0,color=0;
            if(SUCCEEDED(n.GetRenderState(D3DRS_FOGENABLE,&enabled))&&enabled&&SUCCEEDED(n.GetRenderState(D3DRS_FOGVERTEXMODE,&vertex))&&
               SUCCEEDED(n.GetRenderState(D3DRS_FOGTABLEMODE,&table))&&SUCCEEDED(n.GetRenderState(D3DRS_FOGSTART,&start))&&
               SUCCEEDED(n.GetRenderState(D3DRS_FOGEND,&end))&&SUCCEEDED(n.GetRenderState(D3DRS_FOGCOLOR,&color))){
                float s=0,e=0;std::memcpy(&s,&start,4);std::memcpy(&e,&end,4);
                if(((vertex==D3DFOG_LINEAR&&table==D3DFOG_NONE)||(table!=D3DFOG_NONE&&table<=D3DFOG_LINEAR))&&std::isfinite(s)&&std::isfinite(e)&&s>=0&&s<e)
                    p->course_fog={frame,vertex,table,start,end,color};}}
        if(p->live_tuning&&frame!=p->live_key_frame){p->live_key_frame=frame;DWORD pid=0;GetWindowThreadProcessId(GetForegroundWindow(),&pid);
            const bool down=pid==GetCurrentProcessId()&&(GetAsyncKeyState(VK_CONTROL)&0x8000)&&(GetAsyncKeyState(VK_MENU)&0x8000)&&(GetAsyncKeyState('R')&0x8000);
            if(down&&!p->live_key_down)p->live_force=true;p->live_key_down=down;}
        if(!p->package_root.empty()&&p->metadata_poll_frame!=frame){p->metadata_poll_frame=frame;DWORD pid=0;GetWindowThreadProcessId(GetForegroundWindow(),&pid);
            const bool down=pid==GetCurrentProcessId()&&(GetAsyncKeyState(VK_CONTROL)&0x8000)&&(GetAsyncKeyState(VK_MENU)&0x8000)&&(GetAsyncKeyState('M')&0x8000);
            if(down&&!p->metadata_key_down)p->course_dirty=true;p->metadata_key_down=down;}
        if(p->seam_debug&&frame!=p->seam_poll_frame){p->seam_poll_frame=frame;DWORD pid=0;GetWindowThreadProcessId(GetForegroundWindow(),&pid);
            const bool down=pid==GetCurrentProcessId()&&(GetAsyncKeyState(VK_CONTROL)&0x8000)&&(GetAsyncKeyState(VK_MENU)&0x8000)&&(GetAsyncKeyState('L')&0x8000);
            if(down&&!p->seam_key_down){p->world=!p->world;session().write("{\"type\":\"atmosphere_seam_toggle\",\"world_lighting\":"+std::string(p->world?"true":"false")+",\"sky_fog_unchanged\":true,\"frame\":"+std::to_string(frame)+"}");}p->seam_key_down=down;
        }
        if(frame>=p->perf_frame+120){LARGE_INTEGER frequency{};QueryPerformanceFrequency(&frequency);const auto calls=p->cpu_calls-p->perf_previous_calls;
            session().write("{\"type\":\"atmosphere_cpu_window\",\"frame\":"+std::to_string(frame)+",\"frames\":"+std::to_string(frame-p->perf_frame)+",\"cpu_ms\":"+std::to_string(frequency.QuadPart?1000.0*double(p->cpu_ticks-p->perf_previous_ticks)/double(frequency.QuadPart):0)+",\"calls\":"+std::to_string(calls)+",\"accepted_draws\":"+std::to_string(p->world_draws)+",\"copied_bytes\":"+std::to_string(p->copied_bytes)+",\"road_draws\":"+std::to_string(p->category_draws[1])+",\"terrain_draws\":"+std::to_string(p->category_draws[2])+",\"vegetation_draws\":"+std::to_string(p->category_draws[3])+",\"static_object_draws\":"+std::to_string(p->category_draws[4])+"}");
            const auto ranges=p->resolver.classified_ranges();
            if(p->universal)session().write("{\"type\":\"atmosphere_resolver_window\",\"frame\":"+std::to_string(frame)+",\"race_generation\":"+std::to_string(p->observed_race)+
                ",\"cache_entries\":"+std::to_string(p->resolver.entries.size())+",\"cache_bytes\":"+std::to_string(p->resolver.bytes)+",\"cache_hits\":"+std::to_string(p->resolver.hits)+
                ",\"cache_misses\":"+std::to_string(p->resolver.misses)+",\"changed_geometry_rebuilds\":"+std::to_string(p->resolver.rebuilds)+",\"instanced_world_relights\":"+std::to_string(p->resolver.world_relights)+",\"content_comparisons\":"+std::to_string(p->resolver.content_checks)+
                ",\"cache_resets\":"+std::to_string(p->resolver.cache_resets)+",\"normal_hint_matches\":"+std::to_string(p->normal_hints.matched)+",\"normal_hint_fallbacks\":"+std::to_string(p->normal_hints.fallback)+",\"body_cpu_ticks\":"+std::to_string(p->body_cpu_ticks)+",\"qpc_frequency\":"+std::to_string(frequency.QuadPart)+",\"body_calls\":"+std::to_string(p->body_calls)+",\"body_changed_vertices\":"+std::to_string(p->body_vertices)+",\"accepted_draws\":"+std::to_string(p->resolved_draws)+",\"skipped_draws\":"+std::to_string(p->resolver_skipped_draws)+",\"state_rejections\":"+std::to_string(p->world_rejected)+
                ",\"cached_native_ranges\":"+std::to_string(ranges[0])+",\"cached_road_ranges\":"+std::to_string(ranges[1])+",\"cached_terrain_ranges\":"+std::to_string(ranges[2])+",\"cached_vegetation_ranges\":"+std::to_string(ranges[3])+",\"cached_static_ranges\":"+std::to_string(ranges[4])+"}");
            p->perf_frame=frame;p->perf_previous_ticks=p->cpu_ticks;p->perf_previous_calls=p->cpu_calls;}
        const auto life=atmosphere::lifecycle();const auto reset=d.ps2_port()->reset_generation();p->diagnostic_epoch(life.race,reset);p->regional_epoch(life);
        auto context=[&]() {return ",\"device\":"+std::to_string(d.trace.device_id())+",\"frame\":"+std::to_string(d.trace.frame_number())+
            ",\"reset_generation\":"+std::to_string(reset)+",\"race_generation\":"+std::to_string(life.race)+",\"scene_job\":"+std::to_string(life.job)+
            ",\"scene\":"+quote(std::string(life.scene_name.data()))+",\"owner\":"+std::to_string(life.actor)+",\"owner_lifetime\":"+std::to_string(life.owner_lifetime);};
        auto& n=*d.native();DWORD fvf=0;const auto& tracked=d.trace.effective_shadow.bindings.vertex_shader;
        if(tracked.known)fvf=tracked.value;else if(FAILED(n.GetVertexShader(&fvf)))return;
        const bool sky=(vertices==134&&count==196)||(vertices==114&&count==180);
        if(sky&&fvf==0x102){
            ++p->sky_candidates;
            courseintegration::Ref<IDirect3DBaseTexture8> base;
            if(FAILED(n.GetTexture(0,&base.p))||!base.p||base.p->GetType()!=D3DRTYPE_TEXTURE){++p->sky_rejected;return;}
            const auto pointer=reinterpret_cast<uintptr_t>(base.p);const auto serial=d.trace.resources.generation(pointer);
            if(!serial){++p->sky_rejected;return;}
            auto* t=static_cast<IDirect3DTexture8*>(base.p);D3DSURFACE_DESC desc{};
            if(FAILED(t->GetLevelDesc(0,&desc))){++p->sky_rejected;return;}
            atmosphere::Pilot::SkyCache* cache=nullptr;
            for(auto& c:p->sky_cache)if(c.pointer==pointer&&c.generation==serial){cache=&c;break;}
            if(!cache){
                cache=&p->sky_cache[p->sky_cache_next++%p->sky_cache.size()];*cache={};cache->pointer=pointer;cache->generation=serial;
                const char* reason="unsupported_texture_layout";
                if(desc.Width==256&&desc.Height==256&&desc.Pool!=D3DPOOL_DEFAULT&&(desc.Format==D3DFMT_A8R8G8B8||desc.Format==D3DFMT_X8R8G8B8)){
                    std::vector<BYTE> pixels(256*256*4);D3DLOCKED_RECT lock{};
                    if(SUCCEEDED(t->LockRect(0,&lock,nullptr,D3DLOCK_READONLY))){
                        const bool valid=lock.pBits&&lock.Pitch>=1024;
                        if(valid)for(unsigned y=0;y<256;++y)std::memcpy(pixels.data()+y*1024,static_cast<BYTE*>(lock.pBits)+y*lock.Pitch,1024);
                        const auto unlocked=t->UnlockRect(0);
                        if(valid&&SUCCEEDED(unlocked)){
                            if(desc.Format==D3DFMT_X8R8G8B8)for(size_t i=3;i<pixels.size();i+=4)pixels[i]=255;
                            cache->sha=sha256_bytes(pixels.data(),pixels.size());reason="unknown_original_content";
                            for(const auto& id:atmosphere::kSkyIdentities)if(cache->sha==id.sha){cache->preset=int(id.preset);cache->layer=int(id.layer);reason="original_sky_content_matched";break;}
                        }else reason="texture_lock_or_unlock_invalid";
                    }else reason="texture_read_lock_failed";
                }
                cache->reason=reason;
            }
            if(p->first_reason(("sky_serial_"+std::to_string(serial)).c_str())) {
                session().write("{\"type\":\"atmosphere_sky_draw\",\"observation_only\":true,\"reason\":"+quote(std::string(cache->reason))+
                    ",\"preset\":"+std::to_string(cache->preset)+",\"layer\":"+std::to_string(cache->layer)+",\"projection_fix\":"+std::to_string(p->sky_projection)+",\"haze_strength\":"+std::to_string(p->sky_haze)+",\"vertices\":"+std::to_string(vertices)+
                    ",\"triangles\":"+std::to_string(count)+",\"fvf\":"+std::to_string(fvf)+",\"texture_pointer\":"+std::to_string(pointer)+
                    ",\"texture_serial\":"+std::to_string(serial)+",\"format\":"+std::to_string(desc.Format)+",\"width\":"+std::to_string(desc.Width)+
                    ",\"height\":"+std::to_string(desc.Height)+",\"bgra_sha256\":"+quote(cache->sha)+context()+"}");
            }
            if(cache->preset>=0)++p->sky_matched;else ++p->sky_rejected;
        }else if((fvf&D3DFVF_DIFFUSE)&&p->last_fog_frame!=d.trace.frame_number()&&
            groundintegration::stage(d,n,1,D3DTSS_COLOROP,D3DTOP_MODULATE2X)&&groundintegration::render(d,n,D3DRS_FOGENABLE,TRUE)){
            p->last_fog_frame=d.trace.frame_number();DWORD fog=0;
            if(SUCCEEDED(n.GetRenderState(D3DRS_FOGCOLOR,&fog))&&(!p->fog_seen||fog!=p->last_fog)){
                p->last_fog=fog;p->fog_seen=true;
                session().write("{\"type\":\"atmosphere_world_fog\",\"observation_only\":true,\"fog_color\":"+std::to_string(fog)+
                    ",\"fvf\":"+std::to_string(fvf)+",\"vertices\":"+std::to_string(vertices)+",\"triangles\":"+std::to_string(count)+context()+"}");
            }
        }
    }catch(...){}
}
inline HRESULT reject(Device8& d,atmosphere::Pilot& p,const char* reason)noexcept {
    ++p.world_rejected;
    try{if(p.capture.stage||p.coverage.enabled)p.draw_reason=reason;if(p.first_reason(reason))session().write("{\"type\":\"atmosphere_admission_rejected\",\"reason\":"+quote(std::string(reason))+
        ",\"frame\":"+std::to_string(d.trace.frame_number())+",\"race_generation\":"+std::to_string(p.observed_race)+
        ",\"reset_generation\":"+std::to_string(p.observed_reset)+"}");}catch(...){}return S_OK;
}
// Mirror only the range consumed by this draw. An earlier prototype requested
// every preceding vertex and rejected valid streaming buffers with untouched gaps.
struct Geometry {
    std::vector<uint8_t> bytes;std::vector<uint32_t> indices;
    uint64_t vertex_generation=0,index_generation=0,vertex_revision=0,index_revision=0;
};
inline bool geometry(Device8& d,atmosphere::Pilot& p,UINT min,UINT vertices,UINT start,UINT triangles,Geometry& g) {
    auto& n=*d.native();auto& saved=p.pending;
    if(!vertices||vertices>32768||!triangles||triangles>32768||FAILED(n.GetStreamSource(0,&saved.stream,&saved.stride))||!saved.stream||saved.stride<16||saved.stride>128||
        FAILED(n.GetIndices(&saved.indices,&saved.base))||!saved.indices)return false;
    D3DVERTEXBUFFER_DESC vd{};D3DINDEXBUFFER_DESC id{};
    if(FAILED(saved.stream->GetDesc(&vd))||FAILED(saved.indices->GetDesc(&id)))return false;
    const unsigned width=id.Format==D3DFMT_INDEX16?2:id.Format==D3DFMT_INDEX32?4:0;
    const uint64_t offset=(uint64_t(saved.base)+min)*saved.stride,bytes=uint64_t(vertices)*saved.stride;
    const uint64_t io=uint64_t(start)*width,is=uint64_t(triangles)*3*width;
    if(!width||offset>vd.Size||bytes>vd.Size-offset||io>id.Size||is>id.Size-io||(uint64_t(min)+vertices)*saved.stride>2*1024*1024)return false;
    g.vertex_generation=d.trace.resources.generation(reinterpret_cast<uintptr_t>(saved.stream));g.index_generation=d.trace.resources.generation(reinterpret_cast<uintptr_t>(saved.indices));
    std::vector<BYTE> indices;
    if(!g.vertex_generation||!g.index_generation||!d.copy_buffer_shadow(saved.stream,BufferKind::Vertex,g.vertex_generation,offset,static_cast<size_t>(bytes),g.bytes,g.vertex_revision)||
        !d.copy_buffer_shadow(saved.indices,BufferKind::Index,g.index_generation,io,static_cast<size_t>(is),indices,g.index_revision))return false;
    g.indices.reserve(triangles*3);
    for(unsigned i=0;i<triangles*3;++i){uint32_t index=0;if(width==2){uint16_t v=0;std::memcpy(&v,indices.data()+i*2,2);index=v;}else std::memcpy(&index,indices.data()+i*4,4);
        if(index<min||uint64_t(index)>=uint64_t(min)+vertices)return false;g.indices.push_back(index-min);}
    return true;
}
inline HRESULT upload(Device8& d,atmosphere::Pilot& p,UINT min,UINT vertices,const std::vector<uint8_t>& bytes)noexcept {
    auto& n=*d.native();auto& s=p.pending;const UINT size=(min+vertices)*s.stride;
    if(!p.scratch||p.scratch_size<size){if(p.scratch)p.scratch->Release();p.scratch=nullptr;p.scratch_size=0;
        if(FAILED(n.CreateVertexBuffer(size,D3DUSAGE_WRITEONLY,0,D3DPOOL_MANAGED,&p.scratch))||!p.scratch)return E_FAIL;p.scratch_size=size;}
    BYTE* out=nullptr;if(FAILED(p.scratch->Lock(min*s.stride,static_cast<UINT>(bytes.size()),&out,0)))return E_FAIL;
    if(out)std::memcpy(out,bytes.data(),bytes.size());const auto unlocked=p.scratch->Unlock();if(!out||FAILED(unlocked))return E_FAIL;
    s.stream_changed=true;auto hr=n.SetStreamSource(0,p.scratch,s.stride);notify(d,83,pack(0,p.scratch,s.stride),hr);
    if(SUCCEEDED(hr)){s.indices_changed=true;hr=n.SetIndices(s.indices,0);notify(d,85,pack(s.indices,0),hr);}p.copied_bytes+=bytes.size();return hr;
}
inline std::string material_sha(Device8& d,atmosphere::Pilot& p,IDirect3DBaseTexture8* base) {
    if(!base||base->GetType()!=D3DRTYPE_TEXTURE)return {};
    const auto pointer=reinterpret_cast<uintptr_t>(base);const auto generation=d.trace.resources.generation(pointer);if(!generation)return {};
    for(const auto& c:p.material_cache)if(c.pointer==pointer&&c.generation==generation)return c.sha;
    auto& c=p.material_cache[p.material_cache_next++%p.material_cache.size()];c={};c.pointer=pointer;c.generation=generation;
    auto* texture=static_cast<IDirect3DTexture8*>(base);D3DSURFACE_DESC desc{};
    if(FAILED(texture->GetLevelDesc(0,&desc))||!desc.Width||!desc.Height||desc.Width>2048||desc.Height>2048||desc.Pool==D3DPOOL_DEFAULT||
        (desc.Format!=D3DFMT_A8R8G8B8&&desc.Format!=D3DFMT_X8R8G8B8))return {};
    D3DLOCKED_RECT lock{};if(FAILED(texture->LockRect(0,&lock,nullptr,D3DLOCK_READONLY)))return {};
    std::vector<BYTE> pixels(size_t(desc.Width)*desc.Height*4);const bool valid=lock.pBits&&lock.Pitch>=INT(desc.Width*4);
    if(valid)for(unsigned y=0;y<desc.Height;++y)std::memcpy(pixels.data()+size_t(y)*desc.Width*4,static_cast<BYTE*>(lock.pBits)+size_t(y)*lock.Pitch,desc.Width*4);
    const auto hr=texture->UnlockRect(0);if(!valid||FAILED(hr))return {};
    if(desc.Format==D3DFMT_X8R8G8B8)for(size_t i=3;i<pixels.size();i+=4)pixels[i]=255;
    c.opaque=true;for(size_t i=3;i<pixels.size();i+=4)if(pixels[i]!=255){c.opaque=false;break;}
    c.sha=sha256_bytes(pixels.data(),pixels.size());return c.sha;
}
// Bounded private copies: no shared asset mutation, no per-frame pixel read.
// Called only after primary and secondary material certificates are validated.
inline IDirect3DTexture8* environment_copy(Device8& d,atmosphere::Pilot& p,IDirect3DBaseTexture8* source,uint64_t generation,DWORD factor){
    const auto pointer=reinterpret_cast<uintptr_t>(source);
    for(auto& c:p.environment_copies)if(c.source==pointer&&c.generation==generation&&c.factor==factor&&c.texture){++p.environment_hits;return c.texture;}
    if(!source||source->GetType()!=D3DRTYPE_TEXTURE||!generation)return nullptr;
    auto* texture=static_cast<IDirect3DTexture8*>(source);D3DSURFACE_DESC desc{};
    if(FAILED(texture->GetLevelDesc(0,&desc))||!desc.Width||!desc.Height||desc.Width>512||desc.Height>512||desc.Pool==D3DPOOL_DEFAULT||
       (desc.Format!=D3DFMT_A8R8G8B8&&desc.Format!=D3DFMT_X8R8G8B8))return nullptr;
    courseintegration::Ref<IDirect3DTexture8> copy;
    const UINT levels=texture->GetLevelCount();if(!levels||levels>10||FAILED(d.native()->CreateTexture(desc.Width,desc.Height,levels,0,desc.Format,D3DPOOL_MANAGED,&copy.p))||!copy.p)return nullptr;
    for(UINT level=0;level<levels;++level){D3DSURFACE_DESC size{};if(FAILED(texture->GetLevelDesc(level,&size)))return nullptr;
        D3DLOCKED_RECT input{},output{};if(FAILED(texture->LockRect(level,&input,nullptr,D3DLOCK_READONLY)))return nullptr;
        const HRESULT locked=copy.p->LockRect(level,&output,nullptr,0);
        const bool valid=SUCCEEDED(locked)&&input.pBits&&output.pBits&&input.Pitch>=INT(size.Width*4)&&output.Pitch>=INT(size.Width*4);
        if(valid)for(UINT y=0;y<size.Height;++y)for(UINT x=0;x<size.Width;++x){uint32_t pixel=0;
            std::memcpy(&pixel,static_cast<BYTE*>(input.pBits)+y*input.Pitch+x*4,4);pixel=atmosphere::environment_texel(pixel,factor);
            std::memcpy(static_cast<BYTE*>(output.pBits)+y*output.Pitch+x*4,&pixel,4);}
        const auto a=texture->UnlockRect(level);const auto b=SUCCEEDED(locked)?copy.p->UnlockRect(level):locked;
        if(!valid||FAILED(a)||FAILED(b))return nullptr;
    }
    auto& c=p.environment_copies[p.environment_next++%p.environment_copies.size()];if(c.texture)c.texture->Release();
    c={pointer,generation,factor,copy.p};copy.p=nullptr;++p.environment_builds;return c.texture;
}
inline bool defer_until_native_draw(Device8& d)noexcept {
    auto* p=pilot(d);if(!p||!p->enabled()||!p->universal||(!p->custom()&&!p->world_route()))return false;
    const auto& shadow=d.trace.effective_shadow;const auto& fvf=shadow.bindings.vertex_shader;const auto& op=shadow.tss[1][D3DTSS_COLOROP];
    // GroundDetail's proven base_noise path uses the same vertex geometry for
    // its existing two passes and does not infer owner/geometry from VB hashes.
    // ForestFix can also own a blended static environment draw. Prepare its
    // certified private RGB before that early return; ForestFix keeps alpha,
    // blending and its own depth correction. No material proof is bypassed.
    auto* ground=groundintegration::ground(d);
    const bool forest=ground&&ground->forest_fix()&&!ps2port::live::disabled(ps2port::live::Forest);
    return !(fvf.known&&op.known&&atmosphere::world_lighting_before_replacement(fvf.value,op.value,forest));
}
inline HRESULT pc_water_draw(Device8& d,atmosphere::Pilot& p,DWORD fvf,bool& applied){
    applied=false;auto& n=*d.native();
    if(!p.pc_water||!p.world||!p.lighting.active()||(fvf!=0x242&&fvf!=0x252)||
       !groundintegration::render(d,n,D3DRS_ZENABLE,D3DZB_TRUE)||!groundintegration::render(d,n,D3DRS_ALPHATESTENABLE,FALSE)||
       !groundintegration::stage(d,n,0,D3DTSS_COLOROP,D3DTOP_MODULATE)||!groundintegration::stage(d,n,0,D3DTSS_COLORARG1,D3DTA_TEXTURE)||!groundintegration::stage(d,n,0,D3DTSS_COLORARG2,D3DTA_DIFFUSE)||
       !groundintegration::stage(d,n,1,D3DTSS_COLOROP,D3DTOP_ADD)||!groundintegration::stage(d,n,1,D3DTSS_COLORARG1,D3DTA_CURRENT)||!groundintegration::stage(d,n,1,D3DTSS_COLORARG2,D3DTA_TEXTURE)||
       !groundintegration::stage(d,n,0,D3DTSS_TEXCOORDINDEX,0)||!groundintegration::stage(d,n,1,D3DTSS_TEXCOORDINDEX,1)||
       !groundintegration::stage(d,n,0,D3DTSS_RESULTARG,D3DTA_CURRENT)||!groundintegration::stage(d,n,1,D3DTSS_RESULTARG,D3DTA_CURRENT)||
       !groundintegration::stage(d,n,2,D3DTSS_COLOROP,D3DTOP_DISABLE)||!groundintegration::stage(d,n,3,D3DTSS_COLOROP,D3DTOP_DISABLE))return S_OK;
    DWORD blend=0;if(FAILED(n.GetRenderState(D3DRS_ALPHABLENDENABLE,&blend)))return S_OK;
    if(blend&&(!groundintegration::render(d,n,D3DRS_SRCBLEND,D3DBLEND_SRCALPHA)||!groundintegration::render(d,n,D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA)))return S_OK;
    if(!groundintegration::render(d,n,D3DRS_BLENDOP,D3DBLENDOP_ADD))return S_OK;
    D3DMATRIX world{},identity{};identity._11=identity._22=identity._33=identity._44=1;
    if(FAILED(n.GetTransform(D3DTS_WORLD,&world))||std::memcmp(&world,&identity,64))return S_OK;
    courseintegration::Ref<IDirect3DBaseTexture8> secondary;if(FAILED(n.GetTexture(1,&secondary.p))||!secondary.p||!d.trace.resources.generation(reinterpret_cast<uintptr_t>(secondary.p)))return S_OK;
    const auto secondary_sha=material_sha(d,p,secondary.p);
    if(!atmosphere::pc_water_secondary(secondary_sha)){if(p.first_reason(("pc_water_secondary_"+secondary_sha).c_str())){D3DSURFACE_DESC desc{};if(secondary.p->GetType()==D3DRTYPE_TEXTURE)static_cast<IDirect3DTexture8*>(secondary.p)->GetLevelDesc(0,&desc);session().write("{\"type\":\"atmosphere_pc_water_gate\",\"reason\":\"secondary_identity_unproven\",\"sha256\":"+quote(secondary_sha)+",\"fvf\":"+std::to_string(fvf)+",\"format\":"+std::to_string(desc.Format)+",\"pool\":"+std::to_string(desc.Pool)+"}");}return S_OK;}
    if(!p.pc_water_caps){D3DCAPS8 caps{};if(FAILED(n.GetDeviceCaps(&caps))||caps.MaxTextureBlendStages<3){p.pc_water=false;session().write("{\"type\":\"atmosphere_pc_water_gate\",\"reason\":\"third_blend_stage_unsupported\"}");return S_OK;}p.pc_water_caps=true;}
    auto& saved=p.pending;if(saved.any())return D3DERR_DEVICELOST;
    constexpr D3DTEXTURESTAGESTATETYPE keys[]{D3DTSS_COLOROP,D3DTSS_COLORARG1,D3DTSS_COLORARG2,D3DTSS_ALPHAOP,D3DTSS_ALPHAARG1,D3DTSS_RESULTARG,D3DTSS_ALPHAARG2};
    for(unsigned i=0;i<7;++i)if(FAILED(n.GetTextureStageState(2,keys[i],&saved.body_stage[i])))return S_OK;
    if(FAILED(n.GetRenderState(D3DRS_TEXTUREFACTOR,&saved.body_factor)))return S_OK;
    if(p.lighting.fog_enabled&&FAILED(n.GetRenderState(D3DRS_FOGCOLOR,&saved.fog)))return S_OK;
    const DWORD values[]{D3DTOP_MODULATE,D3DTA_CURRENT,D3DTA_TFACTOR,D3DTOP_SELECTARG1,D3DTA_CURRENT,D3DTA_CURRENT,D3DTA_CURRENT};
    const DWORD factor=atmosphere::pc_water_factor(p.lighting,saved.body_factor);
    for(unsigned i:{7u,1u,2u,3u,4u,5u,6u,0u}){saved.body_pending|=1u<<i;const auto hr=i==7?n.SetRenderState(D3DRS_TEXTUREFACTOR,factor):n.SetTextureStageState(2,keys[i],values[i]);
        if(i==7)notify(d,50,pack(D3DRS_TEXTUREFACTOR,factor),hr);else notify(d,63,pack(2,keys[i],values[i]),hr);if(FAILED(hr)){p.pc_water=false;return repair(d);}}
    if(p.lighting.fog_enabled){saved.fog_changed=true;const auto fog=atmosphere::scene_fog(saved.fog,p.lighting);const auto hr=n.SetRenderState(D3DRS_FOGCOLOR,fog);notify(d,50,pack(D3DRS_FOGCOLOR,fog),hr);if(FAILED(hr))return repair(d);}
    applied=true;++p.pc_water_draws;
    if(p.capture.stage||p.coverage.enabled){p.draw_resolved=true;p.draw_lit=true;p.draw_reason="pc_water_energy";}
    if(p.first_reason("pc_water_atmosphere")||d.trace.control.active)session().write("{\"type\":\"atmosphere_pc_water\",\"frame\":"+std::to_string(d.trace.frame_number())+",\"factor\":"+std::to_string(factor)+",\"draws\":"+std::to_string(p.pc_water_draws)+",\"alpha_uv_depth_unchanged\":true,\"path\":\"certified_native_base_water_fallback_only\"}");
    return S_OK;
}
// PC waterfalls are unlit XYZ|TEX1 course cards (no diffuse, fogged, often
// blended), so they kept full texture brightness against the darkened world.
// Only a texture the active course package names as a waterfall material is
// accepted; stage 1 (native DISABLE) multiplies RGB by the PC-water energy.
// Alpha, blending, UV and depth are untouched; states restore after the draw.
inline HRESULT pc_waterfall_draw(Device8& d,atmosphere::Pilot& p,DWORD fvf,const char* course,bool& applied){
    applied=false;auto& n=*d.native();
    if(!p.world||!p.lighting.active()||!p.universal||(fvf!=0x102&&fvf!=0x142)||
       !groundintegration::render(d,n,D3DRS_FOGENABLE,TRUE)||!groundintegration::render(d,n,D3DRS_ZENABLE,D3DZB_TRUE)||
       !groundintegration::stage(d,n,0,D3DTSS_COLOROP,D3DTOP_MODULATE)||!groundintegration::stage(d,n,0,D3DTSS_COLORARG1,D3DTA_TEXTURE)||
       !groundintegration::stage(d,n,0,D3DTSS_RESULTARG,D3DTA_CURRENT)||!groundintegration::stage(d,n,1,D3DTSS_COLOROP,D3DTOP_DISABLE))return S_OK;
    D3DMATRIX world{},identity{};identity._11=identity._22=identity._33=identity._44=1;
    if(FAILED(n.GetTransform(D3DTS_WORLD,&world))||std::memcmp(&world,&identity,64))return S_OK;
    if(!p.select_course(course))return S_OK;p.metadata.load(p.metadata_path);if(!p.metadata.ready)return S_OK;
    courseintegration::Ref<IDirect3DBaseTexture8> texture;if(FAILED(n.GetTexture(0,&texture.p))||!texture.p||!d.trace.resources.generation(reinterpret_cast<uintptr_t>(texture.p)))return S_OK;
    const auto sha=material_sha(d,p,texture.p);if(sha.empty())return S_OK;
    const auto* material=p.metadata.find(course,sha);
    // Waterfalls (Deny by the water word) take the PC-water energy, also as a
    // blended 0x142 card (SpainM/S2). Other XYZ|TEX1 cards need an authored
    // static/vegetation role and get the thin-prop card energy.
    if(!material)return S_OK;
    const bool waterfall=material->name.find("waterfall")!=std::string::npos;
    if(waterfall&&!p.pc_water)return S_OK;
    if(!waterfall&&(fvf!=0x102||(material->flags&atmosphere::Deny)||(material->category!=3&&material->category!=4)))return S_OK;
    auto& saved=p.pending;if(saved.any())return D3DERR_DEVICELOST;
    constexpr D3DTEXTURESTAGESTATETYPE keys[]{D3DTSS_COLOROP,D3DTSS_COLORARG1,D3DTSS_COLORARG2,D3DTSS_ALPHAOP,D3DTSS_ALPHAARG1,D3DTSS_RESULTARG,D3DTSS_ALPHAARG2};
    for(unsigned i=0;i<7;++i)if(FAILED(n.GetTextureStageState(1,keys[i],&saved.body_stage[i])))return S_OK;
    if(FAILED(n.GetRenderState(D3DRS_TEXTUREFACTOR,&saved.body_factor)))return S_OK;
    if(p.lighting.fog_enabled&&FAILED(n.GetRenderState(D3DRS_FOGCOLOR,&saved.fog)))return S_OK;
    saved.body_unit=1;
    const DWORD values[]{D3DTOP_MODULATE,D3DTA_CURRENT,D3DTA_TFACTOR,D3DTOP_SELECTARG1,D3DTA_CURRENT,D3DTA_CURRENT,D3DTA_CURRENT};
    const DWORD factor=waterfall?atmosphere::pc_water_factor(p.lighting,saved.body_factor):((saved.body_factor&0xff000000u)|(atmosphere::card_energy(p.lighting)&0x00ffffffu));
    for(unsigned i:{7u,1u,2u,3u,4u,5u,6u,0u}){saved.body_pending|=1u<<i;const auto hr=i==7?n.SetRenderState(D3DRS_TEXTUREFACTOR,factor):n.SetTextureStageState(1,keys[i],values[i]);
        if(i==7)notify(d,50,pack(D3DRS_TEXTUREFACTOR,factor),hr);else notify(d,63,pack(1,keys[i],values[i]),hr);if(FAILED(hr))return repair(d);}
    if(p.lighting.fog_enabled){saved.fog_changed=true;const auto fog=atmosphere::scene_fog(saved.fog,p.lighting);const auto hr=n.SetRenderState(D3DRS_FOGCOLOR,fog);notify(d,50,pack(D3DRS_FOGCOLOR,fog),hr);if(FAILED(hr))return repair(d);}
    applied=true;++p.pc_water_draws;
    if(p.capture.stage||p.coverage.enabled){p.draw_resolved=true;p.draw_lit=true;p.draw_reason=waterfall?"pc_waterfall_energy":"unlit_card_energy";p.draw_material=material->name;p.draw_category=material->category;}
    if(p.first_reason(waterfall?"pc_waterfall_atmosphere":"unlit_card_atmosphere")||d.trace.control.active)session().write("{\"type\":\"atmosphere_pc_waterfall\",\"frame\":"+std::to_string(d.trace.frame_number())+",\"material\":"+quote(material->name)+",\"factor\":"+std::to_string(factor)+",\"alpha_uv_depth_unchanged\":true}");
    return S_OK;
}
// P0.1 coverage ledger: one pending record per course-loop draw (opened in
// observe, verdict from the same reject/resolver fields as the F10 capture,
// closed when the next draw is observed). Diagnostic only; no state changes.
inline void coverage_start(Device8& d,atmosphere::Pilot& p,UINT count)noexcept{
    auto& c=p.coverage;c.pending=true;c.reached=false;c.frame=d.trace.frame_number();c.triangles=count;c.texture.clear();
    DWORD fvf=0;d.native()->GetVertexShader(&fvf);c.fvf=fvf;
    try{courseintegration::Ref<IDirect3DBaseTexture8> t;if(SUCCEEDED(d.native()->GetTexture(0,&t.p))&&t.p)c.texture=material_sha(d,p,t.p);}catch(...){}
    if(c.texture.empty())c.texture="untextured_or_unhashable";
    p.draw_reason.clear();p.draw_material.clear();p.draw_category=0;p.draw_lit=p.draw_resolved=false;
}
inline void coverage_commit(Device8& d,atmosphere::Pilot& p)noexcept{
    auto& c=p.coverage;if(!c.enabled||!c.pending)return;c.pending=false;
    try{
        const std::string course=p.active_course.empty()?"unknown":p.active_course;const auto& r=p.draw_reason;
        std::string verdict,reason=r;
        if(!c.reached){verdict="Not reached";if(reason.empty())reason="replaced_or_deferred_before_atmosphere";}
        else if(p.draw_resolved)verdict=p.draw_lit?"Lit":"Native control";
        else if(r.empty())verdict=c.fvf==0x102?"Sky or unlit card":"Untouched";
        else verdict=r.find("excluded")!=std::string::npos||r.find("vehicle")!=std::string::npos?"Excluded":
            r.find("unknown")!=std::string::npos||r.find("ambiguous")!=std::string::npos?"Unclassified":
            r.find("shader")!=std::string::npos||r.find("stage")!=std::string::npos||r.find("contract")!=std::string::npos?"Shader mismatch":"Unsupported";
        std::string material=p.draw_material;uint32_t category=p.draw_category;
        if(material.empty()&&p.metadata.ready&&course!="unknown"){if(const auto* m=p.metadata.find(course.c_str(),c.texture)){material=m->name;category=m->category;}}
        c.add(course,material,verdict,reason,category);
    }catch(...){c.overflow=true;}
    (void)d;
}
inline void coverage_flush(Device8& d,atmosphere::Pilot& p,bool force)noexcept{
    auto& c=p.coverage;const auto frame=d.trace.frame_number();
    if(!c.enabled||!c.dirty||(!force&&frame-c.last_flush<900))return;c.last_flush=frame;c.dirty=false;
    try{if(!session().enabled||session().directory.empty())return;
        const auto path=std::filesystem::path(session().directory)/(L"coverage-"+std::to_wstring(GetCurrentProcessId())+L".json");
        auto temporary=path;temporary+=L".tmp";
        {std::ofstream f(temporary,std::ios::binary|std::ios::trunc);f<<c.serialize(frame);if(!f)return;}
        std::error_code ec;std::filesystem::rename(temporary,path,ec);
    }catch(...){}
}
// F10 sidecars remain available even when the ordinary session log reaches
// its fixed size limit. Debug writes are bounded and never run in normal mode.
inline void debug_record(Device8& d,const std::string& record)noexcept {
    try{if(!session().enabled||session().directory.empty())return;
        const auto path=std::filesystem::path(session().directory)/(L"atmosphere22-"+std::to_wstring(GetCurrentProcessId())+L"-d"+std::to_wstring(d.trace.device_id())+L"-f"+std::to_wstring(d.trace.frame_number())+L".jsonl");
        std::ofstream f(path,std::ios::binary|std::ios::app);f<<record<<"\n";
    }catch(...){}
}
// F10 only, fixed budget; no per-frame geometry export. Ctrl+Alt+L in
// SeamDebug changes only colour modulation; scoped fog/admission stay identical.
inline void seam_sample(Device8& d,atmosphere::Pilot& p,const atmosphere::ResolvedGeometry& e,const atmosphere::SceneMaterial* m,
                        const char* course,const std::string& texture,DWORD fvf,UINT min,UINT start,UINT triangles,uint64_t vg,uint64_t ig) {
    if(!p.seam_debug||!d.trace.control.active)return;
    const auto frame=d.trace.frame_number();if(p.seam_frame!=frame){p.seam_frame=frame;p.seam_count=0;}
    if(p.seam_count>=160)return;++p.seam_count;
    DWORD cull=0,alpha=0,stage1=0;d.native()->GetRenderState(D3DRS_CULLMODE,&cull);d.native()->GetRenderState(D3DRS_ALPHATESTENABLE,&alpha);d.native()->GetTextureStageState(1,D3DTSS_COLOROP,&stage1);
    const unsigned stride=fvf==0x152?36:fvf==0x142?24:32,color_offset=fvf==0x152?24:12;std::string samples="[";unsigned count=0;
    auto vector=[](const std::array<float,3>& v){return "["+std::to_string(v[0])+","+std::to_string(v[1])+","+std::to_string(v[2])+"]";};
    for(size_t i=0;i<e.used.size()&&count<32;++i)if(e.used[i]){
        std::array<float,3> xyz{};std::memcpy(xyz.data(),e.original.data()+i*stride,12);uint32_t original=0,lit=0;
        std::memcpy(&original,e.original.data()+i*stride+color_offset,4);std::memcpy(&lit,(p.world?e.lit:e.original).data()+i*stride+color_offset,4);
        float uv[2]{};std::memcpy(uv,e.original.data()+i*stride+color_offset+4,8);
        if(count++)samples+=",";samples+="{\"index\":"+std::to_string(i+min)+",\"xyz\":"+vector(xyz)+",\"uv\":["+std::to_string(uv[0])+","+std::to_string(uv[1])+"],\"geometric_normal\":"+vector(e.geometric_normals[i])+",\"effective_normal\":"+vector(e.effective_normals[i])+",\"source_prelight\":"+std::to_string(original)+",\"effective_color\":"+std::to_string(lit)+"}";
    }
    debug_record(d,"{\"type\":\"atmosphere_seam_range\",\"frame\":"+std::to_string(frame)+",\"course\":"+quote(std::string(course))+",\"material\":"+quote(m?m->name:std::string("automatic_ground"))+
        ",\"texture_sha256\":"+quote(texture)+",\"admission\":"+quote(std::string(e.reason))+",\"category\":"+std::to_string(e.category)+",\"cull\":"+std::to_string(cull)+",\"alpha_test\":"+std::to_string(alpha)+",\"stage1_op\":"+std::to_string(stage1)+",\"fvf\":"+std::to_string(fvf)+",\"winding\":"+std::to_string(m?m->winding:-1)+
        ",\"vertex_generation\":"+std::to_string(vg)+",\"index_generation\":"+std::to_string(ig)+",\"min_index\":"+std::to_string(min)+",\"start_index\":"+std::to_string(start)+",\"triangles\":"+std::to_string(triangles)+",\"hinted_vertices\":"+std::to_string(e.hinted)+",\"duplicate_faces\":"+std::to_string(e.duplicate_faces)+",\"opposite_faces\":"+std::to_string(e.opposite_faces)+",\"world_lighting\":"+(p.world?"true":"false")+",\"samples\":"+samples+"]}");
}
inline void seam_native(Device8& d,atmosphere::Pilot& p,UINT min,UINT vertices,UINT start,UINT triangles,DWORD fvf,
                        bool noise,bool opaque,bool alpha,const atmosphere::SceneMaterial* material,const char* course,const std::string& texture,const char* why) {
    if(!p.seam_debug||!d.trace.control.active||p.pending.any()||(p.seam_frame==d.trace.frame_number()&&p.seam_count>=160))return;
    Geometry geometry_data;if(!geometry(d,p,min,vertices,start,triangles,geometry_data))return;
    atmosphere::ResolvedGeometry sample;sample.original=std::move(geometry_data.bytes);sample.index_bytes.resize(geometry_data.indices.size()*4);
    for(size_t i=0;i<geometry_data.indices.size();++i){const uint32_t index=geometry_data.indices[i]+min;std::memcpy(sample.index_bytes.data()+i*4,&index,4);}
    // Diagnostic reconstruction only. This temporary capability NEVER reaches
    // upload/admission; the native rejected range remains completely unchanged.
    atmosphere::SceneMaterial diagnostic;diagnostic.category=material&&material->category?material->category:2;diagnostic.flags=atmosphere::Noise|atmosphere::Plain;
    diagnostic.winding=material?material->winding:-1;
    if(atmosphere::light_geometry(sample,p.pending.stride,min,vertices,4,&diagnostic,noise,true,false,false,p.lighting)){
        sample.lit=sample.original;sample.accepted=false;sample.reason=why;sample.category=material?material->category:0;
        seam_sample(d,p,sample,material,course,texture,fvf,min,start,triangles,geometry_data.vertex_generation,geometry_data.index_generation);
    }
}
inline HRESULT universal_draw(Device8& d,atmosphere::Pilot& p,UINT min,UINT vertices,UINT start,UINT triangles,
                              DWORD fvf,bool noise,bool alpha_test,const char* course,uint64_t race,uint64_t owner,bool environment=false,
                              const std::array<float,16>* world=nullptr,bool blended=false) {
    auto& n=*d.native();auto& saved=p.pending;
    auto fail=[&](const char* why){if(!saved.any())saved.release();++p.resolver_skipped_draws;return reject(d,p,why);};
    const auto reloads=p.package_reloads;const bool selected=p.select_course(course);
    if(reloads!=p.package_reloads)session().write("{\"type\":\"atmosphere_course_package\",\"course\":"+quote(p.active_course)+",\"reloads\":"+std::to_string(p.package_reloads)+",\"ready\":"+(selected?"true":"false")+",\"reason\":"+quote(std::string(p.metadata.reason))+",\"normal_records\":"+std::to_string(p.normal_hints.records)+"}");
    if(!selected)return fail("course_package_missing_invalid_or_wrong_scope");
    p.metadata.load(p.metadata_path);p.normal_hints.load(p.normals_path);
    if(p.first_reason("normal_hints_status"))session().write("{\"type\":\"atmosphere_normal_hints\",\"reason\":"+quote(std::string(p.normal_hints.reason))+",\"records\":"+std::to_string(p.normal_hints.records)+"}");
    if(p.first_reason("resolver_metadata_status"))session().write("{\"type\":\"atmosphere_resolver_metadata\",\"ready\":"+std::string(p.metadata.ready?"true":"false")+
        ",\"reason\":"+quote(std::string(p.metadata.reason))+",\"materials\":"+std::to_string(p.metadata.size())+",\"payload_sha256\":"+quote(p.metadata.sha)+"}");
    if(!p.metadata.ready&&p.metadata.present)return fail("invalid_present_lighting_metadata");
    courseintegration::Ref<IDirect3DBaseTexture8> texture;if(FAILED(n.GetTexture(0,&texture.p))||!texture.p)return fail("resolver_texture_unavailable");
    const auto texture_pointer=reinterpret_cast<uintptr_t>(texture.p);const auto texture_generation=d.trace.resources.generation(texture_pointer);
    const auto texture_sha=material_sha(d,p,texture.p);if(texture_sha.empty())return fail("resolver_texture_identity_unavailable");
    bool opaque=false;for(const auto& c:p.material_cache)if(c.pointer==texture_pointer&&c.generation==texture_generation){opaque=c.opaque;break;}
    const auto* material=p.metadata.find(course,texture_sha);
    if(p.capture.stage||p.coverage.enabled){p.draw_texture=texture_sha;p.draw_material=material?material->name:"automatic_ground";p.draw_category=material?material->category:2;}
    // Static cutouts use the observed native coverage contract only. Never
    // turn blended/glass/environment passes into an opaque surface.
    // Blended plain course cutouts (SRCALPHA/INVSRCALPHA, no alpha test): only
    // an authored vegetation role or an alpha-tested static cutout role may be
    // relit; RGB only, so native alpha, blending and depth stay untouched.
    if(blended&&(!material||(material->flags&atmosphere::Deny)||!(material->flags&atmosphere::AlphaTest)||(material->category!=3&&material->category!=4)))return fail("resolver_blended_material_unproven");
    const bool coverage=alpha_test||blended;
    if(alpha_test&&material&&material->category==4&&
       (!groundintegration::render(d,n,D3DRS_ALPHAFUNC,D3DCMP_GREATER)||
        !groundintegration::render(d,n,D3DRS_ALPHAREF,128)))return fail("resolver_static_coverage_contract");
    uint64_t secondary_generation=0;courseintegration::Ref<IDirect3DBaseTexture8> environment_source;
    if(environment){
        // Opaque is a PASS property here: diffuse alpha is a gloss mask in
        // this certified combine. Requiring all texture alpha=255 incorrectly
        // excludes metal fences. The native coverage/blend contract is retained.
        // The game also assigns a reflection pass to materials whose source
        // shader binding is plain (TurkeyS1 tyre stacks, FranceW f_conc). A
        // static plain role is enough when the live secondary is a certified
        // static environment texture (checked below); no Deny material passes.
        if(!material||(material->flags&atmosphere::Deny)||!(material->flags&(atmosphere::Environment|atmosphere::Plain))||material->category!=4||(alpha_test&&!(material->flags&atmosphere::AlphaTest)))return fail("resolver_environment_primary_unproven");
        auto& secondary=environment_source;
        if(FAILED(n.GetTexture(1,&secondary.p))||!secondary.p)return fail("resolver_environment_secondary_missing");
        secondary_generation=d.trace.resources.generation(reinterpret_cast<uintptr_t>(secondary.p));
        const auto secondary_sha=material_sha(d,p,secondary.p);const auto* certificate=p.metadata.find(course,secondary_sha);
        if(!secondary_generation||!certificate||certificate->flags!=(atmosphere::Deny|atmosphere::EnvironmentTexture)||
           (certificate->name!="aluminium-tga"&&certificate->name!="whitepaint-tga"&&certificate->name!="silverpaint-tga"&&certificate->name!="glass-tga"&&certificate->name!="rubber-tga"))return fail("resolver_environment_secondary_unproven");
    }
    if(material&&(material->flags&atmosphere::Deny)){seam_native(d,p,min,vertices,start,triangles,fvf,noise,opaque,alpha_test,material,course,texture_sha,"native_material_excluded");return fail("resolver_excluded_material");}
    // Instanced draws need an explicit material role: automatic ground is
    // only ever proven for the static identity-world terrain batches.
    if(world&&!material){
        if(p.first_reason(("instanced_unknown_"+texture_sha).c_str()))session().write("{\"type\":\"atmosphere_instanced_material_unknown\",\"course\":"+quote(std::string(course))+
            ",\"texture_sha256\":"+quote(texture_sha)+",\"vertices\":"+std::to_string(vertices)+",\"triangles\":"+std::to_string(triangles)+",\"frame\":"+std::to_string(d.trace.frame_number())+"}");
        return fail("resolver_instanced_material_unknown");}
    if(world&&vertices>4096)return fail("resolver_instanced_range_too_large");
    if(!material&&(!p.auto_ground||!noise||!opaque||alpha_test)){seam_native(d,p,min,vertices,start,triangles,fvf,noise,opaque,alpha_test,material,course,texture_sha,"native_ambiguous_material");return fail("resolver_ambiguous_material");}
    if(!vertices||vertices>32768||!triangles||triangles>32768||FAILED(n.GetStreamSource(0,&saved.stream,&saved.stride))||!saved.stream||
       saved.stride!=(fvf==0x152?36u:fvf==0x142?24u:32u)||FAILED(n.GetIndices(&saved.indices,&saved.base))||!saved.indices)return fail("resolver_native_buffers");
    D3DVERTEXBUFFER_DESC vd{};D3DINDEXBUFFER_DESC id{};
    if(FAILED(saved.stream->GetDesc(&vd))||FAILED(saved.indices->GetDesc(&id)))return fail("resolver_buffer_description");
    const unsigned width=id.Format==D3DFMT_INDEX16?2:id.Format==D3DFMT_INDEX32?4:0;
    const uint64_t vo=(uint64_t(saved.base)+min)*saved.stride,vs=uint64_t(vertices)*saved.stride,io=uint64_t(start)*width,is=uint64_t(triangles)*3*width;
    if(!width||vo>vd.Size||vs>vd.Size-vo||io>id.Size||is>id.Size-io||(uint64_t(min)+vertices)*saved.stride>2*1024*1024)return fail("resolver_draw_bounds");
    const auto vg=d.trace.resources.generation(reinterpret_cast<uintptr_t>(saved.stream)),ig=d.trace.resources.generation(reinterpret_cast<uintptr_t>(saved.indices));
    if(!vg||!ig||!texture_generation)return fail("resolver_resource_generation");
    DWORD cull=0;if(!groundintegration::stage_value(d,n,0,D3DTSS_RESULTARG,cull)||cull!=D3DTA_CURRENT)return fail("resolver_special_result_arg");
    if(FAILED(n.GetRenderState(D3DRS_CULLMODE,&cull))||(cull!=D3DCULL_NONE&&cull!=D3DCULL_CW&&cull!=D3DCULL_CCW))return fail("resolver_unknown_cull");
    if(!material&&cull!=D3DCULL_CCW)return fail("resolver_automatic_ground_front_face_unproven");
    if(!groundintegration::render(d,n,D3DRS_VERTEXBLEND,D3DVBF_DISABLE)||!groundintegration::render(d,n,D3DRS_INDEXEDVERTEXBLENDENABLE,FALSE))return fail("resolver_vertex_blending_excluded");
    const atmosphere::ResolverKey key{vg,ig,texture_generation,vo,vs,io,is,saved.stride,min,uint64_t(noise)|(uint64_t(alpha_test)<<1)|(uint64_t(cull)<<2)|(uint64_t(environment)<<8)|(uint64_t(blended)<<9),race,owner};
    auto& resolver=p.resolver;auto found=resolver.entries.find(key);bool fresh=found==resolver.entries.end();
    if(fresh&&!resolver.room(size_t(vs*4+is)))return fail("resolver_cache_capacity_native_fallback");
    // Existing proxy provenance, not a READONLY GPU Lock. A missing, poisoned,
    // partial or stale mirror never establishes geometry authority.
    auto vm=d.open_buffer_mirror(saved.stream,BufferKind::Vertex,vg,vd.Size,vd.Usage,vd.Pool);
    auto im=d.open_buffer_mirror(saved.indices,BufferKind::Index,ig,id.Size,id.Usage,id.Pool);
    if(!vm||!im||vm==im)return fail("resolver_cpu_mirrors_unavailable");
    std::vector<uint8_t> current_v,current_i;uint64_t vr=0,ir=0;bool unchanged=false;
    {
        std::scoped_lock locks(vm->mutex,im->mutex);
        auto covered=[](const BufferMirror& m,uint64_t begin,uint64_t bytes){if(!m.available||m.poisoned||!m.revision||begin>m.bytes||bytes>m.bytes-begin)return false;
            for(const auto& r:m.initialized)if(begin>=r.begin&&begin+bytes<=r.end)return true;return false;};
        if(!covered(*vm,vo,vs)||!covered(*im,io,is))return fail("resolver_incomplete_or_poisoned_range");
        vr=vm->revision;ir=im->revision;
        if(!fresh){auto& e=found->second;
            bool compared=false;unchanged=e.same_source(vm->data.data()+vo,size_t(vs),im->data.data()+io,size_t(is),vr,ir,compared);
            if(compared)++resolver.content_checks;
            if(unchanged){e.vertex_revision=vr;e.index_revision=ir;}
        }
        if(!unchanged){current_v.assign(vm->data.begin()+size_t(vo),vm->data.begin()+size_t(vo+vs));current_i.assign(im->data.begin()+size_t(io),im->data.begin()+size_t(io+is));}
    }
    if(fresh){++resolver.misses;found=resolver.entries.emplace(key,atmosphere::ResolvedGeometry{}).first;}
    else if(unchanged)++resolver.hits;else ++resolver.rebuilds;
    auto& entry=found->second;entry.last_frame=d.trace.frame_number();
    // Same source range under another instance matrix: relight the cached
    // original (bounded by the 4096-vertex instanced limit), no mirror re-read.
    const bool relight=!unchanged||!entry.lit_for(world);
    if(unchanged&&relight)++resolver.world_relights;
    if(!unchanged&&(resolver.bytes-entry.storage()>resolver.max_bytes||vs*4+is>resolver.max_bytes-(resolver.bytes-entry.storage())))return fail("resolver_cache_growth_native_fallback");
    if(relight){resolver.bytes-=entry.storage();if(!unchanged){entry.original=std::move(current_v);entry.index_bytes=std::move(current_i);entry.vertex_revision=vr;entry.index_revision=ir;}
        atmosphere::light_geometry(entry,saved.stride,min,vertices,width,material,noise,atmosphere::source_opaque_pass(material,opaque,false,coverage),coverage,p.auto_ground,p.lighting,&p.normal_hints,course,texture_sha,environment,world);resolver.bytes+=entry.storage();}
    if(!entry.accepted){++resolver.skipped;return fail(entry.reason);}
    if(p.lighting.fog_enabled&&FAILED(n.GetRenderState(D3DRS_FOGCOLOR,&saved.fog)))return fail("resolver_fog_capture_failed");
    if(environment&&p.world&&p.lighting.active()){
        const auto factor=atmosphere::world_environment_factor(p.lighting);
        if(factor!=0xffffffffu){auto* copy=environment_copy(d,p,environment_source.p,secondary_generation,factor);if(!copy)return fail("resolver_environment_copy_unavailable");
            saved.environment=environment_source.p;environment_source.p=nullptr;saved.environment_changed=true;
            const auto hr=n.SetTexture(1,copy);notify(d,61,pack(1,copy),hr);if(FAILED(hr))return repair(d);
            if(p.first_reason("static_environment_energy")||d.trace.control.active)session().write("{\"type\":\"atmosphere_static_environment\",\"factor\":"+std::to_string(factor)+",\"builds\":"+std::to_string(p.environment_builds)+",\"hits\":"+std::to_string(p.environment_hits)+",\"alpha_uv_unchanged\":true}");
        }
    }
    seam_sample(d,p,entry,material,course,texture_sha,fvf,min,start,triangles,vg,ig);
    auto hr=upload(d,p,min,vertices,p.world?entry.lit:entry.original);if(FAILED(hr)){if(saved.any())return repair(d);return fail("resolver_private_upload_failed");}
    DWORD effective_fog=saved.fog;
    if(p.lighting.fog_enabled){saved.fog_changed=true;effective_fog=atmosphere::scene_fog(saved.fog,p.lighting);hr=n.SetRenderState(D3DRS_FOGCOLOR,effective_fog);notify(d,50,pack(D3DRS_FOGCOLOR,effective_fog),hr);}
    if(FAILED(hr))return repair(d);
    if(p.capture.stage||p.coverage.enabled){p.draw_resolved=true;p.draw_lit=p.world;p.draw_reason=entry.reason;}
    ++resolver.accepted;++p.resolved_draws;++p.world_draws;++p.category_draws[entry.category];p.category_vertices[entry.category]+=entry.changed;
    if(p.first_reason(("resolver_material_"+texture_sha).c_str()))session().write("{\"type\":\"atmosphere_resolver_draw\",\"course\":"+quote(std::string(course))+
        ",\"material\":"+quote(material?material->name:std::string("automatic_ground"))+",\"reason\":"+quote(std::string(entry.reason))+",\"category\":"+std::to_string(entry.category)+
        ",\"texture_sha256\":"+quote(texture_sha)+",\"vertex_generation\":"+std::to_string(vg)+",\"index_generation\":"+std::to_string(ig)+
        ",\"vertex_revision\":"+std::to_string(vr)+",\"index_revision\":"+std::to_string(ir)+",\"geometry_hash_required\":false,\"normal_source\":"+quote(std::string(environment?"current_authored_vertex_normal":"authored_spatial_or_geometric_fallback"))+",\"shared_buffer_mutated\":false,\"hinted_vertices\":"+std::to_string(entry.hinted)+",\"changed_vertices\":"+std::to_string(p.world?entry.changed:0)+
        ",\"original_fog\":"+std::to_string(saved.fog)+",\"effective_fog\":"+std::to_string(effective_fog)+",\"frame\":"+std::to_string(d.trace.frame_number())+",\"race_generation\":"+std::to_string(race)+",\"owner_lifetime\":"+std::to_string(owner)+"}");
    return S_OK;
}
inline HRESULT begin(Device8& d,D3DPRIMITIVETYPE type,UINT min,UINT vertices,UINT start,UINT count,uintptr_t pc,const DrawClassification* classification=nullptr) noexcept {
    auto* p=pilot(d);if(!p||!p->enabled()||(!p->custom()&&!p->world_route()&&!p->light_probe&&!p->sun_disk&&!p->sun_halo&&!p->sun_flare&&p->sun_style.vignette<=0)||!count||type!=D3DPT_TRIANGLELIST||
        pc!=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr))+groundintegration::COURSE_DRAW_RETURN_RVA||
        !d.trace.scene_active||d.trace.shadow.recording||d.trace.effective_shadow.recording||GetCurrentThreadId()!=d.trace.render_thread_id())return S_OK;
    if(!p->pending.any())p->poll_live(d.trace.frame_number());
    if(p->coverage.pending)p->coverage.reached=true;
    struct Timing {atmosphere::Pilot& p;LARGE_INTEGER start{};Timing(atmosphere::Pilot& x):p(x){QueryPerformanceCounter(&start);}~Timing(){LARGE_INTEGER end{};QueryPerformanceCounter(&end);p.cpu_ticks+=end.QuadPart-start.QuadPart;++p.cpu_calls;}} timer(*p);
    try {
        CaptureDraw capture_draw(d,*p,min,vertices,start,count);
        bool single=false;const auto cert=courseintegration::certificate(d,single);
        if(!single||!cert.valid){
            // Coverage ledger: name the game phase so uncertified frames can be
            // targeted (replay, attract, countdown, finish...). Diagnostic only.
            if(p->coverage.enabled)try{static thread_local uint64_t phase_frame=UINT64_MAX;static thread_local std::string phase;
                if(phase_frame!=d.trace.frame_number()){phase_frame=d.trace.frame_number();const auto hud=ps2port::ps2_race_hud_context();
                    phase=!hud.valid?std::string("hud:")+(hud.reason?hud.reason:"invalid"):
                        std::string(hud.replay?"replay":hud.attract?"attract":hud.startup_countdown?"countdown":hud.paused?"paused":"race")+
                        (!single?":cameras_not_single":std::string(":")+(cert.reason?cert.reason:"invalid"));}
                reject(d,*p,"single_camera_race_certificate_missing");p->draw_reason="certificate_missing:"+phase;return S_OK;}catch(...){}
            return reject(d,*p,"single_camera_race_certificate_missing");}
        auto& n=*d.native();courseintegration::Ref<IDirect3DSurface8> target,back;
        if(FAILED(n.GetRenderTarget(&target.p))||FAILED(n.GetBackBuffer(0,D3DBACKBUFFER_TYPE_MONO,&back.p))||!courseintegration::same_identity(target.p,back.p))return reject(d,*p,"native_target_not_backbuffer");
        DWORD fvf=0,ps=1;if(FAILED(n.GetVertexShader(&fvf))||FAILED(n.GetPixelShader(&ps))||ps||!groundintegration::render(d,n,D3DRS_LIGHTING,FALSE))return reject(d,*p,"fixed_function_shader_or_lighting_mismatch");
        auto& saved=p->pending;if(saved.any())return D3DERR_DEVICELOST;
        auto fail=[&](const char* reason){if(!saved.any())saved.release();return reject(d,*p,reason);};
        if(fvf==0x102&&p->custom()&&groundintegration::render(d,n,D3DRS_FOGENABLE,FALSE)){
            courseintegration::Ref<IDirect3DBaseTexture8> texture;if(FAILED(n.GetTexture(0,&texture.p))||!texture.p)return S_OK;
            const auto pointer=reinterpret_cast<uintptr_t>(texture.p);const auto serial=d.trace.resources.generation(pointer);
            const atmosphere::Pilot::SkyCache* identity=nullptr;
            for(const auto& c:p->sky_cache)if(c.pointer==pointer&&c.generation==serial&&c.preset==int(p->custom_base)&&c.layer>=0){identity=&c;break;}
            if(!identity||!p->load(n))return S_OK;
            if((identity->layer==0&&p->sky_u_scale!=1)||p->sky_projection){Geometry g;if(!geometry(d,*p,min,vertices,start,count,g)||saved.stride!=20)return fail("custom_sky_source_range_unavailable");
                std::array<float,16> w{},view{};if(p->sky_projection&&(FAILED(n.GetTransform(D3DTS_WORLD,reinterpret_cast<D3DMATRIX*>(w.data())))||FAILED(n.GetTransform(D3DTS_VIEW,reinterpret_cast<D3DMATRIX*>(view.data())))))return fail("custom_sky_view_unavailable");
                for(unsigned i=0;i<vertices;++i){auto* vertex=g.bytes.data()+i*20;float u=0,v=0;std::memcpy(&u,vertex+12,4);std::memcpy(&v,vertex+16,4);if(identity->layer==0)u*=p->sky_u_scale;
                    if(p->sky_projection){std::array<float,3> position{};std::memcpy(position.data(),vertex,12);if(!atmosphere::sky_panorama_v(w,view,position,v,v))return fail("custom_sky_nonrigid_projection_rejected");}
                    std::memcpy(vertex+12,&u,4);std::memcpy(vertex+16,&v,4);}
                const auto hr=upload(d,*p,min,vertices,g.bytes);if(FAILED(hr)){if(saved.any())return repair(d);return fail("custom_sky_private_uv_upload_failed");}}
            constexpr D3DTEXTURESTAGESTATETYPE keys[]{D3DTSS_ADDRESSV,D3DTSS_ALPHAOP,D3DTSS_ALPHAARG1,D3DTSS_ALPHAARG2};
            auto sky_stage=[&](unsigned i,DWORD value){auto hr=n.GetTextureStageState(0,keys[i],&saved.sky_stage[i]);if(FAILED(hr))return hr;saved.sky_pending|=1u<<i;hr=n.SetTextureStageState(0,keys[i],value);notify(d,63,pack(0,keys[i],value),hr);return hr;};
            if(p->sky_projection&&FAILED(sky_stage(0,D3DTADDRESS_CLAMP)))return repair(d);
            if(identity->layer==1&&p->sky_haze!=1){if(FAILED(n.GetRenderState(D3DRS_TEXTUREFACTOR,&saved.sky_factor)))return repair(d);saved.sky_pending|=16;
                const DWORD factor=(DWORD(std::lround(p->sky_haze*255))<<24)|0xffffff;const auto hr=n.SetRenderState(D3DRS_TEXTUREFACTOR,factor);notify(d,50,pack(D3DRS_TEXTUREFACTOR,factor),hr);
                if(FAILED(hr)||FAILED(sky_stage(1,D3DTOP_MODULATE))||FAILED(sky_stage(2,D3DTA_TEXTURE))||FAILED(sky_stage(3,D3DTA_TFACTOR)))return repair(d);}
            if(FAILED(n.GetTexture(0,&saved.texture))){if(saved.any())return repair(d);return fail("custom_sky_texture_capture_failed");}saved.texture_changed=true;
            const auto hr=n.SetTexture(0,p->texture(identity->layer));notify(d,61,pack(0,p->texture(identity->layer)),hr);
            if(FAILED(hr))return repair(d);
            ++p->sky_draws;
            if(p->first_reason(("custom_sky_layer_"+std::to_string(identity->layer)).c_str()))session().write("{\"type\":\"atmosphere_custom_sky_draw\",\"layer\":"+std::to_string(identity->layer)+",\"source_native_sha256\":"+quote(identity->sha)+",\"custom_bgra_sha256\":"+quote(sha256_bytes(p->pixels(identity->layer).bgra.data(),p->pixels(identity->layer).bgra.size()*4))+",\"u_scale\":"+std::to_string(identity->layer==0?p->sky_u_scale:1)+",\"vertices\":"+std::to_string(vertices)+",\"triangles\":"+std::to_string(count)+",\"frame\":"+std::to_string(d.trace.frame_number())+",\"race_generation\":"+std::to_string(cert.race_generation)+"}");return S_OK;
        }
        bool water_applied=false;const auto water_status=pc_water_draw(d,*p,fvf,water_applied);if(FAILED(water_status)||water_applied)return water_status;
        {const char* course=cert.course_id.data();if(!_strnicmp(course,"RaceTest/",9))course+=9;
         const auto fall_status=pc_waterfall_draw(d,*p,fvf,course,water_applied);if(FAILED(fall_status)||water_applied)return fall_status;}
        const bool environment=p->universal&&fvf==0x152;
        const bool alpha_blend=groundintegration::render(d,n,D3DRS_ALPHABLENDENABLE,TRUE)&&groundintegration::render(d,n,D3DRS_SRCBLEND,D3DBLEND_SRCALPHA)&&groundintegration::render(d,n,D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA);
        const bool blended_plain=p->universal&&fvf==0x142&&alpha_blend&&groundintegration::render(d,n,D3DRS_ALPHATESTENABLE,FALSE)&&groundintegration::stage(d,n,1,D3DTSS_COLOROP,D3DTOP_DISABLE);
        if((!p->world_route()&&!p->light_probe)||(fvf!=0x142&&fvf!=0x242&&!environment)||(!groundintegration::render(d,n,D3DRS_ALPHABLENDENABLE,FALSE)&&
             !((environment||blended_plain)&&alpha_blend))||
            !groundintegration::render(d,n,D3DRS_ZENABLE,D3DZB_TRUE)||!groundintegration::render(d,n,D3DRS_ZWRITEENABLE,TRUE)||
            !groundintegration::render(d,n,D3DRS_BLENDOP,D3DBLENDOP_ADD)||!groundintegration::render(d,n,D3DRS_FOGENABLE,TRUE)||
            !groundintegration::stage(d,n,0,D3DTSS_COLOROP,D3DTOP_MODULATE)||!groundintegration::stage(d,n,0,D3DTSS_COLORARG1,D3DTA_TEXTURE)||
            !groundintegration::stage(d,n,0,D3DTSS_COLORARG2,D3DTA_DIFFUSE)||!groundintegration::stage(d,n,2,D3DTSS_COLOROP,D3DTOP_DISABLE))return reject(d,*p,"not_source_prelit_world_contract");
        if(p->universal&&classification&&(classification->semantic_source!=VehicleSemanticSource::None||strong_vehicle_proof(classification->transform)))return reject(d,*p,"resolver_known_vehicle_draw_excluded");
        capture_observe(d,*p);
        const bool noise=groundintegration::stage(d,n,1,D3DTSS_COLOROP,D3DTOP_MODULATE2X);
        if(noise){courseintegration::Ref<IDirect3DBaseTexture8> t;if(!groundintegration::stage(d,n,1,D3DTSS_COLORARG1,D3DTA_CURRENT)||!groundintegration::stage(d,n,1,D3DTSS_COLORARG2,D3DTA_TEXTURE)||FAILED(n.GetTexture(1,&t.p)))return reject(d,*p,"base_noise_stage_mismatch");
            const auto id=p->pc_noise_identity.identify(t.p,d.trace.resources.generation(reinterpret_cast<uintptr_t>(t.p)));if(!id.match)return reject(d,*p,id.reason);}
        else if(environment){
            if(!groundintegration::stage(d,n,1,D3DTSS_COLOROP,D3DTOP_MODULATEALPHA_ADDCOLOR)||
               !groundintegration::stage(d,n,1,D3DTSS_COLORARG1,D3DTA_CURRENT)||!groundintegration::stage(d,n,1,D3DTSS_COLORARG2,D3DTA_TEXTURE)||
               !groundintegration::stage(d,n,1,D3DTSS_TEXCOORDINDEX,D3DTSS_TCI_CAMERASPACENORMAL)||!groundintegration::stage(d,n,1,D3DTSS_TEXTURETRANSFORMFLAGS,D3DTTFF_COUNT2)||
               !groundintegration::stage(d,n,0,D3DTSS_ALPHAOP,D3DTOP_MODULATE)||!groundintegration::stage(d,n,0,D3DTSS_ALPHAARG1,D3DTA_TEXTURE)||
               !groundintegration::stage(d,n,0,D3DTSS_ALPHAARG2,D3DTA_DIFFUSE)||!groundintegration::stage(d,n,1,D3DTSS_ALPHAOP,D3DTOP_MODULATE)||
               !groundintegration::stage(d,n,1,D3DTSS_ALPHAARG1,D3DTA_CURRENT)||!groundintegration::stage(d,n,1,D3DTSS_ALPHAARG2,D3DTA_TEXTURE)||
               !groundintegration::stage(d,n,1,D3DTSS_RESULTARG,D3DTA_CURRENT))return reject(d,*p,"world_environment_stage_contract");
        }else if(!groundintegration::stage(d,n,1,D3DTSS_COLOROP,D3DTOP_DISABLE))return reject(d,*p,"world_special_secondary_stage");
        D3DMATRIX world{},identity{};identity._11=identity._22=identity._33=identity._44=1;
        if(FAILED(n.GetTransform(D3DTS_WORLD,&world)))return reject(d,*p,"source_world_transform_unavailable");
        const bool identity_world=!std::memcmp(&world,&identity,64);
        // Placed/instanced course props (checkpoint boards, signs) keep their
        // native matrix; only the universal resolver lights them, in world space.
        if(!identity_world&&!p->universal)return reject(d,*p,"source_static_course_world_not_identity");
        if(p->universal){const char* course=cert.course_id.data();if(!_strnicmp(course,"RaceTest/",9))course+=9;
            std::array<float,16> instance{};std::memcpy(instance.data(),&world,64);
            return universal_draw(d,*p,min,vertices,start,count,fvf,noise,groundintegration::render(d,n,D3DRS_ALPHATESTENABLE,TRUE),course,cert.race_generation,cert.owner_lifetime,environment,identity_world?nullptr:&instance,blended_plain&&!noise&&!environment);}
        if(!p->atlas.load(p->atlas_path))return reject(d,*p,p->atlas.reason);
        Geometry g;if(!geometry(d,*p,min,vertices,start,count,g))return fail("source_draw_vertex_or_index_range_unavailable");
        if(saved.stride!=(fvf==0x142?24u:32u))return fail("source_world_vertex_layout_mismatch");
        std::vector<BYTE> canonical;canonical.reserve(g.indices.size()*24);
        for(auto index:g.indices){const auto* v=g.bytes.data()+index*saved.stride;canonical.insert(canonical.end(),v,v+24);}
        const auto geometry_sha=sha256_bytes(canonical.data(),canonical.size());
        courseintegration::Ref<IDirect3DBaseTexture8> texture;if(FAILED(n.GetTexture(0,&texture.p)))return fail("source_diffuse_texture_missing");
        const auto texture_sha=material_sha(d,*p,texture.p);const char* course=cert.course_id.data();if(!_strnicmp(course,"RaceTest/",9))course+=9;
        const auto* record=p->atlas.find(geometry_sha,course,texture_sha);
        // Opt-in, bounded read-only evidence for differences between original
        // source records and the game's submitted triangle batches. Never use
        // this diagnostic to authorize an otherwise unknown material/draw.
        if(!record&&p->scene_diagnostics&&p->scene_diagnostic_count<16&&count<=512&&
            p->first_reason(("scene_sample_"+texture_sha).c_str())){
            ++p->scene_diagnostic_count;std::string hex;hex.reserve(canonical.size()*2);
            constexpr char digits[]="0123456789abcdef";
            for(auto byte:canonical){hex+=digits[byte>>4];hex+=digits[byte&15];}
            session().write("{\"type\":\"atmosphere_scene_source_sample\",\"course\":"+quote(std::string(course))+
                ",\"texture_sha256\":"+quote(texture_sha)+",\"geometry_sha256\":"+quote(geometry_sha)+
                ",\"corner_layout\":\"xyz_f32_bgra8_uv0_f32_le\",\"expanded_corners_hex\":"+quote(hex)+
                ",\"triangles\":"+std::to_string(count)+",\"vertices\":"+std::to_string(vertices)+
                ",\"frame\":"+std::to_string(d.trace.frame_number())+",\"race_generation\":"+std::to_string(cert.race_generation)+"}");
        }
        if(!record){if(p->first_reason("scene_first_unknown_identity"))session().write("{\"type\":\"atmosphere_scene_identity_rejected\",\"geometry_sha256\":"+quote(geometry_sha)+",\"texture_sha256\":"+quote(texture_sha)+",\"course\":"+quote(std::string(course))+",\"vertices\":"+std::to_string(vertices)+",\"triangles\":"+std::to_string(count)+"}");return fail("source_scene_draw_identity_unknown");}
        const bool alpha_test=groundintegration::render(d,n,D3DRS_ALPHATESTENABLE,TRUE);
        if(alpha_test&&record->category!=3)return fail("source_alpha_test_non_vegetation_excluded");
        if(record->normals.size()!=g.indices.size())return fail("source_normal_count_mismatch");
        const uint32_t color_offset=12;uint64_t changed=0;
        auto& colors=record->lighting_cache;
        if(!colors.matches(g.indices,vertices,p->lighting)){
            std::vector<uint32_t> original(vertices);
            for(unsigned i=0;i<vertices;++i)std::memcpy(&original[i],g.bytes.data()+i*saved.stride+color_offset,4);
            if(!colors.bake(record->normals,g.indices,original,p->lighting))return fail("source_normal_mapping_invalid");
        }
        float phase=0;
        if(p->light_probe){LARGE_INTEGER ticks{},frequency{};QueryPerformanceCounter(&ticks);QueryPerformanceFrequency(&frequency);
            if(frequency.QuadPart)phase=float(std::fmod(double(ticks.QuadPart)/frequency.QuadPart*.5,6.283185307179586));}
        for(unsigned i=0;i<vertices;++i){if(!colors.used[i])continue;auto* v=g.bytes.data()+i*saved.stride;DWORD original=0;std::memcpy(&original,v+color_offset,4);auto color=p->world?colors.colors[i]:original;
            if(p->light_probe){float xyz[3]{};std::memcpy(xyz,v,12);const auto light=atmosphere::point_light(xyz[0],xyz[1],xyz[2],p->source_x+std::sin(phase)*p->radius,p->source_y,p->source_z,p->radius);if(light>0)++p->light_vertices;color=atmosphere::tint(color,1,1,1,light);}
            if(color!=original)++changed;std::memcpy(v+color_offset,&color,4);}
        if(p->world&&p->lighting.fog_enabled&&FAILED(n.GetRenderState(D3DRS_FOGCOLOR,&saved.fog)))return fail("source_fog_capture_failed");
        auto hr=upload(d,*p,min,vertices,g.bytes);if(FAILED(hr)){if(saved.any())return repair(d);return fail("source_private_vertex_upload_failed");}
        if(p->world&&p->lighting.fog_enabled){saved.fog_changed=true;const auto fog=atmosphere::scene_fog(saved.fog,p->lighting);hr=n.SetRenderState(D3DRS_FOGCOLOR,fog);notify(d,50,pack(D3DRS_FOGCOLOR,fog),hr);}
        if(FAILED(hr))return repair(d);
        ++p->world_draws;++p->category_draws[record->category];p->category_vertices[record->category]+=changed;
        if(p->first_reason(("scene_"+record->course+record->material).c_str()))session().write("{\"type\":\"atmosphere_scene_draw\",\"course\":"+quote(record->course)+",\"material\":"+quote(record->material)+",\"category\":"+std::to_string(record->category)+",\"geometry_sha256\":"+quote(geometry_sha)+",\"texture_sha256\":"+quote(texture_sha)+",\"source_normals\":true,\"shared_buffer_mutated\":false,\"changed_vertices\":"+std::to_string(changed)+",\"frame\":"+std::to_string(d.trace.frame_number())+",\"race_generation\":"+std::to_string(cert.race_generation)+",\"owner_lifetime\":"+std::to_string(cert.owner_lifetime)+"}");
        return S_OK;
    }catch(...){if(!p->pending.any())p->pending.release();return repair(d);}
}
} // namespace gfx2::atmosphereintegration
