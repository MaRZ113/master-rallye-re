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

// Extension API for other modules (renderer, tools). Providers run on the game thread inside the
// frontend tick; return non-zero when the action was performed.
typedef int(WINAPI* MRMenuActionV1)(const char* args, int screen, int button);
extern "C" unsigned WINAPI MRMenuAbiV1();
extern "C" BOOL WINAPI MRMenuRegisterActionV1(const char* name, MRMenuActionV1 action);
extern "C" int WINAPI MRMenuQueryV1(char* buffer, int size);

#if defined(RMOD_EXTRA_OPTIONS)
// Implemented by extra_options_runtime.cpp: steps the PS2/PC appearance of the Vehicle Select car.
namespace extra_runtime {
bool appearance_available() noexcept;
bool appearance_step(int direction, char* label, size_t size) noexcept;
}
#endif
