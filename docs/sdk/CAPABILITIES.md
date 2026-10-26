# Rally Workshop capability inventory

Current update: Audio Import 2.0 / optional GT Audio Source Adapter, 26 October 2026.
See [audio results](AUDIO_IMPORT2_RESULTS.md) and the completed
[Physics/Camera milestone](PHYSICS_CAMERA_RESULTS.md). New gameplay/listening is pending.

| Audio Import 2.0 / GT source capability | Implemented boundary |
| --- | --- |
| Ordinary import | Existing PCM WAV decoder; optional local ffmpeg/ffprobe for qualified FLAC, MP3, Ogg Vorbis/Opus and additional PCM/float WAV. No GT ownership dependency. Source ≤30 s/64 MiB; native interval 0.1–4 s |
| Pre-Apply review | Decoded source excerpt vs exact existing-compiler native WAV, waveform/Play/Stop, trim/forward-loop/gain/DC/crossfade, hashes/levels/seam/saturation diagnostics. Settings revisions invalidate stale results; clipping rejects conversion |
| Layer/preset ownership | Four qualified independent layer sources; shared PCM retains per-layer origins; existing response controls, native IDs/namespace, history/reopen, named/rebound/visual-version presets preserved |
| Optional GT source adapter | Read-only Lab catalog/source parsing, exact IDs and verified GT4 model-code joins, shared IDs/tuning variants, record/RPM/loop/source hashes, explicit sample/rate/target assignment. GT3 short mesh-code association unsupported |
| Event evidence | Qualified GT3 native leaf and GT4 comparative anchor pitch; static turbine2/turbine/b_off routes. GT4 drivetrain consumer evidence retained; acoustic identity, exact Beta/CORE pairing and original runtime envelopes remain unqualified |
| Unsupported records | Missing GT4 shift_change program15 and fourteen unsupported INST entries explicitly refused; no replacement/synthesis. GT engine remains a selected single-loop MR adaptation, not multi-band playback |
| Qualification | 894 tests / one optional skip; real Windows import/source/preset/build, six local media variants, 24 INST/107 entries, five independent 1/1/1/1/4 WAV builds with unchanged native patch bytes; original/stock/SDK regressions preserved |
| Native boundary | Existing DSP/hooks/voice lifetime and stock passthrough unchanged. Offline near-listener sums can clip; DirectSound, game timing, real loudness and listening remain owner gates |

| Physics / Camera / Presentation | Implemented boundary |
| --- | --- |
| Physics Studio | Searchable grouped typed addon initialization editor; 173 Lancer rows, 33 schema-qualified retail reference families; source/current/reference, units/guards/pins, compatible group copy, independent family; no live solver or stock physics editor |
| Gameplay Camera | Source-qualified CarID/family/model-SHA follow half-length and height extents, source/changed Z/Y diagram, reset/history/build; separate from orbit/UI cameras; no FOV/smoothing/replay or CarID0 support |
| Vehicle Details | Addon manufacturer/model/combined/Results ASCII labels and project description; conservative SDK text budgets; native IDs, families, namespaces and stock labels locked |
| Friendly texture aliases | Metadata-only, source-hash association, search alias/native, original-resource inspection, history/reopen and compatible version replay; shared atlas roles remain explicit |
| Generate Vehicle Art | Existing bounded CPU DX/DXT renderer plus mr-native-v1; frontend or qualified assembled race rest pose; yaw/pitch/padding; independent 128×128 / 32×16 generation, compare, explicit Apply, pinned inputs and exact single-pass native bank compilation |
| Build/recovery | Shared Core/GUI/CLI, Save/Undo/Redo/Restore/Validate/isolated Build; separate physics-only, camera-only and combined candidates; no installed-resource edits |
| Cross-module | Original models and all four audio layers/presets retained; new visual versions replay authoring layers without baking them into Restore defaults; camera/art requalification conflicts reported |
| Qualification | 862 tests / 1 optional skip; actual Windows GUI, D3D9 regression, native x86 camera/name/audio checks and exact resource differences. New candidate gameplay remains pending |

