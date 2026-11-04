#pragma once
#include "ps2_race_certificate.hpp"
// COLLISION-DEBUG1 native side: the course collision overlay at the typed pre-UI boundary (after the course, water,
// spline objects and birds, before the HUD), single camera only. World pass = verified gameplay VIEW/PROJECTION of this
// frame, identity WORLD, the fixed CourseObjectTransaction (white 1x1 texture x vertex colour, source-alpha blend, no
// cull, no lighting, no fog); depth test LESSEQUAL (ALWAYS for X-RAY), depth write only in SOLID. Overlay vertices are
// pulled toward the camera by CollisionDebugDepthPull of their distance so coplanar render ground does not z-fight.
// Legend = screen-space quads with an orthographic pixel projection. Hotkey polled here (race frames only).
#include "ps2_birds_native_integration.hpp"
#include "collision_debug_pilot.hpp"
#include <algorithm>
#include <cstdio>
#include <string>
#include <vector>

namespace gfx2::collisionintegration {
inline ps2port::CollisionDebugPilot* pilot(Device8& d) noexcept {return d.ps2_port()?d.ps2_port()->collision_debug():nullptr;}

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
    auto& proof=p->proof;
    if(is_view)proof.view_site=false;
    if(is_projection)proof.projection_site=false;
    if(FAILED(hr)||!d.trace.scene_active||GetCurrentThreadId()!=d.trace.render_thread_id())return;
    const auto frame=d.trace.frame_number();const auto reset=d.ps2_port()->reset_generation();
    if(proof.frame!=frame||proof.device!=d.trace.device_id()||proof.reset!=reset){proof.clear();proof.frame=frame;proof.device=d.trace.device_id();proof.reset=reset;}
    const auto& tracked=d.trace.effective_shadow.matrices[type];D3DMATRIX native{};
    if(!tracked.known||FAILED(d.native()->GetTransform(type,&native))||std::memcmp(&native,&tracked.value,64)||!courseintegration::finite_matrix(native))return;
    if(is_view){proof.view=native;proof.view_site=true;}
    if(is_projection&&courseintegration::perspective(native)){proof.projection=native;proof.projection_site=true;}
}

inline std::string course_record(const ps2port::CollisionDebugPilot& p,const char* course,uint64_t race) {
    const auto& m=p.mesh();
    std::string s="{\"type\":\"collision_debug_course\",\"course\":"+quote(std::string(course))+",\"race_generation\":"+std::to_string(race)+
        ",\"status\":"+quote(p.course_reason())+",\"source\":"+quote(p.source())+",\"race_xml\":"+quote(p.race_xml())+",\"landscapes\":[";
    for(size_t i=0;i<p.landscapes().size();++i){const auto& l=p.landscapes()[i];
        s+=std::string(i?",":"")+"{\"dx_path\":"+quote(l.dx_path)+",\"status\":"+quote(l.status)+",\"source\":"+quote(l.source)+
           ",\"dx_sha256\":"+quote(l.sha)+",\"placed_by_matrix\":"+(l.identity?"false":"true")+",\"triangles\":"+std::to_string(l.triangles)+
           ",\"bsp\":"+(l.bsp?"true":"false")+",\"bsp_solid_cells\":"+std::to_string(l.solid_cells)+",\"bsp_object_faces\":"+std::to_string(l.object_faces)+
           ",\"bsp_object_codes\":"+std::to_string(l.object_codes)+"}";}
    s+="],\"data_sma\":"+std::string(p.archive_open()?"true":"false")+",\"load_ms\":"+std::to_string(p.load_ms())+",\"triangles\":"+std::to_string(m.triangles())+",\"vertices\":"+std::to_string(m.positions.size()/3)+
        ",\"edges\":"+std::to_string(m.edges.size()/3)+",\"cell\":"+std::to_string(m.cell)+",\"grid\":["+std::to_string(m.dim0)+","+std::to_string(m.dim1)+"],\"materials\":[";
    for(size_t i=0;i<m.materials.size();++i)s+=std::string(i?",":"")+"{\"surface\":"+quote(colldebug::surface_name(m.material_surface[i]))+",\"name\":"+quote(m.materials[i])+"}";
    return s+"]}";
}

