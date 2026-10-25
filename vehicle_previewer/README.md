# Master Rallye Vehicle Previewer

Windows Win32/D3D9 fixed-function inspector for user-supplied MR DX/DXT.
No game or GT assets are included. Python 3.10+ and the SDK source tree are
needed for resource staging/reload; the interactive renderer is a native EXE.
Blender is not required. Optional Pillow/numpy are research-render dependencies,
not requirements for opening MR vehicles in the native viewer.

## Build and open

From the repository, with CMake and Visual Studio C++/Windows SDK installed:

```powershell
python tools/build_vehicle_previewer.py
python tools/preview_vehicle.py 'C:/your/private/vehicle/complete.dx'
```

Or open `.research-output/vehicles/previewer/build/Release/mr-vehicle-previewer.exe`
and press **O** to choose a DX file. Keep the repository available for the Python
exporter; rebuild after relocating the SDK, or pass `--exporter` explicitly.
`python.exe` must be discoverable when opening the EXE directly. The Python
launcher supplies its own exact interpreter path.

| Control | Action |
| --- | --- |
| Left mouse drag / wheel | Orbit / zoom |
| 1 / 2 / 3 / 4 / 5 / 6 | Front / rear / side / three-quarter / top / opposite side |
| K | Cycle culling NONE / CW / CCW; current mode is in the title |
| Tab / F | Race, frontend, standalone wheel / frame model |
| O / R | Open DX or staged scene / regenerate and reload DX |
| E / B | Native environment helper / qualified `blight` brake switch |
| C | Generic two-case switch alternative; its game controller is not simulated |
| W / D | Wireframe / composed, base-only, vertex-colour inspection |
| L / 0 | Isolate next material draw / show all |
| F1 | Help |

Race wheel rest poses require evidence. Stock Navara/Pajero presentation
geometry can prove repeated wheel transforms. Other vehicles can supply a
bounded `preview-profile.json` alongside the DX, or `--profile path.json`.
The GT4 converter generates this metadata from the source rig. It is preview
metadata and never changes MR physics. An unknown rig is reported, not fitted
to wheel arches. Frontend wheels already embedded in complete.dx remain usable.

## Rendering boundary and the mirroring fix

The SDK uses right-handed XYZ coordinates. Both view and projection are now
right-handed. The original implementation used a left-handed camera and
mirrored stock models. **DX UVs and stored DXT BGRA rows stay unchanged.**
Horizontal and vertical asymmetric fixtures exercise the real GPU path.

Implemented: source diffuse colours/UVs, native two-byte alpha selectors,
GREATER alpha test at 128, source-alpha blending, depth, normal-coordinate
environment helper with COLOROP18, material layers and qualified stock brake
switch spans. Native shader evidence and stock resource structures inform
these rules. No PBR shader or guessed texture-alpha material classification.

Approximations: D3D9 rather than the original D3D8 renderer; neutral lighting
and background; no native world fog/vertex light updates; draw-centre alpha
sorting; inherited instance cull/Z overrides and native quality/mip settings
not fully reproduced. Outside faces are now culled by default: CW is calibrated
for canonical stored-global indices and the right-handed camera (the SDK swaps
wire corners 0/1). `--cull none` explicitly selects the permissive diagnostic;
`--cull ccw` exposes the opposite faces. Front/back GPU fixtures exercise all
three modes, so incorrect wheel-facing conventions are no longer silently
hidden. This is not proof of identical inherited D3D8 instance states, in-game
appearance or PS2 parity.

Preview staging also reports native texture residency. The CLI warns when the
family exceeds the SDK's 16 MiB authoring budget. The qualified retail texture
manager has a 32 MiB source-pixel cache; the D3D9 viewer does not emulate its
eviction. A fast preview therefore does not prove native MR performance. Use
`tools/analyze_vehicle_texture_budget.py` to inspect a converted family.

Pajero, Navara and frozen Subaru were rendered with their own local assets.
Stock reflection/brake toggles and camera/reload events passed application
tests. Actual original-game visual comparison remains a human runtime gate.

```powershell
# Optional GPU acceptance checks; Pillow is needed by this validation helper.
python tools/validate_vehicle_previewer.py --viewer .research-output/vehicles/previewer/build/Release/mr-vehicle-previewer.exe --output .research-output/vehicles/previewer/my-check --stock 'C:/your/stock/Navara'
```

Workflow: **Import → Convert → Preview → Diagnose → Repair → Rebuild → R →
Runtime Validation**. Source GT4 GS diagnostics are separately available via
`tools/render_gt4_scene.py`; unsupported source effects remain explicit there.
# Resource and quality diagnostics (V-SDK1-PERF2)

Press **I** to inspect counts for the visible model/state: draws, triangles,
staged vertices, reflection-capable and alpha draws, referenced textures and
the family source-pixel charge against MR's32MiB cache. With **L** layer
isolation active, the same dialog lists its texture names and dimensions.

`preview_vehicle.py --resource-diagnostics REPORT.json` also writes static DX
complexity and per-texture dimensions, UV/area and image-detail risk evidence.
`vehicle_sdk.py resource-diagnose` supports a source-reference directory for
resolution comparisons. These diagnostics do not measure original-game loading.
The opt-in native QPC candidate and capture tool are documented in
`research/vehicles/vsdk1-perf2/performance.md`.

## Rally Workshop navigation (V-SDK3)

The Studio manages this same native window; its center panel displays the latest
GPU capture. It does not embed a second renderer.

- Left drag: orbit; middle drag: pan both camera and orbit focus; wheel: zoom.
- Click: geometric triangle picking and amber highlight. Alpha texels are not
  sampled by picking, so a transparent surface can be selected.
- F: focus selection; Home: reset model framing; 1–6: camera presets.
- Ctrl1–6: save bookmarks; Shift1–6: recall. Bookmarks persist when a bookmark
  path is supplied. R reload preserves the camera.
- F3: actual Previewer FPS, staged draw/triangle/texture counts, uploaded BGRA
  bytes, declared CarID/provenance and selected material flags. These are
  Previewer measurements, not original-game performance or rendering proof.

Workshop forwards source-draw selection and model switching only to its owned
Previewer process. The CLI defaults and existing material debug controls remain
available. See `docs/sdk/RALLY_WORKSHOP.md` for the editor workflow and limits.

### V-SDK3.1 / V-SDK4A

**A** toggles Raw/Assembled Race; `--raw-race` starts raw. Profile-injected wheel
and attachment draws are separate from the original race resource. Exact embedded
four-wheel matches suppress duplicate assembly without deleting source geometry.
Negative-determinant instances reverse staged winding, preserving outward faces
with the transformed normals. This does not change game DX resources.

For standalone wheels, presets1/2 show outside/inside when source axial normals
provide a clear dominant direction. Ambiguous data retains the generic view;
rotate and inspect both sides. No global mesh flip is applied. F3/title identifies
the active presentation. The Workshop Wheel Fitment panel saves preview-only
positions/orientation/scale; these are not runtime suspension or physics controls.

Source model/draw picking now addresses the hierarchical Studio inspector,
including wheel instances. Material authoring uses the shared attribute writer;
unknown alpha/depth states and texture-slot allocation remain read-only. See
`docs/sdk/VSDK4A_RESULTS.md` for exact functionality and validation evidence.

