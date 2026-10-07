#pragma once
#include "game_fov.hpp"
namespace gfx2 {
inline constexpr uint32_t UI_SORT_RVA=0x00109a21;
inline constexpr std::array<unsigned char,5> UI_SORT_BYTES={0xd8,0x60,0x30,0xd9,0xc0};
inline constexpr uint32_t UI_PACKET_RVA=0x0016d110;
inline constexpr std::array<unsigned char,6> UI_PACKET_BYTES={0x81,0xec,0x08,0x01,0,0};
int margin_direction(float x,float y,float z) noexcept;
bool eligible_ui_packet(uintptr_t entity,uintptr_t coordinates) noexcept;
namespace detail {uintptr_t ui_bridge_for_contract(uintptr_t return_address) noexcept;uintptr_t ui_packet_entity_for_contract() noexcept;uintptr_t ui_packet_bridge_for_contract(uintptr_t return_address) noexcept;}
class UiJumpPatch {
 void* site_=nullptr;std::array<unsigned char,5> after_{};bool installed_=false;
 bool exchange(PatchMemory&,const std::array<unsigned char,5>&,const std::array<unsigned char,5>&) noexcept;
public:
 bool install(PatchMemory&,void*,uintptr_t) noexcept;
 bool remove(PatchMemory&) noexcept;
 bool installed() const noexcept {return installed_;}
};
class UiPacketPatch {
 void* site_=nullptr;std::array<unsigned char,6> after_{};bool installed_=false;
 bool exchange(PatchMemory&,const std::array<unsigned char,6>&,const std::array<unsigned char,6>&) noexcept;
public:
 bool install(PatchMemory&,void*,uintptr_t) noexcept;
 bool remove(PatchMemory&) noexcept;
 bool installed() const noexcept {return installed_;}
};
// Frame-owned coordinate edits, independently tested; never persistent packet identity.
class MarginFrame {
 struct Edit {float* x=nullptr;float original=0,effective=0,y=0,z=0;uintptr_t owner=0;};std::array<Edit,512> edits_{};size_t count_=0;
public:
 uint64_t changed=0,failures=0,overflow=0;
 bool shift(float* xyz,float half,uintptr_t owner=0) noexcept;
 bool restore() noexcept;
 size_t size() const noexcept{return count_;}
};
class UiMargins {
 UiPacketPatch patch_;MarginFrame frame_;
 struct Observation {uintptr_t entity=0,point=0;uint64_t id=0,first=0,last=0,restored=0;float logical=0,effective=0;unsigned visits=0;};
 std::array<Observation,64> observations_{};uint64_t frame_id_=1,next_id_=0;unsigned records_=0,diagnostic_frames_=0;bool capturing_=false;DWORD thread_=0;float half_=0;bool enabled_=false;
public:
 const char* reason="disabled";
 ~UiMargins();
 bool install(bool exact,bool requested) noexcept;
 void dimensions(UINT width,UINT height) noexcept;
 void capture_window(bool active,uint64_t frame) noexcept;
 void reset_diagnostics() noexcept;
 void before_consume(uintptr_t entity) noexcept;
 void before_sort(uintptr_t entity,uintptr_t coordinates) noexcept;
 bool finish_frame() noexcept;
 void disable(const char*) noexcept;
 std::string json() const;
};
}
