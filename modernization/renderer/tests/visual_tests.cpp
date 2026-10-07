#include "wrappers.hpp"
#include <iostream>
#include <stdexcept>
#include <cmath>
#include <cstring>
#include <cfenv>
#define CHECK(x) do{if(!(x))throw std::runtime_error(#x);}while(0)
#include "mock_interfaces.hpp"
using namespace gfx2;
VisualConfig enabled(){return parse_visual_config({{"Renderer.ConfigVersion","1"},{"Filtering.AnisotropicFiltering","true"},{"Camera.GameplayFOV","true"},{"Shadows.Mode","Off"}},true);}
D3DCAPS8 caps(){D3DCAPS8 c{};c.MaxAnisotropy=8;c.TextureFilterCaps=D3DPTFILTERCAPS_MINFANISOTROPIC|D3DPTFILTERCAPS_MAGFANISOTROPIC;return c;}
D3DMATRIX perspective(){D3DMATRIX m{};m._11=1.12245429f;m._22=1.49660575f;m._33=1.00020003f;m._34=1;m._43=-.200040013f;return m;}
void config_contracts(){
 CHECK(!parse_visual_config({},false).fov);auto c=enabled();CHECK(c.version_ok&&c.anisotropy&&c.fov&&c.shadow_off);
 CHECK(!parse_visual_config({{"Renderer.ConfigVersion","2"},{"Camera.GameplayFOV","true"}},true).fov);
 CHECK(!parse_visual_config({{"Camera.GameplayFOV","true"}},true).fov);
 for(const char* bad:{"oops","nan","inf","29.9","110.1","80junk"}){auto m=c.raw_fields;m["Camera.VerticalFOVDegrees"]=bad;std::unordered_map<std::string,std::string> f(m.begin(),m.end());auto a=parse_visual_config(f,true);CHECK(!a.fov&&a.anisotropy&&a.shadow_off&&!a.fov_reason.empty());}
 for(const char* bad:{"0","-1","2.5","oops"}){auto a=parse_visual_config({{"Renderer.ConfigVersion","1"},{"Filtering.AnisotropicFiltering","true"},{"Filtering.MaxAnisotropy",bad},{"Camera.GameplayFOV","true"}},true);CHECK(!a.anisotropy&&a.fov);}
 CHECK(!parse_visual_config({{"Renderer.ConfigVersion","1"},{"Filtering.AnisotropicFiltering","yes"}},true).anisotropy);
 CHECK(!parse_visual_config({{"Renderer.ConfigVersion","1"},{"Shadows.Mode","Opacity"}},true).shadow_off);
 CHECK(parse_visual_config({{"Renderer.ConfigVersion","1"},{"Camera.GameplayFOV","true"},{"Camera.VerticalFOVDegrees","110"}},true).fov);
 auto reflection=parse_visual_config({{"Renderer.ConfigVersion","1"},{"VehicleReflections.Mode","ViewDependent2D"}},true);CHECK(reflection.reflection_mode=="ViewDependent2D");
 VisualPolicy blocked;blocked.configure(reflection,true,nullptr,E_FAIL);CHECK(blocked.effective.reflection_mode=="ViewDependent2D"&&blocked.effective.reflection_reason=="requires_live_or_learned_body_proof_current_material");
 blocked.configure(reflection,false,nullptr,E_FAIL);CHECK(blocked.effective.reflection_mode=="Stock"&&blocked.effective.reflection_reason=="unsupported_build");
 reflection.display_mode="Borderless";reflection.interface_mode="PreserveMargins";reflection.aa_mode="MSAA";reflection.menu_freeze=true;
 blocked.configure(reflection,false,nullptr,E_FAIL);
 CHECK(blocked.requested.display_mode=="Borderless"&&blocked.requested.menu_freeze);
 CHECK(blocked.effective.display_mode=="Borderless"&&blocked.effective.interface_mode=="PreserveMargins"&&blocked.effective.aa_mode=="MSAA"&&blocked.effective.menu_freeze);
 CHECK(blocked.effective.reason=="feature_local_compatibility"); // root/device apply local game-owner capabilities
 auto invalid=parse_visual_config({{"Renderer.ConfigVersion","1"},{"VehicleReflections.Mode","Cubemap"}},true);CHECK(invalid.reflection_mode=="Stock"&&!invalid.reflection_reason.empty());
 std::cout<<"Config missing/version/invalid fields/independence: PASS\n";
}
void policy_contracts(){
 VisualPolicy p;auto c=enabled();auto cap=caps();p.configure(c,true,&cap,S_OK);
 CHECK(p.effective.max_anisotropy==8);CHECK(p.filter(0,D3DTSS_MINFILTER,D3DTEXF_LINEAR)==D3DTEXF_ANISOTROPIC);
 CHECK(p.filter(0,D3DTSS_MAGFILTER,D3DTEXF_LINEAR)==D3DTEXF_LINEAR);
 CHECK(p.filter(0,D3DTSS_MIPFILTER,D3DTEXF_LINEAR)==D3DTEXF_LINEAR);
 CHECK(p.filter(0,D3DTSS_MINFILTER,D3DTEXF_POINT)==D3DTEXF_POINT);
 CHECK(p.filter(1,D3DTSS_MINFILTER,D3DTEXF_LINEAR)==D3DTEXF_LINEAR);
 cap.MaxAnisotropy=16;p.configure(c,true,&cap,S_OK);CHECK(p.effective.max_anisotropy==16);
 cap.TextureFilterCaps=D3DPTFILTERCAPS_MINFANISOTROPIC;p.configure(c,true,&cap,S_OK);CHECK(p.filter(0,D3DTSS_MAGFILTER,D3DTEXF_LINEAR)==D3DTEXF_LINEAR);
 cap.TextureFilterCaps=0;p.configure(c,true,&cap,S_OK);CHECK(!p.effective.anisotropy&&p.effective.fov);
 p.configure(c,true,nullptr,E_FAIL);CHECK(!p.effective.anisotropy);
 cap=caps();p.configure(c,false,&cap,S_OK);CHECK(p.active()&&p.effective.anisotropy&&!p.effective.fov&&!p.effective.shadow_off);CHECK(p.filter(0,D3DTSS_MINFILTER,D3DTEXF_LINEAR)==D3DTEXF_ANISOTROPIC);
 p.configure(parse_visual_config({},false),true,&cap,S_OK);CHECK(!p.active());
 p.configure(c,true,&cap,S_OK);auto original=perspective();D3DMATRIX out{};
 CHECK(!p.projection(D3DTS_PROJECTION,&original,out,false,GAMEPLAY_PROJECTION_RETURN_RVA));
 CHECK(!p.projection(D3DTS_PROJECTION,&original,out,true,99));CHECK(!p.projection(D3DTS_VIEW,&original,out,true,GAMEPLAY_PROJECTION_RETURN_RVA));
 auto unsupported=original;unsupported._31=.1f;CHECK(!p.projection(D3DTS_PROJECTION,&unsupported,out,true,GAMEPLAY_PROJECTION_RETURN_RVA));
 unsupported=original;unsupported._11=0;CHECK(!p.projection(D3DTS_PROJECTION,&unsupported,out,true,GAMEPLAY_PROJECTION_RETURN_RVA));
 unsupported=original;unsupported._22=NAN;CHECK(!p.projection(D3DTS_PROJECTION,&unsupported,out,true,GAMEPLAY_PROJECTION_RETURN_RVA));
 D3DMATRIX ortho{};ortho._11=2.f/640;ortho._22=2.f/480;ortho._44=1;CHECK(!p.projection(D3DTS_PROJECTION,&ortho,out,true,GAMEPLAY_PROJECTION_RETURN_RVA));
 c.vfov=80;p.configure(c,true,&cap,S_OK);CHECK(p.projection(D3DTS_PROJECTION,&original,out,true,GAMEPLAY_PROJECTION_RETURN_RVA));
 CHECK(std::abs(vertical_fov(out)-80)<.0001f);CHECK(std::abs(out._22/out._11-original._22/original._11)<.000001f);
 for(int i=0;i<16;++i)if(i!=0&&i!=5)CHECK(!std::memcmp(&out.m[0][0]+i,&original.m[0][0]+i,4));
 // Authored angle families at both observed aspect ratios, independent of resolution.
 for(double aspect:{640./480.,1920./1027.,.75}){
  for(double angle:{90.,45.,70.,89.98,90.02}){
   auto m=perspective();double vfov=angle/std::max(1.,aspect);
   m._22=static_cast<float>(1./std::tan(vfov*3.14159265358979323846/360.));m._11=static_cast<float>(m._22/aspect);
   CHECK(std::abs(source_camera_angle(m)-angle)<.00002);
   auto before=m;bool accepted=p.projection(D3DTS_PROJECTION,&m,out,true,GAMEPLAY_PROJECTION_RETURN_RVA);
   CHECK(accepted==(angle==90.));CHECK(!std::memcmp(&m,&before,sizeof(m)));
   if(accepted){CHECK(std::abs(vertical_fov(out)-80)<.0001);CHECK(std::abs(out._22/out._11-m._22/m._11)<.000001);
    for(int i=0;i<16;++i)if(i!=0&&i!=5)CHECK(!std::memcmp(&out.m[0][0]+i,&m.m[0][0]+i,4));}
   p.configure(c,false,&cap,S_OK);CHECK(!p.projection(D3DTS_PROJECTION,&m,out,true,GAMEPLAY_PROJECTION_RETURN_RVA));
   p.configure(parse_visual_config({},false),true,&cap,S_OK);CHECK(!p.projection(D3DTS_PROJECTION,&m,out,true,GAMEPLAY_PROJECTION_RETURN_RVA));p.configure(c,true,&cap,S_OK);
  }
 }
 Shadow s;s.rs[27].set(1);s.rs[28].set(0);s.rs[14].set(0);s.bindings.vertex_shader.set(0x142);
 CHECK(p.suppress(70,true,STOCK_SHADOW_RETURN_RVA,s,D3DPT_TRIANGLELIST));CHECK(!p.suppress(71,true,STOCK_SHADOW_RETURN_RVA,s,D3DPT_TRIANGLELIST));
 CHECK(!p.suppress(70,false,STOCK_SHADOW_RETURN_RVA,s,D3DPT_TRIANGLELIST));CHECK(!p.suppress(70,true,99,s,D3DPT_TRIANGLELIST));
 s.rs[28].known=false;CHECK(!p.suppress(70,true,STOCK_SHADOW_RETURN_RVA,s,D3DPT_TRIANGLELIST));
 std::cout<<"Caps / AF / FOV scales, exact Z bits / shadow exact-site policy: PASS\n";
}
struct Raw final:MockDeviceBase {
 Raw(){tss[0][D3DTSS_MAXANISOTROPY]=1;}
 ULONG refs=1;unsigned setters=0,draws=0,caps_calls=0;HRESULT result=S_OK;bool fail_max=false,fail_filter=false;
 DWORD tss[8][64]{};D3DMATRIX matrix_value=perspective();const D3DMATRIX* received=nullptr;
 ULONG STDMETHODCALLTYPE AddRef() override{return ++refs;}ULONG STDMETHODCALLTYPE Release() override{return --refs;}
 HRESULT STDMETHODCALLTYPE GetDeviceCaps(D3DCAPS8* out) override{++caps_calls;if(FAILED(result))return result;*out=caps();return S_OK;}
 HRESULT STDMETHODCALLTYPE SetTextureStageState(DWORD stage,D3DTEXTURESTAGESTATETYPE type,DWORD v) override{++setters;if(FAILED(result))return result;if(type==D3DTSS_MAXANISOTROPY&&fail_max)return E_FAIL;if(fail_filter&&v==D3DTEXF_ANISOTROPIC&&(type==D3DTSS_MINFILTER||type==D3DTSS_MAGFILTER))return D3DERR_INVALIDCALL;tss[stage][type]=v;return S_OK;}
 HRESULT STDMETHODCALLTYPE GetTextureStageState(DWORD stage,D3DTEXTURESTAGESTATETYPE type,DWORD* out) override{if(FAILED(result))return result;*out=tss[stage][type];return S_OK;}
 HRESULT STDMETHODCALLTYPE SetTransform(D3DTRANSFORMSTATETYPE,const D3DMATRIX* v) override{received=v;if(FAILED(result))return result;matrix_value=*v;return S_OK;}
 HRESULT STDMETHODCALLTYPE GetTransform(D3DTRANSFORMSTATETYPE,D3DMATRIX* out) override{if(FAILED(result))return result;*out=matrix_value;return S_OK;}
 HRESULT STDMETHODCALLTYPE DrawPrimitive(D3DPRIMITIVETYPE,UINT,UINT) override{++draws;return result;}
 HRESULT STDMETHODCALLTYPE Reset(D3DPRESENT_PARAMETERS*) override{if(SUCCEEDED(result)){std::memset(tss,0,sizeof(tss));tss[0][D3DTSS_MAXANISOTROPY]=1;}return result;}
 HRESULT STDMETHODCALLTYPE BeginStateBlock() override{return result;}
};
void wrapper_contracts(){
 MockRootBase raw_root;Raw raw;auto* root=new Root8(&raw_root);auto* w=new Device8(&raw,root);auto c=enabled();auto cap=caps();
 CHECK(raw.caps_calls==0);w->SetTextureStageState(0,D3DTSS_MINFILTER,D3DTEXF_LINEAR);CHECK(raw.setters==1&&raw.tss[0][17]==2);
 auto original=perspective();CHECK(w->SetTransform(D3DTS_PROJECTION,&original)==S_OK);CHECK(raw.received==&original);
 CHECK(w->DrawPrimitive(D3DPT_TRIANGLELIST,0,7)==S_OK&&raw.draws==1);
 w->visuals.configure(c,true,&cap,S_OK);CHECK(w->SetTextureStageState(0,D3DTSS_MINFILTER,D3DTEXF_LINEAR)==S_OK);
 CHECK(raw.tss[0][17]==3&&raw.tss[0][21]==8);CHECK(w->DrawIndexedPrimitive(D3DPT_TRIANGLELIST,0,3,0,1)==raw.hr&&raw.last==71);CHECK(w->trace.shadow.tss[0][17].value==2&&w->trace.effective_shadow.tss[0][17].value==3);
 DWORD value=0;CHECK(w->GetTextureStageState(0,D3DTSS_MINFILTER,&value)==S_OK&&value==2);CHECK(w->GetTextureStageState(0,D3DTSS_MAXANISOTROPY,&value)==S_OK&&value==1);
 raw.result=E_FAIL;value=123;CHECK(w->GetTextureStageState(0,D3DTSS_MINFILTER,&value)==E_FAIL&&value==123);
 CHECK(w->SetTextureStageState(0,D3DTSS_MINFILTER,D3DTEXF_POINT)==E_FAIL);CHECK(w->trace.shadow.tss[0][17].value==2&&w->trace.effective_shadow.tss[0][17].value==3);
 CHECK(w->Reset(nullptr)==E_FAIL&&w->trace.shadow.tss[0][17].known);
 raw.result=S_OK;CHECK(w->Reset(nullptr)==S_OK);CHECK(!w->trace.shadow.tss[0][17].known&&!w->trace.effective_shadow.tss[0][17].known&&w->visuals.effective.anisotropy);
 CHECK(w->SetTextureStageState(0,D3DTSS_MINFILTER,D3DTEXF_LINEAR)==S_OK&&raw.tss[0][17]==3&&raw.tss[0][21]==8);
 for(DWORD filter:{static_cast<DWORD>(D3DTEXF_POINT),static_cast<DWORD>(D3DTEXF_LINEAR)}){
  CHECK(w->SetTextureStageState(0,D3DTSS_MAGFILTER,filter)==S_OK&&raw.tss[0][16]==filter);
  CHECK(w->GetTextureStageState(0,D3DTSS_MAGFILTER,&value)==S_OK&&value==filter);
  CHECK(w->trace.shadow.tss[0][16].value==w->trace.effective_shadow.tss[0][16].value);
 }
 CHECK(w->SetTextureStageState(0,D3DTSS_MIPFILTER,D3DTEXF_LINEAR)==S_OK&&raw.tss[0][18]==2);
 CHECK(w->SetTextureStageState(1,D3DTSS_MINFILTER,D3DTEXF_LINEAR)==S_OK);CHECK(raw.tss[1][17]==2&&raw.tss[0][17]==3); // stage1 stays LINEAR; stage0 remains independently overridden.
 CHECK(w->SetTextureStageState(0,D3DTSS_MINFILTER,D3DTEXF_POINT)==S_OK&&raw.tss[0][17]==1);
 raw.matrix_value=original;raw.matrix_value._11=.8f;w->trace.shadow.matrices[3].set(original);w->trace.effective_shadow.matrices[3].set(raw.matrix_value);
 D3DMATRIX got{};CHECK(w->GetTransform(D3DTS_PROJECTION,&got)==S_OK&&!std::memcmp(&got,&original,sizeof(got)));
 CHECK(w->trace.effective_shadow.matrices[3].value._11==.8f);
 raw.result=E_FAIL;std::memset(&got,0,sizeof(got));CHECK(w->GetTransform(D3DTS_PROJECTION,&got)==E_FAIL&&got._11==0);raw.result=S_OK;
 w->trace.control.pending=true;w->trace.after(15,pack(nullptr,nullptr,nullptr,nullptr),S_OK,0);
 w->SetTextureStageState(0,D3DTSS_MINFILTER,D3DTEXF_LINEAR);w->DrawPrimitive(D3DPT_TRIANGLELIST,0,2);w->trace.after(15,pack(nullptr,nullptr,nullptr,nullptr),S_OK,0);
 CHECK(w->BeginStateBlock()==S_OK&&!w->visuals.active());CHECK(raw.tss[0][17]==2&&raw.tss[0][21]==1&&raw.matrix_value._11==original._11);
 // Failed extra MAX falls back to the original filter setter, without failure fiction.
 w->visuals.configure(c,true,&cap,S_OK);CHECK(w->Reset(nullptr)==S_OK);raw.fail_max=true;
 CHECK(w->SetTextureStageState(0,D3DTSS_MINFILTER,D3DTEXF_LINEAR)==S_OK&&raw.tss[0][17]==2);
 CHECK(!w->visuals.effective.anisotropy&&w->visuals.effective.fov);raw.fail_max=false;w->visuals.configure(c,true,&cap,S_OK);CHECK(w->Reset(nullptr)==S_OK);raw.fail_filter=true;CHECK(w->SetTextureStageState(0,D3DTSS_MINFILTER,D3DTEXF_LINEAR)==S_OK&&raw.tss[0][17]==2&&w->trace.shadow.tss[0][17].value==2&&w->trace.effective_shadow.tss[0][17].value==2);
 w->Release();root->Release();std::cout<<"Actual wrappers: default-off args / dual getters / setter failure / Reset / block fallback / bounded trace: PASS\n";
}
int main(){try{config_contracts();policy_contracts();wrapper_contracts();return 0;}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
