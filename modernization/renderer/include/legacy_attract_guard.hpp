#pragma once
#include "game_fov.hpp"
namespace gfx2 {
inline constexpr uint32_t ATTRACT_LOADING_RVA=0x64e40,ATTRACT_PATCH_RVA=0x64f69,ATTRACT_SUCCESS_RVA=0x64f46;
inline constexpr unsigned char ATTRACT_REDIRECT[]={0xe9,0xd8,0xff,0xff,0xff};
class AttractThreadGate {
public: virtual ~AttractThreadGate()=default;
 virtual bool enter(uintptr_t begin,size_t size) noexcept=0;
 virtual void leave() noexcept=0;
};
struct AttractGuardResult {
 bool phase_verified=false,context_verified=false,quiesced=false,applied=false,owned=false,rollback_verified=true;
 const char* reason="unsupported_exe";
};
AttractGuardResult apply_attract_guard(PatchMemory&,AttractThreadGate&,uintptr_t base,uintptr_t caller,bool exact) noexcept;
// One attempt, at the verified initial native factory call before system-D3D creation.
bool install_legacy_attract_guard(uintptr_t caller) noexcept;
}
