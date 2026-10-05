# Stock lighting: established unlit paths, unresolved source lighting

**CONFIRMED_BY_EXE:** all reviewed base/env/noise/water/particle setup methods
write D3DRS_LIGHTING137=0. `0x00577DD0` copies packed vertex diffuse from model
arrays; stage0 typically multiplies texture by that diffuse. Normals are available
for the environment stage and some compiled layouts even when D3D lighting is off.
This prevents interpreting normal presence as proof of live directional sun.

Cache initializer `0x0058E870` sets default LIGHTING1. Runtime defaults also include
AMBIENT139=0, COLORVERTEX141=1, LOCALVIEWER142=1, NORMALIZENORMALS143=0,
SPECULARENABLE29=0 in the other table. Default material-source state entries remain
in [state-defaults](data/state-defaults.json). Later family setup can override them.

**STATIC_INFERENCE:** stock appearance in the mapped families is predominantly
texture/vertex-color driven; precomputed lighting is a plausible origin of some
vertex colors. The phase has not proved a complete baking/cooker light pipeline.

No receiver-confirmed IDirect3DDevice8 SetLight, LightEnable or SetMaterial path
was recovered. Equal numeric vtable offsets elsewhere belong to engine/editor
objects and must not be classified as D3D lights. Number/type/direction/color of
active native lights and a track-specific sun/ambient source remain **HYPOTHESIS /
UNKNOWN**. Sky palette values are confirmed fog inputs, not secretly sun colors.

Future per-pixel lighting needs normal-bearing layouts, resource/material identity
and a policy for source diffuse (avoid double lighting prelit geometry). A first
runtime trace should log SetLight/LightEnable/SetMaterial plus LIGHTING, AMBIENT,
SPECULARENABLE, NORMALIZENORMALS, COLORVERTEX and LOCALVIEWER. Any native light calls
must be added to the map before a lighting replacement is designed.

Brake-light lead `0x004CA110` (RVA0x000CA110) looks up material name `blight`
on the vehicle model at entity+0x50/+0x18 and binds ControllerCarBrokerAccess.
This is a material/controller lead, not a native D3D point light or a proven
headlight projection path. Its activation/color-update policy is still untraced.
