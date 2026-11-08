#pragma once
#include "course_objects_native_integration.hpp"
#include "ground_detail_native.hpp"
#include "atmosphere.hpp"
#include "buffer_provenance.hpp"
#include "brake_glow.hpp"
#include "ps2_hud_damage_feed.hpp"
#include "ps2_perf_timing.hpp"

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
inline void proxy_headlights(Device8& d,atmosphere::Pilot& p,std::vector<ps2port::ObjectVertex>& v)noexcept;
inline void light_proxy_layer_base(Device8& d,std::vector<ps2port::ObjectVertex>& v,bool upright)noexcept;
inline void light_proxy_layer(Device8& d,std::vector<ps2port::ObjectVertex>& v,bool upright)noexcept {
    light_proxy_layer_base(d,v,upright);
    if(auto* p=pilot(d);p&&p->enabled()&&p->world&&p->lighting.active())proxy_headlights(d,*p,v);
}
inline void light_proxy_layer_base(Device8& d,std::vector<ps2port::ObjectVertex>& v,bool upright)noexcept {
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
// Additive environment layers of proxy-drawn props (PS2 bales, barrels):
// texture*diffuse with white vertices; the world environment energy (night-
// scaled) replaces the white so reflections fade with the world.
inline void light_proxy_environment(Device8& d,std::vector<ps2port::ObjectVertex>& v)noexcept {
    auto* p=pilot(d);if(!p||!p->enabled()||!p->world||!p->lighting.active())return;
    const auto factor=atmosphere::world_environment_factor(p->lighting);
    for(auto& x:v)x.color=atmosphere::environment_texel(x.color,factor);
}
inline void log(Device8& d,const char* reason)noexcept {
    try{session().write("{\"type\":\"atmosphere_draw\",\"reason\":"+quote(std::string(reason))+",\"frame\":"+std::to_string(d.trace.frame_number())+"}");}catch(...){}
}
inline void sun_transform(Device8& d,D3DTRANSFORMSTATETYPE type,bool exe,uint32_t rva)noexcept{
    if(!exe||!((type==D3DTS_VIEW&&rva==GAMEPLAY_VIEW_RETURN_RVA)||(type==D3DTS_PROJECTION&&rva==GAMEPLAY_PROJECTION_RETURN_RVA)))return;
    auto* p=pilot(d);if(p&&(p->sun_disk||p->sun_halo||p->sun_flare||p->sun_style.vignette>0))p->sun.clear();
}
// ===== ATMOSPHERE6.3 P2: projected headlights / tail-light ground glow =====
inline bool type_supports_headlight(DWORD fvf)noexcept{return fvf==0x142||fvf==0x242||fvf==0x152;}
inline HRESULT headlight_textures(IDirect3DDevice8& n,atmosphere::Pilot& p)noexcept{
    if(p.headlight_cookie_texture&&p.tail_cookie_texture&&p.headlight_ramp_texture)return S_OK;
    p.release_headlights();
    auto make=[&](IDirect3DTexture8*& t,unsigned w,unsigned h,auto shade)->HRESULT{
        auto hr=n.CreateTexture(w,h,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&t);if(FAILED(hr)||!t)return E_FAIL;
        D3DLOCKED_RECT l{};hr=t->LockRect(0,&l,nullptr,0);if(FAILED(hr)||!l.pBits){if(SUCCEEDED(hr))t->UnlockRect(0);return E_FAIL;}
        for(unsigned y=0;y<h;++y)for(unsigned x=0;x<w;++x){const float v=std::clamp(shade((x+.5f)/w,(y+.5f)/h),0.f,1.f);const DWORD c=DWORD(std::lround(v*255));
            const DWORD px=0xff000000u|c<<16|c<<8|c;std::memcpy(static_cast<uint8_t*>(l.pBits)+size_t(y)*l.Pitch+x*4,&px,4);}
        return t->UnlockRect(0);};
    HRESULT hr=make(p.headlight_cookie_texture,128,128,[](float u,float v){return atmosphere::headlight_cookie(u,v);});
    if(SUCCEEDED(hr))hr=make(p.tail_cookie_texture,64,64,[](float u,float v){return atmosphere::tail_cookie(u,v);});
    if(SUCCEEDED(hr))hr=make(p.headlight_ramp_texture,256,4,[](float u,float){return u<1.f/256?0.f:atmosphere::headlight_ramp(u);});
    if(FAILED(hr))p.release_headlights();return hr;
}
// Per frame: up to HeadlightCars car bodies nearest the camera, each
// extrapolated to this frame when its body was not drawn yet, with its brake
// and reverse state. Texture matrices depend on the current VIEW and are
// rebuilt whenever it changes inside the frame.
inline void gear_probe(Device8& d,atmosphere::Pilot& p,uint64_t frame,float along,bool reversing)noexcept;
inline bool headlight_projectors(Device8& d,atmosphere::Pilot& p,IDirect3DDevice8& n)noexcept{
    const auto frame=d.trace.frame_number();auto& lp=p.lamp_projectors;const auto& style=p.headlight_style;
    D3DMATRIX view{};if(FAILED(n.GetTransform(D3DTS_VIEW,&view)))return false;atmosphere::Mat4 v{};std::memcpy(v.data(),&view,64);
    atmosphere::Mat4 inverse{};if(!atmosphere::mat_inverse(v,inverse))return false;
    if(lp.frame!=frame){
        lp.frame=frame;lp.count=0;lp.view_valid=false;const std::array<float,3> eye{inverse[12],inverse[13],inverse[14]};
        if(p.lamps_last.frame!=UINT64_MAX&&!p.lamps_last.samples.empty()){p.brake_local=p.lamps_last.samples[0].local;p.brake_local_valid=true;}
        // 6.10: selected gear of every Car<N> (reverse lamps), matched to poses by world position.
        std::array<ps2port::HudDamageFeedReader::CarGear,8> gears{};unsigned gear_count=0;
        if(p.reverse_from_gear){bool single=false;const auto cert=courseintegration::certificate(d,single);
            if(single&&cert.valid){if(cert.race_generation!=p.gear_generation){p.gear_generation=cert.race_generation;p.gear_trusted={};}
                static ps2port::HudDamageFeedReader reader;ps2port::HudLiveMemory memory;
                gear_count=reader.car_gears(memory,uint32_t(reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr))),cert.race_generation,gears);
                for(unsigned g=0;g<gears.size();++g)if(gears[g].ok&&gears[g].gear>=2)p.gear_trusted[g]=true;}}
        std::array<std::pair<float,unsigned>,8> order{};unsigned found=0;
        // 6.10: a body draw the observer missed (gate/LOD/state change) no longer drops the lamps at once:
        // the pose is extrapolated for up to HeadlightPoseHold frames.
        for(unsigned i=0;i<p.car_poses.size();++i){const auto& c=p.car_poses[i];if(!c.instance||c.frame==UINT64_MAX||c.frame+p.headlight_pose_hold<frame||c.frame>frame)continue;
            const float dx=c.m[12]-eye[0],dy=c.m[13]-eye[1],dz=c.m[14]-eye[2],dist=dx*dx+dy*dy+dz*dz;if(dist<=150.f*150.f)order[found++]={dist,i};}
        std::sort(order.begin(),order.begin()+found);
        for(unsigned k=0;k<found&&lp.count<std::min<unsigned>(style.cars,4);++k){auto& c=p.car_poses[order[k].second];auto& L=lp.cars[lp.count];L={};L.instance=c.instance;L.car=c.m;
            if(c.prev_frame+1==c.frame){const auto f=atmosphere::normalized({c.m[8],c.m[9],c.m[10]});
                const float along=(c.m[12]-c.prev[12])*f[0]+(c.m[13]-c.prev[13])*f[1]+(c.m[14]-c.prev[14])*f[2];
                // 6.8: latched like a selected reverse gear: on when moving backwards, kept while
                // stopped, off once the car moves forwards again.
                if(along<-.025f)c.reverse_until=UINT64_MAX;else if(along>.02f)c.reverse_until=0;
                if(c.frame<frame){const float t=float(frame-c.frame);for(unsigned i=12;i<15;++i)L.car[i]+=(c.m[i]-c.prev[i])*t;}}
            if(c.frame<frame)++p.headlight_held;
            if(c.lit_frame!=UINT64_MAX&&c.lit_frame+1<frame&&c.lit_frame+120>frame){++p.headlight_gaps;
                if(p.headlight_gaps<=40)session().write("{\"type\":\"atmosphere_headlight_gap\",\"frame\":"+std::to_string(frame)+",\"car\":"+std::to_string(k)+",\"missing_frames\":"+std::to_string(frame-c.lit_frame-1)+",\"pose_age\":"+std::to_string(frame-c.frame)+",\"dist\":"+std::to_string(std::sqrt(order[k].first))+"}");}
            c.lit_frame=frame;
            L.reversing=c.reverse_until&&frame<=c.reverse_until;
            if(gear_count){unsigned best=8;float best_d=16.f;
                for(unsigned g=0;g<gears.size();++g)if(gears[g].ok&&p.gear_trusted[g]){const float gx=gears[g].position[0]-L.car[12],gy=gears[g].position[1]-L.car[13],gz=gears[g].position[2]-L.car[14],dd=gx*gx+gy*gy+gz*gz;if(dd<best_d){best_d=dd;best=g;}}
                if(best<8){L.reversing=gears[best].gear==0;c.reverse_until=0;++p.gear_matched;if(L.reversing)++p.gear_reverse;
                    if(L.reversing&&p.first_reason("lamp_reverse_from_gear"))session().write("{\"type\":\"atmosphere_reverse_gear\",\"frame\":"+std::to_string(frame)+",\"car\":"+std::to_string(best)+",\"dist\":"+std::to_string(std::sqrt(best_d))+"}");}}
            if(k==0&&p.gear_probe){float along=0;if(c.prev_frame+1==c.frame){const auto f=atmosphere::normalized({c.m[8],c.m[9],c.m[10]});along=(c.m[12]-c.prev[12])*f[0]+(c.m[13]-c.prev[13])*f[1]+(c.m[14]-c.prev[14])*f[2];}gear_probe(d,p,frame,along,L.reversing);}
            L.head_frame=atmosphere::light_frame(L.car,style.head);L.head=L.head_frame.valid&&style.intensity>0;
            if(style.tail&&style.tail_intensity>0){L.rear_frame=atmosphere::light_frame(L.car,style.rear);L.rear=L.rear_frame.valid;}
            if(p.lamps_last.frame!=UINT64_MAX&&p.lamps_last.frame+2>=frame)for(const auto& s:p.lamps_last.samples){
                const float dx=s.world[12]-L.car[12],dy=s.world[13]-L.car[13],dz=s.world[14]-L.car[14];if(dx*dx+dy*dy+dz*dz<9.f){L.brake=true;break;}}
            if(L.head||L.rear)++lp.count;}
        if(!lp.count)++p.headlight_no_car;
    }
    if(!lp.count)return false;
    if(!lp.view_valid||lp.view!=v){if(lp.view_valid)++p.headlight_view_changes;lp.view=v;lp.inverse=inverse;lp.view_valid=true;
        for(unsigned i=0;i<lp.count;++i){auto& L=lp.cars[i];
            if(L.head){L.head_cookie=atmosphere::cookie_matrix(inverse,L.head_frame,style.head);L.head_ramp=atmosphere::ramp_matrix(inverse,L.head_frame,style.head);}
            if(L.rear){L.rear_cookie=atmosphere::cookie_matrix(inverse,L.rear_frame,style.rear);L.rear_ramp=atmosphere::ramp_matrix(inverse,L.rear_frame,style.rear);}}}
    return true;
}
// 6.9 diagnostic (GearProbe=1): every 10 frames the local player's
// gaVehicleOutputData object (0x80 bytes) and its vehicle block (0x400 bytes)
// are logged with the car's speed along its own axis, so the selected-gear
// field can be identified offline (forward / stop / reverse selected / reverse).
inline void gear_probe(Device8& d,atmosphere::Pilot& p,uint64_t frame,float along,bool reversing)noexcept{
    try{
        if(!p.gear_probe||frame<p.gear_probe_frame+10)return;p.gear_probe_frame=frame;
        bool single=false;const auto cert=courseintegration::certificate(d,single);if(!single||!cert.valid)return;
        static ps2port::HudDamageFeedReader reader;ps2port::HudLiveMemory memory;
        const auto base=uint32_t(reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr)));uint32_t payload=0,vehicle=0;const char* reason="";
        if(!reader.output_object(memory,base,cert.race_generation,payload,vehicle,reason)){if(p.first_reason(reason))session().write("{\"type\":\"atmosphere_gear_probe_gate\",\"reason\":"+quote(std::string(reason))+"}");return;}
        auto hex=[&](uint32_t address,unsigned bytes){std::string out;out.reserve(bytes*2);static const char* digits="0123456789abcdef";
            for(unsigned at=0;at<bytes;at+=128){uint8_t chunk[128]{};const unsigned n=std::min(128u,bytes-at);if(!ps2port::hud_live_read(address+at,chunk,n))return std::string();
                for(unsigned i=0;i<n;++i){out+=digits[chunk[i]>>4];out+=digits[chunk[i]&15];}}return out;};
        const auto object=hex(payload,0x80),block=hex(vehicle,0x400);if(object.empty()||block.empty())return;
        session().write("{\"type\":\"atmosphere_gear_probe\",\"frame\":"+std::to_string(frame)+",\"along\":"+std::to_string(along)+",\"reversing\":"+std::string(reversing?"true":"false")+
            ",\"payload\":"+std::to_string(payload)+",\"vehicle\":"+std::to_string(vehicle)+",\"object\":\""+object+"\",\"block\":\""+block+"\"}");
    }catch(...){}
}
// 6.7: headlights on proxy-drawn layers (PS2 grass, physics props): the same
// projector light evaluated per world vertex and added to its colour.
inline void proxy_headlights(Device8& d,atmosphere::Pilot& p,std::vector<ps2port::ObjectVertex>& v)noexcept{
    try{
        if(ps2port::perf::atmo(ps2port::perf::AtmoHeadlights))return;
        if(!p.headlight_style.enabled||p.lighting.ambient_strength>=.5f||v.empty()||!headlight_projectors(d,p,*d.native()))return;
        const auto& lp=p.lamp_projectors;const auto& style=p.headlight_style;
        for(auto& x:v){const std::array<float,3> w{x.x,x.y,x.z};std::array<float,3> add{};
            for(unsigned i=0;i<lp.count;++i){const auto& L=lp.cars[i];
                if(L.head){const float k=atmosphere::projector_light(L.head_frame,style.head,true,w)*style.intensity;if(k>0)for(unsigned c=0;c<3;++c)add[c]+=style.rgb[c]*k;}
                if(L.rear){const float k=atmosphere::projector_light(L.rear_frame,style.rear,false,w)*(L.reversing?std::max(1.1f,style.tail_intensity):style.tail_intensity*(L.brake?style.tail_brake:1.f));
                    if(k>0){const auto rgb=L.reversing?std::array<float,3>{1.f,.94f,.86f}:style.tail_rgb;for(unsigned c=0;c<3;++c)add[c]+=rgb[c]*k;}}}
            if(add[0]+add[1]+add[2]<=.002f)continue;++p.proxy_headlight_vertices;
            uint32_t out=x.color&0xff000000u;for(unsigned c=0;c<3;++c){const unsigned shift=(2-c)*8;out|=uint32_t(std::clamp(long(((x.color>>shift)&255)+std::lround(add[c]*255)),0l,255l))<<shift;}x.color=out;}
    }catch(...){}
}
struct HeadlightPass {
    struct Rs{DWORD key,old;};struct Ts{unsigned stage;DWORD key,old;};
    std::vector<Rs> rs;std::vector<Ts> ts;IDirect3DBaseTexture8* texture[2]{};bool texture_set[2]{};D3DMATRIX transform[2]{};bool transform_set[2]{};
    HRESULT set_rs(Device8& d,IDirect3DDevice8& n,DWORD key,DWORD value){for(const auto& r:rs)if(r.key==key){const auto hr=n.SetRenderState(D3DRENDERSTATETYPE(key),value);notify(d,50,pack(key,value),hr);return hr;}
        Rs r{key,0};auto hr=n.GetRenderState(D3DRENDERSTATETYPE(key),&r.old);if(FAILED(hr))return hr;rs.push_back(r);hr=n.SetRenderState(D3DRENDERSTATETYPE(key),value);notify(d,50,pack(key,value),hr);return hr;}
    HRESULT set_ts(Device8& d,IDirect3DDevice8& n,unsigned stage,DWORD key,DWORD value){for(const auto& t:ts)if(t.stage==stage&&t.key==key){const auto hr=n.SetTextureStageState(stage,D3DTEXTURESTAGESTATETYPE(key),value);notify(d,63,pack(stage,key,value),hr);return hr;}
        Ts t{stage,key,0};auto hr=n.GetTextureStageState(stage,D3DTEXTURESTAGESTATETYPE(key),&t.old);if(FAILED(hr))return hr;ts.push_back(t);hr=n.SetTextureStageState(stage,D3DTEXTURESTAGESTATETYPE(key),value);notify(d,63,pack(stage,key,value),hr);return hr;}
    HRESULT set_texture(Device8& d,IDirect3DDevice8& n,unsigned i,IDirect3DTexture8* t){if(!texture_set[i]){auto hr=n.GetTexture(i+1,&texture[i]);if(FAILED(hr))return hr;texture_set[i]=true;}
        const auto hr=n.SetTexture(i+1,t);notify(d,61,pack(i+1,t),hr);return hr;}
    HRESULT set_transform(Device8& d,IDirect3DDevice8& n,unsigned i,const atmosphere::Mat4& m){const auto type=D3DTRANSFORMSTATETYPE(D3DTS_TEXTURE1+i);
        if(!transform_set[i]){auto hr=n.GetTransform(type,&transform[i]);if(FAILED(hr))return hr;transform_set[i]=true;}
        D3DMATRIX x{};std::memcpy(&x,m.data(),64);const auto hr=n.SetTransform(type,&x);notify(d,37,pack(type,&x),hr);return hr;}
    HRESULT restore(Device8& d,IDirect3DDevice8& n)noexcept{HRESULT result=S_OK;auto keep=[&](HRESULT hr){if(FAILED(hr)&&SUCCEEDED(result))result=hr;};
        for(unsigned i=0;i<2;++i)if(transform_set[i]){const auto type=D3DTRANSFORMSTATETYPE(D3DTS_TEXTURE1+i);const auto hr=n.SetTransform(type,&transform[i]);notify(d,37,pack(type,&transform[i]),hr);keep(hr);transform_set[i]=false;}
        for(unsigned i=0;i<2;++i)if(texture_set[i]){const auto hr=n.SetTexture(i+1,texture[i]);notify(d,61,pack(i+1,texture[i]),hr);keep(hr);if(texture[i])texture[i]->Release();texture[i]=nullptr;texture_set[i]=false;}
        for(auto it=ts.rbegin();it!=ts.rend();++it){const auto hr=n.SetTextureStageState(it->stage,D3DTEXTURESTAGESTATETYPE(it->key),it->old);notify(d,63,pack(it->stage,it->key,it->old),hr);keep(hr);}ts.clear();
        for(auto it=rs.rbegin();it!=rs.rend();++it){const auto hr=n.SetRenderState(D3DRENDERSTATETYPE(it->key),it->old);notify(d,50,pack(it->key,it->old),hr);keep(hr);}rs.clear();
        return result;}
    ~HeadlightPass(){for(auto*& t:texture)if(t){t->Release();t=nullptr;}}
};
// PERF-ATMO2: one lamp of a car (head or rear) as the pass/map need it.
struct HeadlightLamp{bool on;const atmosphere::LightFrame* f;const atmosphere::Projector* pr;const atmosphere::Mat4* cookie;const atmosphere::Mat4* ramp;IDirect3DTexture8* texture;std::array<float,3> rgb;float intensity;bool brake;
    DWORD factor()const noexcept{DWORD c=0xff000000u;for(unsigned i=0;i<3;++i)c|=DWORD(std::clamp(std::lround(rgb[i]*intensity*.5f*255),0l,255l))<<((2-i)*8);return c;}};
