#pragma once
#include "game_fov.hpp"
namespace gfx2 {
inline constexpr uint32_t UI_SORT_RVA=0x00109a21;
inline constexpr std::array<unsigned char,5> UI_SORT_BYTES={0xd8,0x60,0x30,0xd9,0xc0};
int margin_direction(float x,float y,float z) noexcept;
bool eligible_ui_packet(uintptr_t entity,uintptr_t coordinates) noexcept;
namespace detail {uintptr_t ui_bridge_for_contract(uintptr_t return_address) noexcept;}
class UiJumpPatch {
 void* site_=nullptr;std::array<unsigned char,5> after_{};bool installed_=false;
 bool exchange(PatchMemory&,const std::array<unsigned char,5>&,const std::array<unsigned char,5>&) noexcept;
public:
 bool install(PatchMemory&,void*,uintptr_t) noexcept;
 bool remove(PatchMemory&) noexcept;
 bool installed() const noexcept {return installed_;}
};
// Frame-owned coordinate edits, independently tested; never persistent packet identity.
class MarginFrame {
 struct Edit {float* x=nullptr;float original=0,effective=0,y=0,z=0;};std::array<Edit,512> edits_{};size_t count_=0;
public:
 uint64_t changed=0,failures=0,overflow=0;
 bool shift(float* xyz,float half) noexcept;
 bool restore() noexcept;
 size_t size() const noexcept{return count_;}
};
class UiMargins {
 UiJumpPatch patch_;MarginFrame frame_;DWORD thread_=0;float half_=0;bool enabled_=false;
public:
 const char* reason="disabled";
 ~UiMargins();
 bool install(bool exact,bool requested) noexcept;
 void dimensions(UINT width,UINT height) noexcept;
 void before_sort(uintptr_t entity,uintptr_t coordinates) noexcept;
 bool finish_frame() noexcept;
 void disable(const char*) noexcept;
 std::string json() const;
};
}
