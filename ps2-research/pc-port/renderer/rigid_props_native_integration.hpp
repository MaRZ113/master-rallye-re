#pragma once
#include "ps2_race_certificate.hpp"
// COURSE-ALIVE3 native side: the PS2 rigid props are simulated once per frame at the typed pre-UI boundary (after the
// course, water, spline objects and birds, before the collision overlay and the HUD) and drawn there with the verified
// gameplay VIEW/PROJECTION of the frame, identity WORLD, the native depth buffer and course fog, through the fixed
// CourseObjectTransaction. Single camera races only (the COLLISION-DEBUG1 admission: gameplay view/projection seen this
// frame, full back buffer with depth, native dependency states).
//
// Vehicles: FLEET-ALL-CARS1 participants (every car of the race), pose = render instance world matrix instance+0x44 (the
// matrix 0x561a40 sets as D3DTS_WORLD for the body, COLLISION-DEBUG1 round 5), hull = car.dx tag101 representation B.
#include "course_objects_native_integration.hpp"
#include "rigid_props.hpp"
#include "atmosphere_native.hpp"
#include "fleet_participants.hpp"
#include "ps2_hud_damage_feed.hpp"
#include "ps2_birds_pilot.hpp"
#include <cstdio>
#include <string>
#include <unordered_map>
#include <vector>

