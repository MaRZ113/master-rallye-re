# ATMOSPHERE1 — source and offline prototype, 2026-11-03

Base: `master` HEAD `9ff5d4868415d5fd8e13458a2e36bc935e34c29f`, existing
`master-rallye-re-general` worktree. No branch switch, game deployment or push.
The frozen renderer tree remains `46663a8db86922443e74f4fb760b29b2d8ae6978`.
Changes enter the existing PS2-enabled D3D8 proxy through its reviewed overlay;
the ordinary baseline source and generated interfaces remain unchanged. Neither
proxy nor atmosphere code depends on Master Rallye Extra Options / dinput8.dll.

## Evidence and current gates

| Part | Implemented evidence | Remaining acceptance |
|---|---|---|
| B0 | Current HEAD checked; original PC bytes, sky geometry/textures, fog/material paths and reflection order reviewed | Current game traces/screenshots on two courses; compatibility matrix |
| B1 | Six-preset catalog; native initialization-time selector; private paired texture sets | In-game 0–5/reload/replay/frontend verification; actual loaded texture format/row identity |
| B2 | Opt-in original-cylinder sunset set; scoped terrain diffuse/fog prototype | Vegetation/buildings/car direct lighting; visual coherence and performance in game |
| B3 | Sun-direction projection and conservative visibility contract, tested | Disk/halo/flare implementation and real depth/coverage observations; all effects suppressed meanwhile |
| B4 | Movable source on private prelit vertices; original France1 road rendered with system D3D8 | In-game movable light; shadows/normals; Reset/MSAA/camera/effect matrix |

**No part is RUNTIME_TESTED or ACCEPTED in the game by this change.** The road
probe is `D3D8_OFFSCREEN_VALIDATED_NOT_GAMEPLAY`, a separate evidence class.
Night and headlights remain outside this implementation.

## Original executable and exact selection seam

Original input `D:\Game\Master Rallye\MRallye.exe`, PE32 x86, base `0x400000`,
SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
Addresses here are VA for this image. REA/Ghidra 12.1.4 independently read the
matching bytes at `0x4b1180` (Evidence
`ev_60949584d2106a71d0be4cc25f9ef3ae6d1e8dc62055dc6316ac5f92863d3c35`).
Its procedure resolver did not expose this function in the fresh analysis;
original instructions were therefore checked directly with objdump. No new
decompiler output is treated as original source. Raw evidence/disassembly is
private under `.research-output/atmosphere-phase1/scratch/`.

* `0x4b0ed0` constructs `gaAiCloudSetUp` (name at `0x6e67fc`), size `0x50`,
  vtable `0x691090`. Serialization starts at `0x4b1030`, deserialization at
  `0x4b10f0`. Authored `Cloud Type 0 - 5` is field `+0x10`; the initializer
  chooses resources from broker state instead. Changing this field alone is
  insufficient for deterministic selection.
* `0x4b1180` reads SkyQuality, keeps native layer enable policy and selects the
  first layer from CloudNumber or CloudNumberReplay. The exact getter call
  `0x4b123c: E8 1F 55 02 00` targets `0x4d6760`.
* The getter reads one stack argument and returns with `RET 4` at `0x4d6860`.
  It may create a broker entry. The replacement uses the matching fastcall
  adapter and ALWAYS calls the original getter first, preserving those effects.
* The returned number is consumed by the native replay-selected write at
  `0x4b125e`, `Misc/Sky/cloud%d/clouds%d` formatting at `0x4b126f`, native model
  load `0x4f5b70`, palette selection and CloudNumberUsed write. Later layers read
  Used at `0x4b1374`, format `Misc/Sky/cloud%d/layer%d` and retain the native
  increment/wrap sequence at `0x4b13ae..b4`. There is no second layer patch.
* Installation verifies supported retail layout, base and exact call bytes,
  quiesces other threads with instruction-pointer checks and pins the proxy.
  Conflicting hooks are left untouched. No file bytes or retail archives change.
  The hook lasts for the process; default Disabled installs no hook.
