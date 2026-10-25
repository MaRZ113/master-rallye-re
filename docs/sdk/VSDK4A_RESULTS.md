# V-SDK3.1 → V-SDK4A delivery

25 October 2026 · `research/vehicles` · working changes based on
`2a42ee769b5a2f014fbe414f6eea11bbe4afe3d7`. **No new commit or push.**

Run **`Rally-Workshop.cmd`** from the checkout root. The local native Previewer
has been rebuilt. A fresh source checkout requires Python with Tk and the existing
CMake/MSVC toolchain: `python tools/build_rally_workshop.py`.

## 1. V-SDK3.1 stabilization completed first

The owner reported successful PNG replacement; that workflow and the graphite/
amber application architecture are retained. Before V-SDK4A extension, the
stabilization tree passed **792 tests, one skipped**, with actual Windows captures.

### Wheel diagnosis

- Subaru frontend recovery proves four repeated wheel parts and 16 matching body
  translations. Two wheel transforms have negative determinant. Staging previously
  transformed positions/normals but retained the original winding, hiding outward
  faces under CW culling. The fix reverses triangle order for reflected instances
  only. Original DX, UVs, normals and game wheel resources are not rewritten.
- A controlled reproduction of the old staged index order changes **31,068 pixel
  bytes** at the affected +40° view with CW culling. With culling disabled, before/
  after captures are **identical**, including the opposite view. This isolates the
  issue to winding/culling, not camera-dependent wheel movement or texture editing.
- Six fixed camera angles for Subaru, Lancer, Pajero and stock Megane preserve the
  staged scene bytes throughout orbit. Reports identify source DX hashes, instance
  transforms, draw IDs, centers, vertex/index hashes and determinant signs.
- Pajero's raw race body references none of the wheel resource textures. Its four
  visible race-preview wheels come from the explicit preview profile. They are now
  separately staged, not removed from the source. Raw Race hides injected wheels
  and attachments; Assembled Race shows them. Exact embedded-four-wheel matches
  suppress extra assembly where that source structure can be proven.
- Lancer's qualified GT4 profile is compatible with the current source frame: its
  wheel file matches, and **87 matched body draws have zero translation** against
  the profile's source build. This is source rest pose, not settled MR suspension.
- Wheel presets1/2 inspect outside/inside. The camera uses dominant axial source
  normals; ambiguity retains the generic camera and is reported. The outside rim
  face was visually checked for all four fixture families. There is no global
  wheel-mesh reversal. The inside of a source wheel can legitimately be a dark cap.

### Inspection and preview authoring

Texture Studio now provides a resizable image canvas, detached window, fit/1:1,
zoom/pan/scroll, checkerboard, RGB/RGBA/Alpha and Original/current comparison.
Real 1024×256 imported texture captures demonstrate full-size inspection.
Only viewport crops are scaled; no persistent full-resolution display duplicates
are generated. Native FEED BGRA rows/alpha and the existing upright PNG convention
are preserved. Window/split dimensions persist in private workspace settings.

Wheel Fitment edits four provenance-bearing preview poses: source-order wheel
selection with +Z-front/+X-left display labels, XYZ, yaw and scale; save/reload,
source reset and explicit manual configuration. Unknown anchors are not guessed.
Preview metadata does **not** modify DX, collision, suspension, physics or build
resources. Manual identity poses are clearly unqualified and initially overlap.

## 2. Exact V-SDK4A functionality matrix

