# X-Trail race material map

Source layer: protected PC `Xtrail/car.dx` compiled records and canonical PS2
`XTRAIL/CAR.PSM` authored visual tree. Source indices below are NOT D3D8 draw ordinals.
Full32CAR/4WHEEL source categories, runs, hashes, bindings and residuals are in
`wheel-glass/source-evidence.json`. Original winding/ADC visibility are not inferred
from a material name or screenshot. All geometry joins use0.001 source-unit tolerance.

| PC source record | Source face range | PS2 owner/category | This iteration |
|---|---|---|---|
|CAR1|0–194|root.1,195carshiny|Existing body partition preserved|
|CAR1|195–208|root.0,14carflat|Stock preserved; this is NOT the number decal|
|CAR4|155faces|root.3 carshiny|Existing Mode4 preserved|
|CAR5|77faces|root.4 carshiny|Existing Mode4 preserved|
|CAR6|144faces|root.6 carshiny|Existing Mode4 preserved|
|CAR9|34faces|root.10 carshiny|Existing Mode4 preserved|
|CAR11|50faces|root.12 carshiny|Existing Mode4 preserved|
|CAR12|166faces|root.13 carshiny|Existing Mode4 preserved|
|CAR14|110faces|root.16 carshiny|Existing Mode4 preserved|
|CAR13|0–13|root.14 carshiny, number sticker|NEW opt-in normals+same Mode4 source, one replacement submission|
|CAR10|18faces|root.19 carglass, front lamp covers|Stock retained; separate glass conversion required|
|CAR21|28faces|root.5 carshiny, later alpha lamp layer|Stock alpha layer retained; not forced opaque body|
|CAR22|14faces|root.11 carshiny, later alpha lamp layer|Stock alpha layer retained; not forced opaque body|
|CAR19|148faces|UNMATCHED driver helmet source|Stock; no unsupported body admission|
|CAR23–29|conditional/brake/window ranges|AMBIGUOUS/unknown/mixed glass|Stock; no new overrides|
|WHEEL0+2|72+54faces|root.0 authored rubber map|Stock rubber retained|
|WHEEL1|36faces|root.1 authored rubber tread|Stock retained|
|WHEEL3|90faces|root.2 carshiny/chrome rim|Stock retained pending authenticated image+UV/current wheel owner|

All eight existing whole-Xtrail reflection registry entries were cross-checked
against the new source categorization: each is fully carshiny, with no discovered
flat/glass/unknown subrange. CAR13 was already a source registry candidate, but the
native0x142 format/disabled-stage1 failed the original environment admission. The
only active mixed body record remains CAR1; its14flat faces occupy an interior
horizontal strip at Y≈0.966–0.994, not the side number plate. Exact named component
identity beyond source root/material remains UNKNOWN.

## Recorded D3D8 observations

Session27240/frame1680, installed DLL1f7c99da…: exact current CAR1 digest
`16c3cf75f8d9aa9f4a9d96c36fb0c4f70e1046ea324123b51237158a7c12a19f`
was submitted as index49392/195shiny and49977/14Stock. All draw HRESULTs0,
`state_restore_pending=false`, one total coverage/no replay. Those ranges are one
recorded session, not persistent classifier constants.

Frame8422/1274 layout correlations:

| Source | Frame8422 arguments | Observed format/states | Evidence boundary |
|---|---|---|---|
|CAR13|DIP(4,8747,20,52275,14)|0x142/24; stage1 disabled; alpha test/blend off; Zwrite on|Layout only; new current mirror+UV/color validation mandatory|
|CAR10|DIP(4,5558,22,51573,18)|0x152/36; both slots lights; env stage; opaque/Zwrite on|Layout only; PS2 glass source differs|
|CAR21|DIP(4,9599,30,54411,28)|0x142/24, alpha blend on|Separate later layer|
|CAR22|DIP(4,6420,18,54495,14)|0x152/36, alpha blend on|Separate later layer|

Source normals/UV residuals and20point-hash guards are compact source evidence,
not native bytes extracted from those F10 files. Raw F10 buffers/draw IDs are not
embedded in the classifier. The new runtime must prove those current bytes itself.

## Wheels and headlights

All252race wheel triangles match PS2; no race mesh transplant is indicated. Rim
PC `xwheel` versus PS2 `jumpwheel64` and UV difference≈0.17088 require source image
and UV conversion, plus original wheel-instance/rotation admission. The race wheel
conclusion does not apply to the higher-detail COMPLETE wheel meshes.

CAR10 front-cover geometry matches18/18, but PS2 primary is16×16WINDSCREEN32 with
stored alpha7…138, not the PC lights image, and UV residual exceeds1. PS2 mode20
combines alpha-blended/no-depth-write primary with a static windscreen-reflect
normal-generated additive highlight weighted96/128. It does not use the Mode4
mixed framebuffer source. Merely changing this opaque draw to shiny or enabling
blending would misrepresent the original contract. No such shortcut is implemented.
