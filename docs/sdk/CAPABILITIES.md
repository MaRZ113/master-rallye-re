# Rally Workshop capability inventory

Current update: V-SDK4C.1, 26 October2026. See [phase results](VSDK4C1_RESULTS.md).
These current entries supersede historical restrictions below. Gameplay remains
an explicit owner acceptance gate, separate from Windows/offline validation.

| Current capability | Status / boundary |
| --- | --- |
| Texture Binding v2 | Implemented: variable-length owned diffuse references and existing opaque env slot; different power-of-two dimensions; material-specific alpha checks; exact semantic/suffix guards |
| Practical picker | Compatible-first, search/filter/counts, compact statuses and large independent texture view; original pixels remain unchanged |
| Reflection Strength | Implemented source-relative weight for independent opaque environment vertices; blend/test/shared/special families read-only; save/build/history tested |
| Reflection mask and controls | D mask mode; F3 current K/W/E/B/D/Z/C/A, layer/model controls; permanent F1 hint; NONE warning; stock/addon native key-state tests |
| GT4 cull-disabled surfaces | Opt-in explicit reverse geometry and normals; default unchanged; no global MR culling change |
| GT4 layered frame material | Explicit source selection; unity-opacity footprint plus alpha-only/environment correspondence; translucent residual preserved |
| Headlamp housing | Owner-approved actual-aperture contour loft; explicit MR approximation, no AABB protruding walls |
| Subaru broken glass | UV-only continuation of repaired V-SDK4C model, adapted repeating MR art; four logical zones unchanged; actual collision routing pending |
| Regression | 822 tests / 1 optional skip; Windows addon/stock builds, history/zero-edit restore, 128 final matrix captures, native CPU replay and sealed candidates PASS |

## Historical V-SDK3.1 / V-SDK4A audit

The following table records the earlier milestone, not current restrictions.
[Master Plan](MASTER_PLAN.md).

| Capability | Existing callable backend / interface | Studio status and boundary |
| --- | --- | --- |
| Selected-surface RGB | `surface_authoring.surface_capabilities/apply_surface_edits`, existing `r4e_writer.patch_dx_attributes`; `WorkshopProject.edit_surface` | Real physical draw vertex RGB. Rejects shared vertices/disabled color stream. Alpha, texture image, UVs, collision and topology unchanged. Baked content on that draw is modulated; not semantic paint |
| Environment assignment | Same writer, `disable_reflection` recipe | Only disable/restore a source-qualified existing environment pass; cannot add arbitrary reflection shaders. Edited native appearance still needs owner gameplay testing |
| Hierarchical inspector | Parsed model → native group → physical draw → material → texture slot | Stable source IDs, core offsets, exact states; unnamed groups remain unclassified. Texture bindings and unknown/native alpha-depth flags are read-only with reasons |
| Texture inspection | `workshop.texture_view.TextureView`, existing FEED/PNG codecs | Resize-aware, detached view, fit/1:1/zoom/pan, RGBA/RGB/Alpha, checkerboard and original/current switch. Scaled images are viewport crops, no persistent high-resolution duplicates |
| Texture impact | `WorkshopProject.texture_usage` | Complete scrollable model/draw/slot usage list; whole-image edit asks impact confirmation and records users. No silent semantic atlas selection |
| Raw/Assembled Race | Native `--raw-race`, A toggle, GUI checkbox; staged wheel model kind5 | Raw shows only car resource; assembled adds provenance-bearing wheel/attachment instances. Exact embedded-instance matches suppress duplicates; unfamiliar baked geometry is never removed |
| Preview wheel fitting | `preview_profile/save_preview_profile` | Four source/manual transforms, named XYZ-side/axle convention, translation/yaw/scale, source reset and saved reload. Preview-only; no physics edits or automatic arch placement |
| Preview orientation repair | `stage_vehicle` determinant/winding correction | Negative determinant reverses staged triangle order, normals use inverse transpose. Source DX/UV unchanged; fixed-camera four-family checks |
| Surface persistence | Shared VehicleProject `surface_layers`, Workshop undo/redo/state | Hash-pinned post-conversion attribute layers preserve existing source authoring. Stock COW still uses its pinned resource ownership; zero-edit restoration produces no overrides |
| Project open/save/restore | `workshop.service.WorkshopProject.create/save/restore/undo` | Real private working project, pinned baseline and content-addressed texture layers; JSON persists edits/history |
| Addon authoring | `VehicleProject.load`, `validate_vehicle`, `addon_sdk.project.build_project` | Reused; GUI RGB/PNG edits use existing `texture_edits` contract; no converter rewrite |
| Full addon candidate | `build_sdk_roster.derive/build/verify`, through Workshop service | Existing qualified roster candidate must contain one matching author entry; build includes existing launcher preflights |
| Stock authoring | `stock_project.create/build/restore/validated_overrides` | Qualified retail Pajero/1 and Megane/18 only; changed DX/DXT ownership and source pins remain enforced |
| Source family inspection | `WorkshopProject.create(kind='family')` | User-supplied converted DX/DXT; asset-only build explicitly NOT an installed new CarID |
| MR mesh/material inspection | `parse_dx_bytes`, `MaterialSemantics.from_draw` | Actual physical draw IDs, groups, flags, texture slots and interpreted semantics; no MatN guesses |
| Texture RGB/PNG override | Existing DXT/PNG codecs, `WorkshopProject.tint/replace_png` | Whole-image multiplier preserves alpha; same-size PNG uses supplied alpha. Not a masked repaint tool; baked lettering may change |
| Viewport | `preview_scene.stage_vehicle`, Win32/D3D9 Previewer | Managed standalone interactive window; center panel is a labelled real GPU capture. No unsafe SetParent/device embedding |
| Navigation/debug | Native Previewer event handlers | Orbit, MMB pan/focus, wheel zoom, selected-draw F, Home, presets, persisted bookmarks, F3 real data/FPS |
| Material picking | Native geometry ray tests + owned-process selection channel | Amber wire highlight, inspector selection. Geometric picking ignores alpha texels/culling; not pixel-perfect shader picking |
| Hot reload | Existing Previewer exporter and atomic Workshop outputs | Separate capture/interactive scene files; unchanged assets skipped; short file-lock retries; view focus retained |
| Physics/audio/camera profiles | Existing `physics_profile`, `audio_profile`, `camera_profile` + native adapters | Preserved in author project/build; dedicated editing UI deferred. No new native fields exposed |
| GT3/GT4 conversion | Existing qualified source adapters/converter CLI | Existing converted project opening supported. Raw-source import wizard deferred; input assets remain optional/local |
| Future modules | `workshop.adapters`, project `extensions` metadata | Reserved panes/masks/transforms/audio/adapters metadata, no native execution. GUI lists limits instead of inert editing controls |

