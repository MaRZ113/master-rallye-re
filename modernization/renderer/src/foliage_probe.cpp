#include "foliage_probe.hpp"
#include "provenance.hpp"
#include <algorithm>
#include <bcrypt.h>
#include <cfenv>
#include <cmath>
#include <sstream>
namespace gfx2 {
namespace {
struct FP {fenv_t saved;FP(){fegetenv(&saved);}~FP(){fesetenv(&saved);}};
std::string digest(const void* data,size_t bytes){
 BCRYPT_ALG_HANDLE a=nullptr;BCRYPT_HASH_HANDLE h=nullptr;std::string out;
 try {if(bytes>UINT32_MAX||BCryptOpenAlgorithmProvider(&a,BCRYPT_SHA256_ALGORITHM,nullptr,0)<0)throw 1;
  if(BCryptCreateHash(a,&h,nullptr,0,nullptr,0,0)<0||BCryptHashData(h,(PUCHAR)data,static_cast<ULONG>(bytes),0)<0)throw 1;
  unsigned char value[32];if(BCryptFinishHash(h,value,32,0)<0)throw 1;
  char b[3];for(auto c:value){sprintf_s(b,"%02x",c);out+=b;}
 }catch(...){out.clear();}if(h)BCryptDestroyHash(h);if(a)BCryptCloseAlgorithmProvider(a,0);return out;
}
template<class T>struct Ref {T* p=nullptr;~Ref(){if(p)p->Release();}};
template<class T>struct ReadLock {
 T* p;bool locked=false;HRESULT& result;FoliageBudget& budget;
 ~ReadLock(){close();}
 void close(){if(locked){locked=false;result=p->Unlock();if(FAILED(result))budget.disabled=true;}}
};
template<class T>void value(std::ostream& o,const Known<T>& v){if(v.known)o<<v.value;else o<<"null";}
}
bool FoliageBudget::take(uint64_t at,uint64_t count) noexcept {
 if(disabled)return false;if(frame!=at){frame=at;bytes=0;draws=0;}
 if(count>FOLIAGE_BYTE_LIMIT||draws>=FOLIAGE_PROBE_LIMIT||bytes>FOLIAGE_BYTE_LIMIT-count)return false;
 ++draws;bytes+=count;return true;
}
bool foliage_layout(DWORD fvf,UINT stride,UINT& diffuse_offset) noexcept {
 diffuse_offset=UINT32_MAX;
 // Known fixed-function XYZ layouts only; no RHW, skinning or shader handles.
 if(fvf!=0x102&&fvf!=0x112&&fvf!=0x142&&fvf!=0x152&&fvf!=0x242&&fvf!=0x252)return false;
 UINT size=12;if(fvf&D3DFVF_NORMAL)size+=12;
 if(fvf&D3DFVF_DIFFUSE){diffuse_offset=size;size+=4;}
 size+=8*((fvf&D3DFVF_TEXCOUNT_MASK)>>D3DFVF_TEXCOUNT_SHIFT);
 return stride==size;
}
std::string foliage_face_hash(const float* xyz9){
 FP fp;std::array<std::array<uint32_t,3>,3> points{};
 for(unsigned i=0;i<9;++i){float f=xyz9[i];if(!std::isfinite(f))return {};if(f==0.f)f=0.f;std::memcpy(&points[i/3][i%3],&f,4);}
 std::sort(points.begin(),points.end());return digest(points.data(),36);
}
FoliageEvidence probe_foliage(IDirect3DDevice8& native,const ResourceRegistry& resources,
 const Args& draw,uint64_t frame,FoliageBudget& budget) noexcept {
 FP fp;FoliageEvidence e;
 try {
  const auto& a=draw.a;
  if(a[0]!=D3DPT_TRIANGLELIST||!a[4]||a[4]>FOLIAGE_FACE_LIMIT||!a[2]||a[2]>2048){e.reason="unsupported_draw_or_size";return e;}
  if(!budget.take(frame,0)){e.reason="capture_budget_or_disabled";return e;}e.attempted=true;
  for(size_t i=0;i<12;++i){DWORD n=0;if(SUCCEEDED(native.GetRenderState(FOLIAGE_RS[i],&n)))e.native_rs[i].set(n);}
  for(DWORD s=0;s<2;++s)for(size_t i=0;i<8;++i){DWORD n=0;if(SUCCEEDED(native.GetTextureStageState(s,FOLIAGE_TSS[i],&n)))e.native_tss[s][i].set(n);}
  D3DMATRIX world{};if(SUCCEEDED(native.GetTransform(D3DTS_WORLD,&world)))e.native_world.set(world);
  D3DMATERIAL8 material{};if(SUCCEEDED(native.GetMaterial(&material)))e.native_material.set(material);
  Ref<IDirect3DBaseTexture8> texture;
  if(SUCCEEDED(native.GetTexture(0,&texture.p))&&texture.p){e.texture=reinterpret_cast<uintptr_t>(texture.p);e.texture_generation=resources.generation(e.texture);}
  UINT diffuse=0;
  if(FAILED(native.GetVertexShader(&e.fvf))){e.reason="native_fvf_unknown";return e;}
  Ref<IDirect3DVertexBuffer8> vb;Ref<IDirect3DIndexBuffer8> ib;
  if(FAILED(native.GetStreamSource(0,&vb.p,&e.stride))||!vb.p||FAILED(native.GetIndices(&ib.p,&e.base))||!ib.p){e.reason="native_buffers_unknown";return e;}
  e.vertex_buffer=reinterpret_cast<uintptr_t>(vb.p);e.index_buffer=reinterpret_cast<uintptr_t>(ib.p);
  e.vertex_generation=resources.generation(e.vertex_buffer);e.index_generation=resources.generation(e.index_buffer);
  if(!e.vertex_generation||!e.index_generation){e.reason="missing_creation_identity";return e;}
  if(!foliage_layout(e.fvf,e.stride,diffuse)){e.reason="unsupported_layout";return e;}
  D3DVERTEXBUFFER_DESC vd{};D3DINDEXBUFFER_DESC id{};
  if(FAILED(vb.p->GetDesc(&vd))||FAILED(ib.p->GetDesc(&id))){e.reason="buffer_descriptor_unknown";return e;}
  e.vertex_usage=vd.Usage;e.index_usage=id.Usage;e.vertex_pool=vd.Pool;e.index_pool=id.Pool;e.index_format=id.Format;
  // Never read GPU-only, WRITEONLY or mutable dynamic allocations. No fallback locks.
  if((vd.Usage|id.Usage)&(D3DUSAGE_WRITEONLY|D3DUSAGE_DYNAMIC)||
     (vd.Pool!=D3DPOOL_MANAGED&&vd.Pool!=D3DPOOL_SYSTEMMEM)||
     (id.Pool!=D3DPOOL_MANAGED&&id.Pool!=D3DPOOL_SYSTEMMEM)){e.reason="buffer_not_safe_for_readonly_probe";return e;}
  unsigned index_size=id.Format==D3DFMT_INDEX16?2:id.Format==D3DFMT_INDEX32?4:0;
  if(!index_size){e.reason="unsupported_index_format";return e;}
  uint64_t vo=(uint64_t(e.base)+a[1])*e.stride,vs=a[2]*e.stride,io=uint64_t(a[3])*index_size,is=a[4]*3*index_size;
  if(vo>vd.Size||vs>vd.Size-vo||io>id.Size||is>id.Size-io){e.reason="draw_outside_buffer";return e;}
  if(vs+is>FOLIAGE_BYTE_LIMIT-budget.bytes){e.reason="capture_byte_budget";return e;}budget.bytes+=vs+is;
  auto read_content=[&](){
  BYTE* vp=nullptr;BYTE* ip=nullptr;ReadLock<IDirect3DVertexBuffer8> vl{vb.p,false,e.vertex_unlock,budget};ReadLock<IDirect3DIndexBuffer8> il{ib.p,false,e.index_unlock,budget};
  e.vertex_lock.set(static_cast<uint32_t>(vb.p->Lock(static_cast<UINT>(vo),static_cast<UINT>(vs),&vp,D3DLOCK_READONLY)));
  if(FAILED(static_cast<HRESULT>(e.vertex_lock.value))){e.reason="vertex_readonly_lock_failed";return;}vl.locked=true;
  e.index_lock.set(static_cast<uint32_t>(ib.p->Lock(static_cast<UINT>(io),static_cast<UINT>(is),&ip,D3DLOCK_READONLY)));
  if(FAILED(static_cast<HRESULT>(e.index_lock.value))){e.reason="index_readonly_lock_failed";return;}il.locked=true;
  std::vector<unsigned char> vertices(static_cast<size_t>(vs)),indices(static_cast<size_t>(is));
  if(!vp||!ip||!safe_copy(vertices.data(),vp,vertices.size())||!safe_copy(indices.data(),ip,indices.size())){e.reason="buffer_read_failed";return;}
  il.close();vl.close();if(FAILED(e.index_unlock)||FAILED(e.vertex_unlock))return;
  std::string all;DWORD amin=255,amax=0;
  for(size_t face=0;face<a[4];++face){float xyz[9]{};
   for(unsigned k=0;k<3;++k){uint32_t ix=0;std::memcpy(&ix,indices.data()+(face*3+k)*index_size,index_size);
    if(ix<a[1]||uint64_t(ix)-a[1]>=a[2]){e.reason="index_outside_declared_draw";e.face_hashes.clear();return;}
    size_t off=static_cast<size_t>((uint64_t(ix)-a[1])*e.stride);std::memcpy(xyz+3*k,vertices.data()+off,12);
    if(diffuse!=UINT32_MAX){DWORD color=0;std::memcpy(&color,vertices.data()+off+diffuse,4);DWORD alpha=color>>24;amin=std::min(amin,alpha);amax=std::max(amax,alpha);}
   }
   auto hash=foliage_face_hash(xyz);if(hash.empty()){e.reason="nonfinite_geometry_or_hash_failed";e.face_hashes.clear();return;}e.face_hashes.push_back(hash);
  }
  std::sort(e.face_hashes.begin(),e.face_hashes.end());for(const auto& hash:e.face_hashes)all+=hash;
  e.geometry_sha=digest(all.data(),all.size());if(e.geometry_sha.empty()){e.reason="hash_failed";e.face_hashes.clear();return;}
  if(diffuse!=UINT32_MAX){e.diffuse_alpha_min.set(amin);e.diffuse_alpha_max.set(amax);}e.reason="content_captured_identity_pending";
  };read_content();
  if(FAILED(e.index_unlock)||FAILED(e.vertex_unlock)){e.reason="unlock_failed_probe_disabled";e.geometry_sha.clear();e.face_hashes.clear();}
 }catch(...){e.reason="probe_exception_stock_forwarding";e.geometry_sha.clear();e.face_hashes.clear();}
 return e;
}
std::string foliage_json(const FoliageEvidence& e){
 std::ostringstream o;o<<"{\"schema\":\"foliage-probe-v1\",\"identity\":\"UNPROVEN\",\"override_applied\":false,\"attempted\":"<<(e.attempted?"true":"false")<<",\"reason\":"<<quote(e.reason)<<",\"geometry_multiset_sha256\":"<<quote(e.geometry_sha)<<",\"face_hashes\":[";
 for(size_t i=0;i<e.face_hashes.size();++i){if(i)o<<',';o<<quote(e.face_hashes[i]);}
 o<<"],\"vertex_buffer\":"<<e.vertex_buffer<<",\"vertex_generation\":"<<e.vertex_generation<<",\"index_buffer\":"<<e.index_buffer<<",\"index_generation\":"<<e.index_generation<<",\"texture0\":"<<e.texture<<",\"texture_generation\":"<<e.texture_generation<<",\"fvf\":"<<e.fvf<<",\"stride\":"<<e.stride<<",\"base_vertex\":"<<e.base<<",\"vertex_usage\":"<<e.vertex_usage<<",\"index_usage\":"<<e.index_usage<<",\"vertex_pool\":"<<e.vertex_pool<<",\"index_pool\":"<<e.index_pool<<",\"index_format\":"<<e.index_format<<",\"native_rs\":{";
 for(size_t i=0;i<12;++i){if(i)o<<',';o<<quote(std::to_string(FOLIAGE_RS[i]))<<':';value(o,e.native_rs[i]);}
 o<<"},\"native_tss\":[";for(size_t s=0;s<2;++s){if(s)o<<',';o<<'{';for(size_t i=0;i<8;++i){if(i)o<<',';o<<quote(std::to_string(FOLIAGE_TSS[i]))<<':';value(o,e.native_tss[s][i]);}o<<'}';}
 o<<"],\"native_world_bits\": [";
 if(e.native_world.known){uint32_t words[16];std::memcpy(words,&e.native_world.value,64);for(unsigned i=0;i<16;++i){if(i)o<<',';o<<words[i];}}
 o<<"],\"native_material_diffuse_alpha\":";if(e.native_material.known&&std::isfinite(e.native_material.value.Diffuse.a))o<<e.native_material.value.Diffuse.a;else o<<"null";
 o<<",\"vertex_diffuse_alpha_min\":";value(o,e.diffuse_alpha_min);o<<",\"vertex_diffuse_alpha_max\":";value(o,e.diffuse_alpha_max);
 o<<",\"vertex_lock_hresult\":";value(o,e.vertex_lock);o<<",\"index_lock_hresult\":";value(o,e.index_lock);
 o<<",\"vertex_unlock_hresult\":"<<static_cast<uint32_t>(e.vertex_unlock)<<",\"index_unlock_hresult\":"<<static_cast<uint32_t>(e.index_unlock)<<'}';return o.str();
}
}
