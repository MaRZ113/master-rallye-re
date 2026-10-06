#include "vehicle_classifier.hpp"
#include <iostream>
#include <stdexcept>
#include <cmath>
#include <memory>
#define CHECK(x) do{if(!(x))throw std::runtime_error(#x);}while(0)
using namespace gfx2;
D3DMATRIX world(float x=0,float z=0,float yaw=0){D3DMATRIX m{};m._11=m._33=std::cos(yaw);m._13=std::sin(yaw);m._31=-m._13;m._22=m._44=1;m._41=x;m._43=z;return m;}
Classification frame(TransformTracker& t,D3DMATRIX w,uint64_t signature=1){auto i=t.observe(w,signature);t.finish_frame();auto p=t.result(i);Classification c=p?*p:Classification{};t.next_frame();return c;}
void temporal(){
 TransformTracker t;Classification c;for(int i=0;i<6;++i)c=frame(t,world());CHECK(c.age==6&&!c.dynamic);
 t.reset();for(int i=0;i<6;++i)c=frame(t,world(i*.2f));CHECK(c.age==6&&c.dynamic);
 t.reset();for(int i=0;i<6;++i)c=frame(t,world(0,0,i*.05f));CHECK(c.dynamic);
 auto old=c.track;auto epoch=t.epoch();t.reset();CHECK(t.epoch()!=epoch);c=frame(t,world());CHECK(!c.dynamic&&c.age==1&&c.track!=old);
 // Missing race frame is a scene boundary; no vehicle identity survives a menu.
 t.finish_frame();t.next_frame();c=frame(t,world());CHECK(c.age==1&&!c.dynamic);
 // A new generation fingerprint starts cold even at the identical WORLD.
 for(int i=0;i<5;++i)c=frame(t,world(i*.2f),1);c=frame(t,world(1),2);CHECK(c.age==1&&!c.dynamic);
}
void instances_and_order(){
 auto aa=std::make_unique<TransformTracker>(),bb=std::make_unique<TransformTracker>();auto& a=*aa;auto& b=*bb;uint64_t id_a=0,id_b=0;
 for(int frame_index=0;frame_index<6;++frame_index){
  auto w1=world(frame_index*.2f),w2=world(20+frame_index*.2f);
  auto i1=a.observe(w1,77),i2=a.observe(w2,77); // Same geometry, two instances.
  a.observe(w1,12);a.observe(w2,13);
  auto j2=b.observe(w2,13);b.observe(w2,77);auto j1=b.observe(w1,12);b.observe(w1,77);
  a.finish_frame();b.finish_frame();CHECK(a.result(i1)->track==b.result(j1)->track&&a.result(i2)->track==b.result(j2)->track);
  CHECK(a.result(i1)->track!=a.result(i2)->track);if(frame_index==5)CHECK(a.result(i1)->dynamic&&a.result(i2)->dynamic);
  id_a=a.result(i1)->track;id_b=a.result(i2)->track;a.next_frame();b.next_frame();
 }
 CHECK(id_a!=id_b);
 auto ambiguous_ptr=std::make_unique<TransformTracker>();auto& ambiguous=*ambiguous_ptr;ambiguous.observe(world(-1),1);ambiguous.observe(world(1),1);ambiguous.finish_frame();ambiguous.next_frame();auto i=ambiguous.observe(world(),1);ambiguous.finish_frame();CHECK(ambiguous.result(i)->ambiguous&&!ambiguous.result(i)->dynamic);
 auto full_ptr=std::make_unique<TransformTracker>();auto& full=*full_ptr;for(int i=0;i<129;++i)full.observe(world(static_cast<float>(i)*2),1);full.finish_frame();CHECK(full.overflowed()&&full.result(0)==nullptr);
 // A huge static identity-WORLD group is left unknown without poisoning car tracks.
 auto saturated_ptr=std::make_unique<TransformTracker>();auto& saturated=*saturated_ptr;for(int k=1;k<=65;++k)saturated.observe(world(),k);auto car=saturated.observe(world(50),100);saturated.finish_frame();CHECK(saturated.result(0)->track==0&&saturated.result(car)->age==1&&!saturated.overflowed());
 auto malformed=world();malformed._11=NAN;CHECK(full.observe(malformed,1)==UINT32_MAX);
}
void wheel_order(){
 auto aa=std::make_unique<TransformTracker>(),bb=std::make_unique<TransformTracker>();auto& a=*aa;auto& b=*bb;
 for(int frame_index=0;frame_index<6;++frame_index){
  std::array<D3DMATRIX,4> wheels={world(-1,frame_index*.2f-1,frame_index*.03f),world(1,frame_index*.2f-1,frame_index*.03f),world(-1,frame_index*.2f+1,frame_index*.03f),world(1,frame_index*.2f+1,frame_index*.03f)};
  std::array<uint32_t,4> x{},y{};for(int i=0;i<4;++i)x[i]=a.observe(wheels[i],77);for(int i:{2,0,3,1})y[i]=b.observe(wheels[i],77);
  a.finish_frame();b.finish_frame();for(int i=0;i<4;++i)CHECK(a.result(x[i])->track==b.result(y[i])->track);a.next_frame();b.next_frame();
 }
}
void signatures_and_scope(){
 Shadow s;ResourceRegistry r;Args draw=pack(D3DPT_TRIANGLELIST,0,20,0,10);
 s.matrices[256].set(world());s.matrices[17].set(world());s.bindings.vertex_shader.set(0x152);s.bindings.streams[0].set({100,36});s.bindings.indices.set({200,0});
 r.add(100,23,pack());r.add(200,24,pack());
 for(int stage=0;stage<2;++stage){s.bindings.textures[stage].set(0);for(int key:{1,2,3,4,5,6,11,24})s.tss[stage][key].set(0);}
 for(int key:{14,15,27})s.rs[key].set(0);s.rs[14].set(1);
 auto fingerprint=geometry_signature(s,r,draw,SHARED_WORLD_RETURN_RVA);CHECK(fingerprint!=0);
 s.matrices[256].set(world(10));CHECK(geometry_signature(s,r,draw,SHARED_WORLD_RETURN_RVA)==fingerprint);
 r.add(100,23,pack());CHECK(geometry_signature(s,r,draw,SHARED_WORLD_RETURN_RVA)!=fingerprint);
 s.bindings.textures[1].set(300);CHECK(geometry_signature(s,r,draw,SHARED_WORLD_RETURN_RVA)==0);r.add(300,20,pack());
 for(auto item:{std::pair<int,DWORD>{1,D3DTOP_MODULATEALPHA_ADDCOLOR},{2,D3DTA_CURRENT},{3,D3DTA_TEXTURE},{4,D3DTOP_MODULATE},{5,D3DTA_CURRENT},{6,D3DTA_TEXTURE},{11,D3DTSS_TCI_CAMERASPACENORMAL},{24,D3DTTFF_COUNT2}})s.tss[1][item.first].set(item.second);
 DrawClassification c;c.reasons=draw_reasons(s,true,true,true)|KNOWN_GEOMETRY;c.transform={1,6,true,false};
 CHECK((c.reasons&(NORMAL_FVF|ENV_STAGE|CL_OPAQUE))==(NORMAL_FVF|ENV_STAGE|CL_OPAQUE));
 CHECK(std::string(object_classification(c))=="DYNAMIC_ENV_OBJECT"); // Still unproven vehicle -> never visual-positive.
 c.transform.dynamic=false;CHECK(std::string(object_classification(c))=="CANDIDATE");
 for(auto gates:{std::array<bool,3>{false,true,true},{true,false,true},{true,true,false}}){c.reasons=draw_reasons(s,gates[0],gates[1],gates[2])|KNOWN_GEOMETRY;CHECK(std::string(object_classification(c))=="UNKNOWN");}
 s.rs[27].set(1);CHECK(!(draw_reasons(s,true,true,true)&CL_OPAQUE));s.bindings.vertex_shader.set(0x142);CHECK(!(draw_reasons(s,true,true,true)&NORMAL_FVF));s.tss[1][1].set(D3DTOP_DISABLE);CHECK(!(draw_reasons(s,true,true,true)&ENV_STAGE));
}

