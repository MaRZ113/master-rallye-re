#include "frontend_model.hpp"
#include "race_model_registry.hpp"
#include <iostream>
#include <map>
#include <fstream>
#include <filesystem>
#include <cstdlib>
using namespace gfx2;using namespace gfx2::ps2port;
int failures=0;
#define CHECK(x) do{if(!(x)){std::cerr<<"FAIL "<<__LINE__<<": "#x"\n";++failures;}}while(0)
#include "mock_interfaces.hpp"
class Texture final:public IDirect3DTexture8 {
public:
 ULONG refs=1;
 std::vector<DWORD> pixels;UINT width=16,height=16;
 HRESULT STDMETHODCALLTYPE QueryInterface(REFIID,void** out) override {if(!out)return E_POINTER;*out=this;AddRef();return S_OK;}
 ULONG STDMETHODCALLTYPE AddRef() override{return ++refs;}
 ULONG STDMETHODCALLTYPE Release() override{return --refs;}
 HRESULT STDMETHODCALLTYPE GetDevice(IDirect3DDevice8**) override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE SetPrivateData(REFGUID,const void*,DWORD,DWORD) override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE GetPrivateData(REFGUID,void*,DWORD*) override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE FreePrivateData(REFGUID) override{return E_NOTIMPL;}
 DWORD STDMETHODCALLTYPE SetPriority(DWORD) override{return 0;}
 DWORD STDMETHODCALLTYPE GetPriority() override{return 0;}
 void STDMETHODCALLTYPE PreLoad() override{}
 D3DRESOURCETYPE STDMETHODCALLTYPE GetType() override{return D3DRTYPE_TEXTURE;}
 DWORD STDMETHODCALLTYPE SetLOD(DWORD) override{return 0;}
 DWORD STDMETHODCALLTYPE GetLOD() override{return 0;}
 DWORD STDMETHODCALLTYPE GetLevelCount() override{return 1;}
 HRESULT STDMETHODCALLTYPE GetLevelDesc(UINT,D3DSURFACE_DESC*) override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE GetSurfaceLevel(UINT,IDirect3DSurface8**) override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE LockRect(UINT,D3DLOCKED_RECT* p,const RECT*,DWORD) override{p->pBits=pixels.data();p->Pitch=width*4;return S_OK;}
 HRESULT STDMETHODCALLTYPE UnlockRect(UINT) override{return S_OK;}
 HRESULT STDMETHODCALLTYPE AddDirtyRect(const RECT*) override{return E_NOTIMPL;}
};