| V-SDK4B.1 capability | Implemented boundary |
| --- | --- |
| Authentic Classic stage | Exact-hash Lancer pilot: approved radial cover reduction, explicit regenerated livery, stock-derived opaque recessed wheel and qualified MR paint material adaptation |
| Source integrity / version graph | Independent Source Fidelity and Classic projects; rebuilding always resolves the immutable import; no repeated lossy pass |
| Import / rebuild | CLI initialization style flag and real Studio Rebuild as Classic entry call the same Core stage |
| Build approval | Generated report and GPU preview before exact-report SHA approval; pending or changed report rejects Classic builds |
| Manual layers | Exact-compatible active texture/surface overrides reapply; incompatible selectors/atlases are conflicts; all old snapshots and parent remain available |
| Texture plan | Separate opaque/cutout paint, exact cutout alpha, retained decal dimensions, measured closure/cache budget; no universal atlas repacker |
| Evidence | 846 tests /1 optional skip; Windows Core/GUI/GPU, sealed alternate candidates and native CPU damage replay; gameplay pending |
| Generalization boundary | Explicit user-editable recipe; stock references private/local; unknown surfaces retained; no automatic all-car decimation/logo recognition |

## Historical V-SDK4B foundation

| V-SDK4B capability | Implemented boundary |
| --- | --- |
| Appearance profiles | Three editable per-project snapshots; source bytes immutable; switch/save/reopen/history/restore |
| Qualified paint | Exact-size hash-pinned masks and named RGB presets; source luminance and alpha preserved; no automatic logo classifier |
| Classic MR Style | Explicit local stock catalogue and native Binding v2; full shared-owner impact; mixed opacity rejected; environment-only opt-in resize |
| Crew Inspector | Existing source-qualified MR crew, component identity, bounded XYZ/yaw, compare/reset/build; no new rigs or animation claims |
| Comparison/help | Matched fixed GPU views, difference, edited resources, delayed hints and offline F1 topics |
| Ownership continuation | Exact unchanged mechanics and shadow footprint checks before dependent model-hash rebinding; no physics/hub/shadow tuning |
| Evidence | 837 tests / 1 optional skip; Windows addon/stock/Classic builds, history and original invariants; see VSDK4B_RESULTS.md and REGRESSION_MATRIX.md |

## Historical V-SDK4C.1 inventory

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
| Subaru broken glass | UV-only continuation of repaired V-SDK4C model, adapted repeating MR art; four logical zones unchanged; owner accepted in supplied Master Plan v4.7, scoped to tested Subaru candidate |
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


## V-SDK4D Audio Studio

Four independent editable source layers for qualified custom-audio addons. Shared
Core GUI/CLI import/assignment, existing WAV compiler and native audio architecture;
source/output hashes, PCM metadata, peak/RMS, loop warnings and clipping rejection.
Named presets with explicit CarID/namespace rebind, source pins, Source/Classic
version persistence, Save/Undo/Redo/Restore/Validate/isolated Build. Native x86
engine DSP plus continuous authored supplemental response audition: Mute/Solo,
RPM steps, drive/coast/neutral, spool/release/BOV, WAV and event diagnostics.

Lancer A–E builds change exactly the selected 1/1/1/1/4 WAVs. Real Windows dialogs,
controls, GPU regressions and native CPU lifecycle/isolation replay pass. Stock
audio authoring, arbitrary GT multi-bank playback and MP3/OGG/FLAC are unsupported.
Engine disabling is audition-only. Spool disable keeps its estimator with zero
audible gain. No physical boost/throttle sensor is claimed. DirectSound/spatial
mixing and actual gameplay listening remain owner tests. No native hook rewrite,
physics/camera/visual changes or roster expansion.