inline HeadlightLamp headlight_lamp(const atmosphere::Pilot& p,const atmosphere::Pilot::CarLamps& L,bool head)noexcept{
    const auto& style=p.headlight_style;
    if(head)return {L.head,&L.head_frame,&style.head,&L.head_cookie,&L.head_ramp,p.headlight_cookie_texture,style.rgb,style.intensity,false};
    return {L.rear,&L.rear_frame,&style.rear,&L.rear_cookie,&L.rear_ramp,p.tail_cookie_texture,L.reversing?std::array<float,3>{1.f,.94f,.86f}:style.tail_rgb,
            L.reversing?std::max(1.1f,style.tail_intensity):style.tail_intensity*(L.brake?style.tail_brake:1.f),L.brake};
}
// PERF-ATMO2 top-down headlight map: kHeadlightMapSize^2 texels over +-kHeadlightMapHalf m around the
// camera (snapped to texels). Every lamp is drawn as one world quad on its car's ground plane with the
// SAME cookie/ramp projector stages as the old per-draw pass, at half energy (the course pass doubles it).
// A vertical fade (HeadlightMapBand/Fade metres around the reaching car) keeps canopies and bridges dark.
inline constexpr unsigned kHeadlightMapSize=1024;inline constexpr float kHeadlightMapHalf=240.f;
inline HRESULT headlight_map_render(Device8& d,atmosphere::Pilot& p,IDirect3DDevice8& n,uint64_t frame)noexcept{
    p.headlight_map_frame=frame;p.headlight_map_ok=false;
    auto failed=[&](const char* why,HRESULT hr){p.headlight_map_failed=true;session().write("{\"type\":\"atmosphere_headlight_map\",\"enabled\":false,\"reason\":"+quote(std::string(why))+",\"hresult\":"+std::to_string(uint32_t(hr))+"}");return S_OK;};
    if(!p.headlight_map){const auto hr=n.CreateTexture(kHeadlightMapSize,kHeadlightMapSize,1,D3DUSAGE_RENDERTARGET,D3DFMT_A8R8G8B8,D3DPOOL_DEFAULT,&p.headlight_map);
        if(FAILED(hr)||!p.headlight_map){p.headlight_map=nullptr;return failed("map_target_unavailable",hr);}}
    if(!p.headlight_height_ramp){const auto& style=p.headlight_style;
        auto hr=n.CreateTexture(256,4,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&p.headlight_height_ramp);if(FAILED(hr)||!p.headlight_height_ramp){p.headlight_height_ramp=nullptr;return failed("height_ramp_unavailable",hr);}
        D3DLOCKED_RECT l{};hr=p.headlight_height_ramp->LockRect(0,&l,nullptr,0);if(FAILED(hr)||!l.pBits){if(SUCCEEDED(hr))p.headlight_height_ramp->UnlockRect(0);return failed("height_ramp_lock",hr);}
        for(unsigned y=0;y<4;++y)for(unsigned x=0;x<256;++x){const float dy=std::abs(((x+.5f)/256-.5f)*2*style.map_fade);
            const float v=dy<=style.map_band?1.f:std::clamp(1-(dy-style.map_band)/(style.map_fade-style.map_band),0.f,1.f);const DWORD c=DWORD(std::lround(v*255)),px=0xff000000u|c<<16|c<<8|c;
            std::memcpy(static_cast<uint8_t*>(l.pBits)+size_t(y)*l.Pitch+x*4,&px,4);}
        hr=p.headlight_height_ramp->UnlockRect(0);if(FAILED(hr))return failed("height_ramp_unlock",hr);}
    const auto& lp=p.lamp_projectors;
    const float texel=2*kHeadlightMapHalf/kHeadlightMapSize;
    p.headlight_map_cx=std::round(lp.inverse[12]/texel)*texel;p.headlight_map_cz=std::round(lp.inverse[14]/texel)*texel;
    const float top=lp.inverse[13]+2000.f,cx=p.headlight_map_cx,cz=p.headlight_map_cz;
    // Looking down -Y: camera x = world x - cx, camera y = world z - cz, depth = top - world y.
    const atmosphere::Mat4 view{1,0,0,0, 0,0,-1,0, 0,1,0,0, -cx,-cz,top,1};atmosphere::Mat4 inverse{};if(!atmosphere::mat_inverse(view,inverse))return failed("map_view_singular",E_FAIL);
    D3DMATRIX projection{};projection._11=projection._22=1/kHeadlightMapHalf;projection._33=1.f/8000.f;projection._44=1;
    courseintegration::Ref<IDirect3DSurface8> surface;{const auto hr=p.headlight_map->GetSurfaceLevel(0,&surface.p);if(FAILED(hr)||!surface.p)return failed("map_surface",hr);}
    D3DMATRIX saved[3]{};const D3DTRANSFORMSTATETYPE kinds[3]{D3DTS_VIEW,D3DTS_PROJECTION,D3DTS_WORLD};
    for(unsigned i=0;i<3;++i)if(FAILED(n.GetTransform(kinds[i],&saved[i])))return failed("transform_capture",E_FAIL);
    const auto writer=[](void* context,uint32_t slot,const Args& args,HRESULT hr)noexcept{notify(*static_cast<Device8*>(context),slot,args,hr);};
    atmosphere::SunTransaction tx;HRESULT hr=tx.capture(n,&d,writer);if(FAILED(hr))return failed("state_capture",hr);
    HeadlightPass stages;   // texture stages 1/2 + their texture matrices, restored below
    auto rs=[&](DWORD k,DWORD v){if(SUCCEEDED(hr))hr=tx.set(n,0,0,k,v);};auto ts=[&](unsigned st,DWORD k,DWORD v){if(SUCCEEDED(hr))hr=tx.set(n,1,st,k,v);};
    bool transforms=false;
    {const D3DVIEWPORT8 viewport{0,0,kHeadlightMapSize,kHeadlightMapSize,0,1};hr=tx.target(n,surface.p,nullptr,viewport);}
    if(SUCCEEDED(hr))hr=n.Clear(0,nullptr,D3DCLEAR_TARGET,0,1,0);
    rs(D3DRS_ZENABLE,D3DZB_FALSE);rs(D3DRS_ZWRITEENABLE,FALSE);rs(D3DRS_ALPHATESTENABLE,FALSE);rs(D3DRS_ALPHABLENDENABLE,TRUE);rs(D3DRS_SRCBLEND,D3DBLEND_ONE);rs(D3DRS_DESTBLEND,D3DBLEND_ONE);
    rs(D3DRS_BLENDOP,D3DBLENDOP_ADD);rs(D3DRS_CULLMODE,D3DCULL_NONE);rs(D3DRS_FILLMODE,D3DFILL_SOLID);rs(D3DRS_LIGHTING,FALSE);rs(D3DRS_FOGENABLE,FALSE);rs(D3DRS_STENCILENABLE,FALSE);
    rs(D3DRS_CLIPPING,TRUE);rs(D3DRS_CLIPPLANEENABLE,0);rs(D3DRS_COLORWRITEENABLE,15);rs(D3DRS_SPECULARENABLE,FALSE);rs(D3DRS_VERTEXBLEND,D3DVBF_DISABLE);rs(D3DRS_INDEXEDVERTEXBLENDENABLE,FALSE);
    rs(D3DRS_WRAP0,0);rs(D3DRS_WRAP1,0);rs(D3DRS_WRAP2,0);rs(D3DRS_MULTISAMPLEANTIALIAS,FALSE);
    if(SUCCEEDED(hr))hr=tx.set(n,3,0,0,D3DFVF_XYZ);if(SUCCEEDED(hr))hr=tx.set(n,4,0,0,0);if(SUCCEEDED(hr))hr=tx.set(n,2,0,0,0,nullptr);
    ts(0,D3DTSS_COLOROP,D3DTOP_SELECTARG1);ts(0,D3DTSS_COLORARG1,D3DTA_TFACTOR);ts(0,D3DTSS_ALPHAOP,D3DTOP_SELECTARG1);ts(0,D3DTSS_ALPHAARG1,D3DTA_TFACTOR);ts(0,D3DTSS_RESULTARG,D3DTA_CURRENT);
    ts(0,D3DTSS_TEXTURETRANSFORMFLAGS,D3DTTFF_DISABLE);
    for(unsigned st=1;st<3;++st){ts(st,D3DTSS_COLOROP,D3DTOP_MODULATE);ts(st,D3DTSS_COLORARG1,D3DTA_TEXTURE);ts(st,D3DTSS_COLORARG2,D3DTA_CURRENT);
        ts(st,D3DTSS_ALPHAOP,D3DTOP_SELECTARG1);ts(st,D3DTSS_ALPHAARG1,D3DTA_CURRENT);ts(st,D3DTSS_RESULTARG,D3DTA_CURRENT);ts(st,D3DTSS_TEXCOORDINDEX,D3DTSS_TCI_CAMERASPACEPOSITION);
        ts(st,D3DTSS_TEXTURETRANSFORMFLAGS,st==1?(D3DTTFF_COUNT3|D3DTTFF_PROJECTED):D3DTTFF_COUNT2);ts(st,D3DTSS_ADDRESSU,D3DTADDRESS_CLAMP);ts(st,D3DTSS_ADDRESSV,D3DTADDRESS_CLAMP);
        ts(st,D3DTSS_MINFILTER,D3DTEXF_LINEAR);ts(st,D3DTSS_MAGFILTER,D3DTEXF_LINEAR);ts(st,D3DTSS_MIPFILTER,D3DTEXF_NONE);}
    ts(3,D3DTSS_COLOROP,D3DTOP_DISABLE);ts(3,D3DTSS_ALPHAOP,D3DTOP_DISABLE);
    if(SUCCEEDED(hr)){transforms=true;D3DMATRIX v{};std::memcpy(&v,view.data(),64);D3DMATRIX identity{};identity._11=identity._22=identity._33=identity._44=1;
        const std::pair<D3DTRANSFORMSTATETYPE,const D3DMATRIX*> sets[3]{{D3DTS_VIEW,&v},{D3DTS_PROJECTION,&projection},{D3DTS_WORLD,&identity}};
        for(const auto& set:sets)if(SUCCEEDED(hr)){hr=n.SetTransform(set.first,set.second);notify(d,37,pack(set.first,set.second),hr);}}
    unsigned lamps_drawn=0;
    for(unsigned ci=0;ci<lp.count&&SUCCEEDED(hr);++ci){const auto& L=lp.cars[ci];
        for(bool head:{true,false}){if(FAILED(hr))break;const auto lamp=headlight_lamp(p,L,head);if(!lamp.on)continue;
            const float r=lamp.pr->range+2,x=lamp.f->position[0],z=lamp.f->position[2],y=L.car[13];
            if(std::abs(x-cx)+r>kHeadlightMapHalf||std::abs(z-cz)+r>kHeadlightMapHalf)continue;   // never let a pool touch the clamped border
            rs(D3DRS_TEXTUREFACTOR,lamp.factor());
            if(SUCCEEDED(hr))hr=stages.set_texture(d,n,0,lamp.texture);if(SUCCEEDED(hr))hr=stages.set_texture(d,n,1,p.headlight_ramp_texture);
            if(SUCCEEDED(hr))hr=stages.set_transform(d,n,0,atmosphere::cookie_matrix(inverse,*lamp.f,*lamp.pr));
            if(SUCCEEDED(hr))hr=stages.set_transform(d,n,1,atmosphere::ramp_matrix(inverse,*lamp.f,*lamp.pr));
            const float quad[12]{x-r,y,z-r, x+r,y,z-r, x-r,y,z+r, x+r,y,z+r};
            if(SUCCEEDED(hr)){hr=tx.draw(n,quad,12);if(SUCCEEDED(hr))++lamps_drawn;}}}
    HRESULT restored=stages.restore(d,n);
    if(transforms)for(unsigned i=0;i<3;++i){const auto r2=n.SetTransform(kinds[i],&saved[i]);notify(d,37,pack(kinds[i],&saved[i]),r2);if(FAILED(r2)&&SUCCEEDED(restored))restored=r2;}
    {const auto r3=tx.restore(n);if(FAILED(r3)&&SUCCEEDED(restored))restored=r3;}
    if(FAILED(restored))return restored;
    if(FAILED(hr))return failed("map_draw",hr);
    p.headlight_map_ok=true;++p.headlight_map_renders;
    if(p.first_reason("headlight_map"))session().write("{\"type\":\"atmosphere_headlight_map\",\"enabled\":true,\"size\":"+std::to_string(kHeadlightMapSize)+",\"half_metres\":"+std::to_string(kHeadlightMapHalf)+",\"lamps\":"+std::to_string(lamps_drawn)+",\"frame\":"+std::to_string(frame)+"}");
    return S_OK;
}
inline HRESULT headlight_world(Device8& d,HRESULT draw_hr,uintptr_t pc)noexcept{
    if(ps2port::perf::atmo(ps2port::perf::AtmoHeadlights))return S_OK;   // PERF-ATMO1 diagnostic A/B
    auto* p=pilot(d);if(!p||!p->enabled()||!p->headlight_style.enabled||FAILED(draw_hr)||!p->lighting.active()||
       pc!=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr))+groundintegration::COURSE_DRAW_RETURN_RVA||!d.trace.scene_active||
       d.trace.shadow.recording||d.trace.effective_shadow.recording||GetCurrentThreadId()!=d.trace.render_thread_id())return S_OK;
    auto& c=p->headlight_candidate;const auto frame=d.trace.frame_number();if(c.frame!=frame)return S_OK;
    const auto cand=c;c.frame=UINT64_MAX;   // consumed: exactly the draw that just ran
    ps2port::perf::Timer perf_timer(ps2port::perf::AtmoHeadlight);
    try{
        auto& n=*d.native();
        if(!p->headlight_caps){D3DCAPS8 caps{};p->headlight_caps=SUCCEEDED(n.GetDeviceCaps(&caps))&&caps.MaxTextureBlendStages>=4&&caps.MaxSimultaneousTextures>=3&&
            (caps.TextureCaps&D3DPTEXTURECAPS_PROJECTED)&&(caps.TextureOpCaps&D3DTEXOPCAPS_MODULATE2X)&&(caps.DestBlendCaps&D3DPBLENDCAPS_ONE)?1:2;
            session().write("{\"type\":\"atmosphere_headlight_caps\",\"supported\":"+std::string(p->headlight_caps==1?"true":"false")+"}");}
        ++p->headlight_candidates;
        if(frame>=p->headlight_log_frame+300){p->headlight_log_frame=frame;unsigned reversing=0,braking=0;for(unsigned i=0;i<p->lamp_projectors.count;++i){reversing+=p->lamp_projectors.cars[i].reversing;braking+=p->lamp_projectors.cars[i].brake;}
            session().write("{\"type\":\"atmosphere_headlight_stats\",\"frame\":"+std::to_string(frame)+",\"candidates\":"+std::to_string(p->headlight_candidates)+",\"draws\":"+std::to_string(p->headlight_draws)+",\"map_renders\":"+std::to_string(p->headlight_map_renders)+",\"map_passes\":"+std::to_string(p->headlight_map_passes)+",\"culled\":"+std::to_string(p->headlight_culled)+",\"no_car_frames\":"+std::to_string(p->headlight_no_car)+",\"view_changes\":"+std::to_string(p->headlight_view_changes)+",\"off_target\":"+std::to_string(p->headlight_off_target)+",\"cars\":"+std::to_string(p->lamp_projectors.count)+",\"reversing\":"+std::to_string(reversing)+",\"braking\":"+std::to_string(braking)+",\"proxy_vertices\":"+std::to_string(p->proxy_headlight_vertices)+",\"lamp_points\":"+std::to_string(p->lamp_points.size())+",\"gear_matched\":"+std::to_string(p->gear_matched)+",\"gear_reverse\":"+std::to_string(p->gear_reverse)+",\"pose_held\":"+std::to_string(p->headlight_held)+",\"gaps\":"+std::to_string(p->headlight_gaps)+",\"rig_matches\":"+std::to_string(p->rig_matches)+",\"rig_misses\":"+std::to_string(p->rig_misses)+",\"rig_points\":"+std::to_string(p->rig_points)+",\"rig_rematches\":"+std::to_string(p->rig_rematches)+",\"rig_blight_off\":"+std::to_string(p->rig_blight_off)+",\"lens_night_draws\":"+std::to_string(p->lens_night_draws)+",\"rear_tints\":"+std::to_string(p->lamp_rear_tints)+",\"reverse_vertices\":"+std::to_string(p->lamp_reverse_vertices)+"}");}
        {courseintegration::Ref<IDirect3DSurface8> target,back;if(FAILED(n.GetRenderTarget(&target.p))||FAILED(n.GetBackBuffer(0,D3DBACKBUFFER_TYPE_MONO,&back.p))||!courseintegration::same_identity(target.p,back.p)){++p->headlight_off_target;return S_OK;}}
        if(p->headlight_caps!=1||FAILED(headlight_textures(n,*p))||!headlight_projectors(d,*p,n))return S_OK;
        DWORD fvf=0,pixel=1;if(FAILED(n.GetVertexShader(&fvf))||!type_supports_headlight(fvf)||FAILED(n.GetPixelShader(&pixel))||pixel)return S_OK;
        const auto& lp=p->lamp_projectors;const auto& style=p->headlight_style;
        // One additive pass over the draw that just ran: stage 0 = its own diffuse texture x TFACTOR,
        // stages 1/2 = textures t1/t2 addressed by camera-space position through m1/m2.
        auto issue=[&](IDirect3DTexture8* t1,IDirect3DTexture8* t2,const atmosphere::Mat4& m1,const atmosphere::Mat4& m2,DWORD factor,bool projected,const char* what,unsigned car,bool brake)->HRESULT{
            HeadlightPass pass;HRESULT hr=S_OK;
            auto rs=[&](DWORD k,DWORD v){if(SUCCEEDED(hr))hr=pass.set_rs(d,n,k,v);};auto ts=[&](unsigned st,DWORD k,DWORD v){if(SUCCEEDED(hr))hr=pass.set_ts(d,n,st,k,v);};
            rs(D3DRS_ZWRITEENABLE,FALSE);rs(D3DRS_ZFUNC,D3DCMP_LESSEQUAL);rs(D3DRS_ALPHABLENDENABLE,TRUE);rs(D3DRS_SRCBLEND,D3DBLEND_SRCALPHA);rs(D3DRS_DESTBLEND,D3DBLEND_ONE);
            rs(D3DRS_BLENDOP,D3DBLENDOP_ADD);rs(D3DRS_FOGCOLOR,0);rs(D3DRS_TEXTUREFACTOR,factor);rs(D3DRS_WRAP1,0);rs(D3DRS_WRAP2,0);rs(D3DRS_SPECULARENABLE,FALSE);
            ts(0,D3DTSS_COLOROP,D3DTOP_MODULATE);ts(0,D3DTSS_COLORARG1,D3DTA_TEXTURE);ts(0,D3DTSS_COLORARG2,D3DTA_TFACTOR);ts(0,D3DTSS_ALPHAOP,D3DTOP_SELECTARG1);ts(0,D3DTSS_ALPHAARG1,D3DTA_TEXTURE);ts(0,D3DTSS_RESULTARG,D3DTA_CURRENT);
            for(unsigned st=1;st<3;++st){ts(st,D3DTSS_COLOROP,st==1?D3DTOP_MODULATE:D3DTOP_MODULATE2X);ts(st,D3DTSS_COLORARG1,D3DTA_TEXTURE);ts(st,D3DTSS_COLORARG2,D3DTA_CURRENT);
                ts(st,D3DTSS_ALPHAOP,D3DTOP_SELECTARG1);ts(st,D3DTSS_ALPHAARG1,D3DTA_CURRENT);ts(st,D3DTSS_RESULTARG,D3DTA_CURRENT);ts(st,D3DTSS_TEXCOORDINDEX,D3DTSS_TCI_CAMERASPACEPOSITION);
                ts(st,D3DTSS_TEXTURETRANSFORMFLAGS,st==1&&projected?(D3DTTFF_COUNT3|D3DTTFF_PROJECTED):D3DTTFF_COUNT2);ts(st,D3DTSS_ADDRESSU,D3DTADDRESS_CLAMP);ts(st,D3DTSS_ADDRESSV,D3DTADDRESS_CLAMP);
                ts(st,D3DTSS_MINFILTER,D3DTEXF_LINEAR);ts(st,D3DTSS_MAGFILTER,D3DTEXF_LINEAR);ts(st,D3DTSS_MIPFILTER,D3DTEXF_NONE);}
            ts(3,D3DTSS_COLOROP,D3DTOP_DISABLE);ts(3,D3DTSS_ALPHAOP,D3DTOP_DISABLE);
            if(SUCCEEDED(hr))hr=pass.set_texture(d,n,0,t1);if(SUCCEEDED(hr))hr=pass.set_texture(d,n,1,t2);
            if(SUCCEEDED(hr))hr=pass.set_transform(d,n,0,m1);if(SUCCEEDED(hr))hr=pass.set_transform(d,n,1,m2);
            if(SUCCEEDED(hr))hr=n.DrawIndexedPrimitive(D3DPT_TRIANGLELIST,cand.min,cand.vertices,cand.start,cand.count);
            const auto restored=pass.restore(d,n);if(FAILED(restored))return restored;
            if(SUCCEEDED(hr))++p->headlight_draws;
            if(p->first_reason(what))session().write("{\"type\":\"atmosphere_headlight\",\"pass\":"+quote(std::string(what))+",\"car\":"+std::to_string(car)+",\"frame\":"+std::to_string(frame)+",\"hresult\":"+std::to_string(uint32_t(hr))+",\"brake\":"+std::string(brake?"true":"false")+"}");
            return S_OK;};
        // PERF-ATMO2: course draws read every pool from the per-frame top-down map in ONE pass
        // (was one pass per car and lamp, ~200 a frame at night). Car bodies keep the exact projectors.
        if(style.map&&!cand.instance&&!p->headlight_map_failed){
            if(p->headlight_map_frame!=frame){const auto mr=headlight_map_render(d,*p,n,frame);if(FAILED(mr))return repair(d);}
            if(p->headlight_map_ok){
                bool any=false;float best=1e30f,height=0;
                for(unsigned ci=0;ci<lp.count;++ci){const auto& L=lp.cars[ci];
                    const bool head=L.head&&atmosphere::light_reaches(L.head_frame,style.head,cand.centre,cand.radius),rear=L.rear&&atmosphere::light_reaches(L.rear_frame,style.rear,cand.centre,cand.radius);
                    if(!head&&!rear)continue;any=true;const float dx=L.car[12]-cand.centre[0],dz=L.car[14]-cand.centre[2],dd=dx*dx+dz*dz;if(dd<best){best=dd;height=L.car[13];}}
                if(!any){++p->headlight_culled;return S_OK;}
                atmosphere::Mat4 to_map{},to_height{};const float half=kHeadlightMapHalf,fade=style.map_fade;
                to_map[0]=.5f/half;to_map[12]=.5f-p->headlight_map_cx*.5f/half;to_map[9]=-.5f/half;to_map[13]=.5f+p->headlight_map_cz*.5f/half;to_map[15]=1;
                to_height[4]=.5f/fade;to_height[12]=.5f-height*.5f/fade;to_height[13]=.5f;to_height[15]=1;
                const auto hr=issue(p->headlight_map,p->headlight_height_ramp,atmosphere::mat_mul(lp.inverse,to_map),atmosphere::mat_mul(lp.inverse,to_height),0xffffffffu,false,"headlight_map_pass",0,false);
                if(FAILED(hr))return repair(d);++p->headlight_map_passes;return S_OK;}
        }
        for(unsigned ci=0;ci<lp.count;++ci){const auto& L=lp.cars[ci];
          if(cand.instance&&cand.instance==L.instance)continue;    // a car never lights itself
          const HeadlightLamp lamps[2]{headlight_lamp(*p,L,true),headlight_lamp(*p,L,false)};
          for(const auto& lamp:lamps){
            if(!lamp.on)continue;
            if(cand.instance&&lamp.texture!=p->headlight_cookie_texture)continue;   // 6.8: tail pools light the ground only
            if(!atmosphere::light_reaches(*lamp.f,*lamp.pr,cand.centre,cand.radius)){++p->headlight_culled;continue;}
            const char* what=cand.instance?(lamp.texture==p->headlight_cookie_texture?"headlight_on_car":"tail_light_on_car"):(lamp.texture==p->headlight_cookie_texture?"headlight_pass":"tail_light_pass");
            const auto hr=issue(lamp.texture,p->headlight_ramp_texture,*lamp.cookie,*lamp.ramp,lamp.factor(),true,what,ci,lamp.brake);if(FAILED(hr))return repair(d);
          }
        }
        return S_OK;
    }catch(...){return repair(d);}
}
inline void sun_world(Device8& d,HRESULT hr,uintptr_t pc)noexcept{
    (void)headlight_world(d,hr,pc);
    auto* p=pilot(d);if(!p||!p->enabled()||!(p->sun_disk||p->sun_halo||p->sun_flare||p->sun_style.vignette>0||p->stars.count||p->glint_style.enabled)||FAILED(hr)||!d.trace.scene_active||
        pc!=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr))+groundintegration::COURSE_DRAW_RETURN_RVA||
        GetCurrentThreadId()!=d.trace.render_thread_id())return;
    ps2port::perf::Timer perf_timer(ps2port::perf::AtmoSunWorld);
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
// ATMOSPHERE6.2 night particles. Retail particle batches (dust clouds RVA
// 0x164ed0, stones/mud 0x1722ee) are DrawPrimitive triangle lists from one
// dynamic VB: FVF 0x142 world-space vertices, texture*diffuse, alpha blended,
// no depth writes, no fog, no lighting, so they glow at night. Night only
// (AmbientStrength < .5): stage 1 multiplies the colour by the moonlit world
// energy (ambient + half the moon); alpha, blend, UV, vertices untouched.
inline constexpr uint32_t PARTICLE_DUST_RVA=0x164ed0,PARTICLE_STONE_RVA=0x1722ee;
inline uint32_t particle_night_factor(const atmosphere::Lighting& s)noexcept{
    uint32_t out=0xff000000u;
    for(unsigned i=0;i<3;++i){const float gain=std::clamp((s.ambient[i]*s.ambient_strength+s.sun[i]*s.sun_strength*.5f)*s.exposure*s.world_brightness,0.f,1.f);
        out|=uint32_t(std::lround(gain*255))<<((2-i)*8);}
    return out;
}
inline HRESULT particle_begin(Device8& d,D3DPRIMITIVETYPE type,UINT,UINT count,uintptr_t pc,bool& pending)noexcept{
    pending=false;auto* p=pilot(d);
    const auto exe=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    if(!p||!p->enabled()||!p->lighting.active()||p->lighting.ambient_strength>=.5f||type!=D3DPT_TRIANGLELIST||!count||(pc!=exe+PARTICLE_DUST_RVA&&pc!=exe+PARTICLE_STONE_RVA)||
       !d.trace.scene_active||d.trace.shadow.recording||d.trace.effective_shadow.recording||GetCurrentThreadId()!=d.trace.render_thread_id()||p->particle.pending)return S_OK;
    try{
        auto& n=*d.native();bool single=false;const auto cert=courseintegration::certificate(d,single);if(!single||!cert.valid)return S_OK;
        DWORD fvf=0,pixel=1;if(FAILED(n.GetVertexShader(&fvf))||fvf!=0x142||FAILED(n.GetPixelShader(&pixel))||pixel||!groundintegration::render(d,n,D3DRS_ALPHABLENDENABLE,TRUE)||
           !groundintegration::render(d,n,D3DRS_LIGHTING,FALSE)||!groundintegration::stage(d,n,0,D3DTSS_COLOROP,D3DTOP_MODULATE)||!groundintegration::stage(d,n,0,D3DTSS_COLORARG1,D3DTA_TEXTURE)||
           !groundintegration::stage(d,n,0,D3DTSS_COLORARG2,D3DTA_DIFFUSE)||!groundintegration::stage(d,n,1,D3DTSS_COLOROP,D3DTOP_DISABLE))return S_OK;
        auto& s=p->particle;constexpr D3DTEXTURESTAGESTATETYPE keys[]{D3DTSS_COLOROP,D3DTSS_COLORARG1,D3DTSS_COLORARG2,D3DTSS_ALPHAOP,D3DTSS_ALPHAARG1};
        for(unsigned i=0;i<5;++i)if(FAILED(n.GetTextureStageState(1,keys[i],&s.stage[i])))return S_OK;
        if(FAILED(n.GetTextureStageState(2,D3DTSS_COLOROP,&s.stage2))||s.stage2!=D3DTOP_DISABLE||FAILED(n.GetRenderState(D3DRS_TEXTUREFACTOR,&s.factor)))return S_OK;
        const DWORD factor=particle_night_factor(p->lighting);
        s.pending=pending=true;
        auto hr=n.SetRenderState(D3DRS_TEXTUREFACTOR,factor);notify(d,50,pack(D3DRS_TEXTUREFACTOR,factor),hr);
        const DWORD values[]{D3DTOP_MODULATE,D3DTA_CURRENT,D3DTA_TFACTOR,D3DTOP_SELECTARG1,D3DTA_CURRENT};
        for(unsigned i=0;i<5&&SUCCEEDED(hr);++i){hr=n.SetTextureStageState(1,keys[i],values[i]);notify(d,63,pack(1u,keys[i],values[i]),hr);}
        // The wrapper returns before the draw on failure, so restore here.
        if(FAILED(hr)){pending=false;HRESULT restored=S_OK;
            for(int i=4;i>=0;--i){const auto r=n.SetTextureStageState(1,keys[i],s.stage[i]);notify(d,63,pack(1u,keys[i],s.stage[i]),r);if(FAILED(r))restored=r;}
            {const auto r=n.SetRenderState(D3DRS_TEXTUREFACTOR,s.factor);notify(d,50,pack(D3DRS_TEXTUREFACTOR,s.factor),r);if(FAILED(r))restored=r;}
            if(SUCCEEDED(restored)){s.pending=false;return S_OK;}return repair(d);}
        ++p->particle_draws;
        if(p->first_reason(pc==exe+PARTICLE_DUST_RVA?"night_particles_dust":"night_particles_stones"))session().write("{\"type\":\"atmosphere_night_particles\",\"site\":"+quote(std::string(pc==exe+PARTICLE_DUST_RVA?"dust":"stones"))+",\"factor\":"+std::to_string(factor)+",\"triangles\":"+std::to_string(count)+",\"frame\":"+std::to_string(d.trace.frame_number())+",\"alpha_unchanged\":true}");
        return S_OK;
    }catch(...){return repair(d);}
}
inline HRESULT particle_end(Device8& d)noexcept{
    auto* p=pilot(d);if(!p||!p->particle.pending)return S_OK;
    auto& s=p->particle;auto& n=*d.native();constexpr D3DTEXTURESTAGESTATETYPE keys[]{D3DTSS_COLOROP,D3DTSS_COLORARG1,D3DTSS_COLORARG2,D3DTSS_ALPHAOP,D3DTSS_ALPHAARG1};
    HRESULT result=S_OK;
    for(int i=4;i>=0;--i){const auto hr=n.SetTextureStageState(1,keys[i],s.stage[i]);notify(d,63,pack(1u,keys[i],s.stage[i]),hr);if(FAILED(hr)&&SUCCEEDED(result))result=hr;}
    {const auto hr=n.SetRenderState(D3DRS_TEXTUREFACTOR,s.factor);notify(d,50,pack(D3DRS_TEXTUREFACTOR,s.factor),hr);if(FAILED(hr)&&SUCCEEDED(result))result=hr;}
    if(SUCCEEDED(result))s.pending=false;else return repair(d);
    return S_OK;
}
// 6.6 GT3-like glints at every lamp lens collected this frame (all cars).
inline HRESULT lamp_glints(Device8& d,atmosphere::Pilot& p,IDirect3DDevice8& n,UINT width,UINT height,uint64_t frame)noexcept{
    const auto& g=p.glint_style;if(!g.enabled||p.lamp_points_frame!=frame||p.lamp_points.empty()||!width||!height)return S_FALSE;
    const auto& view=p.sun.proof.view;const auto& proj=p.sun.proof.projection;if(proj._11<=0||proj._22<=0||proj._34!=1||proj._44!=0)return S_FALSE;
    atmosphere::Mat4 v{},inverse{};std::memcpy(v.data(),&view,64);if(!atmosphere::mat_inverse(v,inverse))return S_FALSE;
    const std::array<float,3> eye{inverse[12],inverse[13],inverse[14]};const float ppt=height*.5f*proj._22;
    auto pixels=[&](float degrees){return std::tan(degrees*.017453293f)*ppt;};
    std::vector<atmosphere::SunVertex> glow,streak;glow.reserve(p.lamp_points.size()*12);streak.reserve(p.lamp_points.size()*12);
    auto colour=[](const std::array<float,3>& rgb,float k){DWORD c=0xff000000u;for(unsigned i=0;i<3;++i)c|=DWORD(std::clamp(std::lround(rgb[i]*k*255),0l,255l))<<((2-i)*8);return c;};
    const auto& style=p.headlight_style;const auto& lp=p.lamp_projectors;
    for(const auto& l:p.lamp_points){
        std::array<float,3> to{eye[0]-l.world[0],eye[1]-l.world[1],eye[2]-l.world[2]};const float dist=std::sqrt(atmosphere::dot3(to,to));if(dist<.5f||dist>400)continue;
        for(auto& x:to)x/=dist;const float facing=std::clamp(atmosphere::dot3(to,l.axis),0.f,1.f);
        // 6.13 roles: head (front white), tail (rear red, always), brake (breaklightson parts, present only
        // while braking), reverse (rear white, only while the car is in reverse).
        const auto* owner_lamps=lp.frame!=UINT64_MAX&&lp.frame+2>=frame?lp.find(l.instance):nullptr;
        if((l.kind==3||l.kind==4)&&!(owner_lamps&&owner_lamps->reversing))continue;
        if(l.kind==4){bool white=false;for(const auto& o:p.lamp_points)if(o.instance==l.instance&&o.kind==3){white=true;break;}if(white)continue;}   // fallback only
        const float rear_k=l.kind==2?g.rear*g.brake:l.kind>=3?g.reverse:g.rear*.55f;
        float k=(l.front?g.front*std::pow(facing,1.6f):rear_k*std::pow(facing,1.2f))+.06f;
        k*=1/(1+(dist/90)*(dist/90));if(k<.02f)continue;
        // Pull the sprite 0.35 m toward the camera so the lens itself never hides it.
        std::array<float,3> w{l.world[0]+to[0]*.35f,l.world[1]+to[1]*.35f,l.world[2]+to[2]*.35f};
        const float x=w[0]*view._11+w[1]*view._21+w[2]*view._31+view._41,y=w[0]*view._12+w[1]*view._22+w[2]*view._32+view._42,z=w[0]*view._13+w[1]*view._23+w[2]*view._33+view._43;
        if(z<=.3f)continue;const float nx=(x*proj._11+z*proj._31)/z,ny=(y*proj._22+z*proj._32)/z,nz=(z*proj._33+proj._43)/z;
        if(!std::isfinite(nx+ny+nz)||std::abs(nx)>1.1f||std::abs(ny)>1.1f||nz<=0||nz>=1)continue;
        const float px=(nx+1)*width*.5f,py=(1-ny)*height*.5f,rhw=1/z;
        auto quad=[&](std::vector<atmosphere::SunVertex>& out,float rx,float ry,DWORD c){
            const atmosphere::SunVertex a{px-rx-.5f,py-ry-.5f,nz,rhw,c,0,0,0,0},b{px+rx-.5f,py-ry-.5f,nz,rhw,c,1,0,0,0},e{px-rx-.5f,py+ry-.5f,nz,rhw,c,0,1,0,0},f{px+rx-.5f,py+ry-.5f,nz,rhw,c,1,1,0,0};
            for(const auto& q:{a,b,e,e,b,f})out.push_back(q);};
        const auto rgb=l.front?style.rgb:style.tail_rgb;const std::array<float,3> glint_rgb=l.front?std::array<float,3>{1.f,.93f,.78f}:l.kind>=3?std::array<float,3>{1.f,.97f,.92f}:std::array<float,3>{1.f,.22f,.14f};const float unit=l.size>0?std::clamp(l.size/.25f,.7f,1.3f):1.f;const float r=std::max(1.5f,pixels(g.glow_degrees)*unit*(.55f+.45f*std::min(1.f,k)));
        quad(glow,r,r,colour(glint_rgb,std::min(1.f,k)));(void)rgb;
        if(g.streak>0&&g.streak_degrees>0){const float star=std::max(r*1.5f,pixels(g.streak_degrees)*(l.front?1.f:.75f)*std::min(1.f,k+.25f));quad(streak,star,star,colour(glint_rgb,std::min(1.f,k*g.streak)));}
    }
    const auto writer=[](void* context,uint32_t slot,const Args& args,HRESULT hr)noexcept{notify(*static_cast<Device8*>(context),slot,args,hr);};
    const auto hr=p.sun.lamp_sprites(n,glow,streak,&d,writer,g.texture);
    if(p.first_reason("lamp_glints")||(d.trace.control.active&&frame%60==0)){unsigned rear=0,kinds[4]{};for(const auto& l:p.lamp_points){rear+=!l.front;++kinds[std::min<unsigned>(l.kind,3)];}
        session().write("{\"type\":\"atmosphere_lamp_glints\",\"frame\":"+std::to_string(frame)+",\"lamps\":"+std::to_string(p.lamp_points.size())+",\"rear_lamps\":"+std::to_string(rear)+",\"head\":"+std::to_string(kinds[0])+",\"tail\":"+std::to_string(kinds[1])+",\"brake\":"+std::to_string(kinds[2])+",\"reverse\":"+std::to_string(kinds[3])+",\"sprite_from_file\":"+std::string(p.sun.glint_from_file()?"true":"false")+",\"sprites\":"+std::to_string((glow.size()+streak.size())/6)+",\"hresult\":"+std::to_string(uint32_t(hr))+"}");}
    return hr;
}
inline HRESULT sun_before_ui(Device8& d,bool ui)noexcept{
    capture_boundary(d,ui);
    auto* p=pilot(d);if(!ui||!p||!p->enabled()||!(p->sun_disk||p->sun_halo||p->sun_flare||p->sun_style.vignette>0||p->stars.count||p->glint_style.enabled)||!d.trace.scene_active||
       d.trace.shadow.recording||d.trace.effective_shadow.recording||GetCurrentThreadId()!=d.trace.render_thread_id())return S_OK;
    auto& sun=p->sun;const auto frame=d.trace.frame_number();if(sun.drawn_frame==frame)return S_OK;
    ps2port::perf::Timer perf_timer(ps2port::perf::AtmoSunUi);
    const bool sun_off=ps2port::perf::atmo(ps2port::perf::AtmoSun),glints_off=ps2port::perf::atmo(ps2port::perf::AtmoGlints);   // PERF-ATMO1 A/B
    auto gate=[&](const char* reason){sun.reason=reason;if(p->first_reason(reason)||(d.trace.control.active&&sun.gate_frame!=frame))try{sun.gate_frame=frame;session().write("{\"type\":\"atmosphere_sun_gate\",\"frame\":"+std::to_string(frame)+",\"reason\":"+quote(std::string(reason))+",\"drawn\":false}");}catch(...){}return S_OK;};
    auto& proof=sun.proof;if(sun.unsafe_frame==frame)return gate("sun_non_depth_writing_course_surface");
    if(!proof.world||proof.frame!=frame)return gate("sun_current_frame_scene_depth_unproven");
    bool single=false;const auto cert=courseintegration::certificate(d,single);
    if(!single||!cert.valid||!proof.world||proof.frame!=frame||proof.race!=cert.race_generation||proof.owner!=cert.owner_lifetime||proof.camera!=cert.camera||proof.reset!=d.ps2_port()->reset_generation())return gate("sun_current_frame_scene_depth_unproven");
    auto& n=*d.native();courseintegration::Ref<IDirect3DSurface8> target,depth;D3DVIEWPORT8 viewport{};D3DSURFACE_DESC desc{};
    if(FAILED(n.GetRenderTarget(&target.p))||FAILED(n.GetDepthStencilSurface(&depth.p))||!courseintegration::same_identity(target.p,proof.target)||!courseintegration::same_identity(depth.p,proof.depth)||
       FAILED(target.p->GetDesc(&desc))||FAILED(n.GetViewport(&viewport))||viewport.X||viewport.Y||viewport.Width!=desc.Width||viewport.Height!=desc.Height||viewport.MinZ!=0||viewport.MaxZ!=1)return gate("sun_depth_or_viewport_changed");
    sun.drawn_frame=frame;
    // ATMOSPHERE6 P1: stars behind the moon, same current-frame scene proof.
    if(p->stars.count&&!sun_off){const auto writer=[](void* context,uint32_t slot,const Args& args,HRESULT hr)noexcept{notify(*static_cast<Device8*>(context),slot,args,hr);};
        try{const auto sr=sun.stars(n,p->stars,p->lighting.direction,frame,desc.Width,desc.Height,&d,writer);if(FAILED(sr))return sr;
            if(p->first_reason("night_stars")||(d.trace.control.active&&frame%60==0))session().write("{\"type\":\"atmosphere_stars\",\"frame\":"+std::to_string(frame)+",\"count\":"+std::to_string(p->stars.count)+",\"drawn_total\":"+std::to_string(sun.stars_drawn)+",\"frames\":"+std::to_string(sun.stars_frames)+",\"hresult\":"+std::to_string(uint32_t(sr))+",\"depth_writes\":false}");
        }catch(...){return repair(d);}}
    if(p->glint_style.enabled&&!glints_off){try{const auto gr=lamp_glints(d,*p,n,desc.Width,desc.Height,frame);if(FAILED(gr))return gr;}catch(...){return repair(d);}}
    if(p->sun_style.vignette>0&&!sun_off){const auto writer=[](void* context,uint32_t slot,const Args& args,HRESULT hr)noexcept{notify(*static_cast<Device8*>(context),slot,args,hr);};
        const auto vr=sun.vignette(n,desc.Width,desc.Height,p->sun_style.vignette,&d,writer);if(FAILED(vr))return vr;
        if(p->first_reason("art_vignette")||d.trace.control.active)session().write("{\"type\":\"atmosphere_art_overlay\",\"effect\":\"vignette\",\"before_hud\":true,\"requested_triangles\":64,\"new_render_targets\":0,\"hresult\":"+std::to_string(uint32_t(vr))+"}");}
    if(sun_off||!(p->sun_disk||p->sun_halo||p->sun_flare))return S_OK;
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
            if(down&&!p->live_key_down)p->live_force=true;p->live_key_down=down;
            const bool dark=pid==GetCurrentProcessId()&&(GetAsyncKeyState(VK_CONTROL)&0x8000)&&(GetAsyncKeyState(VK_MENU)&0x8000)&&(GetAsyncKeyState('N')&0x8000);
            if(dark&&!p->dark_key_down){p->dark_diagnostic=!p->dark_diagnostic;p->live_force=true;
                session().write("{\"type\":\"atmosphere_dark_diagnostic\",\"enabled\":"+std::string(p->dark_diagnostic?"true":"false")+",\"frame\":"+std::to_string(frame)+"}");}
            p->dark_key_down=dark;}
        if(!p->package_root.empty()&&p->metadata_poll_frame!=frame){p->metadata_poll_frame=frame;DWORD pid=0;GetWindowThreadProcessId(GetForegroundWindow(),&pid);
            const bool down=pid==GetCurrentProcessId()&&(GetAsyncKeyState(VK_CONTROL)&0x8000)&&(GetAsyncKeyState(VK_MENU)&0x8000)&&(GetAsyncKeyState('M')&0x8000);
            if(down&&!p->metadata_key_down)p->course_dirty=true;p->metadata_key_down=down;}
        if(p->seam_debug&&frame!=p->seam_poll_frame){p->seam_poll_frame=frame;DWORD pid=0;GetWindowThreadProcessId(GetForegroundWindow(),&pid);
            const bool down=pid==GetCurrentProcessId()&&(GetAsyncKeyState(VK_CONTROL)&0x8000)&&(GetAsyncKeyState(VK_MENU)&0x8000)&&(GetAsyncKeyState('L')&0x8000);
            if(down&&!p->seam_key_down){p->world=!p->world;session().write("{\"type\":\"atmosphere_seam_toggle\",\"world_lighting\":"+std::string(p->world?"true":"false")+",\"sky_fog_unchanged\":true,\"frame\":"+std::to_string(frame)+"}");}p->seam_key_down=down;
        }
        if(frame>=p->perf_frame+120){LARGE_INTEGER frequency{};QueryPerformanceFrequency(&frequency);const auto calls=p->cpu_calls-p->perf_previous_calls;
            session().write("{\"type\":\"atmosphere_cpu_window\",\"frame\":"+std::to_string(frame)+",\"frames\":"+std::to_string(frame-p->perf_frame)+",\"cpu_ms\":"+std::to_string(frequency.QuadPart?1000.0*double(p->cpu_ticks-p->perf_previous_ticks)/double(frequency.QuadPart):0)+",\"calls\":"+std::to_string(calls)+",\"accepted_draws\":"+std::to_string(p->world_draws)+",\"copied_bytes\":"+std::to_string(p->copied_bytes)+",\"road_draws\":"+std::to_string(p->category_draws[1])+",\"terrain_draws\":"+std::to_string(p->category_draws[2])+",\"vegetation_draws\":"+std::to_string(p->category_draws[3])+",\"static_object_draws\":"+std::to_string(p->category_draws[4])+",\"ring_uploads\":"+std::to_string(p->ring_uploads)+",\"ring_discards\":"+std::to_string(p->ring_discards)+"}");
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
// PERF-ATMO1: every private draw used to Lock(0) one shared MANAGED buffer
// (~100-250 times a frame) that the GPU is still reading for the previous
// draw. UploadRing=1 (Atmosphere.ini, or F8 step ring_upload) appends to a
// DYNAMIC DEFAULT ring with NOOVERWRITE and DISCARDs only on wrap; the data is
// placed at vertex P>=min and SetIndices gets BaseVertexIndex P-min, so the
// game's own draw arguments still address exactly these vertices.
inline HRESULT upload_ring(Device8& d,atmosphere::Pilot& p,UINT min,UINT vertices,const std::vector<uint8_t>& bytes)noexcept {
    auto& n=*d.native();auto& s=p.pending;const UINT stride=s.stride;
    if(!stride||bytes.size()!=size_t(vertices)*stride)return S_FALSE;
    constexpr UINT kRing=8u*1024u*1024u;
    if(!p.ring){if(p.ring_failed)return S_FALSE;
        const HRESULT created=n.CreateVertexBuffer(kRing,D3DUSAGE_DYNAMIC|D3DUSAGE_WRITEONLY,0,D3DPOOL_DEFAULT,&p.ring);
        if(FAILED(created)||!p.ring){p.ring=nullptr;p.ring_failed=true;session().write("{\"type\":\"atmosphere_upload_ring\",\"created\":false,\"hresult\":"+std::to_string(uint32_t(created))+"}");return S_FALSE;}
        p.ring_size=kRing;p.ring_cursor=kRing;session().write("{\"type\":\"atmosphere_upload_ring\",\"created\":true,\"bytes\":"+std::to_string(kRing)+"}");}
    uint64_t at=std::max<uint64_t>((uint64_t(p.ring_cursor)+stride-1)/stride,min);DWORD flags=D3DLOCK_NOOVERWRITE;
    if((at+vertices)*stride>p.ring_size){at=min;flags=D3DLOCK_DISCARD;++p.ring_discards;}
    if((at+vertices)*stride>p.ring_size)return S_FALSE;
    BYTE* out=nullptr;if(FAILED(p.ring->Lock(UINT(at*stride),UINT(bytes.size()),&out,flags))||!out){if(out)p.ring->Unlock();return S_FALSE;}
    std::memcpy(out,bytes.data(),bytes.size());if(FAILED(p.ring->Unlock()))return E_FAIL;
    p.ring_cursor=UINT((at+vertices)*stride);++p.ring_uploads;
    s.stream_changed=true;auto hr=n.SetStreamSource(0,p.ring,stride);notify(d,83,pack(0,p.ring,stride),hr);
    if(SUCCEEDED(hr)){s.indices_changed=true;hr=n.SetIndices(s.indices,UINT(at-min));notify(d,85,pack(s.indices,UINT(at-min)),hr);}p.copied_bytes+=bytes.size();return hr;
}
inline HRESULT upload(Device8& d,atmosphere::Pilot& p,UINT min,UINT vertices,const std::vector<uint8_t>& bytes)noexcept {
    ps2port::perf::Timer perf_timer(ps2port::perf::AtmoUpload);
    if(p.upload_ring||ps2port::perf::atmo(ps2port::perf::AtmoRing)){const auto hr=upload_ring(d,p,min,vertices,bytes);if(hr!=S_FALSE)return hr;}
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
// P0.2 lamp observer (see Pilot::LampSample). Reads only the proxy's CPU
// mirror of the current vertex range (never locks GPU memory); a lamp whose
// range is not mirrored is still counted, with the WORLD origin as position.
inline void observe_lamp(Device8& d,atmosphere::Pilot& p,UINT min,UINT vertices,UINT triangles)noexcept{
    try{
        const auto frame=d.trace.frame_number();auto& b=p.lamps_building;
        if(b.frame!=frame){
            if(b.frame!=UINT64_MAX){p.lamps_last=std::move(b);
                if(frame>=p.lamp_log_frame+120&&!p.lamps_last.samples.empty()){p.lamp_log_frame=frame;
                    std::string o="{\"type\":\"atmosphere_lamps\",\"frame\":"+std::to_string(p.lamps_last.frame)+",\"lit_lamp_groups\":"+std::to_string(p.lamps_last.samples.size())+",\"samples\":[";
                    for(size_t i=0;i<p.lamps_last.samples.size()&&i<8;++i){const auto& s=p.lamps_last.samples[i];if(i)o+=",";
                        o+="{\"local\":["+std::to_string(s.local[0])+","+std::to_string(s.local[1])+","+std::to_string(s.local[2])+"],\"world\":["+
                           std::to_string(s.position[0])+","+std::to_string(s.position[1])+","+std::to_string(s.position[2])+"],\"vertices\":"+std::to_string(s.vertices)+"}";}
                    session().write(o+"]}");}}
            b={};b.frame=frame;}
        if(b.samples.size()>=64)return;
        atmosphere::Pilot::LampSample s;s.vertices=vertices;s.triangles=triangles;auto& n=*d.native();
        if(FAILED(n.GetTransform(D3DTS_WORLD,reinterpret_cast<D3DMATRIX*>(s.world.data()))))return;
        courseintegration::Ref<IDirect3DVertexBuffer8> vb;UINT stride=0;courseintegration::Ref<IDirect3DIndexBuffer8> ib;UINT base=0;
        if(SUCCEEDED(n.GetStreamSource(0,&vb.p,&stride))&&vb.p&&stride==20&&SUCCEEDED(n.GetIndices(&ib.p,&base))&&vertices&&vertices<=4096){
            D3DVERTEXBUFFER_DESC vd{};const auto vg=d.trace.resources.generation(reinterpret_cast<uintptr_t>(vb.p));
            if(vg&&SUCCEEDED(vb.p->GetDesc(&vd))){auto m=d.open_buffer_mirror(vb.p,BufferKind::Vertex,vg,vd.Size,vd.Usage,vd.Pool);
                if(m){std::scoped_lock lock(m->mutex);const uint64_t off=(uint64_t(base)+min)*20,bytes=uint64_t(vertices)*20;
                    if(m->available&&!m->poisoned&&off+bytes<=m->data.size()){double sum[3]{};
                        for(UINT i=0;i<vertices;++i){float v[3];std::memcpy(v,m->data.data()+off+uint64_t(i)*20,12);for(int k=0;k<3;++k)sum[k]+=v[k];}
                        for(int k=0;k<3;++k)s.local[k]=float(sum[k]/vertices);
                        // 6.14: the glow card (drawn only while braking) = the brake sections. Its vertex clusters
                        // (.35 m seeds, car space) become this car's brake boxes and brake glint points.
                        atmosphere::Pilot::BrakeBoxes boxes;
                        for(UINT i=0;i<vertices;++i){float v[3];std::memcpy(v,m->data.data()+off+uint64_t(i)*20,12);if(!std::isfinite(v[0]+v[1]+v[2]))continue;unsigned c=0;
                            for(;c<boxes.count;++c){const float cx=(boxes.lo[c][0]+boxes.hi[c][0])*.5f,cy=(boxes.lo[c][1]+boxes.hi[c][1])*.5f,cz=(boxes.lo[c][2]+boxes.hi[c][2])*.5f;
                                if((cx-v[0])*(cx-v[0])+(cy-v[1])*(cy-v[1])+(cz-v[2])*(cz-v[2])<.35f*.35f)break;}
                            if(c==boxes.count){if(boxes.count>=boxes.lo.size())continue;++boxes.count;boxes.lo[c]={v[0],v[1],v[2]};boxes.hi[c]={v[0],v[1],v[2]};}
                            for(int k=0;k<3;++k){boxes.lo[c][k]=std::min(boxes.lo[c][k],v[k]);boxes.hi[c][k]=std::max(boxes.hi[c][k],v[k]);}}
                        const auto& w=s.world;uintptr_t owner=0;float best=2.f*2.f;
                        for(const auto& c:p.car_poses){if(!c.instance||c.frame==UINT64_MAX||c.frame+2<frame)continue;const float dx=c.m[12]-w[12],dy=c.m[13]-w[13],dz=c.m[14]-w[14],dd=dx*dx+dy*dy+dz*dz;if(dd<best){best=dd;owner=c.instance;}}
                        if(owner&&boxes.count){boxes.instance=owner;boxes.frame=frame;atmosphere::Pilot::BrakeBoxes* slot=nullptr;
                            for(auto& x:p.brake_boxes)if(x.instance==owner){slot=&x;break;}
                            if(!slot)for(auto& x:p.brake_boxes)if(!x.instance||x.frame==UINT64_MAX||frame>x.frame+3600){slot=&x;break;}
                            if(slot)*slot=boxes;
                            // 6.15: rig-matched cars only take the brake STATE from the glow card; positions come from the rig.
                            if(auto* ro=p.lamp_rigs.loaded?p.rig_owner(owner,frame,false):nullptr;ro&&ro->rig>=0){ro->braking=frame;}else{
                            if(p.lamp_points_frame!=frame){p.lamp_points.clear();p.lamp_points_frame=frame;}
                            const std::array<float,3> forward=atmosphere::normalized({w[8],w[9],w[10]});
                            for(unsigned c=0;c<boxes.count&&p.lamp_points.size()<96;++c){const float x=(boxes.lo[c][0]+boxes.hi[c][0])*.5f,y=(boxes.lo[c][1]+boxes.hi[c][1])*.5f,z=boxes.lo[c][2];
                                if(z>-1.f)continue;atmosphere::Pilot::LampPoint lp;lp.instance=owner;lp.front=false;lp.kind=2;
                                for(int k=0;k<3;++k){lp.world[k]=x*w[k]+y*w[4+k]+z*w[8+k]+w[12+k];lp.axis[k]=-forward[k];}p.lamp_points.push_back(lp);}
                            }
                            if(p.first_reason("brake_glow_sections"))session().write("{\"type\":\"atmosphere_brake_glow_sections\",\"frame\":"+std::to_string(frame)+",\"sections\":"+std::to_string(boxes.count)+"}");}}}}}
        const auto& w=s.world;for(int k=0;k<3;++k)s.position[k]=s.local[0]*w[k]+s.local[1]*w[4+k]+s.local[2]*w[8+k]+w[12+k];
        b.samples.push_back(s);
    }catch(...){}
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
    // 6.3 headlights: remember this lit draw (args + world bounds) for the
    // light pass issued right after it in sun_world.
    if(p.headlight_style.enabled&&(type_supports_headlight(fvf))){
        if(!entry.has_bounds||entry.bounds_revision!=entry.vertex_revision){entry.has_bounds=false;
            const size_t n_vertices=saved.stride?entry.original.size()/saved.stride:0;std::array<float,3> lo{1e30f,1e30f,1e30f},hi{-1e30f,-1e30f,-1e30f};
            for(size_t i=0;i<n_vertices;++i){float v3[3];std::memcpy(v3,entry.original.data()+i*saved.stride,12);for(unsigned k=0;k<3;++k){lo[k]=std::min(lo[k],v3[k]);hi[k]=std::max(hi[k],v3[k]);}}
            if(n_vertices&&std::isfinite(lo[0]+hi[0]+lo[1]+hi[1]+lo[2]+hi[2])){for(unsigned k=0;k<3;++k)entry.bounds[k]=(lo[k]+hi[k])*.5f;
                entry.bounds[3]=.5f*std::sqrt((hi[0]-lo[0])*(hi[0]-lo[0])+(hi[1]-lo[1])*(hi[1]-lo[1])+(hi[2]-lo[2])*(hi[2]-lo[2]));entry.has_bounds=true;entry.bounds_revision=entry.vertex_revision;}}
        if(entry.has_bounds){auto& c=p.headlight_candidate;c.frame=d.trace.frame_number();c.min=min;c.vertices=vertices;c.start=start;c.count=triangles;c.instance=0;   // 6.11: course draw, not a car (stale car id skipped every own-lamp pass)
           
            const auto& b=entry.bounds;if(world){const auto& w=*world;for(unsigned k=0;k<3;++k)c.centre[k]=b[0]*w[k]+b[1]*w[4+k]+b[2]*w[8+k]+w[12+k];
                const float scale=std::max({std::hypot(w[0],w[1],w[2]),std::hypot(w[4],w[5],w[6]),std::hypot(w[8],w[9],w[10])});c.radius=b[3]*scale;}
            else{c.centre={b[0],b[1],b[2]};c.radius=b[3];}}}
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
    if(ps2port::perf::atmo(ps2port::perf::AtmoWorldNative)&&!p->pending.any())return S_OK;   // PERF-ATMO1 A/B: native course draw
    struct Timing {atmosphere::Pilot& p;LARGE_INTEGER start{};Timing(atmosphere::Pilot& x):p(x){QueryPerformanceCounter(&start);}~Timing(){LARGE_INTEGER end{};QueryPerformanceCounter(&end);p.cpu_ticks+=end.QuadPart-start.QuadPart;++p.cpu_calls;}} timer(*p);
    ps2port::perf::Timer perf_timer(ps2port::perf::AtmoWorld);
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
        // 5.13: remember a classifier-proven blended vehicle body env pass for
        // the night energy stage of the body path (windows under $switch nodes).
        if(classification&&classification->transform.object==ObjectClass::Body&&classification->alpha_blended&&(classification->reasons&ENV_STAGE)&&
           !(classification->reasons&CL_OPAQUE)&&(classification->reasons&RACE_PROJECTION)&&(fvf==0x152||fvf==0x142))
            p->blended_vehicle={d.trace.frame_number(),min,vertices,start,count};
        // P0.2 VehicleGlowFix: the PC glow-on layer of a proven vehicle is an
        // XYZ|TEX1 card drawn SRCALPHA/INVSRCALPHA WITH depth writes and no
        // alpha test, so its transparent texels write Z: rectangular edges and
        // lamps/halos cutting into what is drawn later. Same contract as
        // ForestFix=1: depth writes off for this draw only (test unchanged).
        // Skipped when the PS2 BrakeGlow path owns lamp layers (it proves the
        // native state itself).
        if(p->vehicle_glow_fix&&fvf==0x102&&classification&&(classification->semantic_source!=VehicleSemanticSource::None||strong_vehicle_proof(classification->transform))&&
           !(d.ps2_port()&&d.ps2_port()->brake_glow()&&d.ps2_port()->brake_glow()->requested())&&
           groundintegration::render(d,n,D3DRS_ALPHABLENDENABLE,TRUE)&&groundintegration::render(d,n,D3DRS_SRCBLEND,D3DBLEND_SRCALPHA)&&
           groundintegration::render(d,n,D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA)&&groundintegration::render(d,n,D3DRS_ZWRITEENABLE,TRUE)&&
           groundintegration::render(d,n,D3DRS_ZENABLE,D3DZB_TRUE)&&groundintegration::render(d,n,D3DRS_ALPHATESTENABLE,FALSE)){
            if(FAILED(n.GetRenderState(D3DRS_ZWRITEENABLE,&saved.zwrite)))return reject(d,*p,"vehicle_glow_state_unavailable");
            saved.zwrite_changed=true;const auto hr=n.SetRenderState(D3DRS_ZWRITEENABLE,FALSE);notify(d,50,pack(D3DRS_ZWRITEENABLE,FALSE),hr);if(FAILED(hr))return repair(d);
            ++p->vehicle_glow_draws;observe_lamp(d,*p,min,vertices,count);
            if(p->capture.stage||p->coverage.enabled){p->draw_resolved=true;p->draw_lit=false;p->draw_reason="vehicle_glow_zwrite_off";}
            if(p->first_reason("vehicle_glow_fix"))session().write("{\"type\":\"atmosphere_vehicle_glow_fix\",\"frame\":"+std::to_string(d.trace.frame_number())+",\"z_test_unchanged\":true,\"alpha_unchanged\":true}");
            return S_OK;}
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
