#include "wrappers.hpp"
#include "reflection_scope.hpp"
#include <iostream>
#include <stdexcept>
#include <cmath>
#include <vector>
#define CHECK(x) do{if(!(x))throw std::runtime_error(#x);}while(0)
#include "mock_interfaces.hpp"
using namespace gfx2;
D3DMATRIX world(float x=0,float z=0){D3DMATRIX m{};m._11=m._22=m._33=m._44=1;m._41=x;m._43=z;return m;}
struct Raw:MockDeviceBase {
 std::vector<DWORD> writes;DWORD tci=D3DTSS_TCI_CAMERASPACENORMAL|1,draw_tci=0;unsigned draws=0;
 Trace* disable_logging_on_draw=nullptr;HRESULT draw_hr=S_OK,reset_hr=S_OK;bool fail_temporary=false,fail_restore=false;
 HRESULT STDMETHODCALLTYPE SetTextureStageState(DWORD stage,D3DTEXTURESTAGESTATETYPE key,DWORD value) override {
  CHECK(stage==1&&key==D3DTSS_TEXCOORDINDEX);writes.push_back(value);
  if((value&0xffff0000u)==D3DTSS_TCI_CAMERASPACEREFLECTIONVECTOR&&fail_temporary)return E_FAIL;
  if((value&0xffff0000u)==D3DTSS_TCI_CAMERASPACENORMAL&&fail_restore)return E_FAIL;tci=value;return S_OK;
 }
 HRESULT STDMETHODCALLTYPE DrawIndexedPrimitive(D3DPRIMITIVETYPE,UINT,UINT,UINT,UINT) override{++draws;draw_tci=tci;if(disable_logging_on_draw)disable_logging_on_draw->enabled=false;return draw_hr;}
 HRESULT STDMETHODCALLTYPE DrawPrimitive(D3DPRIMITIVETYPE,UINT,UINT) override{++draws;draw_tci=tci;return draw_hr;}
 HRESULT STDMETHODCALLTYPE GetTextureStageState(DWORD,D3DTEXTURESTAGESTATETYPE,DWORD* out) override{*out=tci;return S_OK;}
 HRESULT STDMETHODCALLTYPE Reset(D3DPRESENT_PARAMETERS*) override{return reset_hr;}
};
void setup(Trace& t){
 auto& s=t.shadow;s.bindings.streams[0].set({100,36});s.bindings.indices.set({200,0});s.matrices[17].set(world());
 for(int stage=0;stage<2;++stage){s.bindings.textures[stage].set(stage?300:0);for(int k:{1,2,3,4,5,6,11,24})s.tss[stage][k].set(0);}
 for(int k:{14,15,27})s.rs[k].set(0);s.rs[14].set(1);
 for(auto kv:{std::pair<int,DWORD>{1,18},{2,1},{3,2},{4,4},{5,1},{6,2},{11,D3DTSS_TCI_CAMERASPACENORMAL|1},{24,2}})s.tss[1][kv.first].set(kv.second);
 t.effective_shadow=s;
}
void race(Trace& t){D3DMATRIX p{};p._11=1.12245429f;p._22=1.49660575f;p._33=1.00020003f;p._34=1;p._43=-.200040013f;t.after(37,pack(D3DTS_PROJECTION,&p),S_OK,0x400000+GAMEPLAY_PROJECTION_RETURN_RVA);CHECK(t.race_context());}
void geometry(Device8& w,float x){
 auto draw=[&](D3DMATRIX matrix,uint32_t fvf,int start){w.trace.shadow.matrices[256].set(matrix);w.trace.shadow.bindings.vertex_shader.set(fvf);w.trace.effective_shadow.bindings.vertex_shader.set(fvf);CHECK(w.draw_indexed_at(D3DPT_TRIANGLELIST,0,20,start,10,0x400000+SHARED_WORLD_RETURN_RVA)==S_OK);};
 draw(world(x),0x152,0);draw(world(x),0x152,30);
 for(int k:{2,0,3,1}){auto m=world(x+(k&1?.9f:-.9f),k&2?1.4f:-1.4f);draw(m,0x112,60);draw(m,0x112,90);}
}
void hud(Device8& w){
 auto& t=w.trace;auto epoch=t.classifier_epoch();D3DMATRIX p{};p._11=2.f/640;p._22=-2.f/480;p._33=.0005f;p._44=1;
 t.after(37,pack(D3DTS_PROJECTION,&p),S_OK,0x400000+GAMEPLAY_PROJECTION_RETURN_RVA);
 CHECK(!t.race_context()&&t.classifier_epoch()==epoch);
 if(!t.enabled){auto c=t.before(71,pack(D3DPT_TRIANGLELIST,0,20,0,10),0x400000+SHARED_WORLD_RETURN_RVA);
  CHECK(c.signature==0&&c.transform.track==0&&!(c.reasons&RACE_PROJECTION));}
 auto n=w.trace.effective_shadow.tss[1][11].value;
 CHECK(w.draw_indexed_at(D3DPT_TRIANGLELIST,0,20,0,10,0x400000+SHARED_WORLD_RETURN_RVA)==S_OK);
 CHECK(w.trace.effective_shadow.tss[1][11].value==n);
}
void full_frame_lifetime(){
 MockRootBase rr;Raw raw;Root8 root(&rr);Device8 w(&raw,&root);auto& t=w.trace;t.configure_classifier(true,0x400000);t.enabled=false;setup(t);
 t.resources.add(100,23,pack(128,0,0,D3DPOOL_MANAGED,0));t.resources.add(200,24,pack(128,0,101,D3DPOOL_MANAGED,0));t.resources.add(300,20,pack(8,8,1,0,21,D3DPOOL_MANAGED,0));
 w.visuals.configure(parse_visual_config({{"Renderer.ConfigVersion","1"},{"VehicleReflections.Mode","ViewDependent2D"}},true),true,nullptr,E_FAIL);
 auto epoch=t.classifier_epoch();uint64_t track=0;uint32_t age=0;
 for(int f=0;f<9;++f){
  race(t);geometry(w,f*.2f);
  t.shadow.matrices[256].set(world(f*.2f));t.shadow.bindings.vertex_shader.set(0x152);
  auto c=t.before(71,pack(D3DPT_TRIANGLELIST,0,20,0,10),0x400000+SHARED_WORLD_RETURN_RVA);
  if(f>=5){CHECK(c.transform.object==ObjectClass::Body&&c.transform.track&&c.transform.age>age);if(track)CHECK(track==c.transform.track);track=c.transform.track;age=c.transform.age;}
  auto n=raw.writes.size();hud(w);CHECK(raw.writes.size()==n);t.after(15,pack(),S_OK,0);CHECK(t.classifier_epoch()==epoch);
 }
 CHECK(track&&age>=7&&!raw.writes.empty());
 // First menu-only frame expires the previous-frame lease; repeated menus do not churn epochs.
 hud(w);t.after(15,pack(),S_OK,0);CHECK(t.classifier_epoch()==epoch+1);epoch=t.classifier_epoch();
 hud(w);t.after(15,pack(),S_OK,0);CHECK(t.classifier_epoch()==epoch);
 race(t);t.shadow.matrices[256].set(world(1.8f));t.shadow.bindings.vertex_shader.set(0x152);
 auto c=t.before(71,pack(D3DPT_TRIANGLELIST,0,20,0,10),0x400000+SHARED_WORLD_RETURN_RVA);CHECK(!c.transform.track&&!c.transform.constellation);
 // A HUD-ending race frame still loses tracks on a real successful Reset and relearns managed buffers.
 auto serial=t.resources.generation(100);CHECK(w.Reset(nullptr)==S_OK&&t.resources.generation(100)==serial&&t.classifier_epoch()==epoch+1);
 setup(t);
 auto n=raw.writes.size();
 for(int f=0;f<8;++f){race(t);geometry(w,2.f+f*.2f);hud(w);t.after(15,pack(),S_OK,0);}
 CHECK(raw.writes.size()>n);
 // Exercise the serialized full interval, including its late HUD projection.
 t.enabled=true;t.control.pending=true;race(t);geometry(w,3.4f);hud(w);t.after(15,pack(),S_OK,0);
 race(t);geometry(w,3.6f);hud(w);t.after(15,pack(),S_OK,0);t.enabled=false;
}
void integration(){
 MockRootBase rr;Raw raw;Root8 root(&rr);Device8 w(&raw,&root);auto& t=w.trace;t.configure_classifier(true,0x400000);t.enabled=false;setup(t);
 t.resources.add(100,23,pack(128,0,0,D3DPOOL_MANAGED,0));t.resources.add(200,24,pack(128,0,101,D3DPOOL_MANAGED,0));t.resources.add(300,20,pack(8,8,1,0,21,D3DPOOL_MANAGED,0));t.resources.add(400,23,pack(128,0,0,D3DPOOL_DEFAULT,0));
 auto config=parse_visual_config({{"Renderer.ConfigVersion","1"},{"VehicleReflections.Mode","ViewDependent2D"}},true);w.visuals.configure(config,true,nullptr,E_FAIL);race(t);
 for(int f=0;f<6;++f){geometry(w,f*.2f);t.after(15,pack(),S_OK,0);}
 // A real bounded capture exercises the serializer on modified and restored draws.
 t.enabled=true;t.control.pending=true;geometry(w,1.1f);t.after(15,pack(),S_OK,0);geometry(w,1.2f);t.after(15,pack(),S_OK,0);t.enabled=false;
 CHECK(raw.writes.size()>0);for(auto v:raw.writes)CHECK(v==(D3DTSS_TCI_CAMERASPACENORMAL|1)||v==(D3DTSS_TCI_CAMERASPACEREFLECTIONVECTOR|1));
 t.shadow.matrices[256].set(world(1.3f));t.shadow.bindings.vertex_shader.set(0x152);
 auto before=raw.writes.size();auto draws=raw.draws;raw.draw_hr=D3DERR_INVALIDCALL;
 CHECK(w.draw_indexed_at(D3DPT_TRIANGLELIST,0,20,0,10,0x400000+SHARED_WORLD_RETURN_RVA)==D3DERR_INVALIDCALL);
 CHECK(raw.draws==draws+1&&raw.writes.size()==before+2&&raw.draw_tci==(D3DTSS_TCI_CAMERASPACEREFLECTIONVECTOR|1));
 CHECK(raw.tci==(D3DTSS_TCI_CAMERASPACENORMAL|1)&&t.shadow.tss[1][11].value==raw.tci&&t.effective_shadow.tss[1][11].value==raw.tci);
 t.enabled=true;raw.disable_logging_on_draw=&t;before=raw.writes.size();CHECK(w.draw_indexed_at(D3DPT_TRIANGLELIST,0,20,0,10,0x400000+SHARED_WORLD_RETURN_RVA)==D3DERR_INVALIDCALL);CHECK(!t.enabled&&raw.writes.size()==before+2&&raw.tci==(D3DTSS_TCI_CAMERASPACENORMAL|1));raw.disable_logging_on_draw=nullptr;
 raw.draw_hr=S_OK;raw.fail_temporary=true;before=raw.writes.size();CHECK(w.draw_indexed_at(D3DPT_TRIANGLELIST,0,20,0,10,0x400000+SHARED_WORLD_RETURN_RVA)==S_OK);CHECK(raw.writes.size()==before+1&&raw.draw_tci==raw.tci);raw.fail_temporary=false;
 // Only mapped indexed owner can qualify: even a matching DrawPrimitive state stays stock.
 before=raw.writes.size();CHECK(w.DrawPrimitive(D3DPT_TRIANGLELIST,0,10)==S_OK&&raw.writes.size()==before);
 // Failed Reset preserves metadata, race context and temporal epoch.
 auto serial=t.resources.generation(100),epoch=t.classifier_epoch();raw.reset_hr=E_FAIL;CHECK(w.Reset(nullptr)==E_FAIL&&t.resources.generation(100)==serial&&t.classifier_epoch()==epoch&&t.race_context());
 raw.reset_hr=S_OK;CHECK(w.Reset(nullptr)==S_OK&&t.resources.generation(100)==serial&&t.resources.generation(400)==0&&t.classifier_epoch()!=epoch&&!t.race_context());
 setup(t);race(t);before=raw.writes.size();geometry(w,1.4f);CHECK(raw.writes.size()==before);t.after(15,pack(),S_OK,0);
 for(int f=1;f<7;++f){geometry(w,1.4f+f*.2f);t.after(15,pack(),S_OK,0);}CHECK(raw.writes.size()>before); // Relearn with surviving MANAGED generations.
 t.shadow.matrices[256].set(world(2.8f));t.shadow.bindings.vertex_shader.set(0x152);
 // VIEW flip keeps race context; projection 45-preview clears it.
 auto view=world();view._11=view._33=-1;t.after(37,pack(D3DTS_VIEW,&view),S_OK,0);CHECK(t.race_context());
 raw.fail_restore=true;draws=raw.draws;CHECK(w.draw_indexed_at(D3DPT_TRIANGLELIST,0,20,0,10,0x400000+SHARED_WORLD_RETURN_RVA)==S_OK);CHECK(raw.draws==draws+1&&t.reflection_restore_pending.known&&t.reflection_disabled);
 DWORD got=0;CHECK(w.GetTextureStageState(1,D3DTSS_TEXCOORDINDEX,&got)==S_OK&&got==(D3DTSS_TCI_CAMERASPACENORMAL|1));
 CHECK(w.DrawPrimitive(D3DPT_TRIANGLELIST,0,10)==E_FAIL&&raw.draws==draws+1);raw.fail_restore=false;CHECK(w.DrawPrimitive(D3DPT_TRIANGLELIST,0,10)==S_OK&&!t.reflection_restore_pending.known&&raw.tci==got);
 auto preview=world();preview._22=static_cast<float>(1./std::tan(45./(4./3.)*3.14159265358979323846/360.));preview._11=preview._22/(4.f/3.f);preview._33=1.00020003f;preview._34=1;preview._43=-.200040013f;preview._44=0;t.after(37,pack(D3DTS_PROJECTION,&preview),S_OK,0x400000+GAMEPLAY_PROJECTION_RETURN_RVA);CHECK(!t.race_context());
}
void stationary_brake_frame(Device8& w,bool brake,bool shuffled){
 auto draw=[&](D3DMATRIX matrix,uint32_t fvf,int start,bool alpha=false){
  auto& t=w.trace;t.shadow.matrices[256].set(matrix);t.shadow.bindings.vertex_shader.set(fvf);t.effective_shadow.bindings.vertex_shader.set(fvf);
  t.shadow.rs[27].set(alpha?1:0);t.shadow.rs[14].set(alpha?0:1);t.effective_shadow.rs[27]=t.shadow.rs[27];t.effective_shadow.rs[14]=t.shadow.rs[14];
  CHECK(w.draw_indexed_at(D3DPT_TRIANGLELIST,0,20,start,start==180?28:10,0x400000+SHARED_WORLD_RETURN_RVA)==S_OK);
 };
 auto body=[&]{if(brake&&shuffled)draw(world(),0x102,150);draw(world(),0x152,0);draw(world(),0x152,30);draw(world(),0x142,120);
  if(brake){if(!shuffled)draw(world(),0x102,150);draw(world(),0x102,180,true);}else draw(world(),0x152,150);
 };
 auto wheels=[&]{for(int k:{2,0,3,1}){auto m=world(k&1?.9f:-.9f,k&2?1.4f:-1.4f);draw(m,0x112,60);draw(m,0x112,90);}};
 if(shuffled){wheels();body();}else{body();wheels();}
 w.trace.shadow.rs[27].set(0);w.trace.shadow.rs[14].set(1);w.trace.effective_shadow.rs[27]=w.trace.shadow.rs[27];w.trace.effective_shadow.rs[14]=w.trace.shadow.rs[14];
 hud(w);
}
void stationary_brake_reflection(){
 MockRootBase rr;Raw raw;Root8 root(&rr);Device8 w(&raw,&root);auto& t=w.trace;t.configure_classifier(true,0x400000);t.enabled=false;
 w.visuals.configure(parse_visual_config({{"Renderer.ConfigVersion","1"},{"VehicleReflections.Mode","ViewDependent2D"}},true),true,nullptr,E_FAIL);
 t.resources.add(100,23,pack(512,0,0,D3DPOOL_MANAGED,0));t.resources.add(200,24,pack(512,0,101,D3DPOOL_MANAGED,0));t.resources.add(300,20,pack(8,8,1,0,21,D3DPOOL_MANAGED,0));setup(t);
 for(uint32_t f=0;f<STRUCTURAL_OBSERVATIONS;++f){race(t);auto n=raw.writes.size();stationary_brake_frame(w,false,false);CHECK(raw.writes.size()==n);t.after(15,pack(),S_OK,0);}
 // No chassis/wheel movement: the first post-proof frame already modifies eligible body draws.
 race(t);auto n=raw.writes.size();stationary_brake_frame(w,false,false);CHECK(raw.writes.size()==n+6);t.after(15,pack(),S_OK,0);
 for(bool shuffled:{false,true}){
  t.enabled=true;t.control.pending=true;race(t);stationary_brake_frame(w,false,false);t.after(15,pack(),S_OK,0);
  race(t);n=raw.writes.size();stationary_brake_frame(w,true,shuffled);CHECK(raw.writes.size()==n+4); // One env removed; both 0x102 layers stay stock.
  t.after(15,pack(),S_OK,0);t.enabled=false;
  race(t);n=raw.writes.size();stationary_brake_frame(w,false,shuffled);CHECK(raw.writes.size()==n+6);t.after(15,pack(),S_OK,0); // Previously proven exact env signature returns immediately; 0x102 never learns.
  race(t);n=raw.writes.size();stationary_brake_frame(w,false,shuffled);CHECK(raw.writes.size()==n+6);t.after(15,pack(),S_OK,0);
 }
}
void gating(){
 Trace t;t.enabled=false;Raw raw;VisualPolicy p;p.configure(parse_visual_config({{"Renderer.ConfigVersion","1"},{"VehicleReflections.Mode","ViewDependent2D"}},true),true,nullptr,E_FAIL);setup(t);
 DrawClassification c;c.reasons=255;c.fvf=0x152;c.transform.track=1;c.transform.constellation=1;c.transform.object=ObjectClass::Body;c.transform.vehicle_reasons=127;c.transform.wheels={2,3,4,5};
 auto check=[&](DrawClassification d,bool modify){auto n=raw.writes.size();auto a=t.shadow.tss[1][11].value;{ReflectionScope scope(raw,t,p,d,0,1);raw.DrawIndexedPrimitive(D3DPT_TRIANGLELIST,0,3,0,1);}CHECK(raw.writes.size()==n+(modify?2:0));CHECK(t.shadow.tss[1][11].value==a&&t.effective_shadow.tss[1][11].value==a);};
 check(c,true);for(int f:{0x112,0x142,0x252}){auto d=c;d.fvf=f;check(d,false);}
 for(uint32_t reason:{EXACT_BUILD,RACE_PROJECTION,CL_OPAQUE,ENV_STAGE,KNOWN_GEOMETRY}){auto d=c;d.reasons&=~reason;check(d,false);}
 auto d=c;d.transform.wheels[3]=0;check(d,false);d=c;d.transform.wheels[3]=d.transform.wheels[2];check(d,false);d=c;d.transform.object=ObjectClass::Wheel;check(d,false);d.transform.object=ObjectClass::Unknown;check(d,false);d=c;d.transform.ambiguous=true;check(d,false);
 p.configure(p.requested,false,nullptr,E_FAIL);check(c,false);p.configure(parse_visual_config({},false),true,nullptr,E_FAIL);check(c,false);
}

