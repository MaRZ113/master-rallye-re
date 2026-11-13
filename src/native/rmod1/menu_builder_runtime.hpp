#pragma once
#include <windows.h>

// Master Rallye Menu Builder native runtime (part of the dinput8 loader).
// Serves compiled layouts from <game>/MenuBuilder/Layouts/<name> to the retail frontend:
//   * scene redirection at the VFS CreateFileA call (0x64D573) for FrontendScreens/*.xml|*.hnt,
//   * custom screens (native IDs 64+) through the GetScreenName call in the screen change (0x45D865),
//     hosted by the gaFEScreenGraphicsMainAI screen AI (init slot 0x690540),
//   * typed actions, Back handling, mouse hitboxes and diagnostics in a detour of the
//     screen command reader GetCommand (0x45D930).
// Disabled (Classic) unless MenuBuilder/MenuBuilder.ini selects an installed layout.
namespace menu_builder {
bool initialize() noexcept;
}

// Extension API for other modules (ABI 2, docs/menu-builder.md "Action bindings"). IDs are lower-case dotted names
// (e.g. "vehicle.paint"); the first valid registration owns an ID, IDs of this module are refused, and callbacks must
// be code inside a loaded module image. Providers run on the game thread inside the frontend tick.
// Action: return non-zero when the action was performed.
typedef int(WINAPI* MRMenuActionV1)(const char* args, int screen, int button);
// Value: write a NUL-terminated ASCII text into buffer and return its length; <= 0 = unavailable (fallback shown).
typedef int(WINAPI* MRMenuValueV1)(char* buffer, int size, int screen);
extern "C" unsigned WINAPI MRMenuAbiV1();
extern "C" unsigned WINAPI MRMenuAbiV2();
extern "C" BOOL WINAPI MRMenuRegisterActionV1(const char* name, MRMenuActionV1 action);
extern "C" BOOL WINAPI MRMenuRegisterValueV1(const char* name, MRMenuValueV1 provider);
extern "C" int WINAPI MRMenuQueryV1(char* buffer, int size);

#if defined(RMOD_EXTRA_OPTIONS)
// Implemented by extra_options_runtime.cpp for the car selected in Vehicle Select (same state as its MODEL row and
// the GENERAL page TYRE TYPE row): vehicle.model_source and vehicle.tyres.
namespace extra_runtime {
bool appearance_available() noexcept;
bool appearance_step(int direction, char* label, size_t size) noexcept;
bool appearance_label(char* label, size_t size) noexcept;
bool tyre_available() noexcept;
bool tyre_step(int direction, char* label, size_t size) noexcept;
bool tyre_label(char* label, size_t size) noexcept;
// vehicle.model_label (MODEL row caption) and vehicle.paint (PAINT row); unavailable = the row has no choices for the
// Vehicle Select car, which is what dynamic visibility ("visible" rows) hides.
bool model_row_available() noexcept;
bool model_caption_label(char* label, size_t size) noexcept;
bool paint_row_available() noexcept;
bool paint_label_of(char* label, size_t size) noexcept;
bool paint_step(int direction, char* label, size_t size) noexcept;
}
#endif
