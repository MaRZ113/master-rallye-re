#pragma once
#include <array>
#include <cstdint>
#include <limits>
namespace gfx2::ps2port {
class KiaWheelWarmup {
 uint64_t frame_=UINT64_MAX;std::array<unsigned,4> masks_{};bool ready_=false;
public:
 bool observe(uint64_t frame,unsigned owner,unsigned source)noexcept{if(owner>=4||source>=4)return false;if(frame_!=frame){bool complete=frame_!=UINT64_MAX&&frame==frame_+1;for(auto mask:masks_)complete=complete&&mask==15;ready_=complete;frame_=frame;masks_={};}masks_[owner]|=1u<<source;return ready_;}
 bool ready(bool all_current_tokens)const noexcept{return ready_&&all_current_tokens;}
};
}
