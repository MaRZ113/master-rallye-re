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

805 tests/one skip in the complete Windows checkout; texture_viewer test checks exact1:1, global fractional mapping, alpha-edge contamination, source immutability, output budget and icon sizes. Private `vsdk4a1/zoom-windows/validation.json` records seven zooms/two windows/four source classes and56 actual captures. `vsdk4a1/ui-controls-final.json` exercises existing four-family GUI features. Original/current image comparison remains distinct from gameplay material qualification.
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