Build outputs use short SDK-owned `.research-output/workshop-builds/<job>`
directories: the deeply nested GUI project path made MSVC compiler detection
fail, whereas the same bundle compiled in a short control directory. The proven
runtime launcher API/behavior was retained. Inputs remain in the project.

## Evidence vocabulary

- Previous SCALE1 capacity, Lancer handling/audio/materials and import milestones
  retain their individually recorded owner gameplay evidence; no new blanket
  roster gameplay qualification is inferred.
- User's V-SDK3 request reports visible per-vehicle camera changes and Pajero
  rear brake illumination. Exact executable capture hashes were not provided;
  follow/replay/split/teardown coverage remains separately bounded.
- Studio tests and GPU captures are offline/Windows application evidence. They
  cannot prove actual MR material, damage or game-camera fidelity.
- Source formats are enumerated in `workshop.adapters.FORMATS`; unknown input
  is rejected by the established parser/decoder, not silently converted.

## Deferred scope

Broken Subaru glass remains owner-observed, cause unknown. No glass repair,
Classic MR Style, semantic masked recoloring, geometry round-trip, scale/fit,
new physics tuning, audio/camera editing GUI, new CarID expansion or fourth
import is included. Existing CLI workflows remain available. V-SDK4A is the
current bounded milestone; V-SDK4B/V-SDK4C and later phases are not started.

## V-SDK4A.1 display/identity update

Filtered Pillow LANCZOS/bicubic resampling with premultiplied alpha replaces integer Tk scaling. Exact1:1/optional nearest, cursor anchoring, bounded viewport and RGB/RGBA/Alpha are Windows-tested; source data is unchanged. Original SVG and multi-resolution ICO are distributable CC0 artwork; Tk/native icons and explicit Tk taskbar identity are implemented. See VSDK4A1_RESULTS.md. V-SDK4C follows by explicit owner authorization; later Paint Studio remains deferred.
# V-SDK4C material/Help additions

## V-SDK4C native glass qualification

Source-audited four-zone native intact/broken ownership repair IMPLEMENTED as an
opt-in source-hash-pinned profile. Subaru experimental candidate prepared; actual
owner collisions remain PENDING. Native getter/setter/front increment verified
with original x86 CPU replay. No independent third shattered stage claimed.
Preview profile `glass_states` selects named source cases for diagnosis; it does
not simulate impacts. Stock/GT4 imported baselines remain unchanged.
See VSDK4C_RESULTS.md for precise boundaries and reproduction.

Existing diffuse-slot assignment: IMPLEMENTED, bounded equal-name-length /
format / dimensions / alpha subset. Unknown states and environment slots are
read-only. Native per-draw persistence, Undo/Redo/Restore, shared compiler and
isolated stock/addon builds verified in Windows. Offline searchable Help, F1
and Material/Texture context help implemented. See VSDK4A2_RESULTS.md.

