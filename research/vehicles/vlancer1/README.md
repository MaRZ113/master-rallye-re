# V-LANCER1 — GT4 source investigation, blocked runtime build

**Status: no complete DX/DXT/runtime candidate produced.** The original menu
source decodes, but an additional qualified T2 slot does not exist in the
current SDK. Source render-state translation/wheel anchors also remain
unqualified. Neither a substitute vehicle nor a replacement Subaru slot was
used. This is an investigation checkpoint, not a successful second import.

Branch: `research/vehicles`. Private evidence and diagnostic images:
`.research-output/vehicles/vlancer1/`. No proprietary inputs are included in the
source review archive. No original EXE, d3d8.dll, Randomizer or stock asset was
modified; no game was launched, physics tuned, commit or push performed.

## Genuine local source and extraction

Source: `D:/Game/GT_Model-Tools/VOL/GT4-Beta_Extracted/extracted/`:

| Member | Bytes | SHA256 |
| --- | ---: | --- |
| car/menu/mits0015 | 473162 | b3e24db37de08aaa7e4df1ab2c8e508c037b1b4ecb3b8c528f769e1214b99a15 |
| car/lod/mits0015 | 495370 | 6586265558f008d69991e8cb1a826136e5209cb063402b6df411653e195ac36c |
| wheel/menu/mits0015 | 47984 | ffd36ff540fc8a379ff7628f3ceb1d3e7a25cfe98d6a6d8738c012c6ad442f51 |
| wheel/lod/mits0015 | 21746 | a27628d87ef3faaf01ddf404cac440b1dbda6ba45e63ddf897f1921f5a7634d3 |

This is the user's **GT4 Beta** corpus, not a verified final retail GT4 build.
The mits0015 identity agrees with the supplied handoff and visible Evo IV rally
livery. A fresh read-only extraction was run from private copies using the
existing GTPS2ModelTool 1.1.1, SHA256
`c37405d818ee309db4e47a06997913c83779b527a6a50df9d22c1e127e4af5a6`.
CAR4 input contains MDLS at offset 3072. Inspected Dumper.cs routes CAR4 via
the offset at 0x18 into ModelSet2; it does not establish all CAR4 placement
metadata. Separate menu wheel is MDLS at offset zero.

Fresh menu body model0: 3226 triangles, 4450 positions/normals, 2681 UV entries,
48 material assignments, all referenced diffuse files present. Texture sizes
range 64×64 to 512×128; decoded alpha histograms are preserved in evidence.
243 UV entries lie outside [0,1], requiring proper repeat/clamp handling.
3921 corners have no UV: these cannot receive invented mapping. Non-UV effect
surfaces need source render-state interpretation, not automatic deletion.
Menu-wheel model0 has 1074 triangles and two materials; four exported models
exist, but they are not established as four instantiated axle wheels.

Fresh original race-body LOD0: 3178 triangles, 4392 positions, 2526 UV entries,
48 normal entries, 3921 corners without UV, 208 forward attribute references.
Positive forward references resolve within final OBJ arrays and must not be
mistaken for out-of-range data. Source-to-UV semantic fidelity still needs
verification against the original draw/VIF data.

## Important provenance / interpretation findings

- The older copied race-body binary differs from the corpus at offset 5897
  (`02` → `00`). Older wheel LOD differs at 12 offsets: 714, 776, 826, 1002,
  1064, 1114, 1290, 1352, 1402, 1578, 1640, 1690 (each `02` → `00`).
  These copies were not substituted for the corpus originals. The meaning
  and correctness of those changes have not been established.
- Original race-wheel extraction exits 0 but emits empty OBJ meshes across
  exported wheel models/LODs. Successful process exit is not successful
  geometry extraction. Original menu-wheel extraction does contain geometry.
- The older handoff calls menu model1 a cockpit and model2 brakes. Actual
  model_set.yaml marks both `UseUnknownShadowFlag: true` with colour/depth
  mask commands. Model2 is planar at Y=0. They must not be installed as
  cockpit/brake geometry on the strength of those old labels.
- GT4 ModelSet2 includes destination-alpha functions, colour masks, depth-mask
  suppression and tail-lamp callbacks. Numeric `MatN` labels are not a portable
  GT3 material class. GT3/Subaru classification and reflection/decal fixes
  therefore cannot be copied blindly.
- Source wheel anchor/instance transforms have not been qualified. No
  arbitrary wheel positions, geometry repair or fabricated missing parts were
  introduced. No complete assembled-wheel or physics claim is made.

## Reusable work delivered

`addon_sdk/external_source.py` provides a shared structural OBJ/MTL inspection
boundary, with finite attributes, valid indices, negative/forward references,
safe texture paths, file hashes, exact material coefficients, UV coverage,
alpha histograms, bounds and explicit **UNKNOWN** render semantics. It has no
Subaru, Lancer or material-number routing rules.

`tools/inspect_external_vehicle_source.py` uses the existing raster/framing
helper to create front/rear/side/three-quarter **source-only diffuse
diagnostics**. They force alpha opaque for inspection, omit faces lacking UV
in the existing OBJ preview path, do not emulate GT4 effects, and do not
assemble wheels. They are not MR candidates or proof of texture transparency.

`lancer-source.json` isolates source selection, axis convention, intended
physics baseline and unresolved parameters as editable data. Anchors and
CarID remain null. It is an investigation configuration, not an addon manifest.

Reusable existing components remain topology writer/validation, texture atlas
packing, optional wheel shelf/recess helpers, protected SDK packaging and UI
generation. Model-specific Subaru repair masks, decal edits, geometry selectors
and wheel-fitment values are excluded. The material adapter and wheel anchor
qualification required to connect these components for GT4 are **not complete**.

## Verified runtime integration blocker

Unchanged `retail-2001.json` supports IDs 26/27 only. Qualified slots are T1
local7 / ID26 and T2 local7 / ID27. Seven stock T2 entries plus Subaru fill
the declared T2 capacity of eight. Actual validator results:

```text
auto with Subaru: T2_ADDON_SLOT_UNAVAILABLE: class-local capacity has no qualified physical slot remaining
ID28: physical ID 28 is outside this target's declared addon capability set
ID26 as T2: physical ID 26 is qualified for T1 local7, not T2
```

This proves the **current SDK profile** cannot install the requested pair,
not that the executable can never support another slot. Qualifying another
CarID/T2 slot and multi-project UI composition is separate required work.
The current custom-UI pipeline also remains bounded to one author project;
independently appending frame32 twice would conflict without composition.
Capability lists were not weakened to turn an unknown layout into a pass.

## Validation, limitations and next gate

200 tests ran: 199 passed, one old private wheel fixture unavailable. All 190
immutable Subaru V4.13 runtime resources match their frozen manifest. Mutable
options.xml was excluded. No fresh full Subaru rebuild was performed, so this
is preservation/regression evidence, not a new reproducibility or game test.
Protected EXE and DLL hashes match their prior exact values.

Required before a complete Lancer candidate: qualify original GT4 wheel LOD /
menu-wheel use and source anchors; implement source-command-aware material
translation; qualify an additional T2 slot and multi-addon UI frames. Then use
the existing DX writer, runtime verifier and native-style UI generator, retaining
the verified physics baseline. No Lancer DX/DXT family, accepted CarID, final UI
icons or runtime success is claimed at this checkpoint.
