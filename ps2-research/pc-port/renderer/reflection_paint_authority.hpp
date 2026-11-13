#pragma once
// REFLECT-ADDON1: PS2 reflections for every car. The PS2 reflection admits only geometry listed in kReflectionMaterials
// (exact hashes of the retail cars' PS2 "carshiny" groups). This hook lets the native side prove a registered paint body
// draw of an add-on (or future) car family instead: fleet owner -> vehicles/<family>/car -> BodyMaterials role paint.
// Returns the interned family name, or nullptr. Installed by atmosphere_body_general.hpp.
#include "sdk.hpp"
namespace gfx2::ps2integration {
inline const char* (*paint_authority_hook)(void* device, UINT min, UINT vertices, UINT start, UINT count) noexcept = nullptr;
}
