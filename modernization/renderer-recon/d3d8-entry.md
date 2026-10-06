# API entry and presentation dependencies

**CONFIRMED_BY_EXE:** static `d3d8.dll!Direct3DCreate8` only in the import
directory. IAT VA `0x0068F414` (RVA `0x0028F414`), thunk `0x005D5244`, call
`0x0055905B` in `ObtainD3D8_00558EE0`. The pushed SDK value is `0x78` (120).
Keep that exact argument; later header constants are not substitutes.

**CONFIRMED_BY_EXE:** linked D3DX assembler body `0x005E311F` contains
GetModuleHandle/LoadLibrary("d3d8.dll") and GetProcAddress for
`ValidateVertexShader` at `0x005E340F` and `ValidatePixelShader` at `0x005E3436`.
Loader IAT `0x0068F0B8`, resolver IAT `0x0068F0C0`. Those export names have no
IAT of their own. Their game reachability is **HYPOTHESIS / unresolved**; code
presence is sufficient reason to include them in a future forwarding audit.

Other loader paths reviewed: `0x005D3750` USER32 message boxes/active window;
`0x005A2830` OleAut32; `0x005AA4D0` type-library helpers;
`0x005C7732` KERNEL32 CPU feature query. None obtains the normal renderer device.

**CONFIRMED_BY_EXE:** DDRAW!DirectDrawCreate IAT `0x0068F018`, thunk
`0x005D5220`, caller `0x0055ADC6`. After successful D3D startup the manager
requests DirectDraw NORMAL cooperative level (8) and a primary surface
(DDSCAPS_PRIMARYSURFACE 0x200). Purpose beyond this auxiliary ownership is
unresolved. This is not evidence for a software/DirectDraw 3D fallback renderer.

Window owner `0x005590C0` registers `D3D Window`, creates or subclasses an HWND,
stores manager+0x5C, defaults focus HWND +0x60 to that handle, and captures window
and client rectangles. `0x0055AED0` adjusts styles/fullscreen placement.
GetClassLongA and device ShowCursor appear in create/reset. GDI imports include
font creation, DIBs and TextOut: `0x0064EC50` is a font/text rasterization lead,
not proof of GDI presentation replacing D3D. Every selected IAT and symbol
reference is in [entry JSON](data/d3d8-entry.json); all DLL imports are in
[imports JSON](data/imports.json).

No gamma DLL import exists; no reviewed device SetGammaRamp call was found.
Gamma API use is **not observed**, rather than proved absent from all possible
indirect code. Device/window cursor behavior must still be forwarded faithfully.
