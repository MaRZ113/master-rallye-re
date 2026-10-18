#include "course_object_transaction.hpp"
#include <array>
#include <cstring>
#include <iostream>
#include <limits>
#include <vector>

using namespace gfx2;
using namespace gfx2::ps2port;
int failures=0;
#define CHECK(x) do{if(!(x)){std::cerr<<"FAIL "<<__LINE__<<": "#x"\n";++failures;}}while(0)
#include "mock_interfaces.hpp"
namespace {
class Texture final:public IDirect3DTexture8 {
public:
 ULONG refs=1;
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
 HRESULT STDMETHODCALLTYPE LockRect(UINT,D3DLOCKED_RECT*,const RECT*,DWORD) override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE UnlockRect(UINT) override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE AddDirtyRect(const RECT*) override{return E_NOTIMPL;}
};
class Buffer final:public IDirect3DVertexBuffer8 {
public:
 ULONG refs=1;
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
 D3DRESOURCETYPE STDMETHODCALLTYPE GetType() override{return D3DRTYPE_VERTEXBUFFER;}
 HRESULT STDMETHODCALLTYPE Lock(UINT,UINT,BYTE**,DWORD) override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE Unlock() override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE GetDesc(D3DVERTEXBUFFER_DESC*) override{return E_NOTIMPL;}
};
D3DMATRIX matrix(float value){D3DMATRIX m{};m._11=m._22=m._33=m._44=value;return m;}
struct Native:MockDeviceBase {
 std::array<DWORD,256> rs{};
 std::array<std::array<DWORD,64>,2> tss{};
 std::array<D3DMATRIX,3> matrices={matrix(3),matrix(4),matrix(5)};
 DWORD vertex_shader=0xdead,pixel_shader=0xbeef;
 Texture original_texture,replacement;
 Buffer original_buffer;
 IDirect3DBaseTexture8* texture=&original_texture;
 IDirect3DVertexBuffer8* stream=&original_buffer;
 UINT stride=36;
 int gets=0,writes=0,draws=0,fail_get=0,fail_set=0,fail_set_again=0;
 int rt_writes=0,viewport_writes=0,index_writes=0,state_blocks=0;
 bool mutate_on_failure=true;
 HRESULT draw_hresult=static_cast<HRESULT>(0x88761234u);
 Native(){for(size_t i=0;i<rs.size();++i)rs[i]=static_cast<DWORD>(1000+i);
  for(size_t s=0;s<tss.size();++s)for(size_t i=0;i<tss[s].size();++i)tss[s][i]=static_cast<DWORD>(2000+s*64+i);}
 bool read(){return ++gets!=fail_get;}
 HRESULT write(){++writes;return writes==fail_set||writes==fail_set_again?D3DERR_INVALIDCALL:S_OK;}
 static size_t matrix_index(D3DTRANSFORMSTATETYPE k){return k==D3DTS_WORLD?0:k==D3DTS_VIEW?1:2;}
 HRESULT STDMETHODCALLTYPE GetRenderState(D3DRENDERSTATETYPE k,DWORD* v) override {if(!read())return E_FAIL;*v=rs[k];return S_OK;}
 HRESULT STDMETHODCALLTYPE SetRenderState(D3DRENDERSTATETYPE k,DWORD v) override {const HRESULT hr=write();if(SUCCEEDED(hr)||mutate_on_failure)rs[k]=v;return hr;}
 HRESULT STDMETHODCALLTYPE GetTextureStageState(DWORD s,D3DTEXTURESTAGESTATETYPE k,DWORD* v) override {if(!read())return E_FAIL;*v=tss[s][k];return S_OK;}
 HRESULT STDMETHODCALLTYPE SetTextureStageState(DWORD s,D3DTEXTURESTAGESTATETYPE k,DWORD v) override {const HRESULT hr=write();if(SUCCEEDED(hr)||mutate_on_failure)tss[s][k]=v;return hr;}
 HRESULT STDMETHODCALLTYPE GetTransform(D3DTRANSFORMSTATETYPE k,D3DMATRIX* v) override {if(!read())return E_FAIL;*v=matrices[matrix_index(k)];return S_OK;}
 HRESULT STDMETHODCALLTYPE SetTransform(D3DTRANSFORMSTATETYPE k,const D3DMATRIX* v) override {const HRESULT hr=write();if(SUCCEEDED(hr)||mutate_on_failure)matrices[matrix_index(k)]=*v;return hr;}
 HRESULT STDMETHODCALLTYPE GetVertexShader(DWORD* v) override {if(!read())return E_FAIL;*v=vertex_shader;return S_OK;}
 HRESULT STDMETHODCALLTYPE SetVertexShader(DWORD v) override {const HRESULT hr=write();if(SUCCEEDED(hr)||mutate_on_failure)vertex_shader=v;return hr;}
 HRESULT STDMETHODCALLTYPE GetPixelShader(DWORD* v) override {if(!read())return E_FAIL;*v=pixel_shader;return S_OK;}
 HRESULT STDMETHODCALLTYPE SetPixelShader(DWORD v) override {const HRESULT hr=write();if(SUCCEEDED(hr)||mutate_on_failure)pixel_shader=v;return hr;}
 HRESULT STDMETHODCALLTYPE GetTexture(DWORD s,IDirect3DBaseTexture8** v) override {CHECK(s==0);if(!read())return E_FAIL;*v=texture;if(texture)texture->AddRef();return S_OK;}
 HRESULT STDMETHODCALLTYPE SetTexture(DWORD s,IDirect3DBaseTexture8* v) override {CHECK(s==0);const HRESULT hr=write();if(SUCCEEDED(hr)||mutate_on_failure){if(v)v->AddRef();if(texture)texture->Release();texture=v;}return hr;}
 HRESULT STDMETHODCALLTYPE GetStreamSource(UINT s,IDirect3DVertexBuffer8** v,UINT* n) override {CHECK(s==0);if(!read())return E_FAIL;*v=stream;*n=stride;if(stream)stream->AddRef();return S_OK;}
 HRESULT STDMETHODCALLTYPE SetStreamSource(UINT s,IDirect3DVertexBuffer8* v,UINT n) override {CHECK(s==0);const HRESULT hr=write();if(SUCCEEDED(hr)||mutate_on_failure){if(v)v->AddRef();if(stream)stream->Release();stream=v;stride=n;}return hr;}
 HRESULT STDMETHODCALLTYPE DrawPrimitiveUP(D3DPRIMITIVETYPE p,UINT n,const void*,UINT bytes) override {
  CHECK(p==D3DPT_TRIANGLELIST&&n==1&&bytes==24);++draws;
  if(stream)stream->Release();stream=nullptr;stride=0;return draw_hresult;
 }
 HRESULT STDMETHODCALLTYPE SetRenderTarget(IDirect3DSurface8*,IDirect3DSurface8*) override {++rt_writes;return S_OK;}
 D3DVIEWPORT8 viewport{0,0,640,480,0.f,1.f};
 int fail_viewport_get=0,fail_viewport_set=0; // n-th viewport call fails (and still mutates on a failed set).
 int viewport_gets=0;
 HRESULT STDMETHODCALLTYPE GetViewport(D3DVIEWPORT8* v) override {if(++viewport_gets==fail_viewport_get)return E_FAIL;*v=viewport;return S_OK;}
 HRESULT STDMETHODCALLTYPE SetViewport(const D3DVIEWPORT8* v) override {++viewport_writes;if(v&&(viewport_writes!=fail_viewport_set||mutate_on_failure))viewport=*v;
  return viewport_writes==fail_viewport_set?D3DERR_INVALIDCALL:S_OK;}
 HRESULT STDMETHODCALLTYPE SetIndices(IDirect3DIndexBuffer8*,UINT) override {++index_writes;return S_OK;}
 HRESULT STDMETHODCALLTYPE BeginStateBlock() override {++state_blocks;return S_OK;}
};
struct Initial {
 std::array<DWORD,256> rs;
 std::array<std::array<DWORD,64>,2> tss;
 std::array<D3DMATRIX,3> matrices;
 DWORD vs,ps;IDirect3DBaseTexture8* texture;IDirect3DVertexBuffer8* stream;UINT stride;
 explicit Initial(const Native& n):rs(n.rs),tss(n.tss),matrices(n.matrices),vs(n.vertex_shader),ps(n.pixel_shader),texture(n.texture),stream(n.stream),stride(n.stride){}
 bool matches(const Native& n)const{return rs==n.rs&&tss==n.tss&&std::memcmp(matrices.data(),n.matrices.data(),sizeof(matrices))==0&&
  vs==n.vertex_shader&&ps==n.pixel_shader&&texture==n.texture&&stream==n.stream&&stride==n.stride;}
};
struct Record{uint32_t slot;Args args;HRESULT hr;};
void default_and_capture(){
 Native n;CourseObjectTransaction t;CHECK(!t.captured()&&!t.has_pending());
 auto writer=[](uint32_t,const Args&,HRESULT)noexcept{};
 CHECK(FAILED(t.apply(n,&n.replacement,matrix(7),matrix(8),writer)));CHECK(n.gets==0&&n.writes==0);
 CHECK(SUCCEEDED(t.restore(n,writer)));CHECK(n.writes==0);
 for(int failure=1;failure<=34;++failure){
  Native x;Initial initial(x);CourseObjectTransaction tx;x.fail_get=failure;
  CHECK(FAILED(tx.capture(x)));CHECK(x.writes==0&&!tx.captured()&&!tx.has_pending());
  CHECK(initial.matches(x)&&x.original_texture.refs==1&&x.original_buffer.refs==1);
 }
 CHECK(SUCCEEDED(t.capture(n)));CHECK(n.gets==34&&n.writes==0);
 CHECK(n.original_texture.refs==2&&n.original_buffer.refs==2);
 t.release();CHECK(n.original_texture.refs==1&&n.original_buffer.refs==1&&!t.captured());
}
void preview_draw_restore(){
 Native n;Initial initial(n);CourseObjectTransaction t;std::vector<Record> log;
 auto writer=[&](uint32_t slot,const Args& args,HRESULT hr)noexcept{log.push_back({slot,args,hr});};
 CHECK(SUCCEEDED(t.capture(n)));CHECK(SUCCEEDED(t.apply(n,&n.replacement,matrix(7),matrix(8),writer)));
 CHECK(n.gets==34&&n.writes==33&&t.has_pending());
 CHECK(n.vertex_shader==0x142&&n.pixel_shader==0&&n.texture==&n.replacement);
 CHECK(n.rs[D3DRS_ZENABLE]==D3DZB_TRUE&&n.rs[D3DRS_ZWRITEENABLE]==TRUE&&n.rs[D3DRS_ZFUNC]==D3DCMP_LESSEQUAL);
 CHECK(n.rs[D3DRS_ALPHATESTENABLE]==FALSE&&n.rs[D3DRS_ALPHABLENDENABLE]==TRUE);
 CHECK(n.rs[D3DRS_SRCBLEND]==D3DBLEND_SRCALPHA&&n.rs[D3DRS_DESTBLEND]==D3DBLEND_INVSRCALPHA);
 CHECK(n.rs[D3DRS_CULLMODE]==D3DCULL_NONE&&n.rs[D3DRS_LIGHTING]==FALSE&&n.rs[D3DRS_FOGENABLE]==FALSE);
 CHECK(n.rs[D3DRS_STENCILENABLE]==FALSE&&n.rs[D3DRS_CLIPPLANEENABLE]==0&&n.rs[D3DRS_COLORWRITEENABLE]==15);
 CHECK(n.tss[0][D3DTSS_ALPHAOP]==D3DTOP_MODULATE&&n.tss[0][D3DTSS_ALPHAARG1]==D3DTA_TEXTURE&&n.tss[0][D3DTSS_ALPHAARG2]==D3DTA_DIFFUSE);
 CHECK(n.tss[0][D3DTSS_ADDRESSU]==D3DTADDRESS_WRAP&&n.tss[0][D3DTSS_ADDRESSV]==D3DTADDRESS_WRAP);
 CHECK(n.tss[1][D3DTSS_COLOROP]==D3DTOP_DISABLE&&n.tss[1][D3DTSS_ALPHAOP]==initial.tss[1][D3DTSS_ALPHAOP]);
 t.mark_up_stream_changed();const HRESULT draw=n.DrawPrimitiveUP(D3DPT_TRIANGLELIST,1,nullptr,24);
 CHECK(draw==n.draw_hresult&&n.draws==1&&n.stream==nullptr);
 CHECK(SUCCEEDED(t.restore(n,writer)));CHECK(initial.matches(n)&&!t.has_pending()&&!t.captured());
 CHECK(n.original_texture.refs==1&&n.replacement.refs==1&&n.original_buffer.refs==1);
 CHECK(n.rt_writes==0&&n.viewport_writes==0&&n.index_writes==0&&n.state_blocks==0);
 CHECK(log.size()==67); // 33 setters + all 34 changed/implicit slots restored.
 CHECK(log[33].slot==83); // UP stream restored first.
}
void partial_apply(){
 auto writer=[](uint32_t,const Args&,HRESULT)noexcept{};
 for(int failure=1;failure<=33;++failure){
  Native n;Initial initial(n);CourseObjectTransaction t;n.fail_set=failure;
  CHECK(SUCCEEDED(t.capture(n)));CHECK(t.apply(n,&n.replacement,matrix(7),matrix(8),writer)==D3DERR_INVALIDCALL);
  CHECK(initial.matches(n)&&!t.has_pending()&&!t.captured());
  CHECK(n.original_texture.refs==1&&n.replacement.refs==1&&n.original_buffer.refs==1&&n.draws==0);
 }
}
void restore_retry(){
 auto writer=[](uint32_t,const Args&,HRESULT)noexcept{};
 for(int failure=1;failure<=34;++failure){
  Native n;Initial initial(n);CourseObjectTransaction t;
  CHECK(SUCCEEDED(t.capture(n)));CHECK(SUCCEEDED(t.apply(n,&n.replacement,matrix(7),matrix(8),writer)));
  t.mark_up_stream_changed();CHECK(n.DrawPrimitiveUP(D3DPT_TRIANGLELIST,1,nullptr,24)==n.draw_hresult);
  n.fail_set=n.writes+failure;CHECK(t.restore(n,writer)==D3DERR_INVALIDCALL);CHECK(t.has_pending()&&t.captured());
  const int reads=n.gets;CHECK(t.capture(n)==D3DERR_INVALIDCALL);CHECK(n.gets==reads);
  CHECK(n.original_texture.refs>=1&&n.original_buffer.refs>=1);
  n.fail_set=0;CHECK(SUCCEEDED(t.restore(n,writer)));CHECK(initial.matches(n)&&!t.has_pending());
  CHECK(n.original_texture.refs==1&&n.replacement.refs==1&&n.original_buffer.refs==1&&n.draws==1);
 }
 Native n;Initial initial(n);CourseObjectTransaction t;
 n.fail_set=33;n.fail_set_again=34; // Texture apply and its rollback both mutate then fail.
 CHECK(SUCCEEDED(t.capture(n)));
 CHECK(t.apply(n,&n.replacement,matrix(7),matrix(8),writer)==D3DERR_INVALIDCALL);
 CHECK(t.has_pending()&&t.captured()&&t.pending_mask()==(uint64_t(1)<<32)&&n.original_texture.refs>=1);
 const int reads=n.gets,writes=n.writes;
 CHECK(FAILED(t.apply(n,&n.replacement,matrix(7),matrix(8),writer)));
 CHECK(n.gets==reads&&n.writes==writes); // No overlapping transaction while repair is pending.
 n.fail_set=n.fail_set_again=0;
 CHECK(SUCCEEDED(t.restore(n,writer))&&initial.matches(n));
 CHECK(n.original_texture.refs==1&&n.replacement.refs==1&&n.original_buffer.refs==1);
}
void invalid_and_empty_binding(){
 auto writer=[](uint32_t,const Args&,HRESULT)noexcept{};
 Native n;Initial initial(n);CourseObjectTransaction t;CHECK(SUCCEEDED(t.capture(n)));
 D3DMATRIX bad=matrix(7);bad._12=std::numeric_limits<float>::quiet_NaN();
 CHECK(FAILED(t.apply(n,&n.replacement,bad,matrix(8),writer)));CHECK(n.writes==0&&initial.matches(n));
 CHECK(FAILED(t.apply(n,nullptr,matrix(7),matrix(8),writer)));CHECK(n.writes==0);
 t.release();CHECK(n.original_texture.refs==1&&n.original_buffer.refs==1);
 Native empty;empty.texture->Release();empty.texture=nullptr;empty.stream->Release();empty.stream=nullptr;empty.stride=0;
 Initial empty_initial(empty);CourseObjectTransaction tx;CHECK(SUCCEEDED(tx.capture(empty)));
 CHECK(SUCCEEDED(tx.apply(empty,&empty.replacement,matrix(7),matrix(8),writer)));
 tx.mark_up_stream_changed();CHECK(empty.DrawPrimitiveUP(D3DPT_TRIANGLELIST,1,nullptr,24)==empty.draw_hresult);
 CHECK(SUCCEEDED(tx.restore(empty,writer)));CHECK(empty_initial.matches(empty)&&empty.replacement.refs==1);
 Native equal;
 for(const auto& op:kCourseObjectStateOps){
  if(op.kind==CourseObjectStateKind::Render)equal.rs[op.key]=op.preview;
  if(op.kind==CourseObjectStateKind::Stage)equal.tss[op.stage][op.key]=op.preview;
 }
 equal.vertex_shader=0x142;equal.pixel_shader=0;
 equal.matrices={matrix(1),matrix(7),matrix(8)};
 Initial equal_initial(equal);CourseObjectTransaction same;
 CHECK(SUCCEEDED(same.capture(equal)));
 CHECK(SUCCEEDED(same.apply(equal,equal.texture,matrix(7),matrix(8),writer)));
 CHECK(!same.has_pending()&&equal.writes==0); // Preserve captured stream ownership until UP.
 same.mark_up_stream_changed();CHECK(equal.DrawPrimitiveUP(D3DPT_TRIANGLELIST,1,nullptr,24)==equal.draw_hresult);
 CHECK(SUCCEEDED(same.restore(equal,writer))&&equal_initial.matches(equal)&&equal.writes==1);
}
void grass_material_policy(){
 auto writer=[](uint32_t,const Args&,HRESULT)noexcept{};
 const CourseObjectMaterialState grass{FALSE,D3DTADDRESS_CLAMP,D3DTADDRESS_CLAMP};
 Native n;Initial original(n);CourseObjectTransaction t;CHECK(SUCCEEDED(t.capture(n)));
 CHECK(SUCCEEDED(t.apply(n,&n.replacement,matrix(7),matrix(8),writer,grass)));
 CHECK(n.rs[D3DRS_ZWRITEENABLE]==FALSE&&n.rs[D3DRS_ALPHATESTENABLE]==FALSE&&n.rs[D3DRS_ALPHABLENDENABLE]==TRUE);
 CHECK(n.tss[0][D3DTSS_ADDRESSU]==D3DTADDRESS_CLAMP&&n.tss[0][D3DTSS_ADDRESSV]==D3DTADDRESS_CLAMP);
 CHECK(SUCCEEDED(t.restore(n,writer))&&original.matches(n));
 for(int failure=1;failure<=33;++failure){
  Native partial;Initial before(partial);CourseObjectTransaction tx;partial.fail_set=failure;
  CHECK(SUCCEEDED(tx.capture(partial)));
  CHECK(tx.apply(partial,&partial.replacement,matrix(7),matrix(8),writer,grass)==D3DERR_INVALIDCALL);
  CHECK(before.matches(partial)&&!tx.has_pending());
 }
 Native invalid;Initial before(invalid);CourseObjectTransaction tx;CHECK(SUCCEEDED(tx.capture(invalid)));
 CHECK(FAILED(tx.apply(invalid,&invalid.replacement,matrix(7),matrix(8),writer,CourseObjectMaterialState{2,1,1})));
 CHECK(FAILED(tx.apply(invalid,&invalid.replacement,matrix(7),matrix(8),writer,CourseObjectMaterialState{0,99,1})));
 CHECK(invalid.writes==0&&before.matches(invalid));
}
}
bool same_viewport(const D3DVIEWPORT8& a,const D3DVIEWPORT8& b){return !std::memcmp(&a,&b,sizeof(a));}
// SPLIT-GRASS1: split passes draw into their half; the UI viewport is always restored and reported as slot 40.
void split_viewport_transaction(){
 const CourseObjectMaterialState grass{FALSE,D3DTADDRESS_CLAMP,D3DTADDRESS_CLAMP};
 const D3DVIEWPORT8 ui{0,0,640,480,0.f,1.f},top{0,0,640,238,0.f,1.f},bottom{0,240,640,238,0.f,1.f};
 for(const auto& half:{top,bottom}){
  Native n;Initial initial(n);CourseObjectTransaction t;std::vector<Record> log;
  auto writer=[&](uint32_t slot,const Args& args,HRESULT hr)noexcept{
   if(slot==CourseObjectTransaction::kSetViewportSlot){D3DVIEWPORT8 seen{};std::memcpy(&seen,reinterpret_cast<const void*>(args.a[0]),sizeof(seen));
    CHECK(same_viewport(seen,n.viewport));} // The tracker reads the value synchronously, as set.
   log.push_back({slot,args,hr});};
  CHECK(FAILED(t.capture_viewport(n))); // Only after capture().
  CHECK(SUCCEEDED(t.capture(n))&&SUCCEEDED(t.capture_viewport(n))&&t.viewport_captured()&&!t.has_pending());
  CHECK(FAILED(t.capture_viewport(n))); // Once per transaction.
  CHECK(SUCCEEDED(t.apply_viewport(n,half,writer))&&t.viewport_pending()&&t.has_pending()&&same_viewport(n.viewport,half));
  CHECK(log.size()==1&&log[0].slot==40&&log[0].hr==S_OK);
  CHECK(FAILED(t.apply_viewport(n,half,writer))); // No second viewport apply while pending.
  CHECK(SUCCEEDED(t.apply(n,&n.replacement,matrix(1),matrix(8),writer,grass)));
  t.mark_up_stream_changed();CHECK(n.DrawPrimitiveUP(D3DPT_TRIANGLELIST,1,nullptr,24)==n.draw_hresult);
  CHECK(same_viewport(n.viewport,half)&&n.viewport_writes==1);
  CHECK(SUCCEEDED(t.restore(n,writer)));
  CHECK(initial.matches(n)&&same_viewport(n.viewport,ui)&&!t.has_pending()&&!t.captured()&&!t.viewport_captured());
  CHECK(n.viewport_writes==2&&log.back().slot==40); // Viewport restored last, after every fixed state.
  CHECK(n.original_texture.refs==1&&n.replacement.refs==1&&n.original_buffer.refs==1);
 }
 { // Same viewport: no setter and nothing pending.
  Native n;CourseObjectTransaction t;int writes=0;auto writer=[&](uint32_t,const Args&,HRESULT)noexcept{++writes;};
  CHECK(SUCCEEDED(t.capture(n))&&SUCCEEDED(t.capture_viewport(n))&&SUCCEEDED(t.apply_viewport(n,ui,writer)));
  CHECK(!t.has_pending()&&writes==0&&n.viewport_writes==0);t.release();
 }
 { // Invalid viewport or failed GetViewport: nothing written.
  Native n;CourseObjectTransaction t;auto writer=[](uint32_t,const Args&,HRESULT)noexcept{};
  CHECK(SUCCEEDED(t.capture(n))&&SUCCEEDED(t.capture_viewport(n)));
  D3DVIEWPORT8 empty=top;empty.Width=0;CHECK(FAILED(t.apply_viewport(n,empty,writer)));
  D3DVIEWPORT8 nan=top;nan.MaxZ=std::numeric_limits<float>::quiet_NaN();CHECK(FAILED(t.apply_viewport(n,nan,writer)));
  CHECK(n.viewport_writes==0&&!t.has_pending());t.release();
  Native g;Initial gi(g);CourseObjectTransaction tg;g.fail_viewport_get=1;
  CHECK(SUCCEEDED(tg.capture(g))&&FAILED(tg.capture_viewport(g))&&!tg.viewport_captured());
  CHECK(FAILED(tg.apply_viewport(g,top,writer))&&g.viewport_writes==0&&gi.matches(g));tg.release();
 }
 { // Failed viewport setter mutates the slot: rolled back immediately.
  Native n;CourseObjectTransaction t;auto writer=[](uint32_t,const Args&,HRESULT)noexcept{};n.fail_viewport_set=1;
  CHECK(SUCCEEDED(t.capture(n))&&SUCCEEDED(t.capture_viewport(n)));
  CHECK(t.apply_viewport(n,top,writer)==D3DERR_INVALIDCALL);
  CHECK(same_viewport(n.viewport,ui)&&!t.has_pending()&&n.viewport_writes==2);
 }
 { // A failing fixed state after the viewport rolls back the viewport too.
  for(int failure=1;failure<=33;++failure){
   Native n;Initial initial(n);CourseObjectTransaction t;auto writer=[](uint32_t,const Args&,HRESULT)noexcept{};
   CHECK(SUCCEEDED(t.capture(n))&&SUCCEEDED(t.capture_viewport(n))&&SUCCEEDED(t.apply_viewport(n,bottom,writer)));
   n.fail_set=n.writes+failure;
   CHECK(t.apply(n,&n.replacement,matrix(1),matrix(8),writer,grass)==D3DERR_INVALIDCALL);
   CHECK(initial.matches(n)&&same_viewport(n.viewport,ui)&&!t.has_pending());
  }
 }
 { // Viewport restore fails: stays pending (repair later), no new transaction until it is restored.
  Native n;CourseObjectTransaction t;auto writer=[](uint32_t,const Args&,HRESULT)noexcept{};
  CHECK(SUCCEEDED(t.capture(n))&&SUCCEEDED(t.capture_viewport(n))&&SUCCEEDED(t.apply_viewport(n,top,writer)));
  CHECK(SUCCEEDED(t.apply(n,&n.replacement,matrix(1),matrix(8),writer,grass)));
  n.fail_viewport_set=2;n.mutate_on_failure=false;
  CHECK(t.restore(n,writer)==D3DERR_INVALIDCALL&&t.has_pending()&&t.viewport_pending()&&t.pending_mask()==0);
  CHECK(same_viewport(n.viewport,top));
  const int reads=n.gets;CHECK(t.capture(n)==D3DERR_INVALIDCALL&&n.gets==reads);
  CHECK(SUCCEEDED(t.restore(n,writer))&&same_viewport(n.viewport,ui)&&!t.has_pending());
 }
 { // The single-camera transaction never reads or writes the viewport.
  Native n;CourseObjectTransaction t;auto writer=[](uint32_t,const Args&,HRESULT)noexcept{};
  CHECK(SUCCEEDED(t.capture(n))&&SUCCEEDED(t.apply(n,&n.replacement,matrix(7),matrix(8),writer,grass)));
  t.mark_up_stream_changed();n.DrawPrimitiveUP(D3DPT_TRIANGLELIST,1,nullptr,24);
  CHECK(SUCCEEDED(t.restore(n,writer))&&n.viewport_gets==0&&n.viewport_writes==0);
 }
}
int main(){default_and_capture();preview_draw_restore();partial_apply();restore_retry();invalid_and_empty_binding();grass_material_policy();
 split_viewport_transaction();
 if(failures)std::cerr<<failures<<" failed checks\n";return failures?1:0;}