// One fixed-transaction pass of an UP vertex list (triangles or lines), chunked.
template<class Writer>
inline HRESULT draw_pass(Device8& d,ps2port::CollisionDebugPilot& p,D3DPRIMITIVETYPE type,const std::vector<colldebug::Vertex>& v,
                         const D3DMATRIX& view,const D3DMATRIX& projection,const ps2port::CourseObjectMaterialState& material,
                         Writer& writer,UINT& primitives) noexcept {
    const UINT per=type==D3DPT_LINELIST?2u:3u;if(v.size()<per)return S_OK;
    auto& n=*d.native();
    HRESULT hr=p.transaction.capture(n);if(FAILED(hr))return hr;
    hr=p.transaction.apply(n,p.texture(),view,projection,writer,material);
    if(SUCCEEDED(hr)){
        constexpr UINT kChunk=12000;const UINT total=static_cast<UINT>(v.size()/per);
        p.transaction.mark_up_stream_changed();
        for(UINT first=0;first<total&&SUCCEEDED(hr);first+=kChunk){
            const UINT count=std::min(kChunk,total-first);
            hr=n.DrawPrimitiveUP(type,count,v.data()+size_t(first)*per,sizeof(colldebug::Vertex));
            if(SUCCEEDED(hr))primitives+=count;
        }
    }
    const HRESULT restored=p.transaction.has_pending()?p.transaction.restore(n,writer):S_OK;
    if(FAILED(restored)){p.disable("native_collision_state_restore_failed");return restored;}
    p.transaction.release();
    if(FAILED(hr))p.disable("native_collision_draw_failed");
    return S_OK;
}

