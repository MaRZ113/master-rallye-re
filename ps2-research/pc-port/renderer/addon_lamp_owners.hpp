#pragma once
#include "lamp_continuity.hpp"
namespace gfx2::ps2port {
// Different participants (including duplicate cars) need separate healthy
// witnesses. Looking up a damaged car must never clear another car's proof.
class AddonLampOwners {
 struct Entry {unsigned profile;LampOwnerContext owner;NativeLampContinuity continuity;};
 std::vector<Entry> entries_;uint64_t device_=0,race_=0,reset_=0;
public:
 NativeLampContinuity* find(unsigned profile,const LampOwnerContext& owner,uint64_t reset,bool learn){
  if(!owner.owner_verified||!owner.device||!owner.race||!owner.lifetime)return nullptr;
  if(device_!=owner.device||race_!=owner.race||reset_!=reset){entries_.clear();device_=owner.device;race_=owner.race;reset_=reset;}
  for(auto& e:entries_)if(e.profile==profile&&e.owner.same_owner(owner))return &e.continuity;
  if(!learn||entries_.size()>=4096)return nullptr;
  entries_.push_back({profile,owner,{}});return &entries_.back().continuity;
 }
};
}
