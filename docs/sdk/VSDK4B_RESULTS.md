# V-SDK4B — Paint, Classic MR Style and Crew Inspector

Branch: `research/vehicles`. Baseline: `9a0b167` / `63f56cb` (V-SDK4C.1).
Owner Master Plan v4.7 is preserved in MASTER_PLAN.md. Its acceptance of the
previous Subaru glass and Pajero appearance checks closes those specific owner
gates; it does not qualify every version, capacity or this new appearance phase.

## Delivered functionality

| Capability | Actual scope |
| --- | --- |
| Source Fidelity / Classic MR Style / Custom | Three editable per-project recipe snapshots, automatic outgoing save, switch/reopen/history/restore; original DX/DXT immutable. Crew corrections are separate. Classic starts from source, with explicit assignments rather than heuristic shader matching. |
| Paint Studio | Named explicit hash-pinned PNG regions, RGB byte presets and user-named colours. Luminance-preserving masked tint; exact source alpha and zero-mask pixels retained. The existing whole-image multiplier stays distinctly labelled. |
| Paint qualification | Exact texture dimensions/PNG orientation, opaque greyscale masks, provenance and immutable mask hashes. Invisible-only blended decal masks rejected. No automatic semantic/logo classifier is claimed. |
| Stock material references | Local read-only model/draw/slot catalogue with hashes, dimensions, alpha and native semantics. Exact compatibility check across ALL shared owners and a complete impact dialog before private image replacement. |
| Texture Binding v2 | Existing structural assignment picker retained. Explicit owned environment reassignment precedes stock transfer when the original image also belongs to glass. Unknown/special stages remain protected. |
| UV / resolution | Diffuse transfer requires matching dimensions; native UVs unchanged. Opaque environment-only premultiplied LANCZOS resizing is explicitly opt-in and logged. No automatic diffuse UV repair. |
| Crew Inspector | Existing stock MR driver/co-driver, exact model/vertex/draw identity, component roles, XYZ/yaw relative to rest pose, reset/highlight/compare/build. Exact converter report qualification or explicit source-pinned preset import. |
| Crew limits | Static imported seated pose stays static. No new rigs, skeletons, animation implementation, arbitrary character injection or runtime hide toggles. Control records, UVs, alpha, draw ordering and collision remain unchanged. |
| Clipping diagnostics | Bounds and optional qualified cockpit-envelope warnings. No automatic seat/roof triangle-intersection guarantee. |
| Comparison | Actual native D3D9 Original/Modified captures with the same fixed camera/assembly and amplified difference; edited-resource list, delayed hints and offline F1 Help. Interactive bookmarks/navigation remain in the Previewer. |

### Conservative shared-texture fallback

Stock reference transfer replaces a project's existing owned image. It does not
silently clone a shared atlas or claim a private per-draw image. Every affected
draw is shown. A mixed opacity/reflection use fails closed. The author can bind a
compatible independent existing image explicitly or decline. This restriction is
intentional: native texture rebinding does not imply semantic paint ownership.

## Real input demonstrations

Private evidence: `.research-output/vehicles/vsdk4b/`.

* **Lancer paint:** original opaque body atlas `gt4-ad685e510aa08e4ace49-tga`,
  1024×256, explicitly inspected undecorated white strips only. Separate sponsor
  overlays and the black/red livery region remain untouched. Initial investigation
  rejected a transparent decal-atlas choice: changing invisible background RGB
  was not accepted as visible paint. The corrected mask produces a measured GPU
  difference and retains source alpha/dimensions. This is partial qualified panel
  authoring, not complete automatic repaint of every Lancer panel.
* **Stock/plain-colour exercise:** Megane `sbshade16-tga`, 16×16, an inspected
  undecorated blue shaded panel. It exercises civilian-style plain-colour
  authoring while keeping all sponsor/light/glass images unchanged. Megane is
  still a rally prototype; no separate civilian model was imported or qualified.
  A very conservative BF logo-protection mask was also investigated, but its
  insignificant visible coverage was not used as the successful demonstration.
* **Classic MR Style:** actual local Megane `whitepaint-tga` reflection reference,
  explicit opaque target bindings in race/frontend, opt-in 64→32 environment
  resizing. Lancer's original shared image also serves blended draws and cannot
  be replaced globally; the existing independent opaque image is selected through
  Binding v2. Glass, wheel resources and other environment images remain intact.
* **Crew:** exact V-LANCER6 converter output hashes qualify 326 driver and 292
  co-driver vertices. Harnesses and helmet brow/shell batches are included.
  A deliberately small driver −15 mm Y correction demonstrates actual resource
  authoring in both variants; it is not a newly claimed ideal seat fit. Co-driver
  remains at the accepted baseline position.

