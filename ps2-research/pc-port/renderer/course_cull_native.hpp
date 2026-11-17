#pragma once
// RCX-PERF1 course culling, device glue (pure core: course_cull.hpp).
// observe() runs first in the DrawIndexedPrimitive chain (from
// atmosphereintegration::observe) and decides; atmosphereintegration::begin
// skips a decided draw (no relight, no ring upload) and the ground handler
// consumes it (groundintegration::draw returns handled S_OK without drawing).
// Gate: identity-WORLD draw from the native course loop, valid race
// certificate, course listed in PS2Port.ini [CourseCull] Courses.
#include "course_cull.hpp"
#include "course_objects_native_integration.hpp"
#include "ground_detail_native.hpp"

namespace gfx2::coursecull {

inline void flush_stats(Device8& d,State& s,uint64_t frame) noexcept {
    if(!s.stats||frame<s.stats_frame+600)return;
    if(s.considered)try{session().write("{\"type\":\"course_cull_stats\",\"frame\":"+std::to_string(frame)+",\"frames\":"+std::to_string(frame-s.stats_frame)+
        ",\"course\":"+quote(s.gate_course)+",\"enabled\":"+std::string(s.enabled?"true":"false")+
        ",\"considered_draws\":"+std::to_string(s.considered)+",\"culled_draws\":"+std::to_string(s.culled)+
        ",\"kept_vertices\":"+std::to_string(s.kept_vertices)+",\"culled_vertices\":"+std::to_string(s.culled_vertices)+
        ",\"boxes\":"+std::to_string(s.boxes.size())+",\"box_builds\":"+std::to_string(s.box_builds)+",\"box_failures\":"+std::to_string(s.box_failures)+
        ",\"revision_rebuilds\":"+std::to_string(s.revision_rebuilds)+",\"znear\":"+std::to_string(s.frust.znear)+",\"zfar\":"+std::to_string(s.frust.zfar)+
        ",\"margin\":"+std::to_string(s.margin)+",\"max_distance\":"+std::to_string(s.max_distance)+
        ",\"fog_cull\":"+std::string(s.fog_cull?"true":"false")+",\"fog_end\":"+std::to_string(s.fog_end)+",\"fog_culled_draws\":"+std::to_string(s.fog_culled)+"}");}catch(...){}
    s.stats_frame=frame;s.considered=s.culled=s.kept_vertices=s.culled_vertices=s.box_builds=s.box_failures=s.revision_rebuilds=s.fog_culled=0;
}

inline void observe(Device8& d,D3DPRIMITIVETYPE type,UINT min,UINT vertices,UINT start,UINT count,uintptr_t pc) noexcept {
    auto& s=state();s.pending=false;s.load();
    if(!count||type!=D3DPT_TRIANGLELIST||!d.trace.scene_active||d.trace.shadow.recording||d.trace.effective_shadow.recording||
       GetCurrentThreadId()!=d.trace.render_thread_id()||
       pc!=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr))+groundintegration::COURSE_DRAW_RETURN_RVA)return;
    try {
        const uint64_t frame=d.trace.frame_number();
        if(frame!=s.frustum_frame){s.frustum_frame=frame;
            // Ctrl+Alt+K: A/B switch for the owner (logged).
            DWORD pid=0;GetWindowThreadProcessId(GetForegroundWindow(),&pid);
            const bool down=pid==GetCurrentProcessId()&&(GetAsyncKeyState(VK_CONTROL)&0x8000)&&(GetAsyncKeyState(VK_MENU)&0x8000)&&(GetAsyncKeyState('K')&0x8000);
            if(down&&!s.toggle_down){s.enabled=!s.enabled;session().write("{\"type\":\"course_cull_toggle\",\"enabled\":"+std::string(s.enabled?"true":"false")+",\"frame\":"+std::to_string(frame)+"}");}
            s.toggle_down=down;flush_stats(d,s,frame);}
        if(!s.enabled||!groundintegration::course_world(d))return;
        bool single=false;const auto cert=courseintegration::certificate(d,single);
        if(!cert.valid)return;
        if(s.gate_race!=cert.race_generation){s.gate_race=cert.race_generation;s.gate_course=cert.course_id.data();
            s.gate=course_listed(s.courses,cert.course_id.data());s.boxes.clear();
            session().write("{\"type\":\"course_cull_gate\",\"course\":"+quote(s.gate_course)+",\"active\":"+std::string(s.gate?"true":"false")+
                ",\"courses\":"+quote(s.courses)+",\"race_generation\":"+std::to_string(cert.race_generation)+"}");}
        if(!s.gate)return;
        const auto& view=d.trace.effective_shadow.matrices[D3DTS_VIEW];const auto& projection=d.trace.effective_shadow.matrices[D3DTS_PROJECTION];
        if(!view.known||!projection.known)return;
        s.frust=frustum(view.value.m,projection.value.m);if(!s.frust.valid)return;
        ++s.considered;
        auto& n=*d.native();IDirect3DVertexBuffer8* stream=nullptr;UINT stride=0;IDirect3DIndexBuffer8* indices=nullptr;UINT base=0;
        if(FAILED(n.GetStreamSource(0,&stream,&stride))||!stream){if(stream)stream->Release();return;}
        const HRESULT got_indices=n.GetIndices(&indices,&base);if(indices)indices->Release();
        const uintptr_t raw=reinterpret_cast<uintptr_t>(stream);stream->Release();
        if(FAILED(got_indices)||stride<12||stride>256)return;
        const uint64_t generation=d.trace.resources.generation(raw);if(!generation)return;
        const Key key{raw,generation,uint32_t(base+min),uint32_t(vertices),uint32_t(stride)};
        // A 12-byte read returns the shadow revision: a rewritten buffer rebuilds its box.
        std::vector<BYTE> probe;uint64_t revision=0;
        if(!d.copy_buffer_shadow(reinterpret_cast<void*>(raw),BufferKind::Vertex,generation,uint64_t(key.first)*stride,12,probe,revision))return;
        auto it=s.boxes.find(key);
        if(it==s.boxes.end()||it->second.revision!=revision){
            if(it!=s.boxes.end())++s.revision_rebuilds;
            std::vector<BYTE> bytes;uint64_t full=0;
            if(!d.copy_buffer_shadow(reinterpret_cast<void*>(raw),BufferKind::Vertex,generation,uint64_t(key.first)*stride,size_t(vertices)*stride,bytes,full)){++s.box_failures;return;}
            Entry e{box(bytes.data(),vertices,stride),full};if(!e.box.valid){++s.box_failures;return;}
            ++s.box_builds;it=s.boxes.insert_or_assign(key,e).first;}
        // Linear vertex fog (the course loop state): FOGEND is an eye depth.
        float fog_end=0;
        if(s.fog_cull){const auto& rs=d.trace.effective_shadow.rs;
            const auto& on=rs[D3DRS_FOGENABLE];const auto& vertex=rs[D3DRS_FOGVERTEXMODE];const auto& table=rs[D3DRS_FOGTABLEMODE];const auto& end=rs[D3DRS_FOGEND];
            if(on.known&&on.value&&vertex.known&&table.known&&end.known&&
               ((vertex.value==D3DFOG_LINEAR&&table.value==D3DFOG_NONE)||table.value==D3DFOG_LINEAR)){
                std::memcpy(&fog_end,&end.value,4);if(!std::isfinite(fog_end)||fog_end<50.f)fog_end=0;}}
        s.fog_end=fog_end;
        const bool fogged=beyond_fog(s.frust,it->second.box,fog_end,s.margin);
        if(fogged||outside(s.frust,it->second.box,s.margin,s.max_distance)){
            if(fogged)++s.fog_culled;
            s.pending=true;s.pending_frame=frame;s.pending_args[0]=min;s.pending_args[1]=vertices;s.pending_args[2]=start;s.pending_args[3]=count;
            ++s.culled;s.culled_vertices+=vertices;}
        else s.kept_vertices+=vertices;
    }catch(...){s.pending=false;}
}

} // namespace gfx2::coursecull
