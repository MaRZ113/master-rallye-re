# V-LANCER3 + MR Vehicle Previewer

Branch: `research/vehicles`. Result: **offline-validated Lancer asset and
external runtime candidates, ready for human inspection; not full GT4 render
parity or confirmed gameplay.** Subaru V-MESH4.13 remains frozen.

Private output root: `.research-output/vehicles/vlancer3/`.

## Delivered locally

| Output | Purpose |
| --- | --- |
| `final-assets/assets/` | Real `car.dx`, `complete.dx`, `wheel.dx`, 59 referenced DXT textures and preview rig metadata |
| `final-assets/renders/` | Front, rear, side, top, three-quarter native-preview captures |
| `source-assembled/` | Ordered GS software diagnostic renders and full source-shape inventory |
| `final-candidate/` | Editable SDK project, author build, separate sealed runtime and matched external launcher |
| `offline-validation.json` | Geometry/texture/rig, rebuild and frozen-Subaru checks |
| `determinism.json` | Two separate build roots produce identical DX/DXT bytes |
| `tests-final.log` | Synthetic regression suite |
| `protected-files.json` | Original MR EXE, graphics DLL and original GT4 CORE hashes preserved |
| `GALLERY.html` | Source / converted views and corrected stock preview |

The standalone Windows viewer executable is at
`.research-output/vehicles/previewer/build/Release/mr-vehicle-previewer.exe`.
See [viewer controls and rendering boundary](../../../vehicle_previewer/README.md).
It loads real MR resources, supports orbit/zoom/presets, race/frontend/wheel
models, material isolation, reload, reflections and qualified stock brake cases.

## Source identity and reconstruction

Authority is the user's immutable `GT4-Beta_Extracted/extracted` set, model
`mits0015`. No retail GT4/another vehicle geometry was substituted. Its sibling
boot file names `SCUS_974.36`; the sibling CORE authenticates with RSA exponent
81001, labelled Online US in the local PDTools loader. These identifiers are
reported explicitly rather than silently treating an arbitrary Online build as
Beta evidence. Native formulas refer to this supplied CORE; whole-disc pairing
and original GT4 runtime appearance have not been independently requalified.

| Resource | Stored shapes | Stored triangles | Texture banks |
| --- | ---: | ---: | --- |
| Body menu | 30 | 5350 | 56 |
| Body race, all stored LODs | 93 | 8249 | 56 / 52 / 46 / 1 |
| Menu wheel | 2 | 1074 | 1 |
| Race wheel, all stored LODs | 10 | 220 | 1 / 0 / 1 / 1 / 1 / 2 / 2 / 1 / 1 |

These totals are **not** one merged visible model. Model0 / LOD0 is selected
explicitly. All stored body shapes have reachable command uses recorded;
unselected LODs/conditional passes remain inventoried. The empty race-wheel
texture bank is retained at its own index, not redirected to a different LOD.

Direct decoding covers packet-local strips, float/fixed positions and UVs,
signed delta UVs, packed signed normal directions, vertex colours, GS textures
and palettes, ModelSet2 state/control flow and two-endpoint morph channels.
Fixed a second sign-extension error on negative UVs in STMOD0. Float normals
remain original; byte normals become unit **directions**, with their raw uploads
retained. The original VU lighting gain/program is not claimed reconstructed.

Embedded CAR4 menu rims are byte-identical to the independent menu-wheel file.
Embedded front/rear tyre models are decoded separately. Original DBT/IDI rows
and native constructor instructions provide wheelbase, visual tracks, tyre/rim
dimensions and rest hubs. SQLite column names and wheel-arch fitting are not
used. 3896 instruction-byte mappings were checked against original ELF segments
and independently disassembled with Rabbitizer R5900; Ghidra pseudocode remains
an analysis aid, not original source.

For this profile: wheelbase 2.510m, tracks 1.490m, tyre width .215m, rim radius
.2286m, outer radius .32535m. Hubs are body-relative. Steering/spin are zero;
dynamic camber/toe, suspension and root ground/pitch pose are not simulated.
The same body frame is used for geometry and diagnostic wheel assembly.

CAR4 field0x34 contains another MDLS (one shape, 11 triangles). It is decoded
and separately inventoried; its runtime purpose and instance are unresolved.
It is not invented into a driver, shadow, spare wheel or body repair.

## Shared SDK changes

- Original Tex1 transfers, GS palette/address handling and raw alpha unity128.
- Explicit GS test, DATE, FBMSK, depth and blend semantics, independent of MatN.
- Source-relative wheel reconstruction from raw DBT/IDI and source callbacks.
- Existing volumetric GT4 rims/tyres are preserved; no extra shelf is added on
  top of already valid source layers. MR race wheels remain separate resources.
- Affine UV remapping plus edge-extended guard textures reproduces admitted
  clamp regions in MR wrap slots; repeat axes retain their original wrapping.
- Shared variable-draw DX writer and explicit `scene_candidate` authoring route.
  Pinned donor collision, material words, resource bounds and grammar are checked.
  Existing same-draw `topology_candidate` validation was not weakened.
- Optional MR environment fallback pairs exact triangle geometry, verifies
  complete opaque coverage and DATE, then uses a user-selected local MR helper.
  It preserves source base alpha as reflection weight. No material-name guesses.