| Function | Delivered status | Qualification / limit |
| --- | --- | --- |
| Hierarchical inspector | WINDOWS-VERIFIED | Model → native group → physical draw → material → texture slot. Exact IDs and source states; unnamed groups stay unclassified |
| Picking/highlight | WINDOWS-VERIFIED | Real geometric ray selection and native wire highlight; source identifiers stay linked across wheel instances. Alpha texels are not sampled |
| Selected-surface RGB | OFFLINE/WINDOWS-VERIFIED | Native **vertex diffuse RGB**, through the existing attribute writer. Alpha, UVs, topology, collision and texture bytes remain unchanged. Refuses disabled color streams or shared vertices |
| Environment pass | OFFLINE-VERIFIED | Disable/restore an existing source-qualified environment bit through the same writer; no arbitrary reflective material creation. Owner must qualify edited appearance in MR |
| Texture-slot assignment | READ-ONLY | Inspect exact bindings; this editor does not qualify resource allocation/length-changing reassignment or expose a fake shader selector |
| Alpha/depth/unknown flags | READ-ONLY | Explanations preserve damage/reflection ownership; no speculative glass state edits |
| Image channels and A/B | WINDOWS-VERIFIED | Detached/embedded image controls, Original/current, RGB/RGBA/Alpha. Original GPU comparison uses the center capture; live native window remains edited |
| Texture usage/impact | WINDOWS-VERIFIED | Complete scrollable model/draw/slot user list. Whole-image edits require explicit confirmation and record affected users |
| Targeted edit vs atlas tint | DISTINCT | Surface RGB changes selected draw vertices, not a shared texture. Baked logos on that draw are also modulated; no semantic paint mask is claimed |
| Shared-vertex conflict | FAIL-CLOSED | Explains conflicting draw IDs. Conservative fallback is the existing explicitly confirmed whole-texture operation, never silently labelled selective |
| Persistence/history | OFFLINE/WINDOWS-VERIFIED | Save/reopen, Undo/Redo/Restore; source-hash-pinned attribute layers compose with existing addon authoring. Legacy V-SDK3 texture history remains readable |
| Stock/addon builds | OFFLINE/WINDOWS-VERIFIED | Shared SDK build services; qualified stock Megane18/Pajero1 only. Generic resource-family export does not register a CarID |
| Gameplay fidelity | OWNER CHECK REQUIRED | GUI/GPU/package acceptance is not MR gameplay validation |

## 3. Real end-to-end demonstrations

Actual Tk controls and native SDK builds were exercised; only file-picker
answers were supplied by the harness. No compiler, resource or renderer mock.

| Demo | Selected source | Visible GPU change | Candidate resource change |
| --- | --- | --- | --- |
| Pajero addon | `complete.dx`, physical draw63 | 13,162 pixel bytes | 84 RGB bytes in `DataGx/Vehicles/SdkPajero85/complete.dx` |
| Stock Megane | `complete.dx`, physical draw1 | 66,477 pixel bytes | 1,506 RGB bytes in the COW `DataGx/Vehicles/Megane/complete.dx` override |

All bytes outside the selected vertices' RGB ranges remain identical. **All DXT
resources, alpha bytes and draw/material records remain identical.** The demo is
frontend-variant scoped; it does not silently apply a matching race draw edit.

For both projects the test uses Save, Validate, actual candidate Build, reopen,
Undo, Redo and Restore. Undo/Restore reproduce the original GPU image byte-for-byte;
Redo reproduces the edited image. A third build after stock Restore emits **zero
stock overrides**. Snapshotted recipes remain reproducible after GUI Restore.

### Private candidate launchers

- Addon edit: `.research-output/workshop-builds/e649f95c0e39/candidate/Launch-SDK-Roster.cmd`.
- Stock edit: `.research-output/workshop-builds/801e0afd14a9/candidate/Launch-SDK-Roster.cmd`.
- Restored stock: `.research-output/workshop-builds/8185dba791e8/candidate/Launch-SDK-Roster.cmd`.

These intentionally visible edits are demonstration candidates, not replacements
for the frozen visual milestones. The test projects were restored afterwards.
Existing owner library projects are retained.

## 4. Evidence and regression boundaries

Private evidence roots, excluded from source archives:

| Evidence | Path |
| --- | --- |
| Stabilization regression | `.research-output/vehicles/vsdk31/tests.txt` |
| Four-family wheel poses / source hashes / saved preview | `vsdk31/wheel-validation.json`, `lancer-body-frame.json` |
| Controlled winding/cull experiment | `vsdk31/cull-evidence.json`, `cull-pixel-comparison.json` |
| Texture and wheel views | `vsdk31/large-texture-alpha.png`, `large-texture-rgba.png`, `wheel-outside-inside-contact.png` |
| Current full suite | `.research-output/vehicles/vsdk4a/tests-release.txt`: **799 tests, one skipped** |
| Real GUI surface builds/history | `vsdk4a/gui-history-final/gui-validation.json`, before/after BMPs and GUI PNGs |
| Four-family final controls / read-only fields | `vsdk4a/ui-controls-final.json`, `studio-final.png` |
| GPU UV/culling/glass-depth/reflection/brake checks | `vsdk4a/gpu-final/validation.json` |
| Native input/navigation/reload | `vsdk4a/navigation-final.json` |
| Reusable preview-check tool run | `vsdk4a/preview-tool-final/wheel-validation.json` |
| Source-reproduced candidate and byte ownership | `vsdk4a/candidate-preservation.json` |

All `vsdk31/...` and `vsdk4a/...` short paths above are relative to
`.research-output/vehicles/`. The GUI report's historical status string mentions
two builds; its action log records the third zero-edit build too.

Candidate audits reproduce the sealed bundles, compare immutable resources with
the original roster, and prove identical native payload. Player-state files and
the already-qualified mutable options file are excluded from immutable-resource
comparisons; this does not weaken launcher checks or asset ownership.

Original executable SHA256 remains
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`;
graphics DLL remains
`eb7ea3d9501b514bff668f1e75e86041906c5fe4e8afa89f06d658751429aaf4`.
UI, audio, physics, race wheels, crew, brake/damage structures and PERF2 native
hooks are unchanged. No new live gameplay performance measurement is claimed.

## 5. Reproduce and owner acceptance

```powershell
python tools/build_rally_workshop.py
.\Rally-Workshop.cmd
$env:PYTHONPATH='src;tools;.;tests/synthetic;.research-output/vehicles/scale1/python-tools'
python -m unittest discover -s tests/synthetic
```

The recorded Windows regression environment uses Python3.15/Tk9, the established
MSVC toolchain and existing local native-analysis dependencies. The final path
entry above exposes the existing optional Rabbitizer binary for instruction
checks; it is not a Workshop application dependency or part of the source archive.
The GUI itself adds no pip framework requirement.

1. Open a private project. In Race compare the assembly checkbox; in Wheel use
   presets1/2. Open Wheel Fitment, change a preview pose, save/reopen and reset.
2. Select a physical draw in Inspect / Texture. Read its capability explanation,
   set RGB, apply, Save/Validate/Build. Disabled/unknown fields remain read-only.
3. In Texture Studio inspect every shared user, detach the image, compare Original,
   inspect Alpha and test a local same-size PNG. Confirm whole-image impact only
   when intended. Test Undo/Redo and Restore before further builds.
4. Launch demonstration candidates yourself; check frontend and race, damage/glass,
   reflections on/off, lamps, audio, camera, AI, finish/Results/re-entry and unrelated
   vehicles. Surface demos intentionally modify frontend only. Original-game tests
   remain necessary even though package/native payload preservation passed.

Reproducible diagnostic tools accept explicit private inputs:
`tools/validate_workshop_preview.py --library ... --viewer ... --output ...` and
`tools/validate_rally_workshop.py --surface` with the existing addon/roster/retail
input arguments. No retail/GT resource ships with these tools or the archive.

V-SDK4B/V-SDK4C, semantic masks/Classic MR Style, glass damage, Blender/geometry,
scale/fit authoring, Physics/Audio/Camera Studio and Fleet Builder remain deferred.