struct Native:MockDeviceBase {
 std::map<DWORD,DWORD> rs;std::map<std::pair<DWORD,DWORD>,DWORD> ts;IDirect3DBaseTexture8* texture[2]{};IDirect3DVertexBuffer8* stream=nullptr;UINT stride=24;DWORD vertex=0x142,pixel=0;D3DMATRIX matrix{};unsigned writes=0,fail=0,draws=0;HRESULT drawn=S_FALSE;
 std::vector<std::unique_ptr<Texture>> allocated;unsigned creates=0,fail_create=0;
 HRESULT STDMETHODCALLTYPE CreateTexture(UINT w,UINT h,UINT levels,DWORD usage,D3DFORMAT f,D3DPOOL pool,IDirect3DTexture8** out)override{CHECK(levels==1&&usage==0&&f==D3DFMT_A8R8G8B8&&pool==D3DPOOL_MANAGED);if(++creates==fail_create){*out=nullptr;return E_FAIL;}auto t=std::make_unique<Texture>();t->width=w;t->height=h;t->pixels.resize(w*h);*out=t.get();allocated.push_back(std::move(t));return S_OK;}
 Native(){matrix._11=matrix._22=matrix._33=matrix._44=1;for(const auto& op:kFrontendOps){if(op.render)rs[op.key]=op.key+100;else ts[{op.stage,op.key}]=op.key+op.stage*100+200;}}
 HRESULT write()noexcept{return ++writes==fail?E_FAIL:S_OK;}
 HRESULT STDMETHODCALLTYPE GetRenderState(D3DRENDERSTATETYPE k,DWORD* v)override{*v=rs[k];return S_OK;}
 HRESULT STDMETHODCALLTYPE SetRenderState(D3DRENDERSTATETYPE k,DWORD v)override{rs[k]=v;return write();}
 HRESULT STDMETHODCALLTYPE GetTextureStageState(DWORD s,D3DTEXTURESTAGESTATETYPE k,DWORD* v)override{*v=ts[{s,k}];return S_OK;}
 HRESULT STDMETHODCALLTYPE SetTextureStageState(DWORD s,D3DTEXTURESTAGESTATETYPE k,DWORD v)override{ts[{s,k}]=v;return write();}
 HRESULT STDMETHODCALLTYPE GetTexture(DWORD s,IDirect3DBaseTexture8** v)override{*v=texture[s];return S_OK;}
 HRESULT STDMETHODCALLTYPE SetTexture(DWORD s,IDirect3DBaseTexture8* v)override{texture[s]=v;return write();}
 HRESULT STDMETHODCALLTYPE GetStreamSource(UINT,IDirect3DVertexBuffer8** v,UINT* s)override{*v=stream;*s=stride;return S_OK;}
 HRESULT STDMETHODCALLTYPE SetStreamSource(UINT,IDirect3DVertexBuffer8* v,UINT s)override{stream=v;stride=s;return write();}
 HRESULT STDMETHODCALLTYPE GetVertexShader(DWORD* v)override{*v=vertex;return S_OK;}
 HRESULT STDMETHODCALLTYPE SetVertexShader(DWORD v)override{vertex=v;return write();}
 HRESULT STDMETHODCALLTYPE GetPixelShader(DWORD* v)override{*v=pixel;return S_OK;}
 HRESULT STDMETHODCALLTYPE SetPixelShader(DWORD v)override{pixel=v;return write();}
 HRESULT STDMETHODCALLTYPE GetTransform(D3DTRANSFORMSTATETYPE,D3DMATRIX* v)override{*v=matrix;return S_OK;}
 HRESULT STDMETHODCALLTYPE SetTransform(D3DTRANSFORMSTATETYPE,const D3DMATRIX* v)override{matrix=*v;return write();}
 HRESULT STDMETHODCALLTYPE DrawPrimitiveUP(D3DPRIMITIVETYPE,UINT,const void*,UINT)override{++draws;stream=nullptr;stride=0;return drawn;}
};
void transactions(){auto notify=[](uint32_t slot,const Args&,HRESULT)noexcept{CHECK(slot==50||slot==63||slot==61||slot==76||slot==88||slot==37||slot==83||slot==72);};auto* primary=reinterpret_cast<IDirect3DTexture8*>(0x10000);auto* secondary=reinterpret_cast<IDirect3DTexture8*>(0x20000);
 for(unsigned failure=0;failure<=38;++failure){Native n;const auto rs=n.rs;const auto ts=n.ts;FrontendTransaction t;CHECK(SUCCEEDED(t.capture(n)));n.fail=failure;auto env=n.matrix;env._31=.5f;const auto hr=t.material(n,3,primary,secondary,env,notify);if(SUCCEEDED(hr)){t.before_up();const auto drawn=n.DrawPrimitiveUP(D3DPT_TRIANGLELIST,1,nullptr,36);CHECK(drawn==S_FALSE&&n.draws==1);}n.fail=0;CHECK(SUCCEEDED(t.restore(n,notify)));CHECK(!t.pending());CHECK(n.rs==rs&&n.ts==ts&&n.texture[0]==nullptr&&n.texture[1]==nullptr&&n.stream==nullptr&&n.stride==24&&n.vertex==0x142&&n.pixel==0);CHECK(n.matrix._31==0);}
 Native pending;FrontendTransaction retained;CHECK(SUCCEEDED(retained.capture(pending)));CHECK(SUCCEEDED(retained.material(pending,3,primary,secondary,pending.matrix,notify)));pending.fail=pending.writes+1;CHECK(FAILED(retained.restore(pending,notify)));CHECK(retained.pending());pending.fail=0;CHECK(SUCCEEDED(retained.restore(pending,notify)));CHECK(!retained.pending());
 Native n;FrontendTransaction t;CHECK(SUCCEEDED(t.capture(n)));n.fail=1;CHECK(FAILED(t.material(n,20,primary,nullptr,n.matrix,notify)));CHECK(n.draws==0);CHECK(SUCCEEDED(t.restore(n,notify)));
}
void effective_shadow(){Native n;Shadow effective,logical;for(const auto& op:kFrontendOps){if(op.render)effective.update(50,pack(op.key,n.rs[op.key]),S_OK);else effective.update(63,pack(op.stage,op.key,n.ts[{op.stage,op.key}]),S_OK);}logical=effective;FrontendTransaction t;CHECK(SUCCEEDED(t.capture(n)));auto writer=[&](uint32_t slot,const Args& args,HRESULT hr)noexcept{effective.update(slot,args,static_cast<uint32_t>(hr));};CHECK(SUCCEEDED(t.material(n,20,reinterpret_cast<IDirect3DTexture8*>(0x10000),nullptr,n.matrix,writer)));CHECK(effective.rs[D3DRS_ALPHABLENDENABLE].value==TRUE&&effective.rs[D3DRS_ZWRITEENABLE].value==FALSE);CHECK(logical.rs[D3DRS_ZWRITEENABLE].value==D3DRS_ZWRITEENABLE+100);CHECK(SUCCEEDED(t.restore(n,writer)));for(const auto& op:kFrontendOps)if(op.render)CHECK(effective.rs[op.key].known&&effective.rs[op.key].value==logical.rs[op.key].value);}
void primary_orientation(){FrontendVertex v{{1,2,3},{4,5,6},0x12345678,{.25f,.125f}};const auto sampled=frontend_primary_sample_vertex(v);CHECK(sampled.uv[0]==.25f&&sampled.uv[1]==.875f);CHECK(v.uv[1]==.125f);CHECK(std::memcmp(v.xyz,sampled.xyz,sizeof(v.xyz))==0&&std::memcmp(v.normal,sampled.normal,sizeof(v.normal))==0&&v.color==sampled.color);for(float y:{0.f,.5f,1.f,-.25f,1.25f}){v.uv[1]=y;CHECK(frontend_primary_sample_vertex(v).uv[1]==1.f-y);}}
void assets(){CHECK(frontend_fixed_pixel_shader(0,false,0));CHECK(frontend_fixed_pixel_shader(0,true,0));CHECK(!frontend_fixed_pixel_shader(1,false,0));CHECK(!frontend_fixed_pixel_shader(0,true,1));FrontendAsset a;CHECK(!decode_frontend_asset({},a));FrontendModel stock(true,L"Z:\\missing\\PS2Port.ini");CHECK(!stock.requested()&&stock.asset().vertices.empty());auto p=std::filesystem::temp_directory_path()/"mrr-frontend-mode-test.ini";for(const auto* mode:{L"0",L"2",L"-1",L"1x"}){std::ofstream f(p);std::wstring m(mode);f<<"[PS2Port]\nFrontendModelMode="<<std::string(m.begin(),m.end())<<"\n";f.close();FrontendModel x(true,p.wstring());CHECK(!x.requested());}if(const char* path=std::getenv("MRR_FRONTEND_MODEL_ASSET")){std::ifstream f(path,std::ios::binary);std::vector<uint8_t> bytes((std::istreambuf_iterator<char>(f)),{});CHECK(decode_frontend_asset(bytes,a));CHECK(a.meshes.size()==24&&a.vertices.size()==6606&&a.indices.size()==13908&&a.textures.size()==28);CHECK(a.meshes[17].mode==0&&a.meshes[17].texture[0]==27&&a.meshes[17].texture[1]==UINT32_MAX);bytes.back()^=1;CHECK(!decode_frontend_asset(bytes,a));std::ofstream ini(p);ini<<"[PS2Port]\nFrontendModelMode=1\nFrontendModelAsset="<<path<<"\n";ini.close();FrontendModel valid(true,p.wstring());CHECK(valid.requested());for(size_t i=0;i<valid.asset().meshes.size();++i){const auto& mesh=valid.asset().meshes[i];for(unsigned k=0;k<mesh.count;++k){const auto& original=valid.asset().vertices[valid.asset().indices[mesh.first+k]];const auto& sampled=valid.expanded()[i][k];CHECK(sampled.uv[0]==original.uv[0]&&sampled.uv[1]==1.f-original.uv[1]);CHECK(std::memcmp(original.xyz,sampled.xyz,sizeof(original.xyz))==0);}}Native upload;CHECK(valid.initialize(upload));CHECK(upload.creates==28);CHECK(valid.initialize(upload)&&upload.creates==28);CHECK(upload.allocated[27]->pixels.size()==64&&upload.allocated[27]->pixels[0]==0xff000000);valid.reset();for(const auto& t:upload.allocated)CHECK(t->refs==0);CHECK(valid.initialize(upload)&&upload.creates==56);valid.reset();for(const auto& t:upload.allocated)CHECK(t->refs==0);FrontendModel failed(true,p.wstring());Native missing;missing.fail_create=13;CHECK(!failed.initialize(missing));for(const auto& t:missing.allocated)CHECK(t->refs==0);CHECK(!failed.requested());CHECK(!failed.initialize(missing)&&missing.creates==13);FrontendModel unknown(false,p.wstring());CHECK(!unknown.requested());std::ofstream bad(p);bad<<"[PS2Port]\nFrontendModelMode=1\nFrontendModelVersion=9\nFrontendModelAsset="<<path<<"\n";bad.close();FrontendModel version(true,p.wstring());CHECK(!version.requested());}
 std::filesystem::remove(p);
}
void queue_owner(){std::map<uintptr_t,uint32_t> memory;const uintptr_t stack=0x10000,base=0x400000,mesh=0x90000;auto read=[&](uintptr_t a,uint32_t& v)noexcept{auto i=memory.find(a);if(i==memory.end())return false;v=i->second;return true;};for(auto ret:{0x5628c1u,0x5629eeu}){memory={{stack+0x48,ret},{stack+0x28,0x20000},{stack+0x24,1},{stack+0x20,1},{0x20044,0x30000},{0x20048,0x30008},{0x30004,0x40000},{0x40000,0x80000},{0x40004,uint32_t(mesh)},{stack+0x4c,0x25}};uintptr_t owner=0;CHECK(frontend_queue_owner(stack,base,mesh,read,owner)&&owner==0x80000);memory[0x40004]=0x90004;CHECK(!frontend_queue_owner(stack,base,mesh,read,owner));memory[0x40004]=mesh;memory[stack+0x48]=0x562900;CHECK(!frontend_queue_owner(stack,base,mesh,read,owner));memory[stack+0x48]=ret;memory[0x20048]=0x30004;CHECK(!frontend_queue_owner(stack,base,mesh,read,owner));}}
void race_policy(){CHECK(race_warmup_admitted(0x1fff,true,true));CHECK(!race_warmup_admitted(0x1ffe,true,true));CHECK(!race_warmup_admitted(0,true,true));CHECK(!race_warmup_admitted(0x3fff,true,true));CHECK(!race_warmup_admitted(0x1fff,false,true));CHECK(!race_warmup_admitted(0x1fff,true,false));FrontendModel stock(true,L"Z:\\missing\\PS2Port.ini",true);CHECK(!stock.requested());if(const auto path=std::getenv("MRR_RACE_MODEL_ASSET")){std::ifstream f(path,std::ios::binary);std::vector<uint8_t> bytes((std::istreambuf_iterator<char>(f)),{});FrontendAsset asset;CHECK(decode_frontend_asset(bytes,asset,true));CHECK(!decode_frontend_asset(bytes,asset,false));CHECK(decode_frontend_asset(bytes,asset,true));CHECK(asset.meshes.size()==20&&asset.vertices.size()==3292&&asset.indices.size()==5940&&asset.textures.size()==24);auto ini=std::filesystem::temp_directory_path()/"mrr-race-model-test.ini";for(auto mode:{"0","2","-1","1x","1"}){std::ofstream o(ini);o<<"[PS2Port]\nRacePS2ModelMode="<<mode<<"\nRacePS2ModelAsset="<<path<<"\n";o.close();FrontendModel x(true,ini.wstring(),true);CHECK(x.requested()==(std::string(mode)=="1"));CHECK(!x.parts_enabled());CHECK(!FrontendModel(true,ini.wstring()).requested());if(x.requested()){Native n;CHECK(x.initialize(n)&&n.creates==24);x.reset();for(auto& t:n.allocated)CHECK(t->refs==0);}}for(auto parts:{0,1,2,-1}){std::ofstream o(ini);o<<"[PS2Port]\nRacePS2ModelMode=1\nRacePS2ModelParts="<<parts<<"\nRacePS2ModelAsset="<<path<<"\n";o.close();FrontendModel x(true,ini.wstring(),true);CHECK(x.parts_enabled()==(parts==1));}std::filesystem::remove(ini);bytes.back()^=1;CHECK(!decode_frontend_asset(bytes,asset,true));}}
int main(){race_policy();primary_orientation();queue_owner();transactions();effective_shadow();assets();return failures?1:0;}