## Safe dependent-profile continuation

Appearance editing exposed legitimate source-hash dependencies in Lancer's
mechanical attachments and shadow profile. They remain strict at the build gate.

`rebase_unchanged_mechanics` first verifies the original pin, topology, collision,
every selected record byte and every selected position/normal/colour/UV. Only
then can it pin an unrelated body/crew edit. The original profile is saved
immutably; hub coordinates, attachment policy and physics parameters do not change.

`rebase_unchanged_footprint` checks the exact original shadow pin, unchanged XZ
footprint and byte-identical native bounds after the existing mechanical builder.
Only its model hash changes. Shadow texture, scale, margins and offsets remain
unchanged. A changed footprint or selected brake component is rejected.

## Validation evidence

| Evidence | Meaning |
| --- | --- |
| `tests-final.txt` | 837 tests PASS, 1 optional skip; includes 15 new paint/profile/crew/hash-rebase/publication tests. |
| `gui-final/validation.json` | Real Windows widgets, workers and GPU; addon/stock painting, profiles, named colour, history, exact reopen and TWO sealed candidate builds. |
| `style-gui/validation.json` | Actual Binding v2 picker, local-stock browser, complete shared-impact dialog, explicit environment adaptation, comparison and Classic candidate build. |
| `regression-binding/gui-validation.json` | Existing Pajero/stock binding/save/build/restore workflow, including zero-edit stock rebuild. |
| `zoom-windows/validation.json` | Seven zoom factors, embedded/detached, RGB/RGBA/alpha/pixel/cursor mapping and immutable source bytes. |
| `native-controls-*.json` | Native picking, orbit/pan/zoom, bookmarks, reload/camera retention, focus, model/preset/layer controls and actual cull-state checks. |
| `preservation.json` | Original EXE/DLL and untouched roster-family hashes, unchanged physics/audio/UI/wheels/mechanics and shadow parameters; expected appearance deltas enumerated. |

Full-suite runs reproduced Windows `WinError 5` during temporary author-project
publication, while the focused test passed. A bounded Windows access/sharing-error
retry now preserves atomic publication and refuses an existing destination. Its
retry/no-overwrite test and the complete 837-test suite pass. The exact external
lock owner was not established; failed logs remain private evidence, not hidden.
Early GUI runs also caught the invisible-mask and dependent-hash failures above.

No offline result is promoted to new gameplay qualification. The native Previewer
remains a fixed-function D3D9 approximation. The main GUI harness inherits a Race
mode for its stock step; Megane's unqualified automatic race wheel assembly is
explicitly empty, rather than guessed. Use its Frontend mode to inspect its
complete stock vehicle. Neither stock DX nor wheel fitment is changed by this.

## Open and reproduce

Run root `Rally-Workshop.cmd` (or rebuild with `python tools/build_rally_workshop.py`).
The private phase launcher `Launch-VSDK4B-Workshop.cmd` opens the prepared Lancer
and Megane examples with their local masks/profiles. Those assets stay private.
Open an SDK author project or create a qualified stock copy. Select Custom,
inspect texture usage, import a qualified mask, choose colour, compare, Save,
Validate and Build. Use the Classic profile and explicit stock reference workflow
for selected material adaptation. Crew Inspector accepts the original matching
converter ledger; unknown model revisions are read-only until qualified.

Core interfaces: `paint_authoring.masked_paint`,
`crew_authoring.qualify_converted_crew/apply_crew_fit`, existing surface and texture
binding writers; Workshop is a service client. `vehicle_project.crew_layer` makes
the same corrections reproducible in CLI builds. Source inputs and proprietary
images/meshes are not bundled in archives.

## Owner gameplay checklist and candidates

1. `gui-final/addon-build/candidate/Launch-SDK-Roster.cmd`: Lancer partial blue
   panel paint and driver correction; inspect both sides, source logos, crew,
   reflections on/off, damage, brake lights, wheels and race re-entry.
2. `style-gui/build/candidate/Launch-SDK-Roster.cmd`: separately qualified offline
   Classic reference/binding recipe; inspect reflection transitions and glass.
3. `gui-final/stock-build/candidate/Launch-SDK-Roster.cmd`: stock Megane private
   panel-colour override. Confirm the small panel difference and unchanged logos.

These paths are relative to the private phase evidence root above. Candidates
are isolated and use existing qualified roster IDs, physics, audio and UI. Prior
Subaru/Pajero baselines are preserved. No capacity expansion, physics/ride-height
tuning, Blender/scale, Audio/Camera GUI, new glass behavior or Fleet Builder was
started. No push/publication or old-runtime deletion was performed.