void learned_semantics(){
 MockRootBase rr;Raw raw;Root8 root(&rr);Device8 w(&raw,&root);auto& t=w.trace;t.configure_classifier(true,0x400000);t.enabled=false;setup(t);
 t.resources.add(100,23,pack(128,0,0,D3DPOOL_MANAGED,0));t.resources.add(200,24,pack(128,0,101,D3DPOOL_MANAGED,0));t.resources.add(300,20,pack(8,8,1,0,21,D3DPOOL_MANAGED,0));
 auto configure=[&](const char* mode){w.visuals.configure(parse_visual_config({{"Renderer.ConfigVersion","1"},{"VehicleReflections.Mode",mode}},true),true,nullptr,E_FAIL);};configure("ViewDependent2D");
 auto draw=[&](float x,float z,uint32_t fvf,int start){t.shadow.matrices[256].set(world(x,z));t.shadow.bindings.vertex_shader.set(fvf);t.effective_shadow.bindings.vertex_shader.set(fvf);auto n=raw.writes.size();CHECK(w.draw_indexed_at(D3DPT_TRIANGLELIST,0,20,start,10,0x400000+SHARED_WORLD_RETURN_RVA)==S_OK);return raw.writes.size()-n;};
 auto partial=[&](float x){CHECK(draw(x,0,0x152,0)==2);CHECK(draw(x,0,0x152,30)==2);for(int k:{0,1}){CHECK(draw(x+(k&1?.9f:-.9f),-1.4f,0x112,60)==0);CHECK(draw(x+(k&1?.9f:-.9f),-1.4f,0x112,90)==0);}};
 // Discovery still takes the unchanged four-wheel dynamic or stationary oracle.
 for(int f=0;f<8;++f){race(t);geometry(w,f*.2f);t.after(15,pack(),S_OK,0);}
 CHECK(t.learned_signatures()==2);
 // B: sustained two-wheel submission, well beyond the 3-frame object grace.
 for(int f=0;f<12;++f){race(t);partial(1.6f+f*.2f);hud(w);t.after(15,pack(),S_OK,0);}
 race(t);t.shadow.matrices[256].set(world(4.f));t.shadow.bindings.vertex_shader.set(0x152);
 auto c=t.before(71,pack(D3DPT_TRIANGLELIST,0,20,0,10),0x400000+SHARED_WORLD_RETURN_RVA);
 CHECK(c.transform.object!=ObjectClass::Body&&!c.transform.constellation&&c.semantic_id&&c.semantic_source==VehicleSemanticSource::Learned&&std::strcmp(reflection_exclusion(c),"eligible")==0);
 // Capture the learned draw without any live proof; HUD and wheels remain stock.
 t.enabled=true;t.control.pending=true;partial(4.f);hud(w);t.after(15,pack(),S_OK,0);
 race(t);partial(4.2f);hud(w);t.after(15,pack(),S_OK,0);t.enabled=false;
 // An unrelated pointer reuse resets object tracking but must not revoke valid asset proof.
 t.resources.add(900,20,pack(8,8,1,0,21,D3DPOOL_MANAGED,0));auto epoch=t.classifier_epoch();uintptr_t recreated=900;
 t.after(20,pack(8,8,1,0,21,D3DPOOL_MANAGED,&recreated),S_OK,0);
 CHECK(t.classifier_epoch()>epoch&&t.learned_signatures()==2);
 t.enabled=true;t.control.pending=true;race(t);partial(4.2f);hud(w);t.after(15,pack(),S_OK,0);
 race(t);partial(4.4f);hud(w);t.after(15,pack(),S_OK,0);t.enabled=false;
 // C: full proof returns; native reflection did not toggle during its absence.
 for(int f=0;f<6;++f){race(t);auto n=raw.writes.size();geometry(w,4.4f+f*.05f);CHECK(raw.writes.size()==n+4);t.after(15,pack(),S_OK,0);}
 // A failed unseen draw is never promoted, despite complete live vehicle support.
 race(t);raw.draw_hr=E_FAIL;t.shadow.matrices[256].set(world(4.5f));t.shadow.bindings.vertex_shader.set(0x152);CHECK(w.draw_indexed_at(D3DPT_TRIANGLELIST,0,20,360,10,0x400000+SHARED_WORLD_RETURN_RVA)==E_FAIL);raw.draw_hr=S_OK;geometry(w,4.5f);t.after(15,pack(),S_OK,0);CHECK(t.learned_signatures()==2);
 // Shared exact asset on a distant, cold second instance is intentionally eligible.
 race(t);CHECK(draw(40,0,0x152,0)==2);CHECK(draw(40,0,0x152,30)==2);
 // Same env material but distinct geometry/LOD/resource signature must remain unproven.
 CHECK(draw(80,0,0x152,300)==0);CHECK(draw(40,0,0x152,330)==0);
 CHECK(draw(40,0,0x102,0)==0);CHECK(draw(40,0,0x112,0)==0);
 t.shadow.rs[27].set(1);CHECK(draw(40,0,0x152,0)==0);t.shadow.rs[27].set(0);
 t.shadow.rs[14].set(0);CHECK(draw(40,0,0x152,0)==0);t.shadow.rs[14].set(1);
 auto saved=t.shadow.tss[1][11];t.shadow.tss[1][11].set(0x30001);CHECK(draw(40,0,0x152,0)==0);t.shadow.tss[1][11]=saved;
 auto serial=t.resources.generation(100);t.resources.add(400,23,pack(128,0,0,D3DPOOL_MANAGED,0));t.shadow.bindings.streams[0].set({400,36});CHECK(draw(80,0,0x152,0)==0);t.shadow.bindings.streams[0].set({100,36});
 // Failed draw does not add new semantic knowledge; failed Reset preserves it.
 raw.reset_hr=E_FAIL;CHECK(w.Reset(nullptr)==E_FAIL&&t.learned_signatures()==2);raw.reset_hr=S_OK;
 // Stock is a hard no-write policy even with a learned asset.
 configure("Stock");CHECK(draw(40,0,0x152,0)==0);configure("ViewDependent2D");CHECK(draw(40,0,0x152,0)==2);
 // Generation reuse cannot inherit proof, regardless of raw pointer equality.
 t.resources.add(100,23,pack(128,0,0,D3DPOOL_MANAGED,0));CHECK(t.resources.generation(100)!=serial);CHECK(draw(40,0,0x152,0)==0);t.after(15,pack(),S_OK,0);CHECK(t.learned_signatures()==0);
 // Relearn then a real successful Reset: managed metadata survives, ALL semantics/tracks clear.
 for(int f=0;f<8;++f){race(t);geometry(w,f*.2f);t.after(15,pack(),S_OK,0);}CHECK(t.learned_signatures()==2);
 serial=t.resources.generation(100);CHECK(w.Reset(nullptr)==S_OK&&t.resources.generation(100)==serial&&t.learned_signatures()==0);setup(t);race(t);CHECK(draw(40,0,0x152,0)==0);t.after(15,pack(),S_OK,0);
 for(int f=0;f<8;++f){race(t);geometry(w,f*.2f);t.after(15,pack(),S_OK,0);}CHECK(t.learned_signatures()==2);
 hud(w);t.after(15,pack(),S_OK,0);CHECK(t.learned_signatures()==0);race(t);CHECK(draw(40,0,0x152,0)==0);
 for(int f=0;f<8;++f){race(t);geometry(w,f*.2f);t.after(15,pack(),S_OK,0);}CHECK(t.learned_signatures()==2);
 t.after(15,pack(),E_FAIL,0);CHECK(t.learned_signatures()==0);
 t.configure_classifier(false,0x400000);CHECK(!t.learned_signatures());CHECK(draw(40,0,0x152,0)==0);
}
void semantic_key_contracts(){
 Trace t;t.enabled=false;setup(t);t.shadow.bindings.vertex_shader.set(0x152);
 t.resources.add(100,23,pack(128,0,0,D3DPOOL_MANAGED,0));t.resources.add(200,24,pack(128,0,101,D3DPOOL_MANAGED,0));t.resources.add(300,20,pack(8,8,1,0,21,D3DPOOL_MANAGED,0));
 auto a=pack(D3DPT_TRIANGLELIST,0,20,0,10);auto key=vehicle_signature_key(t.shadow,t.resources,a,SHARED_WORLD_RETURN_RVA);CHECK(key.valid(t.resources));
 t.shadow.matrices[256].set(world(100));CHECK(vehicle_signature_key(t.shadow,t.resources,a,SHARED_WORLD_RETURN_RVA)==key);
 a.a[3]=30;CHECK(!(vehicle_signature_key(t.shadow,t.resources,a,SHARED_WORLD_RETURN_RVA)==key));
 auto collision=key;collision.words[18]^=1;CHECK(!(collision==key));
 t.resources.add(300,20,pack(8,8,1,0,21,D3DPOOL_MANAGED,0));CHECK(!key.valid(t.resources));
}
int main(){try{gating();integration();full_frame_lifetime();stationary_brake_reflection();learned_semantics();semantic_key_contracts();std::cout<<"Native reflection / full race-HUD-Present lifetime / menu transition / Reset relearn / fail-closed gates: PASS\n";return 0;}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