* Network contexts or unreadable network fields use the original getter result.
  Auto/invalid preset uses the original result. A valid digit 0–5 is reread at
  the next first-layer initialization, so race reloads are deterministic. Other
  profile keys require restart. Manual replay appearance is intentional.

## Native sky resources and fog

The current protected PC corpus has six normal cloud directories plus a seventh
debug/resource set; the native cycle is exactly 0–5. All selected sky textures
are 256×256, a 20-byte FEED wrapper followed by BGRA8 pixels, **not block DXT**.
Each selected cloudsN mesh has 134 vertices; layerN has 114. Common bounds are
X ±1000, Y approximately 0..1000, Z ±984.8078. These are cylindrical geometry,
not six cubemap faces. Slot0 references the corresponding cloud/layer texture;
other slots are Null. `sky-catalog.json` records exact names/hashes/flags.

| Preset | Selected cloud texture | Native fog RGB (float) |
|---|---|---|
| 0 | clouds0-tga | .87, .86, .86 |
| 1 | cloud1-tga | .57, .66, .80 |
| 2 | cloud2-tga | .47, .53, .59 |
| 3 | cloud3-tga | .56, .36, .24 |
| 4 | cloud4-tga | .27, .33, .40 |
| 5 | cloud5-tga | .88, .94, .98 |

Cloud3's source RGB texture is visibly warm orange. Thumbnail RGB inspection
forces alpha opaque and preserves stored rows; original-alpha PNGs are also
provided. Cloud0's base texture has alpha=0 throughout, so naive transparent PNG
previews hide its RGB. A texture thumbnail is never a runtime sky screenshot.

Existing executable/corpus research establishes clouds0–5 opaque compiled flags,
layer alpha flags, base/base_alpha family, expected FVF0x102/stride20, camera-X/Z
centering mode2, and fog disabled on the sky packet. Actual last-state depth,
order, shader and replacement identities still require new F10 traces. The
native fog uses LINEAR vertex fog, ViewDist 300/400/500, span .9, so start
30/40/50; far clip is twice fog end. See the preserved renderer-recon sky/fog
reports and `course-light1/findings.md` for their separate static/runtime grades.

## Custom sunset and narrow lighting experiment

`Atmosphere.ini` is separate from PS2Port.ini. Enabled, WorldLighting, LightProbe,
Sun and SunFlare default to 0; SkyPreset defaults to Auto. No stable PS2 key is
reused. The catalog tool privately derives a mild sunset colour experiment from
native preset3: B×.82, G×.94, R×1.04+5, alpha unchanged. This is a starting
GT3-inspired art direction, **not GT3 assets or a verified GT3 visual match**.

CustomSet names a directory containing clouds.dxt and layer.dxt. Support is
bounded to the extracted native 256×256 geometry/UV contract and CustomBase
0–5. The paired assets are preflighted for dimensions, size and original alpha
mask identities before any replacement draw. RGB/alpha/row layout is explicit;
there is no arbitrary skybox/PNG/cubemap support. Missing/unsupported resources
fall back to original textures. Actual sky draws additionally require current
race ownership, one camera, native backbuffer, no fog, FVF0x102, supported shader
states, registered texture lifetime and exact original BGRA content identity.
No reflected-image orientation, texture transform or native UV is flipped.

The world prototype admits only the opaque course base_noise path at native
return `0x57707e`, the exact existing noise-tga identity, current race/camera,
backbuffer and fixed-function prelit state. It copies the admitted native vertex
range from the verified mirror into a private buffer, preserves positions, UVs,
indices and alpha, and scales prelight RGB by (1,.86,.68). Scoped fog is
0x008e4f29. Both PC noise and existing PS2 GroundDetail see the same copied
vertices; the latter retains its separate subtract pass. This does not relight
all objects or directly alter car/glass/lamp/HUD colours. The changed sky/terrain
can enter the normal environment capture, with no extra reflection pass or gain.
That expected coherence remains an in-game test requirement.

