# Vehicle Presentation checks

| Check | Evidence under `.research-output/vehicles/presentation/` | Boundary |
|---|---|---|
| Full synthetic suite | phase-tests-final-state.log:923 tests,2 prior fixture skips | Current Windows checkout |
| Actual Studio | windows-delivery/validation.json | Tk/D3D9; not D3D8 |
| Original/static target ABI | native-delivered.json | Actual original + generated x86, typed service seams |
| Results identity | results-native.json | Delivered string consumer, record unchanged |
| Separate name/framing builds | candidate-differences.json; n/f-validation.json |313 immutable resources identical, save separate |
| Same-config determinism | candidate-differences.json | Metadata/payload/image reproducible |
| Materials/audio/physics/art | regressions/; native-*.json | Full qualified Windows tools and native audio CPU checks |
| Native presentation | Owner checklist in VEHICLE_PRESENTATION_RESULTS.md | PENDING_OWNER |

---
# Gameplay Camera 2.0 checks

| Check | Evidence | Boundary |
|---|---|---|
| Full suite | camera2/phase-tests.log:916 tests /2 pre-existing optional skips | Windows Python checkout |
| Source dispatcher/projection | Original4B8170,4F2350,5D681F instructions | Source-matched CPU, not live game |
| Mode isolation/ABI | native-delivered.json:80 delivered-payload cases | Name/Broker/bounds typed seams |
| Five vehicles | native-model-matrix.json:5×80 parameter +5×6 Fixed cases;25 GPU views | Pajero/Trooper separate29 rosters |
| Live GUI | windows-phase/validation.json; source/modified, numeric/drag/wheel, same PID, captures/history/reopen | Actual Tk/D3D9 |
| Accepted resource preservation | candidate-differences.json:313 immutable matches; prefix129440 bytes identical | Fresh root save separately accounted |
| Determinism/originals | preservation.json | Exact EXE/DLL/SMA hashes; repeated same-config derivations |
| Other modules | regressions/windows-regressions.json plus Physics/Camera matched-baseline result | Actual Windows tools; D3D8 new cameras pending |

Prior Heritage Trooper gameplay gates are now owner-confirmed (v6.1): geometry,
wheels, physics, lamps/glass, audio, art, finish and re-entry. Camera2.0 remains
a distinct owner gameplay gate.

---

# MR Heritage Garage regression matrix

27 October 2026. See [results](HERITAGE_GARAGE_RESULTS.md).

| Check | Result / private evidence | Boundary |
|---|---|---|
| Complete synthetic suite | tests-final.log:910 tests /2 existing optional skips | No private assets in fixtures |
| Edition/source qualification | edition-catalog-qualified.json; source pins |33 Demo folders /26 retail families, not playable counts |
| Native prefix/GXI mapping | direct upgrader, exact local GXI pairs, synthetic orientation/CRC tests | Unsupported revisions fail closed |
| Source surfaces/collision | native-feature-validation.json | All1911 intact/off triangles; added40 alternative-state triangles |
| Reindexed wheel rest pose | wheel-rest-pose.json |3 independent parts;8.94e-8m, not live suspension |
| Studio Heritage workflow | windows-delivery/validation.json and actual captures | Inspect/Preview/Create/Configure/Validate/Build; history/reopen/Restore |
| Determinism and build diffs | offline-acceptance.json |101 author files; two native derivations; zero sealed resource differences |
| Roster and native package | final-roster-validation.json |313 resources;185 frozen resources, player/AI gameplay pending |
| Original source/original game | offline-acceptance.json |60 Demo snapshot files, original EXE/DLL/SMAs, clean R-DEMO worktree |
| Save seeding | offline-acceptance.json |Byte-identical root PlayerState copy, no fabricated unlocks |
| Cross-module Windows suite | regressions/windows-regressions.json |Audio/Paint/Crew/reference/zoom/material/stock/Physics/Camera/art |
| Native audio | native-engine/sfx/multi/failures.json |ABI, lifecycle, stock and failures; devices/inputs mocked |
| Shadow arithmetic | shadow-native-three-models.json |4 models ×58 controlled native cases, no new gameplay claim |
| Slot research | class-helper-emulation.json + ignored REA snapshot |Original12; hypothetical13/16; production count guard unchanged |