- Standalone fixed-function viewer reuses SDK parsers/material interpretation.

The editable source profile supplies only hashes, source labels, selected
models/LODs/callback states, explicit morph freezing, helper choice and addon
identity. No Subaru geometry, source repairs or vehicle-specific draw IDs are
used by the new builder.

## Converted resources and visual discrepancy boundary

| Resource | Vertices | Triangles | Draws | MR helper parts |
| --- | ---: | ---: | ---: | ---: |
| complete.dx | 6983 | 5789 | 162 | 55 |
| car.dx, without baked race wheels | 2905 | 2081 | 92 | 7 |
| wheel.dx | 827 | 745 | 16 | 12 |

1. **Source structures still unresolved:** live VM morph weights and supplemental
   field0x34 instance. Four deformable race parts retain the first genuine source
   endpoint under an explicit profile policy; the second endpoint is retained.
2. **Translation limitations:** MR helper textures approximate GT4 generated
   environments. Unadmitted transparent/DATE effects and additive brake-disc
   colour passes remain reported, not forced opaque. Source tail-lamp branches
   are decoded, but their MR brake/controller mapping is not qualified; this
   candidate retains the selected day branch. Stock brake behavior in the viewer
   is tested separately and does not qualify Lancer brake behavior.
3. **Lighting/render differences:** VU lighting, GS fog/filtering, destination
   alpha and dynamic generated textures have no fully qualified MR equivalent
   here. The GS reference renderer implements ordered fragment tests/masks/blends,
   but its neutral-light views are not proof of native GT4 appearance.
4. **Intentional approximations:** high-detail menu wheel/tyre geometry for MR
   race wheels, frozen morph endpoint, native MR helper for proven opaque pairs,
   unchanged Navara collision/physics baseline and MR-style authored UI cameras.
5. **Human tests needed:** actual surface visibility/culling, glass sorting,
   reflections on/off, frontend framing/UI and the donor-controlled race wheel
   fitment. Source preview wheel anchors are not runtime wheel/physics tuning.

No official same-vehicle GT4 runtime screenshot was supplied or independently
qualified in this pass. The supplied source and converted diagnostic views are
comparable engineering evidence, not a visual-parity certificate.

## Mirrored stock preview correction

The initial native viewer used a left-handed camera on SDK right-handed data.
Both camera matrices are corrected. UVs and DXT rows are unchanged; a temporary
row-flip experiment was reverted. GPU tests prove horizontal red-left/blue-right
and vertical stored-row0-above-row1 orientation. Pajero now reads `203` correctly.
Stock Navara reflection/brake toggles and interactive reload/orbit/zoom pass.

## Runtime scope and launch

The fresh bundle uses the existing qualified **ID26/T1 Mercedes + ID27/T2**
layout, with independent Lancer resources at ID27. It does not change stock
resources, expand capacity or modify EXE/DLL files. It is separate from frozen
Subaru; simultaneous Subaru+Lancer would require an already qualified second
T2 slot, which SCALE1 did not establish through human runtime evidence.

From this repository, to start the candidate **yourself**:

```powershell
$candidate = (Resolve-Path '.research-output/vehicles/vlancer3/final-candidate').Path
& "$candidate/launcher/mr-runtime-launcher.exe" --integrated 'D:/Game/Master Rallye/MRallye.exe' "$candidate/runtime"
```

Use its own disposable state. Test Vehicle Select, race/AI, Results and return
to frontend, reflections on/off. Wheel placement and physics tuning remain a
later phase. No game launch was performed during this work.

## Reproduce / use another user-supplied GT4 car

1. Supply your own immutable CAR4/menu/race and wheel resources plus original
   DBT/IDI files. Copy/edit `lancer-source-profile.json`: change model code/hashes,
   original labels, selected model/LOD/callback policy and addon identity.
2. Build into a new private destination:

```powershell
python tools/build_gt4_vehicle.py --source-root 'D:/your/extracted' --profile 'your-profile.json' --donor 'D:/your/stock/Navara' --output '.research-output/your-candidate'
python tools/preview_vehicle.py '.research-output/your-candidate/assets/complete.dx'
python tools/validate_gt4_vehicle.py --source-root 'D:/your/extracted' --profile 'your-profile.json' --donor 'D:/your/stock/Navara' --candidate '.research-output/your-candidate' --output '.research-output/your-validation.json'
```

3. `prepare_gt4_addon.py` connects the candidate to the existing SDK project/UI
   builder. Build/verify via `mrtool addon project-build`, `runtime-prepare`,
   `runtime-verify` and `runtime-launcher-build`, using your own pinned retail
   inputs and the existing qualified layout. Never promote experimental capacity
   profiles to runtime-qualified automatically.
4. Inspect source reports before accepting a different car. Unknown VIF cycles,
   formats, palette variations, callbacks, blend/test states and layouts fail
   explicitly or remain unsupported source records; this is an admitted GT4
   grammar, not a claim to support every GT4 effect/model without qualification.

Original models, textures, CORE/ELF and captures stay private in ignored output.
The source-review archive contains only own SDK source, documentation and tests.
No extracted assets are committed, bundled in that archive, published or pushed.