LightProbe adds a bounded quadratic distance term, maximum .4, to these same
prelit vertices. The source moves along X as `LightX + sin(t*.5)*LightRadius`;
Y/Z and radius are configurable world coordinates. It is a vertex-frequency,
unshadowed research light: coarse meshes can produce coarse illumination, and
it has no surface-normal term, headlight cone, shadow map or night mode.

Every changed texture/stream/index/fog state is restored after the entire native
draw path, including early replacement returns. Native-only writes update the
effective state tracker. Partial or failed setters are marked before mutation;
failed restorations remain pending and block later native submissions until
repair. Reset releases private GPU resources after the existing repair gate.
Off adds no native D3D calls inside the new admission path. Automated tests cover
the restoration slots and each individual failed-restore/retry case; game Reset,
AA and timing compatibility remain pending.

## Reproduction and validation

From the repository root:

```powershell
python ps2-research/pc-port/tools/atmosphere_catalog.py --source '../Data.sma_unpacked/DataGx/Misc/Sky' --output .research-output/atmosphere-phase1/catalog --registry ps2-research/pc-port/renderer/atmosphere_sky_registry.hpp
$env:MRR_ATMOSPHERE_EXE='D:\Game\Master Rallye\MRallye.exe'
python ps2-research/pc-port/overlay/build_overlay.py
python ps2-research/pc-port/tools/atmosphere_road_probe.py --course '../Data.sma_unpacked/DataGx/Course/France1/france1.dx' --output .research-output/atmosphere-phase1/road-probe
ps2-research/pc-port/.build/ps2-enabled/Release/atmosphere_gpu_probe.exe .research-output/atmosphere-phase1/road-probe/road.bin .research-output/atmosphere-phase1/road-probe/rendered
```

The isolated system-D3D8 probe draws one original France1 road batch, 58
triangles, with original road texture/prelight. Baseline and two source positions
produce distinct GPU readbacks; 108 and 72 vertex submissions receive light in
the two positions. It uses a diagnostic top-down projection, bypasses the engine,
fog, PS2 subtract pass and all gameplay/effect ownership. Its source manifest
preserves the Course SDK warning: complete course/trailing tag100 reconstruction
is not claimed. This probe validates rendering the chosen road batch only.

Build/test totals and artifact hashes live in `validation.json` and the private
build report. The frozen baseline DLL remains the same deterministic
`eb7ea3d9501b514bff668f1e75e86041906c5fe4e8afa89f06d658751429aaf4`.
The exact selector bytes and RET-4 ABI are separately tested against the original
EXE; the optional input must be present to claim that corpus check.

Runtime acceptance is tracked in `runtime-matrix.json`, initially all pending.
Use selector-only preset3 as A, custom-sky preset3 as B, then terrain preset3 as
C. Keep course, car, camera, point, quality and CloudNumberUsed identical; retain
F10 traces/environment targets with the screenshots. Classic Disabled vs
selector-only with matching native preset is a separate identity comparison.
Test Turkey3 and France1, water/grass/foliage/glass/glow/HUD, Reflection=4 and
VehicleLighting=1, both independent DLL combinations, reload/replay/frontend,
Reset/resolution/AA/camera switches and missing custom assets. Never treat a
passed build, offscreen road image or old screenshot as this acceptance.

GT3 unpacked VOL path supplied by the owner exists. The other supplied path,
`E:\Games\GT_Model-Tools\GT3_Extracted`, is absent on this machine. Neither
external GT3 source was copied or changed. Installed game EXEs, DLLs, archives,
settings, saves and historical research were not edited by this work.


BL1 follow-up: [first-load baseline diagnosis and guarded candidate](../atmosphere-bl1/README.md).
The original first-phase candidate does not fix the cold-start publication race.
