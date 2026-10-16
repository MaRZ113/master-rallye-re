#pragma once
#include <array>
#include <cstdint>
namespace gfx2::ps2port {
struct CarQueueStats{uint32_t missing=0,duplicate=0,subindex=0,entries=0;};
// Original562810 rebuilds current44/48 from TWO contiguous24-byte submission
// vectors. Preflight their union before opaque dispatch; opaque end is cleared
// before alpha dispatch. Current sorted pointer-vector is not the full cohort.
template<class Read> bool car_queue_cohort(uintptr_t stack,uintptr_t instance,const uintptr_t* meshes,unsigned count,Read read,CarQueueStats* stats=nullptr){
 if(stats)*stats={};if(!count||count>30)return false;uint32_t manager=0;if(!read(stack+0x28,manager)||manager<0x10000||(manager&3))return false;
 std::array<unsigned,30> hits{};unsigned total=0;bool subindices=true;
 for(unsigned offset:{0x24u,0x34u}){uint32_t begin=0,end=0;if(!read(manager+offset,begin)||!read(manager+offset+4,end))return false;if(!begin&&!end)continue;if(begin<0x10000||(begin&3)||(end&3)||end<begin||(end-begin)%24||(end-begin)/24>4096||total+(end-begin)/24>4096)return false;total+=(end-begin)/24;
  for(uintptr_t record=begin;record<end;record+=24){uint32_t owner=0,mesh=0,sub=0;if(!read(record,owner)||!read(record+4,mesh))return false;for(unsigned i=0;i<count;++i)if(mesh==meshes[i]&&owner==instance){if(!read(record+8,sub))return false;++hits[i];if(sub)subindices=false;if(stats){++stats->entries;if(sub)stats->subindex|=1u<<i;if(hits[i]>1)stats->duplicate|=1u<<i;}}}
 }
 bool complete=subindices;for(unsigned i=0;i<count;++i)if(hits[i]!=1){complete=false;if(stats&&hits[i]==0)stats->missing|=1u<<i;}return complete;
}
}
