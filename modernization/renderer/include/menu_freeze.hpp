#pragma once
#include "game_fov.hpp"
namespace gfx2 {
inline constexpr uint32_t FREEZE_CONTEXT_RVA=0x001b015a,FREEZE_PATCH_RVA=0x001b015c;
inline constexpr unsigned char FREEZE_CONTEXT[]={0x85,0xff,0x75,0x11,0x8b,0x44,0x24,0x10,0x8b,0x4e,0x18,0x50,0xe8,0x15,0x2f,0x0a,0x00,0xff,0x44,0x24,0x14,0x84,0xdb};
struct FreezeResult {bool context_validated=false,applied=false,already=false,owned=false,rollback_verified=false;const char* reason="disabled";};
FreezeResult apply_freeze_patch(PatchMemory&,void* context,bool validated,bool enabled) noexcept;
void install_menu_freeze(bool known,bool enabled) noexcept;
}