inline HRESULT before_ui(Device8& d,bool ui_callsite) noexcept {
    ps2port::perf::Timer perf_timer(ps2port::perf::UiCollision);
    auto* p=pilot(d);if(!p||!p->active()||!ui_callsite)return S_OK;
    if(GetCurrentThreadId()!=d.trace.render_thread_id()||!d.trace.scene_active||d.trace.shadow.recording||d.trace.effective_shadow.recording)return S_OK;
    const uint64_t frame=d.trace.frame_number(),reset=d.ps2_port()->reset_generation();
    if(!p->consume_boundary(frame,reset))return S_OK;
    if(p->poll_hotkey()||p->take_mode_log())try{session().write("{\"type\":\"collision_debug_mode\",\"frame\":"+std::to_string(frame)+
        ",\"mode\":"+std::to_string(static_cast<uint32_t>(p->mode()))+",\"name\":"+quote(colldebug::mode_name(p->mode()))+"}");}catch(...){}
    if(p->mode()==colldebug::Mode::Off&&!p->markers_mode()&&!p->cars_mode())return S_OK;
    auto gate=[&](const char* reason){if(p->claim_log(false))try{session().write("{\"type\":\"collision_debug_gate\",\"reason\":"+quote(reason)+
        ",\"frame\":"+std::to_string(frame)+"}");}catch(...){}return S_OK;};
    bool single=false;const auto cert=courseintegration::certificate(d,single);
    if(!single||!cert.valid)return gate(single?"race_certificate_invalid":"no_single_camera_race");
    const bool selected=p->select_course(cert.course_id.data(),cert.race_generation);
    if(p->take_course_log())try{session().write(course_record(*p,cert.course_id.data(),cert.race_generation));}catch(...){}
    if(!selected)return S_OK;
    auto& proof=p->proof;auto& n=*d.native();
    if(proof.frame!=frame||proof.device!=d.trace.device_id()||proof.reset!=reset||!proof.view_site||!proof.projection_site)return gate("gameplay_view_projection_not_seen_this_frame");
    courseintegration::Ref<IDirect3DSurface8> target,back,depth;D3DVIEWPORT8 viewport{};D3DSURFACE_DESC desc{};
    if(FAILED(n.GetRenderTarget(&target.p))||FAILED(n.GetBackBuffer(0,D3DBACKBUFFER_TYPE_MONO,&back.p))||!courseintegration::same_identity(target.p,back.p)||
       FAILED(n.GetDepthStencilSurface(&depth.p))||!depth.p||FAILED(n.GetViewport(&viewport))||FAILED(target.p->GetDesc(&desc))||
       viewport.X||viewport.Y||viewport.Width!=desc.Width||viewport.Height!=desc.Height)return gate("target_not_full_backbuffer_with_depth");
    if(!courseintegration::native_dependencies(n))return gate("native_dependency_states");
    ps2birds::Vec3 camera{},look{},up{};
    if(!ps2port::birds_camera(proof.view,camera,look,up))return gate("camera_not_orthonormal");
    const float cam[3]={camera[0],camera[1],camera[2]};
    try{colldebug::build_batch(p->mesh(),p->mode(),cam,p->settings(),p->batch);}catch(...){p->batch.clear();return gate("batch_build_failed");}
    const auto writer=[&](uint32_t slot,const Args& args,HRESULT hr) noexcept {courseintegration::after_setter(d,slot,args,hr);};
    auto& b=p->batch;UINT tris=0,lines=0,quads=0;HRESULT hr=S_OK;
    ps2port::CourseObjectMaterialState fill{static_cast<DWORD>(b.fill_depth_write?TRUE:FALSE),D3DTADDRESS_CLAMP,D3DTADDRESS_CLAMP,TRUE,FALSE,D3DCMP_LESSEQUAL};
    ps2port::CourseObjectMaterialState wire{FALSE,D3DTADDRESS_CLAMP,D3DTADDRESS_CLAMP,TRUE,FALSE,static_cast<DWORD>(b.lines_depth_test?D3DCMP_LESSEQUAL:D3DCMP_ALWAYS)};
    // Vehicle collision hulls (with every collision mode) and race markers (own key), drawn as lines.
    std::vector<colldebug::Vertex> hull_lines,marker_lines;std::vector<uint32_t> marker_counts;
    // Pose = the render instance world matrix (instance+0x44, the matrix 0x561a40 sets as D3DTS_WORLD for the body and
    // each wheel), read after the car draws of this frame: the hull sits exactly on the drawn body.
    uint32_t hulls_drawn=0,hulls_participants=0,wheels_drawn=0;const char* hull_reason="off";
    ps2port::HudLiveMemory hull_memory;
    if(p->cars_mode())try{
        const auto table=p->participants.resolve(hull_memory,0x400000,cert,1);
        hull_reason=table.reason;hulls_participants=table.count;
        for(uint32_t i=0;i<table.count&&i<table.cars.size();++i){
            const auto& car=table.cars[i];if(!car.valid)continue;
            const std::string folder(car.folder.data());float m16[16];colldebug::VehiclePose pose;
            if(const auto* h=p->hull(folder))
                if(hull_memory.read(car.instance+0x44,m16,64)&&colldebug::pose_from_world(m16,pose)){
                    colldebug::hull_lines(*h,pose,colldebug::with_alpha(car.player_type==1?colldebug::kHullLocalRgb:colldebug::kHullRgb,0xf0),hull_lines);++hulls_drawn;}
            if(const auto* w=p->wheel(folder))
                for(unsigned k=0;k<4;++k)if((car.wheel_mask&(1u<<k))&&hull_memory.read(car.wheel_instance[k]+0x44,m16,64)&&colldebug::pose_from_world(m16,pose)){
                    colldebug::cylinder_lines(*w,pose,colldebug::with_alpha(colldebug::kWheelRgb,0xf0),hull_lines);++wheels_drawn;}
        }
    }catch(...){hull_lines.clear();}
    if(p->markers_mode())try{colldebug::marker_lines(p->markers(),cam,std::max(200.f,p->settings().range*2.f),marker_lines,marker_counts);}catch(...){marker_lines.clear();}
    if(p->take_hull_log())try{session().write("{\"type\":\"collision_debug_hulls\",\"participants\":"+std::to_string(hulls_participants)+",\"drawn\":"+std::to_string(hulls_drawn)+
        ",\"wheels\":"+std::to_string(wheels_drawn)+",\"loaded\":"+std::to_string(p->hulls_loaded())+",\"failed\":"+std::to_string(p->hulls_failed())+",\"missing_car_dx\":"+quote(p->missing_cars())+",\"game_roots\":"+quote(p->roots_text())+",\"reason\":"+quote(hull_reason)+"}");}catch(...){}
    hr=draw_pass(d,*p,D3DPT_TRIANGLELIST,b.fill,proof.view,proof.projection,fill,writer,tris);
    if(SUCCEEDED(hr)&&p->active())hr=draw_pass(d,*p,D3DPT_LINELIST,b.lines,proof.view,proof.projection,wire,writer,lines);
    // Hulls through the car body (depth ALWAYS), markers depth tested unless the marker X-RAY state is selected.
    const ps2port::CourseObjectMaterialState over{FALSE,D3DTADDRESS_CLAMP,D3DTADDRESS_CLAMP,TRUE,FALSE,D3DCMP_ALWAYS};
    const ps2port::CourseObjectMaterialState tested{FALSE,D3DTADDRESS_CLAMP,D3DTADDRESS_CLAMP,TRUE,FALSE,D3DCMP_LESSEQUAL};
    UINT hull_prims=0,marker_prims=0;
    if(SUCCEEDED(hr)&&p->active())hr=draw_pass(d,*p,D3DPT_LINELIST,hull_lines,proof.view,proof.projection,p->cars_mode()==1?over:tested,writer,hull_prims);
    if(SUCCEEDED(hr)&&p->active())hr=draw_pass(d,*p,D3DPT_LINELIST,marker_lines,proof.view,proof.projection,p->markers_mode()==2?over:tested,writer,marker_prims);
    if(SUCCEEDED(hr)&&p->active()&&p->legend_enabled()){
        // Drawn by the next Present over the finished frame (HUD included): PS2PortExtension::color_present.
        // Player car (Broker Car0 -> gaVehicleOutputData +0xec, the reader of the spline objects) and the collision
        // surface under it: "CAR X Y Z  GROUND <surface> <height> (<car height above it>)".
        std::string info;
        {
            const char* why="not_read";ps2spline::Vec3 car{};ps2port::HudLiveMemory memory;
            if(splineintegration::observer_reader().read(memory,0x400000,cert.race_generation,car,why)){
                char text[160];std::snprintf(text,sizeof(text),"CAR X %.2f Y %.2f Z %.2f",double(car[0]),double(car[1]),double(car[2]));info=text;
                const auto g=colldebug::probe_ground(p->mesh(),car[0],car[1],car[2]);
                if(g.hit){std::snprintf(text,sizeof(text),"  GROUND %s Y %.2f (+%.2f)",colldebug::surface_name(g.surface),double(g.height),double(car[1]-g.height));info+=text;}
                else info+="  NO GROUND UNDER CAR";
            }else info=std::string("CAR ")+why;
            for(auto& c:info)c=static_cast<char>(c>='a'&&c<='z'?c-'a'+'A':c=='_'?' ':c);
        }
        std::vector<std::pair<std::string,uint32_t>> extra;
        if(p->cars_mode()){
            extra.emplace_back("CAR HULL "+std::to_string(hulls_drawn)+"/"+std::to_string(hulls_participants)+(p->cars_mode()==2?" DEPTH (":" (")+p->cars_key_name()+")",colldebug::kHullRgb);
            extra.emplace_back("WHEELS "+std::to_string(wheels_drawn),colldebug::kWheelRgb);
        }
        if(p->markers_mode()){
            extra.emplace_back(std::string(p->markers_mode()==2?"MARKERS X-RAY (":"MARKERS (")+p->markers_key_name()+")",colldebug::argb(0,90,90,90));
            const auto& lists=p->markers();
            for(size_t i=0;i<lists.size()&&i<marker_counts.size();++i)
                extra.emplace_back(colldebug::marker_label(lists[i].name)+" "+std::to_string(lists[i].pos.size()/3),colldebug::marker_rgb(lists[i].name));
            if(lists.empty())extra.emplace_back("NO MARKER LISTS",colldebug::argb(0,90,90,90));
        }
        try{colldebug::build_legend(p->legend,p->mode(),b,p->source(),p->key_name(),viewport.Width,viewport.Height,info,extra);}catch(...){p->legend.quads.clear();}
        quads=static_cast<UINT>(p->legend.quads.size()/3);p->stage_legend(viewport.Width,viewport.Height);
    }
    if(p->claim_log(true)||FAILED(hr))try{session().write("{\"type\":\"collision_debug_draw\",\"course\":"+quote(std::string(cert.course_id.data()))+
        ",\"frame\":"+std::to_string(frame)+",\"mode\":"+quote(colldebug::mode_name(p->mode()))+",\"source\":"+quote(p->source())+
        ",\"visible_triangles\":"+std::to_string(b.visible_triangles)+",\"triangles_drawn\":"+std::to_string(tris)+",\"lines_drawn\":"+std::to_string(lines)+",\"hull_lines\":"+std::to_string(hull_prims)+",\"marker_lines\":"+std::to_string(marker_prims)+
        ",\"legend_triangles\":"+std::to_string(quads)+",\"camera\":["+std::to_string(cam[0])+","+std::to_string(cam[1])+","+std::to_string(cam[2])+
        "],\"status\":"+quote(p->active()?"drawn":p->reason())+",\"hresult\":"+std::to_string(static_cast<uint32_t>(hr))+"}");}catch(...){}
    return hr;
}
} // namespace gfx2::collisionintegration
