// COURSE-ALIVE3 contracts: the portable PS2 rigid prop physics (ps2_rigid_props.hpp), the asset layout and the per-race
// runtime. Optional private inputs: MRR_RIGID_TEST_ASSET (the pinned PS2RigidProps.ps2rgd), MRR_RIGID_TEST_COURSE_DX
// (an installed PS2 course package DX of a prop course) and MRR_RIGID_TEST_CAR_DX (a retail car.dx).
#include "rigid_props.hpp"
#include "provenance.hpp"
#include "ps2_audio_options.hpp"
#include "pause_settings.hpp"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
using namespace gfx2::ps2port;
using ps2rigid::V3;
using ps2rigid::operator+;using ps2rigid::operator-;using ps2rigid::operator*;
int failures=0;
#define CHECK(x) do{if(!(x)){std::cerr<<"FAIL "<<__LINE__<<": "#x"\n";++failures;}}while(0)

namespace {
bool approx(float a,float b,float e=1e-4f){return std::fabs(a-b)<=e;}
// Box hull of half extents (hx, hy, hz) from its six face loops (the car.dx loop form).
ps2rigid::Hull box(float hx,float hy,float hz){
    std::vector<V3> p;
    for(int i=0;i<8;++i)p.push_back({i&1?hx:-hx,i&2?hy:-hy,i&4?hz:-hz});
    const std::vector<std::vector<uint32_t>> loops={{0,2,3,1},{4,5,7,6},{0,1,5,4},{2,6,7,3},{0,4,6,2},{1,3,7,5}};
    ps2rigid::Hull h;CHECK(ps2rigid::hull_from_loops(p,loops,h));return h;
}
// Flat tag1400-style ground at height y over [-s, s]^2: two triangles, plane normal down (drivable side -n).
void ground(ps2rigid::Terrain& t,float y,float s,bool up_wound=false){
    std::vector<float> c={-s,y,-s, s,y,-s, s,y,s,  -s,y,-s, s,y,s, -s,y,s};
    const float k=up_wound?1.f:-1.f;
    std::vector<float> pl={0,k,0,-k*y, 0,k,0,-k*y};
    CHECK(t.build(c,pl));
}
ps2rigid::BodyDef def(const ps2rigid::Hull& h,float x,float y,float z,float mass=500,V3 moi={565,447,565}){
    ps2rigid::BodyDef d;d.hull=&h;d.mass=mass;d.moi=moi;d.matrix={1,0,0,0,1,0,0,0,1,x,y,z};d.restitution=.15f;d.friction=.7f;d.rolling=2.5f;return d;
}
// The PS2 hay hull shape: an octagonal prism along X (tag101 representation B: 16 points, 10 faces).
ps2rigid::Hull bale_hull(){
    std::vector<V3> p;const float r=.92f,hx=.8f;
    for(int side=0;side<2;++side)for(int i=0;i<8;++i){const float t=6.2831853f*(float(i)+.5f)/8.f;p.push_back({side?hx:-hx,r*std::cos(t),r*std::sin(t)});}
    std::vector<std::vector<uint32_t>> loops={{0,7,6,5,4,3,2,1},{8,9,10,11,12,13,14,15}};
    for(uint32_t i=0;i<8;++i)loops.push_back({i,(i+1)%8,8+(i+1)%8,8+i});
    ps2rigid::Hull h;CHECK(ps2rigid::hull_from_loops(p,loops,h));return h;
}
ps2rigid::TickInput near_camera(V3 at){ps2rigid::TickInput in;in.have_camera=true;in.camera=at;return in;}

void math(){
    // Authored rows (Italy2 haybale, two decimals) -> quaternion -> R columns = orthonormalised rows.
    const std::array<float,9> rows={-.69f,0,.73f, 0,1,0, -.73f,0,-.69f};
    const auto q=ps2rigid::quat_from_rows(rows);const auto r=ps2rigid::rotation(q);
    const float l=std::sqrt(.69f*.69f+.73f*.73f);
    CHECK(approx(r.m[0],-.69f/l,1e-4f)&&approx(r.m[3],0)&&approx(r.m[6],.73f/l,1e-4f));   // column 0 = row 0
    CHECK(approx(r.m[4],1)&&approx(r.m[8],-.69f/l,1e-3f));
    // Local +X maps to authored row 0: the D3D row-vector convention of en3d matrices.
    const auto w=ps2rigid::mul(r,{1,0,0});CHECK(approx(w[0],-.69f/l,1e-4f)&&approx(w[2],.73f/l,1e-4f));
    for(const auto& t:{std::array<float,9>{1,0,0,0,1,0,0,0,1},std::array<float,9>{-1,0,0,0,1,0,0,0,-1},std::array<float,9>{1,0,0,0,-1,0,0,0,-1}}){
        const auto rr=ps2rigid::rotation(ps2rigid::quat_from_rows(t));
        for(int i=0;i<3;++i)for(int j=0;j<3;++j)CHECK(approx(rr.m[i*3+j],t[j*3+i],1e-5f));
    }
    // Quaternion length < 0.001 -> identity (2661e0).
    const auto id=ps2rigid::normalized({0,0,0,0});CHECK(id.w==1&&id.x==0);
    // Car pose velocity: 1 m in 0.1 s along x and a 0.1 rad yaw.
    ps2rigid::Pose a,b;b.t={1,0,0};const float c=std::cos(.1f),s=std::sin(.1f);b.r.m={c,0,s,0,1,0,-s,0,c};
    V3 v,om;ps2rigid::pose_velocity(a,b,.1,v,om);CHECK(approx(v[0],10,1e-3f)&&approx(om[1],1,1e-2f));
    b.t={100,0,0};ps2rigid::pose_velocity(a,b,.1,v,om);CHECK(v[0]==0&&om[1]==0);  // teleport (reset) -> no velocity
    // D3D rows of an orthonormal car world matrix.
    const float m12[12]={1,0,0,0,1,0,0,0,1,5,6,7};ps2rigid::Pose p;CHECK(ps2rigid::pose_from_rows(m12,p)&&p.t[2]==7);
    const float skew[12]={1,0,0,.5f,1,0,0,0,1,0,0,0};CHECK(!ps2rigid::pose_from_rows(skew,p));
}
void hull_and_terrain(){
    const auto h=box(1,1,1);CHECK(h.planes.size()==6&&approx(h.radius,std::sqrt(3.f)));
    // A non-convex loop set is refused.
    std::vector<V3> pts={{0,0,0},{1,0,0},{0,1,0},{0,0,1},{.1f,.1f,.1f}};
    ps2rigid::Hull bad;CHECK(!ps2rigid::hull_from_loops(pts,{{0,1,4}},bad));
    ps2rigid::Terrain t;ground(t,10,50);
    V3 n;float d;
    CHECK(!t.contact({0,10.1f,0},.75f,n,d));                       // above: outside
    CHECK(t.contact({0,9.8f,0},.75f,n,d)&&approx(d,.2f)&&approx(n[1],1));  // below: pushed up
    CHECK(!t.contact({0,8.f,0},.75f,n,d));                         // deeper than the contact band
    CHECK(!t.contact({60,9.8f,0},.75f,n,d));                       // outside the triangles
    float hgt=0;CHECK(t.ground(5,12,5,3,hgt)&&approx(hgt,10));
    // Ground stored with an upward normal is still solid below.
    ps2rigid::Terrain u;ground(u,0,10,true);CHECK(u.contact({1,-.1f,1},.75f,n,d)&&approx(n[1],1));
    CHECK(!ps2rigid::Terrain{}.contact({0,0,0},1,n,d));
}
void placement_and_settled(){
    const auto h=box(.8f,.9f,.9f);ps2rigid::Terrain t;ground(t,0,100);
    ps2rigid::World w;
    // Half sunk: lifted by 0.01, 0.02, ... until clear (16f2f0).
    CHECK(w.start(&t,{def(h,0,.5f,0)}));
    const auto& b=w.bodies()[0];
    CHECK(b.x[1]>=.9f&&b.x[1]<.9f+.1f&&b.lifted>0);
    // The lift sum is a triangular number of 0.01 steps.
    const float k=std::round(b.lifted/.01f);float tri=0;for(int i=1;tri<k-.5f;++i)tri+=float(i);CHECK(approx(tri,k,.6f));
    // Settled and near: proximity alone does not wake it, no gravity.
    const float y0=b.x[1];
    for(int i=0;i<30;++i)w.tick(near_camera({0,2,-10}));
    CHECK(b.state==ps2rigid::State::Asleep&&b.x[1]==y0);
    // Floating authored prop also stays where it was put until something hits it (PS2 tumbleweeds sit ~0.3 m high).
    ps2rigid::World f;CHECK(f.start(&t,{def(h,0,3,0)}));for(int i=0;i<10;++i)f.tick(near_camera({0,2,-10}));
    CHECK(f.bodies()[0].x[1]==3.f&&f.bodies()[0].lifted==0);
}
void free_fall_rest_and_far(){
    const auto h=box(.8f,.9f,.9f);ps2rigid::Terrain t;ground(t,0,100);
    ps2rigid::World w;CHECK(w.start(&t,{def(h,0,5,0)}));
    auto& b=w.body(0);b.state=ps2rigid::State::Active;
    w.tick(near_camera({0,2,-10}));
    // One tick of gravity from rest (two half steps, exact for a constant force).
    CHECK(approx(b.v[1],-ps2rigid::kGravity*ps2rigid::kTick,1e-3f));
    CHECK(approx(b.x[1],5-.5f*ps2rigid::kGravity*ps2rigid::kTick*ps2rigid::kTick,2e-3f));
    // Lands, settles on the ground and goes to sleep after MaxClampTime of rest.
    for(int i=0;i<200&&b.state==ps2rigid::State::Active;++i)w.tick(near_camera({0,2,-10}));
    CHECK(b.state==ps2rigid::State::Asleep);
    CHECK(b.x[1]>.85f&&b.x[1]<.95f);
    CHECK(ps2rigid::length(b.P)==0&&ps2rigid::length(b.L)==0);
    // Far: an active body away from the camera is paused and its momenta decay by 1/60 per invocation, zero on the 60th.
    ps2rigid::World f;CHECK(f.start(&t,{def(h,0,5,0)}));
    auto& c=f.body(0);c.state=ps2rigid::State::Active;c.P={500,0,0};
    ps2rigid::TickInput away=near_camera({500,2,0});
    f.tick(away);CHECK(c.state==ps2rigid::State::Far&&c.far_decay==59&&approx(c.P[0],500.f/60.f,1e-3f)&&c.x[1]==5.f);
    for(int i=0;i<58;++i)f.tick(away);CHECK(c.far_decay==1&&c.state==ps2rigid::State::Far);   // 500/60^59 underflows: float32 as on the PS2
    f.tick(away);CHECK(c.far_decay==0&&c.P[0]==0);
    // Near again: resumes (falls).
    f.tick(near_camera({0,2,-10}));CHECK(c.state==ps2rigid::State::Active&&c.x[1]<5.f);
    // Frustum: behind the camera is not near.
    ps2rigid::TickInput behind=near_camera({0,2,-10});behind.frustum.push_back({0,0,1,10});   // visible where z >= -10 - 4
    CHECK(ps2rigid::World::is_near(c,behind));behind.frustum[0]={0,0,1,-30};CHECK(!ps2rigid::World::is_near(c,behind));
}
void car_knocks_bale(){
    const auto bale=box(.8f,.9f,.9f),car=box(.9f,.7f,2.f);ps2rigid::Terrain t;ground(t,0,200);
    ps2rigid::World w;CHECK(w.start(&t,{def(bale,0,.9f,0),def(bale,0,.9f,5.f)}));
    // Car drives along +z at 20 m/s through the first bale.
    ps2rigid::Kinematic k;k.hull=&car;k.valid=true;k.v={0,0,20};k.pose.t={0,.75f,-4};
    ps2rigid::TickInput in=near_camera({0,3,-15});
    bool woke=false;float top=0;
    for(int i=0;i<60;++i){
        k.pose.t[2]=-4.f+20.f*ps2rigid::kTick*float(i);in.cars={k};
        w.tick(in);
        woke=woke||w.bodies()[0].state==ps2rigid::State::Active;
        top=std::max(top,w.bodies()[0].v[2]);
    }
    const auto& b=w.bodies()[0];
    CHECK(woke&&b.wakes>=1);
    CHECK(top>10.f&&top<40.f);           // pushed ahead at about the car speed (effective car mass, restitution 0.15)
    CHECK(b.x[2]>5.f);                    // carried forward
    CHECK(b.x[1]>.5f);                    // never sinks through the ground
    CHECK(w.bodies()[1].wakes>=1);        // the second bale was hit by the car or the first bale
    // Without the car nothing moves.
    ps2rigid::World q;CHECK(q.start(&t,{def(bale,0,.9f,0)}));for(int i=0;i<30;++i)q.tick(near_camera({0,3,-15}));
    CHECK(q.bodies()[0].state==ps2rigid::State::Asleep&&q.bodies()[0].wakes==0);
    // Tumbleweed (mass 5) is thrown much faster than a bale.
    const auto weed=box(.675f,.482f,.675f);ps2rigid::World tw;CHECK(tw.start(&t,{def(weed,0,.482f,0,5,{2,2,2})}));float tw_top=0;
    for(int i=0;i<20;++i){k.pose.t[2]=-4.f+20.f*ps2rigid::kTick*float(i);in.cars={k};tw.tick(in);tw_top=std::max(tw_top,ps2rigid::length(tw.bodies()[0].v));}
    CHECK(tw_top>20.f&&tw_top<60.f);
    // Interpolated pose lies between ticks.
    const auto p=w.pose(0,.5f);CHECK(approx(p.t[2],(b.prev_x[2]+b.x[2])*.5f,1e-3f));
}
// Minimal synthetic asset in the PS2RGD02 layout: two textures (paint, shadow), one box model with an environment layer,
// one course, one prop.
std::vector<uint8_t> synthetic(){
    std::vector<uint8_t> o;auto put=[&](const void* p,size_t n){const auto* b=static_cast<const uint8_t*>(p);o.insert(o.end(),b,b+n);};
    auto u32=[&](uint32_t v){put(&v,4);};auto f=[&](float v){put(&v,4);};auto text=[&](const char* s,size_t n){std::vector<char> b(n,0);std::memcpy(b.data(),s,std::strlen(s));put(b.data(),n);};
    const auto h=box(1,1,1);
    put("PS2RGD02",8);u32(2);u32(2);u32(1);u32(6);u32(8);u32(6);u32(1);u32(1);u32(1);
    u32(2);u32(2);for(int i=0;i<4;++i)u32(0xff808080u);
    u32(2);u32(2);for(int i=0;i<4;++i)u32(0xff000000u);
    text("haybale",16);u32(0);u32(1);u32(0);u32(0);u32(6);u32(0);u32(0);u32(0);f(1.5f);u32(0);u32(8);u32(0);u32(6);f(h.radius);
    u32(0);for(float x:{-1.f,-1.f,-1.f,1.f,1.f,1.f})f(x);
    for(int i=0;i<6;++i){ObjectVertex v{float(i%2),float(i/3),0,0xfe727272u,0,0};put(&v,sizeof(v));}
    for(int i=0;i<6;++i){f(0);f(1);f(0);}
    for(const auto& p:h.points){f(p[0]);f(p[1]);f(p[2]);}
    for(const auto& q:h.planes){f(q[0]);f(q[1]);f(q[2]);f(q[3]);}
    text("RaceTest/ItalyS1",48);text("DataGx/Course/Italy_S1/italy_s1.dx",64);for(int i=0;i<32;++i)o.push_back(uint8_t(i));u32(0);u32(1);
    text("haybale",32);u32(0);u32(1);f(500);f(565);f(447);f(565);f(5);
    for(float x:{1.f,0.f,0.f,0.f,1.f,0.f,0.f,0.f,1.f,-22.f,-31.f,504.f})f(x);
    return o;
}
void asset_and_runtime(){
    auto bytes=synthetic();RigidPropsAsset a;
    CHECK(decode_rigid_props_layout(bytes.data(),bytes.size(),a));
    CHECK(a.models.size()==1&&a.models[0].hull.planes.size()==6&&a.props.size()==1&&a.props[0].casts_shadow&&a.props[0].mass==500.f);
    CHECK(a.models[0].env==0&&a.shadow_texture==1&&a.normals.size()==6&&a.models[0].aabb[3]==1.f);
    CHECK(rigid_course_index(a,"RaceTest/ItalyS1")==0&&rigid_course_index(a,"RaceTest/Turkey3")==SIZE_MAX);
    CHECK(!decode_rigid_props_asset(bytes.data(),bytes.size(),"0000",a));   // digest pinned
    {auto b=bytes;b.push_back(0);CHECK(!decode_rigid_props_layout(b.data(),b.size(),a));}            // trailing byte
    {auto b=bytes;b[8]=1;CHECK(!decode_rigid_props_layout(b.data(),b.size(),a));}                     // version
    {auto b=bytes;b[40]=2;CHECK(!decode_rigid_props_layout(b.data(),b.size(),a));}                    // shadow texture index
    {auto b=bytes;float bad=-1;std::memcpy(b.data()+b.size()-4*17,&bad,4);CHECK(!decode_rigid_props_layout(b.data(),b.size(),a));} // mass
    // A plane that cuts a hull point is refused (convexity).
    {auto b=bytes;const size_t planes=44+2*24+100+6*24+6*12+8*12;float bad=-.5f;std::memcpy(b.data()+planes+12,&bad,4);CHECK(!decode_rigid_props_layout(b.data(),b.size(),a));}
    CHECK(decode_rigid_props_layout(bytes.data(),bytes.size(),a));
    // Runtime over a flat course below the prop: shadow, object and environment passes in that order.
    ps2rigid::Terrain t;ground(t,-32,1000);
    RigidCourseRuntime rt;CHECK(!rt.start(a,0,ps2rigid::Terrain{},1));CHECK(rt.start(a,0,t,7)&&rt.ready()&&rt.race()==7);
    const float view[16]={1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1};
    std::vector<RigidBatch> batches;CHECK(rt.build({0,0,0},view,1000.f,batches)&&batches.size()==3);
    if(batches.size()==3){
        CHECK(batches[0].pass==RigidPass::Shadow&&batches[0].texture==1&&!batches[0].vertices.empty());
        CHECK(batches[1].pass==RigidPass::Object&&batches[1].vertices.size()==6&&batches[1].vertices[0].color==0xfe727272u);
        CHECK(approx(batches[1].vertices[0].x,-22.f,1e-3f)&&approx(batches[1].vertices[0].z,504.f,1e-3f));
        // Up normal, identity view: UV (0.5, 0) and white.
        CHECK(batches[2].pass==RigidPass::Env&&batches[2].texture==0&&approx(batches[2].vertices[0].u,.5f)&&approx(batches[2].vertices[0].v,0.f)&&batches[2].vertices[0].color==0xffffffffu);
        // Shadow vertices: lifted 0.1 over the ground, black, alpha 0.85 n.y with the depth attenuation (centre 1 m
        // above the lifted ground: d = 0.9 - 0.5 -> 1 / (0.3 + 1)).
        const auto& v=batches[0].vertices[0];
        CHECK(approx(v.y,-31.9f,1e-3f)&&(v.color&0xffffffu)==0);
        CHECK(std::abs(int(v.color>>24)-int(.85f/1.3f*255.f+.5f))<=1);
    }
    // Out of the shadow range: no shadow pass.
    CHECK(rt.build({0,0,0},view,10.f,batches)&&batches.size()==2&&batches[0].pass==RigidPass::Object);
    {auto in=near_camera({-22,-30,490});CHECK(rt.advance(.1,true,in)==0);CHECK(rt.advance(.1,false,in)==3);}
    // Car inputs: velocity from the previous pose of the same instance, unknown hull folder skipped, body coupling.
    const auto car=box(.9f,.7f,2);std::unordered_map<std::string,const ps2rigid::Hull*> hulls{{"megane",&car}};
    RigidCarInput c;c.instance=0x1000;c.folder="Megane";c.pose_valid=true;c.rows={1,0,0,0,1,0,0,0,1,0,0,0};
    RigidCarInput other=c;other.instance=0x2000;other.folder="Unknown";
    std::vector<ps2rigid::Kinematic> k;
    rt.cars({c,other},hulls,10.0,k);CHECK(k.size()==1&&k[0].v[2]==0&&k[0].mass==0);
    c.rows[11]=2;c.body=0x5000;c.mass=1300;c.com={0,.5f,2};rt.cars({c},hulls,10.1,k);
    CHECK(k.size()==1&&approx(k[0].v[2],20,1e-2f)&&k[0].mass==1300.f&&k[0].body==0x5000);
    float e=0,mu=0,roll=0;rigid_material_coefficients(kRigidMaterialTreeblend,e,mu,roll);CHECK(e>.2f&&roll>0);
    rigid_material_coefficients(kRigidMaterialMetal,e,mu,roll);CHECK(e>.2f&&mu>.3f&&roll>1.f);
}
// COURSE-ALIVE4: the barrel flag, the per-INI member selection and the PS2-AUDIO1 site rules.
void checkpoint_and_audio(){
    auto bytes=synthetic();RigidPropsAsset a;
    const size_t flags=bytes.size()-72;   // flags word of the last (only) prop record
    {auto b=bytes;b[flags]=3;CHECK(!decode_rigid_props_layout(b.data(),b.size(),a));}   // barrel flag on a non-checkpoint model
    {auto b=bytes;b[flags]=4;CHECK(!decode_rigid_props_layout(b.data(),b.size(),a));}   // unknown flag
    {auto b=bytes;std::memcpy(b.data()+44+2*24,"checkpoint\0\0\0\0\0",16);           // model name -> checkpoint
     CHECK(!decode_rigid_props_layout(b.data(),b.size(),a));                            // ... without the flag: refused
     b[flags]=3;CHECK(decode_rigid_props_layout(b.data(),b.size(),a)&&a.props[0].checkpoint&&a.props[0].casts_shadow);
     CHECK(rigid_members(a,0,{true,true}).size()==1&&rigid_members(a,0,{true,false}).empty()&&rigid_members(a,0,{false,true}).size()==1);
     ps2rigid::Terrain t;ground(t,-32,1000);RigidCourseRuntime rt;
     CHECK(!rt.start(a,0,t,3,{true,false}));                                            // props only: nothing on this course
     CHECK(rt.start(a,0,t,3,{false,true})&&rt.barrels()==1&&rt.members().size()==1&&rt.members()[0]==0);}
    CHECK(decode_rigid_props_layout(bytes.data(),bytes.size(),a)&&!a.props[0].checkpoint);
    CHECK(rigid_members(a,0,{false,true}).empty()&&rigid_members(a,0,{true,false}).size()==1&&rigid_members(a,5,{}).empty());
    using namespace gfx2::ps2port::audio;
    const uint8_t jz[2]={0x74,0x3d},jmp[2]={0xeb,0x3d},other[2]={0x75,0x3d};
    CHECK(classify(kCheckpointSound,jz)==Site::Original&&classify(kCheckpointSound,jmp)==Site::Patched&&classify(kCheckpointSound,other)==Site::Mismatch);
    const uint8_t mov[4]={0xc6,0x40,0x0e,0x01},nop[4]={0x90,0x90,0x90,0x90},jnz[2]={0x75,0x3c},bad[4]={0xc6,0x40,0x0e,0x00};
    CHECK((group_ready<2>({&kFinishJingle,&kFinishFade},{mov,jnz})));
    CHECK((group_ready<2>({&kFinishJingle,&kFinishFade},{nop,jnz})));                   // half patched before: completes
    CHECK(!(group_ready<2>({&kFinishJingle,&kFinishFade},{bad,jnz})));                  // other code: nothing written
    CHECK(!(group_ready<1>({&kFinishFade},{nullptr})));
    {const uint8_t push[2]={0x68,0xe8},jmp39[2]={0xeb,0x39};
     CHECK((group_ready<2>({&kCheckpointSound,&kSplitTimeSound},{jz,push})));
     CHECK((group_ready<2>({&kCheckpointSound,&kSplitTimeSound},{jmp,jmp39})));          // re-run after an earlier proxy
     CHECK(!(group_ready<2>({&kCheckpointSound,&kSplitTimeSound},{jz,jz})));
     CHECK(kSplitTimeSound.va+2+kSplitTimeSound.replacement[1]==0x4a9169u);}
    CHECK(kFinishJingle.va%4==0&&kCheckpointSound.original[1]==kCheckpointSound.replacement[1]&&kFinishFade.original[1]==kFinishFade.replacement[1]);
    // FPS1 PS2ResetTiming: retail bytes of MRallye.exe at 0x4cde6c / 0x4cd4ba, only the immediates change.
    {const uint8_t cmp7[4]={0x83,0x3c,0x07,0x07},cmp0[4]={0x83,0x3c,0x07,0x00},mov5[4]={0xbf,0x05,0x00,0x00},mov2[4]={0xbf,0x02,0x00,0x00},cmp8[4]={0x83,0x3d,0x07,0x07};
     CHECK((group_ready<2>({&kLimitSamples,&kResetTimer},{cmp7,mov5}))&&(group_ready<2>({&kLimitSamples,&kResetTimer},{cmp0,mov2})));
     CHECK(!(group_ready<2>({&kLimitSamples,&kResetTimer},{cmp8,mov5})));
     CHECK(kLimitSamples.va%4==0&&kLimitSamples.replacement[3]==0&&kResetTimer.replacement[1]==2);}
}
void two_way(){
    // A coupled 1300 kg car at 20 m/s into a 500 kg bale: the car slows down by about the momentum it gives the bale,
    // the bale leaves faster than a tumbleweed would make the car lose speed.
    const auto bale=bale_hull(),car=box(.9f,.7f,2.f);ps2rigid::Terrain t;ground(t,0,200);
    ps2rigid::World w;CHECK(w.start(&t,{def(bale,0,.9f,0)}));CHECK(bale.planes.size()==10);
    ps2rigid::Kinematic k;k.hull=&car;k.valid=true;k.v={0,0,20};k.pose.t={0,.75f,-3.1f};k.mass=1300;k.com=k.pose.t;k.body=1;
    ps2rigid::TickInput in=near_camera({0,3,-15});in.cars={k};
    float lost=0;V3 total{};
    // The car moves with the velocity the coupling leaves it (in the game: the next frame's measured velocity).
    for(int i=0;i<15;++i){
        in.cars[0].pose.t[2]+=in.cars[0].v[2]*ps2rigid::kTick;in.cars[0].com=in.cars[0].pose.t;in.cars[0].impulse=in.cars[0].angular={};
        w.tick(in);
        total=total+in.cars[0].impulse;
        if(std::getenv("MRR_RIGID_TEST_VERBOSE")){const auto& bb=w.bodies()[0];std::cout<<"  tick "<<i<<" car v "<<in.cars[0].v[2]<<" z "<<in.cars[0].pose.t[2]<<" J "<<in.cars[0].impulse[1]<<","<<in.cars[0].impulse[2]<<" bale v "<<bb.v[1]<<","<<bb.v[2]<<" x "<<bb.x[1]<<","<<bb.x[2]<<" w "<<bb.w[0]<<" contacts "<<w.last_contacts()<<" car "<<w.last_car_contacts()<<"\n";}
    }
    lost=20.f-in.cars[0].v[2];
    const auto& b=w.bodies()[0];
    CHECK(b.wakes>=1);
    if(std::getenv("MRR_RIGID_TEST_VERBOSE"))std::cout<<"two-way: lost "<<lost<<" total "<<total[0]<<","<<total[1]<<","<<total[2]<<" bale v "<<b.v[0]<<","<<b.v[1]<<","<<b.v[2]<<" x "<<b.x[2]<<"\n";
    CHECK(lost>3.f&&lost<9.f);                           // inelastic 1300/500 kg: ~5.6 m/s, restitution and ground drag around it
    CHECK(total[2]<0.f);                                 // pushed backwards
    // Momentum balance of the first hit: what the car lost, the bale gained (within the ground's share).
    CHECK(std::fabs(-total[2]-1300.f*lost)<1.f);         // the summed impulse is what the car lost
    CHECK(b.def.mass*b.v[2]<=-total[2]+1.f);             // the bale never gains more than the car gave
    // Kinematic (no body): nothing is summed.
    ps2rigid::World q;CHECK(q.start(&t,{def(bale,0,.9f,0)}));
    ps2rigid::TickInput in2=near_camera({0,3,-15});k.mass=0;in2.cars={k};
    for(int i=0;i<10;++i){in2.cars[0].pose.t[2]+=20.f*ps2rigid::kTick;q.tick(in2);}
    CHECK(in2.cars[0].impulse[2]==0.f&&in2.cars[0].v[2]==20.f);
    // Water triangles cast no shadow; the near query sees each triangle once.
    ps2rigid::Terrain wt;std::vector<float> c={-5,0,-5, 5,0,-5, 5,0,5, -5,0,-5, 5,0,5, -5,0,5};std::vector<float> pl={0,-1,0,0, 0,-1,0,0};
    std::vector<uint8_t> water={1,0};CHECK(wt.build(c,pl,1.f,&water));
    int seen=0,wet=0;wt.for_near(0,0,3,[&](const float*,const float*,bool w2){++seen;wet+=w2;});CHECK(seen==2&&wet==1);
    ps2rigid::Pose pose;pose.t={0,.9f,0};std::vector<ObjectVertex> sh;rigid_shadow_triangles(wt,pose,{-.8f,-.9f,-.9f,.8f,.9f,.9f},sh);
    CHECK(sh.size()==3);
}
void private_inputs(){
    if(const char* path=std::getenv("MRR_RIGID_TEST_ASSET")){
        std::ifstream f(path,std::ios::binary);std::vector<uint8_t> b((std::istreambuf_iterator<char>(f)),{});
        RigidPropsAsset a;CHECK(decode_rigid_props_asset(b.data(),b.size(),gfx2::sha256_bytes(b.data(),b.size()),a));
        CHECK(a.courses.size()==36&&a.props.size()==515&&a.models.size()==3);
        size_t hay=0,barrels=0;for(const auto& p:a.props){hay+=a.models[p.model].name=="haybale";barrels+=p.checkpoint;}CHECK(hay==58&&barrels==432);
        for(size_t i=0;i<a.courses.size();++i)CHECK(rigid_members(a,i,{false,true}).size()==12);
        std::cout<<"private asset: "<<a.props.size()<<" props\n";
        if(const char* dx=std::getenv("MRR_RIGID_TEST_COURSE_DX")){
            std::ifstream g(dx,std::ios::binary);std::vector<uint8_t> c((std::istreambuf_iterator<char>(g)),{});
            ps2rigid::Terrain t;size_t records=0;CHECK(rigid_terrain_from_course_dx(c.data(),c.size(),t,records)&&records>1000);
            // Every prop of that course starts at rest on (or within its lift of) the PS2 ground, and stays asleep.
            for(size_t i=0;i<a.courses.size();++i){
                RigidCourseRuntime rt;if(!rt.start(a,i,t,1))continue;
                size_t on_ground=0;
                for(const auto& body:rt.world().bodies()){float h=0;if(t.ground(body.x[0],body.x[1],body.x[2],1.f,h)&&body.x[1]-h<1.5f)++on_ground;}
                std::cout<<"course "<<a.courses[i].id<<": "<<on_ground<<"/"<<rt.world().bodies().size()<<" props over ground\n";
                if(on_ground!=rt.world().bodies().size())continue;
                {   // PS2 drop shadows on the real ground: every shadow-casting prop gets some triangles.
                    const float view[16]={1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1};std::vector<RigidBatch> batches;
                    const auto& first=rt.world().bodies()[0].x;
                    CHECK(rt.build(first,view,1e5f,batches));
                    size_t shadow=0,casters=0;for(const auto& b:batches)if(b.pass==RigidPass::Shadow)shadow+=b.vertices.size()/3;
                    for(uint32_t k=0;k<a.courses[i].count;++k)casters+=a.props[a.courses[i].first+k].casts_shadow;
                    std::cout<<"  shadow "<<a.courses[i].id<<": "<<shadow<<" triangles for "<<casters<<" casters\n";
                    CHECK(casters==0||shadow>=casters);
                }
                // Stress on the real PS2 ground: each prop in turn kicked sideways and up (a car hit at ~15 m/s), 20 s of
                // ticks with the camera on it: no NaN, nothing through the ground, asleep at the end.
                size_t asleep=0,through=0,bad=0;float lowest=1e9f;
                auto& w=rt.world_mut();
                for(size_t k=0;k<w.bodies().size();++k){
                    auto& body=w.body(k);body.state=ps2rigid::State::Active;
                    body.P=V3{15.f*float(k%3)-15.f,4.f,12.f}*body.def.mass;body.L=V3{0,0,.5f*body.def.moi[2]};
                    for(int n=0;n<600;++n){ps2rigid::TickInput in;in.have_camera=true;in.camera=w.bodies()[k].x+V3{0,3,0};rt.tick(1,in);}
                    const auto& b2=w.bodies()[k];
                    if(!ps2rigid::finite(b2.x)){++bad;continue;}
                    float h=0;
                    if(!t.ground(b2.x[0],b2.x[1],b2.x[2],2.f,h)||b2.x[1]-h<.2f)++through;else lowest=std::min(lowest,b2.x[1]-h);
                    asleep+=b2.state==ps2rigid::State::Asleep;
                    if(std::getenv("MRR_RIGID_TEST_VERBOSE")&&b2.state!=ps2rigid::State::Asleep)
                        std::cout<<"    awake "<<k<<": speed "<<ps2rigid::length(b2.v)<<" spin "<<ps2rigid::length(b2.w)<<" rest "<<b2.rest
                                 <<" y-ground "<<(b2.x[1]-h)<<" moved "<<ps2rigid::length(b2.x-V3{a.props[a.courses[i].first+k].matrix[9],a.props[a.courses[i].first+k].matrix[10],a.props[a.courses[i].first+k].matrix[11]})<<"\n";
                }
                std::cout<<"  stress "<<a.courses[i].id<<": asleep "<<asleep<<"/"<<w.bodies().size()<<", below ground "<<through<<", nan "<<bad
                         <<", lowest centre above ground "<<lowest<<"\n";
                CHECK(bad==0&&through==0);
            }
            std::cout<<"private course DX: "<<records<<" records\n";
        }
    }else std::cout<<"MRR_RIGID_TEST_ASSET not set: private asset check NOT_PERFORMED\n";
    if(const char* car=std::getenv("MRR_RIGID_TEST_CAR_DX")){
        std::ifstream f(car,std::ios::binary);std::vector<uint8_t> b((std::istreambuf_iterator<char>(f)),{});
        ps2rigid::Hull h;CHECK(rigid_vehicle_hull(b.data(),b.size(),h)&&h.valid());
        std::cout<<"private car hull: "<<h.points.size()<<" points, "<<h.planes.size()<<" planes\n";
    }
}
} // namespace

