#pragma once
#include "sdk.hpp"
#include <string>

namespace mrsetup {
// Called only by the isolated renderer build; installed renderer is untouched.
void frame(IDirect3DDevice8&) noexcept;
bool pilot_family_allowed(const char* family) noexcept;
unsigned revision(const char* family) noexcept;
bool pixels(const char* family, unsigned index, unsigned width, unsigned height,
            const void* original, void* output, unsigned bytes) noexcept;
}