void constellation_contracts(){
 for(float width:{.75f,.875f,1.f,.825f,1.5f})for(float base:{1.225f,1.385f,1.375f,1.2f,2.3f}){
  std::array<TransformGroup,5> g{};g[0].world=world();g[0].result={100,6,true,false};g[0].draws=g[0].body_draws=3;g[0].body_env_draws=2;g[0].size=3;
  for(int k=0;k<4;++k){g[k+1].world=world(k&1?width:-width,k&2?base:-base);g[k+1].result={static_cast<uint64_t>(k+1),1,false,false};g[k+1].draws=g[k+1].wheel_draws=4;}
  classify_constellations(g.data(),g.size());CHECK(g[0].result.object==ObjectClass::Body&&g[0].result.constellation==100);
  for(int k=1;k<5;++k)CHECK(g[k].result.object==ObjectClass::Wheel&&!g[k].result.dynamic);
  std::swap(g[1],g[4]);classify_constellations(g.data(),g.size());CHECK(g[0].result.object==ObjectClass::Body);
  classify_constellations(g.data(),4);CHECK(g[0].result.object==ObjectClass::Unknown); // 3 wheels.
  g[0].result.dynamic=false;classify_constellations(g.data(),5);CHECK(g[0].result.object==ObjectClass::Unknown);
 }
 std::array<TransformGroup,10> g{};
 for(int car=0;car<2;++car){int b=car*5;g[b].world=world(car*5.f);g[b].result={static_cast<uint64_t>(100+car),6,true,false};g[b].draws=g[b].body_draws=g[b].size=2;g[b].body_env_draws=1;
  for(int k=0;k<4;++k){g[b+k+1].world=world(car*5.f+(k&1?.9f:-.9f),k&2?1.4f:-1.4f);g[b+k+1].result={static_cast<uint64_t>(b+k+1),1,false,false};g[b+k+1].draws=g[b+k+1].wheel_draws=4;}
 }
 classify_constellations(g.data(),10);CHECK(g[0].result.object==ObjectClass::Body&&g[5].result.object==ObjectClass::Body);CHECK(g[1].result.constellation!=g[6].result.constellation);
 auto five=g;five[5]=g[1];five[5].world._41-=.02f;five[5].result.track=77;classify_constellations(five.data(),6);CHECK(five[0].result.object==ObjectClass::Unknown); // 5 wheels, two plausible rectangles.
 auto conflict=g;conflict[5]=g[0];conflict[5].result.track=200;classify_constellations(conflict.data(),6);CHECK(conflict[0].result.object==ObjectClass::Unknown&&conflict[5].result.object==ObjectClass::Unknown);
 float error=0;CHECK(!wheel_rectangle({LocalWheel{NAN,0,1},LocalWheel{},LocalWheel{},LocalWheel{}},error));
 // Temporal learning uses the same resources/signatures across instances; wheel dynamics are unnecessary.
 TransformTracker t;Classification c;
 for(int f=0;f<6;++f){auto body=t.observe(world(f*.2f),1,{0x152,ENV_STAGE|CL_OPAQUE,100});t.observe(world(f*.2f),2,{0x142,CL_OPAQUE,100});
  for(int k:{2,0,3,1}){auto w=world(f*.2f+(k&1?.9f:-.9f),k&2?1.4f:-1.4f);t.observe(w,3,{0x112,ENV_STAGE|CL_OPAQUE,100});t.observe(w,4,{0x112,ENV_STAGE|CL_OPAQUE,152});}
  t.finish_frame();c=*t.result(body);t.next_frame();
 }
 CHECK(c.object==ObjectClass::Body);auto predicted=t.predict(world(1.2f),1);CHECK(predicted.constellation==c.constellation);
 for(uint64_t signature=1;signature<=65;++signature)t.observe(world(1.2f),signature,{0x152,ENV_STAGE|CL_OPAQUE,1});CHECK(t.predict(world(1.2f),1).object==ObjectClass::Unknown);
 CHECK(t.predict(world(1.2f),99).object==ObjectClass::Unknown);t.reset();CHECK(t.predict(world(1.2f),1).object==ObjectClass::Unknown);
}
void rotated_shared_instances(){
 TransformTracker t;std::array<uint32_t,2> bodies{};
 for(int f=0;f<6;++f){for(int car=0;car<2;++car){auto b=world(car*20.f+f*.2f,0,.6f);bodies[car]=t.observe(b,1,{0x152,ENV_STAGE|CL_OPAQUE,100});t.observe(b,2,{0x142,CL_OPAQUE,20});
   for(int k:{3,1,0,2}){float x=k&1?.9f:-.9f,z=k&2?1.4f:-1.4f;auto w=world(b._41+x*b._11+z*b._31,x*b._13+z*b._33,.6f);
    t.observe(w,3,{0x112,ENV_STAGE|CL_OPAQUE,73});t.observe(w,4,{0x112,ENV_STAGE|CL_OPAQUE,91});}
  }t.finish_frame();if(f==5){CHECK(t.result(bodies[0])->object==ObjectClass::Body&&t.result(bodies[1])->object==ObjectClass::Body);CHECK(t.result(bodies[0])->constellation!=t.result(bodies[1])->constellation);CHECK(t.stats().constellations==2&&t.stats().wheel_draws==16);}t.next_frame();
 }
}
void pool_contracts(){
 ResourceRegistry r;auto m=r.add(1,20,pack(8,8,1,0,21,D3DPOOL_MANAGED,0));auto vb=r.add(2,23,pack(32,0,0,D3DPOOL_MANAGED,0));auto ib=r.add(3,24,pack(32,0,101,D3DPOOL_MANAGED,0));
 r.add(4,20,pack(8,8,1,0,21,D3DPOOL_DEFAULT,0));r.add(5,23,pack(32,0,0,D3DPOOL_DEFAULT,0));r.add(6,25,pack());r.add(7,26,pack());r.add(8,27,pack());r.add(9,20,pack(8,8,1,0,21,D3DPOOL_SYSTEMMEM,0));r.add(10,20,pack(8,8,1,0,21,D3DPOOL_SCRATCH,0));r.add(11,21,pack(8,8,8,1,0,21,D3DPOOL_MANAGED,0));r.add(12,22,pack(8,1,0,21,D3DPOOL_DEFAULT,0));
 auto serial=r.next_serial;CHECK(r.successful_reset()==5);CHECK(r.next_serial==serial&&r.generation(1)==m.serial&&r.generation(2)==vb.serial&&r.generation(3)==ib.serial);
 for(int p:{8,9,10,11})CHECK(r.generation(p));for(int p:{4,5,6,7,12})CHECK(!r.generation(p));CHECK(r.add(5,23,pack(32,0,0,D3DPOOL_DEFAULT,0)).serial>serial);
}
int main(){try{temporal();instances_and_order();wheel_order();signatures_and_scope();constellation_contracts();rotated_shared_instances();pool_contracts();std::cout<<"Bounded temporal classifier / instances / permutation / Reset / generations / fail-closed scope: PASS\n";return 0;}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