void pause_settings_menu(){
    using namespace gfx2::ps2port::pause;
    // CALL rel32 encoding of the four redirected sites (retail bytes).
    CHECK((call_bytes(0x455600,0x455210)==std::array<uint8_t,5>{0xe8,0x0b,0xfc,0xff,0xff}));
    CHECK((call_bytes(0x4551a7,0x455280)==std::array<uint8_t,5>{0xe8,0xd4,0x00,0x00,0x00}));
    CHECK((call_bytes(0x531105,0x531110)==std::array<uint8_t,5>{0xe8,0x06,0x00,0x00,0x00}));
    CHECK(frame_tiles(2)==5&&frame_tiles(3)==7);CHECK(std::wstring(fov_section(2))==L"Quality"&&std::wstring(fov_section(0))==L"Camera");
    Menu m;CHECK(!m.usable());m.original={"CONTINUE","QUIT"};CHECK(m.usable());m.configured=75.f;
    CHECK((m.labels()==std::vector<std::string>{"CONTINUE","SETTINGS","QUIT"}));
    int next=-1;CHECK(m.accept(0,next)==Action::Native);CHECK(m.accept(2,next)==Action::NativeQuit);
    CHECK(m.accept(1,next)==Action::Stay&&next==0&&m.mode==Mode::Settings);
    CHECK((m.labels()==std::vector<std::string>{"CAMERA FOV 75","BACK"}));
    CHECK(m.accept(0,next)==Action::Stay&&next==0&&m.fov()==80);
    m.live=100.f;CHECK(!m.step(+1,false)&&m.fov()==100);CHECK(m.step(+1,true)&&m.fov()==50);CHECK(!m.step(-1,false));
    CHECK(m.step(+1,false)&&m.fov()==55);m.live=77.f;CHECK(m.step(+1,false)&&m.fov()==80);
    CHECK(m.back(next)&&next==1&&m.mode==Mode::Main);CHECK(!m.back(next));
    CHECK(m.accept(1,next)==Action::Stay);CHECK(m.accept(1,next)==Action::Stay&&next==1&&m.mode==Mode::Main);
    Menu stock;stock.original={"A","B"};stock.mode=Mode::Settings;CHECK((stock.labels()[0]=="CAMERA FOV STOCK"));CHECK(!stock.step(+1,true));
}
int main(){
    math();hull_and_terrain();placement_and_settled();free_fall_rest_and_far();car_knocks_bale();asset_and_runtime();checkpoint_and_audio();two_way();private_inputs();pause_settings_menu();
    if(failures){std::cerr<<failures<<" failures\n";return 1;}
    std::cout<<"rigid props contracts passed\n";return 0;
}
