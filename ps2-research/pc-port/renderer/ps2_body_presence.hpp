#pragma once
// Current-frame successful PS2 submissions, independent of the last selected
// fleet child. Alpha lamps can arrive after opaque bodies of other participants.
#include <array>
#include <cstdint>
#include <cstring>
namespace gfx2::ps2port {
class Ps2BodyPresence {
 struct Entry {uintptr_t instance=0,packet=0,model=0;const char* family=nullptr;};
 std::array<Entry,64> entries_{};unsigned size_=0;
 uint64_t device_=0,reset_=0,frame_=UINT64_MAX;
 void scope(uint64_t device,uint64_t reset,uint64_t frame)noexcept{
  if(device_!=device||reset_!=reset||frame_!=frame){device_=device;reset_=reset;frame_=frame;size_=0;}
 }
public:
 void submitted(uint64_t device,uint64_t reset,uint64_t frame,uintptr_t instance,uintptr_t packet,uintptr_t model,const char* family)noexcept{
  scope(device,reset,frame);if(!instance||!packet||!model||!family)return;
  for(unsigned i=0;i<size_;++i)if(entries_[i].instance==instance&&entries_[i].packet==packet&&entries_[i].model==model){entries_[i].family=family;return;}
  if(size_<entries_.size())entries_[size_++]={instance,packet,model,family};
 }
 bool contains(uint64_t device,uint64_t reset,uint64_t frame,uintptr_t instance,uintptr_t packet,uintptr_t model,const char* family)noexcept{
  scope(device,reset,frame);if(!family)return false;
  for(unsigned i=0;i<size_;++i){const auto& e=entries_[i];if(e.instance==instance&&e.packet==packet&&e.model==model&&!std::strcmp(e.family,family))return true;}
  return false;
 }
};
inline thread_local Ps2BodyPresence ps2_body_presence;
}
