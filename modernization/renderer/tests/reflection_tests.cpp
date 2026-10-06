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
void gating(){
 Trace t;t.enabled=false;Raw raw;VisualPolicy p;p.configure(parse_visual_config({{"Renderer.ConfigVersion","1"},{"VehicleReflections.Mode","ViewDependent2D"}},true),true,nullptr,E_FAIL);setup(t);
 DrawClassification c;c.reasons=255;c.fvf=0x152;c.transform.track=1;c.transform.constellation=1;c.transform.object=ObjectClass::Body;c.transform.vehicle_reasons=127;c.transform.wheels={2,3,4,5};
 auto check=[&](DrawClassification d,bool modify){auto n=raw.writes.size();auto a=t.shadow.tss[1][11].value;{ReflectionScope scope(raw,t,p,d,0,1);raw.DrawIndexedPrimitive(D3DPT_TRIANGLELIST,0,3,0,1);}CHECK(raw.writes.size()==n+(modify?2:0));CHECK(t.shadow.tss[1][11].value==a&&t.effective_shadow.tss[1][11].value==a);};
 check(c,true);for(int f:{0x112,0x142,0x252}){auto d=c;d.fvf=f;check(d,false);}
 for(uint32_t reason:{EXACT_BUILD,RACE_PROJECTION,CL_OPAQUE,ENV_STAGE,KNOWN_GEOMETRY}){auto d=c;d.reasons&=~reason;check(d,false);}
 auto d=c;d.transform.wheels[3]=0;check(d,false);d=c;d.transform.wheels[3]=d.transform.wheels[2];check(d,false);d=c;d.transform.object=ObjectClass::Wheel;check(d,false);d.transform.object=ObjectClass::Unknown;check(d,false);d=c;d.transform.ambiguous=true;check(d,false);
 p.configure(p.requested,false,nullptr,E_FAIL);check(c,false);p.configure(parse_visual_config({},false),true,nullptr,E_FAIL);check(c,false);
}
int main(){try{gating();integration();std::cout<<"Native draw-local reflection / failure restore / pool-aware Reset relearn / trace-off / VIEW / fail-closed gates: PASS\n";return 0;}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
