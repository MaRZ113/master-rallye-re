# Screenshot comparison and first transferable feature

The user's PC and PCSX2 screenshots show a clear ground-detail difference:
individual grass-like tufts are visible across the PS2 foreground, while the
corresponding PC view shows the ground texture alone. Different sponsor stands
are explicitly excluded from the platform-difference list.

| Input | Pixel size | SHA-256 |
|---|---|---|
| PC `MRallye_7qd231CnzV.png` | 640×480 | `f1a6efe13e2077be0c1294206310a49421036c14a51333fc0d588971b3e44f9e` |
| PS2 `Master Rallye_SLES-50906_20261013143351.png` | 1318×981 | `41d062fce138cb8c451c9026489419037a825e531954dfe5694d781301be479d` |

These are supplied runtime screenshots. The image-to-feature comparison is
SCREENSHOT_CORRELATION, supported by USER_RUNTIME_OBSERVATION. A picture does
not prove an exact material, course identity, texture binding or per-instance
generator output. Resolution, camera and elapsed race time differ. No exact
camera transform is recovered by fitting these images. The associated PC
session `session-20261013-043937-5748.jsonl` reports gameplay FOV enabled with
vertical FOV 60 and proxy SHA-256
`a69643d96c6c722ae2f2e678ab9738099083544df34f4a9b4c5003565510994c`.
Therefore this PC screenshot already uses an opt-in camera policy; it is not
an untouched retail PC camera reference. The baseline vehicle-reflection policy
was Stock, but the independent PS2 extension had ReflectionMode1 configured and
its static image uploaded. No target-material application record exists in that
session, so its effect on the pictured car is not proved. This screenshot does
not test the new Mode4 mixed target. FoliageMode3 was also configured. The session
SHA-256 is `fbf178f3eda335a59f93d1ebe47567e06e3236c73cc67f300de505e27b98d71c`.
The PS2 capture has no matching camera-matrix trace here. Turkey3 is confirmed
by the user and supported by the corresponding live course-certificate records.

## Transfer assessment

| Feature | Visible difference | Current source support | Remaining interface / evidence |
|---|---|---|---|
| Ground detail | Numerous individual PS2 tufts | GRASS1 recovered spatial source material/category, strict near-flat slope, deterministic scanline/hash/jitter positions, radial fade and sprite-oriented submission; original GRASS1/BUSH1 textures are decoded | Exact camera-history clipping and live VU residency are unverified. The first PC preview uses an explicitly labelled full-triangle generation policy and adapted PC sprite size |
| HUD | Square route minimap rather than circular grid; different gauge/layout | UI1 PSB/GXI banks are decoded. UI2 recovered player-centred heading-relative RaceLine projection/clipping and marker producer | Full replacement needs live PC race/vehicle data, selective native HUD suppression and final screen-layout policy; ordinary PS2 sprite/video/display composition is not fully proved |
| Reflection | PS2 car roof/body appear brighter in the supplied pair | REFL1 recovered static ENV plus flipped framebuffer source and normal coordinates. Reflection PORT1.1 contains a separately gated mixed-source pilot | The new mode still needs its own same-car/camera runtime A/B. These two images cannot attribute brightness to a single reflection, lighting or texture operation |
| Camera | PS2 view exposes more roof and places the car lower | Existing PC Free Camera/bookmarks and opt-in FOV permit controlled comparison | Authentic automatic chase-camera behaviour needs original pose/owner/time evidence. An approximate screenshot FOV fit would not establish it |

The first implementation is deliberately grass-only and opt-in. It uses source
PS2 spatial detail categories instead of guessing eligibility from PC texture
names or draw ordinals. It adds its private sprite batch at the previously
verified world-to-UI boundary, under a same-frame gameplay camera, depth and
course certificate. Stock defaults remain unchanged. The original game draws
are neither replayed nor reordered.

## Original contract and preview limits

GRASS1 proves pitch `float32(1.33)`, category grass/shrubs selection, strict
upward `Ny>.975`, a fixed original jitter table and world-coordinate hash.
The generator does not use per-instance random scale, yaw, tint, crossed
geometry or wind. The traced embedded program expands one point into a
screen-aligned textured rectangle. The PC preview preserves that broad shape,
not an invented crossed-quad plant model.

The committed source includes no original texture or point list. A verified
local artifact supplies original-derived points and texture; it remains
ignored and external to the handoff. This artifact is
`SYNTHETIC_FULL_TRIANGLE_ACTIVATION`, not a captured PS2 live population. PC
triangle quads, source-alpha blend and native LESSEQUAL depth convention are
renderer adaptations; no exact GS raster, live order or pixel parity is claimed.
The original 32×32 grass RGBA image was inspected locally: raw row 0 has zero
alpha and the blade/root orientation is upright with PC top `V=0`, bottom
`V=1`. The preview therefore retains raw rows and that D3D mapping. This is
`PC_UV_MAPPING_NOT_PS2_STQ_PARITY`; UI1's PSB V convention is not silently
treated as a verified grass-sprite sampler convention. No source texture is
flipped, edited or committed.

Use the final runtime handoff to compare GrassMode 0 and 1 on Turkey3 from the
same Free Camera bookmark and unchanged display/material settings. Keep foliage,
reflection, pixel probe and additional course objects in Stock for the first
isolation test. Evaluate presence, source-height placement, silhouette, terrain
occlusion, fading, camera changes and unrelated UI/vehicle state. A native build
and passing mock tests do not constitute visual acceptance.

## Evidence sources

- `ps2-research/grass1/material-directive-contract.md`
- `ps2-research/grass1/surface-eligibility.md`
- `ps2-research/grass1/placement-and-density.md`
- `ps2-research/grass1/randomness.md`
- `ps2-research/grass1/primitive-geometry.md`
- `ps2-research/grass1/culling-and-animation.md`
- `ps2-research/ui/final-report.md` and `ui/hud-resource-map.md`
- `ps2-research/ui2/final-report.md` and `ui2/minimap.md`
- `ps2-research/refl1/final-report.md`
- `modernization/renderer/include/free_camera.hpp` and its INI example

HUD, chase camera and broader vehicle reflections are assessed here; they are
not implemented or expanded by this grass-only pass.
