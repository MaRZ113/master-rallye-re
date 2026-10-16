#pragma once
#include <array>
#include <cstdint>
namespace gfx2::ps2port {
struct RaceDescriptors {uintptr_t vertex=0,index=0;std::array<uint32_t,6> vd{};std::array<uint32_t,5> id{};};
// Original retail 00576970 / 00568660 / 00568AB0, guarded allocator table bounds.
// Deliberately excludes multi-material leaves and pre-emitter callbacks.
template<class Read> bool race_descriptors(uintptr_t base,uintptr_t leaf,Read read,RaceDescriptors& out){
 auto ptr=[&](uintptr_t at,uintptr_t& value){uint32_t v=0;if(!read(at,v)||v<0x10000||v>0x7ffffffc||(v&3))return false;value=v;return true;};
 auto lookup=[&](uintptr_t manager,unsigned offset,uint32_t handle,uintptr_t& result){uintptr_t table=0,begin=0;uint32_t end=0;if(!ptr(manager+offset,table)||!ptr(table+8,begin)||!read(table+12,end)||end<begin||end>0x7ffffffc||(end-begin)%12||(end-begin)/12>1048576||handle>=(end-begin)/12)return false;return ptr(begin+uintptr_t(handle)*12,result);};
 uintptr_t materials=0,begin=0,handles=0,global=0,manager=0;uint32_t end=0,callback=0,vhandle=0,ihandle=0;
 if(!ptr(leaf+0x38,materials)||!ptr(materials+4,begin)||!read(materials+8,end)||end!=begin+4||!read(leaf+0x44,callback)||callback||!ptr(leaf+0x18,handles)||!read(handles,vhandle)||!read(leaf+0x24,ihandle)||!ptr(base+0x2f9cf0,global)||!ptr(global+0x28,manager)||!lookup(manager,0x28,vhandle,out.vertex)||!lookup(manager,0x2c,ihandle,out.index))return false;
 for(unsigned i=0;i<6;++i)if(!read(out.vertex+i*4,out.vd[i]))return false;
 for(unsigned i=0;i<5;++i)if(!read(out.index+i*4,out.id[i]))return false;
 return true;
}
}