Evidence root: `.research-output/vehicles/heritage/`. An initially mismatched
Physics regression baseline was corrected to the same Source Fidelity/Pajero
roster; the original failure remains recorded. Regression-only runtime leaves
are quarantined after validation. Owner D3D8 checklist remains pending.

---

# Game Camera Lab regression matrix

26 October 2026. See [results](GAME_CAMERA_LAB_RESULTS.md).

| Check | Evidence | Boundary |
|---|---|---|
| Full synthetic suite | camera-lab/tests-release.log:901 /2 optional skips | Not game/device proof |
| Original pose/basis and actual models | native-static-pose-matrix.json, real-projects.json |16 controlled cases +4 resource pairs; flat first update |
| Shadow Studio | shadow-gui/validation.json, shadow-native-three-models.json | Real GUI and3×58 native cases; gameplay pending |
| Delivered camera-only adapter | native-camera-guard.json |18 ABI/guard cases, live ownership pending |
| Marker candidate emission | native-marker-roster.json | Exact CarID28 RGBA arguments, typed constructor seams mocked |
| Camera/marker GUI | windows-release/windows-validation.json | Actual Save/history/reset/reopen/captures; D3D8 pending |
| Independent candidates | candidate-differences.json, t/*/roster-validation.json |369 sealed resources identical; native data isolated |
| Mutable save / sealed assets | save-integrity.json | Native verifier accepts save edit, rejects changed DXT |
| Audio lifetime/ABI/stock/failures | native-engine/sfx/multi/failures.json | Original code + typed device/services, listening pending |
| Windows existing modules | regressions/windows-regressions.json | Audio/Paint/Crew/stock-reference/25–400% texture viewer |
| Material/binding/reflection/stock | ../gcm/gui-validation.json | Real GPU editing, isolated builds, zero-edit Restore |
| Physics/camera/names/art | ../gcp/windows-validation.json | Real GUI/build and exact resource changes, no handling claim |

Evidence root `.research-output/vehicles/camera-lab/` unless noted. Regression-only
runtime leaves are moved to quarantine after validation; reports/sources retained.

---

# Vehicle Fidelity regression results

26 October 2026: see [Vehicle Fidelity results](VEHICLE_FIDELITY_RESULTS.md).
Shadow Studio, MR tyre/glass pilot, source-paint policy and responsive action UI
are implemented. Owner-approved Classic report ff0925d6... is built alongside
Source Fidelity and Custom shadow. Three isolated 30-entry packages/preflights
pass; 894 synthetic tests / two documented missing private-fixture skips.
Actual Windows style/shadow/audio/paint/stock-reference/texture/DPI checks and
native CPU replay pass. Gameplay/D3D8/mixed-monitor DPI remain owner gates.
Unchanged Physics/Camera is not claimed as a newly rerun complete GUI build matrix.
Prior history below is preserved. No push/publication or next milestone.

---

 Audio Import 2.0 / optional GT source adapter — 26 October 2026

Evidence `.research-output/vehicles/audio-import2/`; details in
[AUDIO_IMPORT2_RESULTS.md](AUDIO_IMPORT2_RESULTS.md). Gameplay listening pending.

| Check | Evidence/result | Boundary |
| --- | --- | --- |
| Full checkout | 894 tests, one optional fixture skip; reviewed Lab30 plus new import/ownership/origin tests | No GT/MR assets in synthetic fixtures |
| Ordinary decoder | WAV, FLAC, MP3, Vorbis, Opus, float WAV96k stereo; installed FFmpeg8.0.1; originals unchanged | Optional external decoding, 30 s/64 MiB guards; native interval0.1–4 s |
| Pre-Apply review | Real Windows waveform/source/native playback, gain invalidation, stale worker-result rejection, exact compiler/hash checks | Windows playback calls, not game listening |
| Per-layer ownership | Real Engine/Whine/Spool/BOV assignment and preset/reopen/reset; disabled layer replacement preserves disable state | Existing qualified response defaults required |
| Source association | Live mits0015/ENGINE1605/Sound22601, shared11 rows; alternate tuning selection and eight RPM bands | Default turbo3 candidate is static, historical build pairing unresolved |
| GT3 source |244 CAR /1215 member catalog and qualified b_off native leaf route | No sb0097 CAR inference or full repeated span audit |
| INST/unsupported |24 banks/107 records/93 PCM/14 unsupported; missing shift_change program15 refuses | No silent synthesis/replacement; no exact acoustic identity claim |
| Isolated A–E |1/1/1/1/4 named WAV differences; sealed native validation and identical patch bytes | No model/UI/physics/camera/other-vehicle changes |
| Native safety | Original engine ABI, two interleaved owners, stock fallback, re-entry, RX/RW and three allocation failures | Broker/device calls mocked, gameplay pending |
| Cross-module/versions | Physics/camera/names/aliases/art intact; RPM edit retains GT preset; Source/Classic layer origins preserved | No baked source author defaults |
| Windows preservation | Repeated Material/stock builds, legacy Audio, full Physics/Camera, Paint/Crew, Classic, stock browser,56 texture zoom captures | D3D9/offline, not D3D8 |
| Protected inputs |736 accepted resource hashes; EXE/DLL/retail/installed SMA and clean independent Lab worktree | Private assets excluded from source archive |
| Mix diagnostics | Scripted near-listener all-layer audition reports2747 clipped samples | No hidden normalization; not proof of actual game clipping or loudness |

---

# Physics & Camera / Vehicle Presentation — 26 October 2026

Private evidence root: `.research-output/vehicles/pcstudio/`. See
[implementation/results](PHYSICS_CAMERA_RESULTS.md). Existing phase evidence
below remains historical. Actual new-candidate D3D8 gameplay is pending.

| Check | Result / evidence | Boundary |
| --- | --- | --- |
| Complete Windows checkout | 862 tests / one optional skip, 47.458 s; eight new generated-fixture tests | Optional absent fixture not converted into a pass |
| Physics GUI | 173 typed rows, 33 source families; mass/RPM/reference group edit, reject guards, history and reopen | Initialization profiles, not live simulation; no stock physics authoring |
| Physics isolation | 1320→1386 kg; only LancerEvo4/Chassis/TotalMass differs in vehicles.xml | Deliberate mass demonstration, not fitment/handling retuning |
| Camera GUI/build | Exact CarID28/family/car SHA, source/extents overlay, Reset/Undo/Redo; zero game-resource changes | Follow extents, no direct distance/FOV/replay controls |
| Native camera | 18 original-x86 target/model/stock/unknown-slot/missing-Broker cases | Typed services stubbed; no dynamic game camera proof |
| Names and aliases | Native display literals/Results; two real shared atlas aliases; search/history/reopen | Native filenames/IDs/families fixed; ASCII SDK budgets, unknown screen-width limits |
| Art | Both native dimensions, frontend/race presentation, deterministic rerender, independent role Apply, full input pins, exact composer output | Approximate CPU diffuse; stock bank-frame replacement unsupported |
| Combined GUI Build | Exactly vehicles.xml + Lancer carsheet033/smallcarsheet031 frames changed | Models/audio/other vehicle resources byte-identical; owner gameplay pending |
| Save/recovery/versions | Scoped and global Restore/Undo, reopening, real Source/Classic layers, customized audio preset retained | New camera/art require source requalification; no lossy output reused as import |
| Material / stock regression | Actual Windows selected RGB, Binding v2, reflection, addon/stock candidates and zero stock overrides after Restore | D3D9 and package validation, not D3D8 |
| Audio regression | Four source imports, presets, five auditions; engine/owner/reentry/stock passthrough and three allocation-failure native replays | DirectSound device and listening pending |
| Appearance regression | Paint/Crew, stock material browser, Classic GUI and 30 diagnostic captures, deterministic conversion/native damage | No new Classic approval or visual tuning |
| Texture Viewer | 4 images × 7 zooms × 2 windows; BGRA/PNG unchanged | Display-only captures |
| Preservation | 736 accepted Source/Classic resources, previous five audio candidates, EXE/DLL/retail/installed SMA hashes rechecked | Private sealed resources excluded from archive |

---

# V-SDK3.1 / V-SDK4A regression and acceptance matrix

Evidence root: `.research-output/vehicles/vsdk3/`. Private captures/candidates
are not shipped in the source archive. Final commands/results are recorded in
the delivery report; failed intermediate GUI runs remain private diagnostics.

Current phase roots: `.research-output/vehicles/vsdk31/` (792 tests, one skip,
four-family fixed-camera assembly/texture checks) and
`.research-output/vehicles/vsdk4a/` (full regression, GUI build and preservation
evidence). See `VSDK4A_RESULTS.md` for final run names and boundaries.

| New check | Evidence / acceptance | Boundary |
| --- | --- | --- |
| Subaru mirrored wheels | Reverse winding on negative determinant; six fixed camera poses with unchanged staged vertex/index hashes | Frozen runtime DX is not edited |
| Lancer source assembly | Original wheel SHA matches; 87 body draws show zero frame translation | Original GT4 rest pose, not settled MR suspension |
| Pajero raw/assembled | Raw source has no references to wheel resource textures; profile adds four separate instances | No authentic geometry is stripped |
| Stock wheels | Original Megane resource culling/UV/render smoke and outside/inside views | Unqualified wheel anchors stay unavailable, manual preview explicit |
| Image inspection | Actual 1024×256 texture, alpha/RGBA, fit/actual/zoom/pan, detached-window capture | No generated texture included in source archive |
| Selected-surface editing | Stock and addon real GUI pick/Save/Validate/Build/Restore; before/after captures; textures unchanged | Source-draw RGB, not masked texture repaint |
| Shared vertex ownership | Conflicting draw set rejects RGB edit; unknown shader/slot fields read-only | Conservative fallback is explicitly confirmed whole-texture edit |
| Persistence | Reopen, Undo/Redo, restore, original author layers composed via source SHA pins | No game resources edited in place |
| Material preservation | Only selected RGB ranges/qualified env bit allowed; alpha/normals/UV/topology/collision retained | Owner validates damage/glass/brakes/reflections in MR |
| Candidate isolation | Resource manifests, native payload, EXE/DLL hashes, stock zero-edit rebuild | Not gameplay confirmation |

| Area | Automated / visual check | Runtime boundary |
| --- | --- | --- |
| Prior tree | Precommit778 synthetic tests,1 skip;43 local phase commits | No historical intermediate revision reconstruction |
| Workshop core | Synthetic source preservation, additive PNG edit contract, alpha, row orientation, invalid parameters, drift, undo/reopen/restore, stock changed-only, resource-only non-installability | No game launch |
| Windows GUI | Actual Tk buttons/dialogs and background SDK operations for one addon and one stock vehicle | Native GUI behavior, not MR gameplay |
| Visible edits | GPU capture differs after edit; original capture restored byte-for-byte | D3D9 diagnostic renderer |
| Builds | GUI compiles author resources and complete sealed external candidate; launcher verification/environment/allocation preflights | User still tests race/menu/AI/re-entry |
| Stock identity | Qualified Megane18/Pajero1 core; zero-edit/restore emits zero overrides; one selected resource changes | No unlock/class/AI/save identity edits |
| Navigation | Native Windows messages exercise orbit, MMB pan, zoom, F3, focus/pick, bookmarks, reload and presets | Not native gameplay camera calculations |
| Renderer regressions | Existing generated asymmetry/UV/culling/glass-depth GPU smoke suite | World lighting/fog/sorting remain approximations |
| Baselines | Compare GUI candidate to input candidate: unchanged DX/wheels, UI/audio/physics/native payload; only chosen DXT differs | Repeated gameplay must be checked by owner |
| Original files | EXE, graphics DLL, source project/resource/archive hashes | Original retail files are never output destinations |
| Privacy | Local build/preview files ignored; source archive excludes retail/GT models/textures/audio/icons and compiled artifacts | No push/publication |

## Owner acceptance checklist

1. Launch Rally Workshop; select a stock/addon project or import one using GUI
   file pickers. Verify status/provenance, Race/Frontend/Wheel views and real
   material/texture fields.
2. Open interactive3D; drag MMB, orbit/zoom, geometric pick, F/Home, F3,
   Ctrl1–6 bookmark/Shift1–6 recall. Verify highlight and texture inspection.
3. Apply a clearly visible whole-texture edit (including baked content warning),
   Save, Validate, Build. Launch the generated candidate yourself.
4. Restore texture/all, reopen the project and rebuild. Confirm stock/addon
   identity and unrelated cars remain intact.
5. Exercise actual game reflections, damage/glass, lights, audio, camera modes,
   UI, AI, finish/Results/re-entry. Prior qualification does not automatically
   cover each newly edited candidate.

Do not mark native gameplay acceptance from the GUI harness or GPU smoke output.

## V-SDK4A.1

805 tests/one skip in the complete Windows checkout; texture_viewer test checks exact1:1, global fractional mapping, alpha-edge contamination, source immutability, output budget and icon sizes. Private `vsdk4a1/zoom-windows-delivery/validation.json` records seven zooms/two windows/four source classes and56 actual captures. `vsdk4a1/ui-controls-final.json` exercises existing four-family GUI features. Original/current image comparison remains distinct from gameplay material qualification.
# V-SDK4C material/Help regression

## Release evidence

`vsdk4c/tests-release.txt`: **814 tests, 1 skip, PASS**. Native glass synthetic
tests cover full triangle accounting, missing/duplicate ownership rejection,
case orientation, collision suffix, deterministic output, untouched unrelated
draws, absent/invalid preview states and rejection of unknown/stock repair targets.
Original-instruction switch and deformation replay PASS; 64 real D3D9 comparative
captures PASS. 368 candidate resources: only Subaru race car.dx differs; native
extension, native patch operations and addon plan identical to the qualified
three-car baseline. Actual gameplay and collision-trigger classification PENDING.

810 synthetic Windows tests / 1 optional skip. Existing shared texture used by
an additional selected draw: native descriptor byte isolation, untouched image,
Save/reopen, Undo/Redo/Restore and asset inclusion via actual addon and stock
candidate builds PASS. Restore stock emits zero overrides. Aliased descriptors,
unsupported slots, alpha changes, path traversal and missing resources reject.
Offline Help locale fallback/search data, visible controls and real Tk capture
PASS. Gameplay remains an owner test. See VSDK4A2_RESULTS.md.



## V-SDK4C.1 — 26 October2026 (current)

| Gate | Evidence | Result |
| --- | --- | --- |
| Complete Windows synthetic suite | vsdk4c1/tests-final.txt | 822 PASS / 1 optional skip |
| Native viewer build and controls | application-build.json; stock/addon-controls.json | MSVC build; real key events, cull state and label roundtrips PASS |
| Binding v2 | test_texture_binding; gui-binding/gui-validation.json | Variable names/resolution, alpha/state guards, structural receipts; actual stock/addon save/reopen/build/history PASS |
| Reflection strength | test_surface_authoring; gui-reflection/gui-validation.json | Opaque source-relative weight, texture invariance, stock/addon visible GPU change and zero-edit restore PASS |
| 2D viewer preservation | zoom-windows-delivery/validation.json | 56 fresh Windows captures, exact source bytes, seven scales and both windows PASS |
| Picker raster | picker-full-preview.png; picker-preview-evidence.json | Actual mapped Tk popup with rendered image, counts and compact list PASS |
| GT4 source/determinism | pajero-final-source-validation.json | Original relocated Beta hashes, reconstruction/rebuild/DX/DXT semantics PASS |
| Culling/housing/material views | pajero-final-visibility/validation.json | 64 fixed-camera CW/CCW/NONE/mask/env captures; GPU inspection only |
| Subaru continuation | glass-validation/validation.json | 64 captures, broken-UV-only ownership, native switch and unchanged deformation CPU replay PASS |
| Pajero damage/brakes | pajero-native-damage.json; pajero-native-brake-validation.json | Original CPU replay, coverage alpha, native alternatives PASS |
| Candidate isolation | candidate-preservation.json | Pajero 2 DX +1 new DXT only; Subaru car.dx only; other resources and originals unchanged, known user saves excluded |
| Roster/cache/preflight | both candidate validation.json; candidate-preservation.json | Resource/environment/native allocation PASS; bounded synthetic race LRU zero warm evictions, not FPS |
| Actual MR gameplay | Owner checklist in VSDK4C1_RESULTS.md | PENDING: visibility, damaged reflections, collision routing and re-entry |

Earlier equal-name-length/dimension/alpha restrictions describe the superseded
V-SDK4C writer. Later tests retain rejection of unknown shader/stage activation,
paths, aliased descriptors and switch-owned uncoordinated light/glass edits.


## V-SDK4B — current evidence

Private root `.research-output/vehicles/vsdk4b/`. This table supersedes older
PENDING entries only where the supplied owner v4.7 explicitly accepts Subaru
glass / Pajero appearance. New appearance candidates remain gameplay-pending.

| Check | Evidence | Result / boundary |
| --- | --- | --- |
| Paint/profile/crew Core | test_appearance_authoring; tests-final.txt | 837 tests / 1 optional skip; masks/alpha/rows/pins, profiles/reopen/history, batch crew transactions and exact shared compiler PASS |
| Dependency continuation | visual_fitment / vehicle_shadow tests | Reject selected mechanics or footprint changes; only exact unchanged ownership re-pinned |
| Actual Windows appearance | gui-final/validation.json | Two real GUI/GPU edited candidates, named colours, history, save/reopen PASS |
| Classic MR Style | style-gui/validation.json | Actual native picker/browser/complete impact dialog, environment adaptation and isolated build PASS |
| Old binding/stock restore | regression-binding/gui-validation.json | Pajero/stock actions and zero-edit restored stock build PASS |
| Texture inspection | zoom-windows-delivery/validation.json | 56 embedded/detached captures, seven scales, alpha/RGBA/pixel/anchor/source-byte guards PASS |
| Native controls | native-controls-lancer.json; native-controls-stock.json | Actual pick/focus/orbit/pan/bookmarks/reload/culling and material-mode controls PASS |
| Resource preservation | preservation.json | Original EXE/DLL, frozen families, physics/audio/UI/wheels/mechanics and shadow parameters PASS |
| Owner gameplay | VSDK4B_RESULTS.md checklist | PENDING for new colour/reference/crew edits; offline evidence is not gameplay |

Scope limits: partial explicitly masked paint regions, civilian-style colour
exercise on a stock rally vehicle, existing static crew only, envelope diagnostics
rather than triangle collision, no global texture matching or diffuse UV repair.

## V-SDK4B.1 — actual Classic pilot

Private evidence: `.research-output/vehicles/vsdk4b1/`. Owner approval of the
final Previewer/report permits building; it is not gameplay acceptance.

| Check | Evidence | Result / boundary |
| --- | --- | --- |
| Full complete-checkout suite | regression-final.log; test_classic_style.py | 846 tests, 1 optional skip; previous Subaru/Pajero/SDK paths retained |
| Stock ranges / frozen reference | stock-reference.json; references/ | 21 read-only ordinary stock families, per-class ranges; frozen Subaru data; real native diagnostic views |
| Body / rim / livery | qualification-final/validation.json | Exact contour, 48→16 covers, 537→162 rim, explicit regenerated red/charcoal livery; fixed slots; no global decimator |
| Determinism / source restoration | qualification-final/validation.json; windows-classic-final2/validation.json | Two byte-identical Core runs/reports; independent source baseline and GUI dropdown/reopen |
| Ownership / alpha / lights | qualification-final/validation.json | Every unaffected draw, tyre, collision, logical lamp case and protected cutout alpha preserved |
| Original damage instructions | qualification-final/validation.json native_damage | 0 split position groups; 0 protected alpha losses with bridge, 41 without; same native positions/RGB/ABI; offline CPU only |
| Actual new Studio workflow | windows-classic-final2/ | Real Rebuild button, native GPU comparison, report dialog, pending-build gate, independent versions |
| Existing GUI build / restore | w/gui-validation.json | Real targeted addon/stock edit, binding, reflection, Undo/Redo and zero-edit restored stock candidates |
| Paint / crew | paint-win/validation.json | Actual Windows paint masks, names, crew correction, save/reopen, builds and history |
| Manual reference catalogue | reference-gui02/validation.json | Custom reference layer, actual picker/browser/impact warning and matched GPU views; no implicit Classic conversion |
| Texture / native controls | zoom-windows-delivery/validation.json; references/controls-*.json | Seven scales, RGB/RGBA/Alpha, pixel/anchor/pan; actual native pick/focus/presets/reload/culling controls |
| Isolated bundles | roster-sf-validation.json; roster-cl-validation.json; preservation.json | Qualified 30-entry composition; only 12 Lancer-family paths differ; physics/audio/UI/other vehicles exact |
| Owner gameplay | VSDK4B1_RESULTS.md | PENDING: D3D8 brightness/reflections/damage/brakes, AI, re-entry and live loading |

The first long-name build hit MSVC FTK1011; unchanged source/build logic passed
with short `sf` /`cl` output names. An old locked Previewer remains untouched;
tests use the actual hash-named new executable from application-build.json.


## V-SDK4D — Audio Studio acceptance

Evidence root `.research-output/vehicles/vsdk4d/`; see VSDK4D_RESULTS.md.

| Check | Evidence | Boundary |
|---|---|---|
| Four source replacements, responses, presets, Undo/Redo/Restore and reopen | `win-release/windows-validation.json`, actual import/picker/panel/audition captures | Windows Tk/native DSP; listening pending |
| A/B/C/D single-layer and E combined candidate isolation | `t/matrix.json`, five `t/*/roster-validation.json` | Exact WAV-only resource-root differences; no live race |
| Engine source CarID/stock passthrough | `native-engine-28.json` | Original x86 instructions + typed seam stubs |
| SFX ABI/protected memory, stock optional ownership, gain curve, lifecycle and map stress | `native-sfx.json` | 28 replay cases, 10001 gain cases, original DS COM paths with device mocks |
| Multi-owner SFX/BOV isolation, survivor, cleanup, reentry | `native-multi.json` | 24 voices freed; no device/player/AI gameplay claim |
| Engine/Whine/Spool/BOV/mix/coast/neutral signal reports | `audition-final/*.json` | All seven zero mixed clipping; scripted load, not actual throttle/boost |
| Scoped materials/binding/reflection and stock restoration builds | `reg/gui-validation.json` | Actual Windows actions and sealed addon/stock candidates |
| Paint/Crew | `paint-reg2/validation.json` | Actual GUI/GPU in private clones |
| Source/Classic rebuild, approval gate and navigation | `style-reg/validation.json` | Actual Windows, no new owner approval inferred |
| Texture viewer | `zoom-reg/validation.json` | Embedded/detached, 25–400%, RGB/RGBA/Alpha, pixel mode and pan/anchor |
| Local stock reference browser/binding impact | `reference-reg/validation.json` | Actual GUI/GPU, no additional runtime copies |
| Existing game/roster/retail protection | `preservation.json` | Original EXE/DLL, accepted sf/cl manifests, original author and resource hashes |
| Full qualified checkout tests | `tests-release.log` | Synthetic/CPU tests; optional fixture skip explicitly counted |

Source Fidelity vs Classic gameplay and new audio listening remain separately
PENDING_OWNER. No V4E/Blender Bridge work or capacity expansion.
