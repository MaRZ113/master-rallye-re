#include "state_tracker.hpp"
namespace gfx2 {
bool safe_copy(void* dst,const void* src,size_t n) noexcept {
 __try {std::memcpy(dst,src,n);return true;} __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
void Shadow::invalidate() noexcept { *this=Shadow{}; }
Snapshot Shadow::snapshot() const noexcept {
 Snapshot s=bindings;
 for(size_t i=0;i<24;++i)s.rs[i]=rs[RS_KEYS[i]];
 for(size_t i=0;i<5;++i)s.matrices[i]=matrices[MATRIX_KEYS[i]];
 for(size_t i=0;i<8;++i)for(size_t j=0;j<32;++j)s.tss[i][j]=tss[i][j+1];
 return s;
}
void Shadow::update(uint32_t slot,const Args& args,uint32_t result) noexcept {
 const auto& a=args.a;
 if(static_cast<int32_t>(result)<0)return;
 if(slot==14 || slot==54) {invalidate();return;}
 if(slot==52){invalidate();recording=true;return;}
 if(slot==53){invalidate();return;}
 if(recording)return; // Never report recorded setters as observed live state.
 switch(slot){
 case 37: if(a[0]<512)matrices[a[0]].read(reinterpret_cast<const D3DMATRIX*>(a[1]));break;
 case 38: if(a[0]<512)matrices[a[0]].read(reinterpret_cast<const D3DMATRIX*>(a[1]));break;
 case 39: if(a[0]<512)matrices[a[0]].known=false;break;
 case 40: case 41: bindings.viewport.read(reinterpret_cast<const D3DVIEWPORT8*>(a[0]));break;
 case 50: if(a[0]<256)rs[a[0]].set(static_cast<uint32_t>(a[1]));break;
 case 51: if(a[0]<256)rs[a[0]].read(reinterpret_cast<const uint32_t*>(a[1]));break;
 case 61: if(a[0]<8)bindings.textures[a[0]].set(a[1]);break;
 case 60: if(a[0]<8)bindings.textures[a[0]].read(reinterpret_cast<const uintptr_t*>(a[1]));break;
 case 63: if(a[0]<8&&a[1]<64)tss[a[0]][a[1]].set(static_cast<uint32_t>(a[2]));break;
 case 62: if(a[0]<8&&a[1]<64)tss[a[0]][a[1]].read(reinterpret_cast<const uint32_t*>(a[2]));break;
 case 76:bindings.vertex_shader.set(static_cast<uint32_t>(a[0]));break;
 case 77:bindings.vertex_shader.read(reinterpret_cast<const uint32_t*>(a[0]));break;
 case 88:bindings.pixel_shader.set(static_cast<uint32_t>(a[0]));break;
 case 89:bindings.pixel_shader.read(reinterpret_cast<const uint32_t*>(a[0]));break;
 case 83:if(a[0]<16)bindings.streams[a[0]].set({a[1],static_cast<uint32_t>(a[2])});break;
 case 84:if(a[0]<16){uintptr_t p;uint32_t n;bindings.streams[a[0]].known=false;if(safe_copy(&p,(void*)a[1],4)&&safe_copy(&n,(void*)a[2],4))bindings.streams[a[0]].set({p,n});}break;
 case 85:bindings.indices.set({a[0],static_cast<uint32_t>(a[1])});break;
 case 86:{uintptr_t p;uint32_t n;bindings.indices.known=false;if(safe_copy(&p,(void*)a[0],4)&&safe_copy(&n,(void*)a[1],4))bindings.indices.set({p,n});}break;
 case 78:if(bindings.vertex_shader.known&&bindings.vertex_shader.value==a[0])bindings.vertex_shader.known=false;break;
 case 90:if(bindings.pixel_shader.known&&bindings.pixel_shader.value==a[0])bindings.pixel_shader.known=false;break;
 case 31:bindings.target.set(a[0]);bindings.depth.set(a[1]);bindings.viewport.known=false;break;
 case 32:bindings.target.read(reinterpret_cast<const uintptr_t*>(a[0]));break;
 case 33:bindings.depth.read(reinterpret_cast<const uintptr_t*>(a[0]));break;
 case 72:bindings.streams[0].set({0,0});break;
 case 73:bindings.streams[0].set({0,0});bindings.indices.set({0,0});break;
 }
}
Resource ResourceRegistry::add(uintptr_t p,uint32_t method,const Args& args,uintptr_t creation_caller){
 Resource r{};r.serial=++next_serial;r.method=method;r.creation_caller=creation_caller;r.args=args;
 int index=method==20?5:method==21?6:method==22?4:(method==23||method==24)?3:-1;
 if(index>=0)r.pool.set(static_cast<uint32_t>(args.a[index]));
 else if(method==27)r.pool.set(D3DPOOL_SYSTEMMEM); // CreateImageSurface is system memory.
 r.reset_survivor=r.pool.known&&(r.pool.value==D3DPOOL_MANAGED||r.pool.value==D3DPOOL_SYSTEMMEM||r.pool.value==D3DPOOL_SCRATCH);
 if(items.size()>=8192 && items.find(p)==items.end())items.clear();
 items[p]=r;return r;
}
size_t ResourceRegistry::successful_reset() noexcept {
 size_t removed=0;for(auto it=items.begin();it!=items.end();)if(!it->second.reset_survivor){it=items.erase(it);++removed;}else ++it;return removed;
}
uint64_t ResourceRegistry::generation(uintptr_t p) const noexcept {
 auto it=items.find(p);return it==items.end()?0:it->second.serial;
}
}