namespace gfx2::rigidintegration {
using ps2rigid::operator+;using ps2rigid::operator-;using ps2rigid::operator*;
inline ps2port::RigidPropsPilot* pilot(Device8& d) noexcept {return d.ps2_port()?d.ps2_port()->rigid_props():nullptr;}
inline ps2port::FleetParticipantResolver& participants() noexcept {static ps2port::FleetParticipantResolver r;return r;}

// PC vehicle physics bodies (COURSE-ALIVE3 two-way coupling). Collision holder 0x6F957C -> +0x08 backend (vtable
// 0x692318) -> convex instance vector +0x14/+0x18 -> instance+0x0C body. A body of class 0x691A04 has the PS2 body
// layout (RIGID1 / PC 0x4FF3E0, 0x4FF4E0): mass +0x20, position +0xA0, quaternion +0xAC, momentum P +0x104, angular
// momentum L +0x110, velocity +0x11C (= P / mass, derived again by the PC state restore). RIGID-PORT1.1 observed the
// race car itself as the one such body on a course without props.
inline constexpr uint32_t kPhysicsHolder=0x6F957C,kCollisionBackendVtable=0x692318,kBodyVtable=0x691A04;
struct VehicleBody { uint32_t body=0; float mass=0; ps2rigid::V3 position{}; };
inline std::vector<VehicleBody> vehicle_bodies(ps2port::HudLiveMemory& m) {
    std::vector<VehicleBody> out;
    auto word=[&](uint32_t a,uint32_t& v){return !(a&3)&&m.read(a,&v,4);};
    auto pointer=[&](uint32_t a,uint32_t& v){return word(a,v)&&v>=0x10000&&v<=0x7ffffffc&&!(v&3);};
    uint32_t holder=0,backend=0,vt=0,begin=0,end=0;
    if(!pointer(kPhysicsHolder,holder)||!pointer(holder+8,backend)||!word(backend,vt)||vt!=kCollisionBackendVtable||
       !word(backend+0x14,begin)||!word(backend+0x18,end)||end<begin||(end-begin)%4||(end-begin)/4>256)return out;
    for(uint32_t a=begin;a<end;a+=4){
        uint32_t inst=0,body=0,bvt=0;float mass=0;ps2rigid::V3 pos{};
        if(!pointer(a,inst)||!pointer(inst+0x0C,body)||!word(body,bvt)||bvt!=kBodyVtable||!m.read(body+0x20,&mass,4)||!m.read(body+0xA0,pos.data(),12))continue;
        if(!(mass>100.f&&mass<20000.f)||!ps2rigid::finite(pos))continue;
        bool seen=false;for(const auto& b:out)seen=seen||b.body==body;
        if(!seen)out.push_back({body,mass,pos});
    }
    return out;
}
inline bool live_write(uint32_t address,const void* data,size_t bytes) noexcept {
    if(address<0x10000||address>0x7fffffff||bytes>64||bytes>0x7fffffffu-address)return false;
    __try{std::memcpy(reinterpret_cast<void*>(static_cast<uintptr_t>(address)),data,bytes);return true;}
    __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
// Adds the summed reaction of the props to a vehicle body: P += J, L += A, v = P / mass. |J| / mass is limited to
// 12 m/s per frame. Returns the applied velocity change.
inline float apply_vehicle_impulse(ps2port::HudLiveMemory& m,const ps2rigid::Kinematic& k) noexcept {
    if(!k.body||!(k.mass>0.f))return 0.f;
    ps2rigid::V3 j=k.impulse,a=k.angular;
    if(!ps2rigid::finite(j)||!ps2rigid::finite(a))return 0.f;
    const float dv=ps2rigid::length(j)/k.mass;
    if(!(dv>1e-4f))return 0.f;
    if(dv>12.f){const float s=12.f/dv;j=j*s;a=a*s;}
    uint32_t vt=0;float mass=0;ps2rigid::V3 P{},L{};
    if(!m.read(k.body,&vt,4)||vt!=kBodyVtable||!m.read(k.body+0x20,&mass,4)||std::fabs(mass-k.mass)>1e-3f*k.mass||
       !m.read(k.body+0x104,P.data(),12)||!m.read(k.body+0x110,L.data(),12)||!ps2rigid::finite(P)||!ps2rigid::finite(L))return 0.f;
    P=P+j;L=L+a;const ps2rigid::V3 v=P*(1.f/mass);
    if(!live_write(k.body+0x104,P.data(),12)||!live_write(k.body+0x110,L.data(),12)||!live_write(k.body+0x11C,v.data(),12))return 0.f;
    return std::min(dv,12.f);
}

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
// The four side planes of view*projection (D3D row vectors: clip = p * VP), normalised to world units.
inline std::vector<std::array<float,4>> side_planes(const D3DMATRIX& view,const D3DMATRIX& projection) {
    float vp[4][4];
    for(int r=0;r<4;++r)for(int c=0;c<4;++c){float s=0;for(int k=0;k<4;++k)s+=view.m[r][k]*projection.m[k][c];vp[r][c]=s;}
    auto column=[&](int c){return std::array<float,4>{vp[0][c],vp[1][c],vp[2][c],vp[3][c]};};
    const auto c0=column(0),c1=column(1),c3=column(3);
    std::vector<std::array<float,4>> out;
    for(const auto& q:{std::array<float,4>{c3[0]+c0[0],c3[1]+c0[1],c3[2]+c0[2],c3[3]+c0[3]},std::array<float,4>{c3[0]-c0[0],c3[1]-c0[1],c3[2]-c0[2],c3[3]-c0[3]},
                       std::array<float,4>{c3[0]+c1[0],c3[1]+c1[1],c3[2]+c1[2],c3[3]+c1[3]},std::array<float,4>{c3[0]-c1[0],c3[1]-c1[1],c3[2]-c1[2],c3[3]-c1[3]}}){
        const float l=std::sqrt(q[0]*q[0]+q[1]*q[1]+q[2]*q[2]);
        if(l>1e-6f&&std::isfinite(l))out.push_back({q[0]/l,q[1]/l,q[2]/l,q[3]/l});
    }
    return out;
}
inline std::string state_record(const ps2port::RigidPropsPilot& p,uint64_t frame,size_t cars) {
    const auto& rt=p.runtime();const auto& a=p.asset();const auto& c=a.courses[rt.course()];const auto& w=rt.world();
    std::string s="{\"type\":\"ps2_rigid_props_state\",\"course\":"+quote(c.id)+",\"frame\":"+std::to_string(frame)+
        ",\"race_generation\":"+std::to_string(rt.race())+",\"ticks\":"+std::to_string(w.ticks())+",\"cars\":"+std::to_string(cars)+
        ",\"contacts\":"+std::to_string(w.last_contacts())+",\"car_contacts\":"+std::to_string(w.last_car_contacts())+",\"props\":[";
    for(size_t i=0;i<w.bodies().size()&&i<rt.members().size();++i){const auto& b=w.bodies()[i];char buf[256];
        const char* state=b.state==ps2rigid::State::Active?"active":b.state==ps2rigid::State::Far?"far":"asleep";
        std::snprintf(buf,sizeof(buf),"%s{\"egg\":\"%s\",\"state\":\"%s\",\"near\":%s,\"wakes\":%u,\"lifted\":%.3f,\"position\":[%.3f,%.3f,%.3f],\"speed\":%.3f}",
            i?",":"",a.props[rt.members()[i]].egg.c_str(),state,b.in_view?"true":"false",unsigned(b.wakes),double(b.lifted),
            double(b.x[0]),double(b.x[1]),double(b.x[2]),double(ps2rigid::length(b.v)));s+=buf;}
    return s+"]}";
}
// COURSE-ALIVE4: a native draw of the PC checkpoint boards (Misc/Checkpoints/checkpoint.dx, stage-0 texture content
// i2a_planks2-tga with 48 triangles or stamp_01-tga with 4, non-identity WORLD = an Egg model) in a race whose PS2 barrels
// are simulated and drawn is skipped: on the PS2 the checkpoint is the barrel. Anything else draws as before.
struct BoardResult { bool handled=false; HRESULT hr=S_OK; };
inline BoardResult hide_checkpoint_board(Device8& d,D3DPRIMITIVETYPE type,UINT count) noexcept {
    auto* p=pilot(d);if(!p||!p->barrels_requested()||!p->active())return {};
    if(type!=D3DPT_TRIANGLELIST||(count!=ps2port::kPcCheckpointPlanksTriangles&&count!=ps2port::kPcCheckpointStampTriangles))return {};
    if(!d.trace.scene_active||d.trace.shadow.recording||d.trace.effective_shadow.recording||GetCurrentThreadId()!=d.trace.render_thread_id())return {};
    bool single=false;const auto cert=courseintegration::certificate(d,single);
    if(!single||!cert.valid||!p->hide_boards(cert.race_generation))return {};
    auto& n=*d.native();
    courseintegration::Ref<IDirect3DBaseTexture8> texture;
    if(FAILED(n.GetTexture(0,&texture.p))||!texture.p)return {};
    const auto id=reinterpret_cast<uintptr_t>(texture.p);
    const auto& tracked=d.trace.effective_shadow.bindings.textures[0];
    if(!tracked.known||tracked.value!=id)return {};
    const int kind=p->board_texture(texture.p,d.trace.resources.generation(id));
    if(!(kind==1&&count==ps2port::kPcCheckpointPlanksTriangles)&&!(kind==2&&count==ps2port::kPcCheckpointStampTriangles))return {};
    // An Egg model has its own WORLD; an identity WORLD would be course geometry with the same texture.
    D3DMATRIX world{};const auto& tw=d.trace.effective_shadow.matrices[D3DTS_WORLD];
    if(tw.known)world=tw.value;else if(FAILED(n.GetTransform(D3DTS_WORLD,&world)))return {};
    D3DMATRIX identity{};identity._11=identity._22=identity._33=identity._44=1.f;
    if(!std::memcmp(&world,&identity,sizeof(identity)))return {};
    const auto hidden=p->note_board_hidden();
    if(auto* x=d.ps2_port())x->note(ps2diag::Effect::RigidProps,"checkpoint_board_hidden");
    if(p->claim_board_log())try{session().write("{\"type\":\"ps2_checkpoint_board_hidden\",\"race_generation\":"+std::to_string(cert.race_generation)+
        ",\"kind\":"+(kind==1?"\"planks\"":"\"stamp\"")+",\"hidden\":"+std::to_string(hidden)+",\"barrels\":"+std::to_string(p->runtime().barrels())+"}");}catch(...){}
    return {true,S_OK};
}
inline HRESULT before_ui(Device8& d,bool ui_callsite) noexcept {
    ps2port::perf::Timer perf_timer(ps2port::perf::UiRigid);
    auto* p=pilot(d);if(!p||!p->active()||!ui_callsite)return S_OK;
    if(GetCurrentThreadId()!=d.trace.render_thread_id()||!d.trace.scene_active||d.trace.shadow.recording||d.trace.effective_shadow.recording)return S_OK;
    const uint64_t frame=d.trace.frame_number(),reset=d.ps2_port()->reset_generation();
    if(!p->consume_boundary(frame,reset))return S_OK;
    auto note=[&](const char* why){if(auto* x=d.ps2_port())x->note(ps2diag::Effect::RigidProps,why);};
    auto gate=[&](const char* reason){note(reason);if(p->claim_log(false))try{session().write("{\"type\":\"ps2_rigid_props_gate\",\"reason\":"+quote(reason)+
        ",\"frame\":"+std::to_string(frame)+"}");}catch(...){}return S_OK;};
    bool single=false;const auto cert=courseintegration::certificate(d,single);
    if(!single||!cert.valid)return gate(single?"race_certificate_invalid":"no_single_camera_race");
    const bool selected=p->select_course(cert.course_id.data(),cert.race_generation);
    if(p->take_course_log()&&p->diagnostics())try{session().write("{\"type\":\"ps2_rigid_props_course\",\"course\":"+quote(std::string(cert.course_id.data()))+
        ",\"race_generation\":"+std::to_string(cert.race_generation)+",\"selected\":"+(selected?"true":"false")+",\"course_guard\":"+quote(p->guard_reason())+
        ",\"terrain\":"+quote(p->terrain_reason())+",\"terrain_records\":"+std::to_string(p->terrain_records())+",\"terrain_ms\":"+std::to_string(p->terrain_ms())+
        ",\"props\":"+std::to_string(selected?p->runtime().world().bodies().size():0)+"}");}catch(...){}
    if(!selected){note(p->guard_reason());return S_OK;}
    auto& proof=p->proof;auto& n=*d.native();
    if(proof.frame!=frame||proof.device!=d.trace.device_id()||proof.reset!=reset||!proof.view_site||!proof.projection_site)return gate("gameplay_view_projection_not_seen_this_frame");
    ps2birds::Vec3 camera{},look{},up{};
    if(!ps2port::birds_camera(proof.view,camera,look,up))return gate("camera_not_orthonormal");
    // Physics first, once per frame: it must not depend on whether this frame's draw is admitted.
    ps2rigid::TickInput in;in.camera={camera[0],camera[1],camera[2]};in.have_camera=true;
    try{in.frustum=side_planes(proof.view,proof.projection);}catch(...){in.frustum.clear();}
    std::vector<ps2port::RigidCarInput> cars;std::unordered_map<std::string,const ps2rigid::Hull*> hulls;
    const char* car_reason="not_read";
    try{
        ps2port::HudLiveMemory memory;
        const auto table=participants().resolve(memory,0x400000,cert,1);car_reason=table.reason;
        for(uint32_t i=0;i<table.count&&i<table.cars.size();++i){
            const auto& car=table.cars[i];if(!car.valid)continue;
            ps2port::RigidCarInput c;c.instance=car.instance;c.folder=car.folder.data();c.local=car.player_type==1;
            float m16[16];
            if(memory.read(car.instance+0x44,m16,64)&&std::fabs(m16[3])<1e-4f&&std::fabs(m16[7])<1e-4f&&std::fabs(m16[11])<1e-4f&&std::fabs(m16[15]-1.f)<1e-4f){
                for(int r=0;r<4;++r)for(int k=0;k<3;++k)c.rows[size_t(r*3+k)]=m16[r*4+k];
                c.pose_valid=true;
            }
            std::string key=c.folder;for(auto& ch:key)ch=static_cast<char>(ch>='A'&&ch<='Z'?ch-'A'+'a':ch);
            if(!hulls.count(key))hulls[key]=p->hull(c.folder);
            cars.push_back(std::move(c));
        }
    }catch(...){cars.clear();}
    // Two-way coupling: each car takes the nearest unused vehicle body within 3 m of its render origin.
    size_t coupled=0;
    if(p->car_impulse())try{
        ps2port::HudLiveMemory memory;
        auto bodies=vehicle_bodies(memory);
        for(auto& c:cars){
            if(!c.pose_valid)continue;
            const ps2rigid::V3 at{c.rows[9],c.rows[10],c.rows[11]};
            float best=9.f;size_t pick=SIZE_MAX;
            for(size_t b=0;b<bodies.size();++b){if(!bodies[b].body)continue;const auto dd=bodies[b].position-at;const float d2=ps2rigid::dot(dd,dd);if(d2<best){best=d2;pick=b;}}
            if(pick==SIZE_MAX)continue;
            c.body=bodies[pick].body;c.mass=bodies[pick].mass;c.com=bodies[pick].position;bodies[pick].body=0;++coupled;
        }
    }catch(...){}
    p->runtime_mut().cars(cars,hulls,p->host_seconds(),in.cars);
    const auto pause=read_pause_menu_state_readonly();
    p->advance_frame(frame,pause.present&&pause.tag==0&&pause.value!=0,in);
    float pushed=0.f;
    if(p->car_impulse()){ps2port::HudLiveMemory memory;for(const auto& k:in.cars)pushed=std::max(pushed,apply_vehicle_impulse(memory,k));}
    if(pushed>0.f&&p->claim_impulse_log())try{session().write("{\"type\":\"ps2_rigid_props_car_impulse\",\"frame\":"+std::to_string(frame)+
        ",\"coupled\":"+std::to_string(coupled)+",\"delta_v\":"+std::to_string(pushed)+"}");}catch(...){}
    if(p->claim_state_log())try{session().write(state_record(*p,frame,in.cars.size()));}catch(...){}
    courseintegration::Ref<IDirect3DSurface8> target,back,depth;D3DVIEWPORT8 viewport{};D3DSURFACE_DESC desc{};
    if(FAILED(n.GetRenderTarget(&target.p))||FAILED(n.GetBackBuffer(0,D3DBACKBUFFER_TYPE_MONO,&back.p))||!courseintegration::same_identity(target.p,back.p)||
       FAILED(n.GetDepthStencilSurface(&depth.p))||!depth.p||FAILED(n.GetViewport(&viewport))||FAILED(target.p->GetDesc(&desc))||
       viewport.X||viewport.Y||viewport.Width!=desc.Width||viewport.Height!=desc.Height)return gate("target_not_full_backbuffer_with_depth");
    if(!courseintegration::native_dependencies(n))return gate("native_dependency_states");
    std::vector<ps2port::RigidBatch> batches;
    float view16[16];for(int r=0;r<4;++r)for(int k=0;k<4;++k)view16[r*4+k]=proof.view.m[r][k];
    // No drop shadow: the owner checked on the PS2 that neither bales nor tumbleweeds cast one (shadow range 0).
    if(!p->runtime().build(in.camera,view16,0.f,batches)){p->proof.clear();return gate("world_vertices_nonfinite");}
    // ATMOSPHERE2.5: lit like the course objects; additive environment and shadow passes keep their source colour.
    for(auto& batch:batches)if(batch.pass!=ps2port::RigidPass::Env&&batch.pass!=ps2port::RigidPass::Shadow)atmosphereintegration::light_proxy_layer(d,batch.vertices,false);
    // Course fog as the game left it: linear vertex fog, or any table (pixel) fog mode. Without a fog source the
    // fixed-function vertex fog would read the missing specular alpha, so fog stays off then.
    bool fog=false;DWORD fog_vertex=0,fog_table=0,fog_enable=0;float fog_start=0,fog_end=0;
    {DWORD start=0,end=0;
     if(SUCCEEDED(n.GetRenderState(D3DRS_FOGVERTEXMODE,&fog_vertex))&&SUCCEEDED(n.GetRenderState(D3DRS_FOGTABLEMODE,&fog_table))&&
        SUCCEEDED(n.GetRenderState(D3DRS_FOGSTART,&start))&&SUCCEEDED(n.GetRenderState(D3DRS_FOGEND,&end))&&SUCCEEDED(n.GetRenderState(D3DRS_FOGENABLE,&fog_enable))){
         std::memcpy(&fog_start,&start,4);std::memcpy(&fog_end,&end,4);
         fog=(fog_vertex==D3DFOG_LINEAR&&fog_table==D3DFOG_NONE&&std::isfinite(fog_start)&&std::isfinite(fog_end)&&fog_start>=0.f&&fog_start<fog_end)||
             (fog_table!=D3DFOG_NONE&&fog_table<=D3DFOG_LINEAR);}}
    const auto writer=[&](uint32_t slot,const Args& args,HRESULT hr) noexcept {courseintegration::after_setter(d,slot,args,hr);};
    HRESULT captured=S_OK,applied=S_OK,draw=E_PENDING,restored=S_OK;UINT triangles=0,draws=0;
    for(const auto& batch:batches){
        if(batch.vertices.empty())continue;
        captured=p->transaction.capture(n);if(FAILED(captured))break;
        // Object: opaque, depth written (PS2 object/dull primary); environment: added (mode-3 secondary Cd + Cs, depth
        // test only); treeblend: source alpha blend, no depth write (mode2, ZMSK1); shadow: alpha blend, no depth write.
        const DWORD fog_state=static_cast<DWORD>(fog?TRUE:FALSE);
        ps2port::CourseObjectMaterialState material{TRUE,D3DTADDRESS_WRAP,D3DTADDRESS_WRAP,FALSE,fog_state};
        if(batch.pass==ps2port::RigidPass::Treeblend)material=ps2port::CourseObjectMaterialState{FALSE,D3DTADDRESS_WRAP,D3DTADDRESS_WRAP,TRUE,fog_state};
        if(batch.pass==ps2port::RigidPass::Shadow)material=ps2port::CourseObjectMaterialState{FALSE,D3DTADDRESS_CLAMP,D3DTADDRESS_CLAMP,TRUE,fog_state};
        if(batch.pass==ps2port::RigidPass::Env){material=ps2port::CourseObjectMaterialState{FALSE,D3DTADDRESS_CLAMP,D3DTADDRESS_CLAMP,TRUE,FALSE};
            material.src_blend=D3DBLEND_ONE;material.dest_blend=D3DBLEND_ONE;}
        if(batch.pass!=ps2port::RigidPass::Env&&batch.pass!=ps2port::RigidPass::Shadow)atmosphereintegration::proxy_fog(d,material);
        applied=p->transaction.apply(n,p->texture(batch.texture),proof.view,proof.projection,writer,material);
        if(SUCCEEDED(applied)){
            p->transaction.mark_up_stream_changed();
            draw=n.DrawPrimitiveUP(D3DPT_TRIANGLELIST,static_cast<UINT>(batch.vertices.size()/3),batch.vertices.data(),sizeof(ps2port::ObjectVertex));
            if(FAILED(draw))p->disable("native_rigid_props_draw_failed");
            else{triangles+=static_cast<UINT>(batch.vertices.size()/3);++draws;}
        }
        if(p->transaction.has_pending())restored=p->transaction.restore(n,writer);
        if(FAILED(restored)){p->disable("native_rigid_props_state_restore_failed");break;}
        p->transaction.release();
        if(FAILED(applied)||FAILED(draw))break;
    }
    note(FAILED(restored)?"restore_failed":FAILED(draw)?"draw_failed":FAILED(applied)?"apply_failed":FAILED(captured)?"capture_failed":draws?"drawn":"nothing_visible");
    if(p->claim_log(true)||FAILED(restored))try{
        const auto& course=p->asset().courses[p->runtime().course()];
        session().write("{\"type\":\"ps2_rigid_props_draw\",\"course\":"+quote(course.id)+",\"frame\":"+std::to_string(frame)+
        ",\"race_generation\":"+std::to_string(cert.race_generation)+",\"props\":"+std::to_string(p->runtime().world().bodies().size())+
        ",\"draws\":"+std::to_string(draws)+",\"triangles\":"+std::to_string(triangles)+",\"fog\":"+(fog?"true":"false")+",\"fog_states\":["+std::to_string(fog_enable)+","+std::to_string(fog_vertex)+","+std::to_string(fog_table)+","+std::to_string(fog_start)+","+std::to_string(fog_end)+"],\"coupled_cars\":"+std::to_string(coupled)+
        ",\"cars\":"+std::to_string(in.cars.size())+",\"car_reason\":"+quote(car_reason)+",\"missing_hulls\":"+quote(p->missing_hulls())+
        ",\"frustum_planes\":"+std::to_string(in.frustum.size())+",\"course_guard\":"+quote(p->guard_reason())+
        ",\"apply_hresult\":"+std::to_string(static_cast<uint32_t>(applied))+",\"draw_hresult\":"+std::to_string(static_cast<uint32_t>(draw))+
        ",\"restore_hresult\":"+std::to_string(static_cast<uint32_t>(restored))+",\"artifact_sha256\":"+quote(ps2port::kRigidPropsArtifactSha)+
        ",\"runtime_visibility\":\"PENDING_USER\"}");}catch(...){}
    return FAILED(restored)?restored:S_OK;
}
} // namespace gfx2::rigidintegration
