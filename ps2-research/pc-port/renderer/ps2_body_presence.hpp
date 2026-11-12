#pragma once
// Current-frame successful PS2 submissions, independent of the last selected
// fleet child. Alpha lamps can arrive after opaque bodies of other participants.
// The immediately preceding frame is kept for body-scoped lamp sets: an opaque
// ON core may be queued before the same owner's body inside one frame.
#include <array>
#include <cstdint>
#include <cstring>
namespace gfx2::ps2port {
class Ps2BodyPresence {
 struct Entry {uintptr_t instance=0,packet=0,model=0;const char* family=nullptr;};
 std::array<Entry,64> entries_{},previous_{};unsigned size_=0,previous_size_=0;
 uint64_t device_=0,reset_=0,frame_=UINT64_MAX;
 void scope(uint64_t device,uint64_t reset,uint64_t frame)noexcept{
  if(device_!=device||reset_!=reset||frame_!=frame){
   const bool next=device_==device&&reset_==reset&&frame_!=UINT64_MAX&&frame==frame_+1;
   if(next){previous_=entries_;previous_size_=size_;}else previous_size_=0;
   device_=device;reset_=reset;frame_=frame;size_=0;
  }
 }
 static bool find(const std::array<Entry,64>& list,unsigned size,uintptr_t instance,uintptr_t packet,uintptr_t model,const char* family)noexcept{
  for(unsigned i=0;i<size;++i){const auto& e=list[i];if(e.instance==instance&&e.packet==packet&&e.model==model&&!std::strcmp(e.family,family))return true;}
  return false;
 }
public:
 void submitted(uint64_t device,uint64_t reset,uint64_t frame,uintptr_t instance,uintptr_t packet,uintptr_t model,const char* family)noexcept{
  scope(device,reset,frame);if(!instance||!packet||!model||!family)return;
  for(unsigned i=0;i<size_;++i)if(entries_[i].instance==instance&&entries_[i].packet==packet&&entries_[i].model==model){entries_[i].family=family;return;}
  if(size_<entries_.size())entries_[size_++]={instance,packet,model,family};
 }
 bool contains(uint64_t device,uint64_t reset,uint64_t frame,uintptr_t instance,uintptr_t packet,uintptr_t model,const char* family)noexcept{
  scope(device,reset,frame);if(!family)return false;
  return find(entries_,size_,instance,packet,model,family);
 }
 // This frame or the directly preceding one (same device and reset generation).
 bool recent(uint64_t device,uint64_t reset,uint64_t frame,uintptr_t instance,uintptr_t packet,uintptr_t model,const char* family)noexcept{
  scope(device,reset,frame);if(!family)return false;
  return find(entries_,size_,instance,packet,model,family)||find(previous_,previous_size_,instance,packet,model,family);
 }
};
inline thread_local Ps2BodyPresence ps2_body_presence;
}
