# Master Rallye Vehicle SDK — Master Plan / Rally Workshop

**Working baseline:** 26 October 2026 (revision 4.8: qualified V-SDK4B.1 Classic Lancer pilot; owner gameplay review pending; historical sections retained)
**Repository:** `master-rallye-re-vehicles` · **branch:** `research/vehicles`  
**Purpose:** single living specification for development, review, acceptance and public beta planning.  
**Status disclaimer:** this document summarizes previous source-review discussions and reported gameplay tests. It is **not** a new repository or binary audit; verify each item against the current checkout before implementation. Update the ledger after every development phase.


> **HISTORICAL DECISION — 2026-10-26 / revision 4.7:** The owner reports successful in-game tests of the V-SDK4C.1 fixes: Subaru glass now breaks correctly, and Pajero's visual corrections are accepted. This supersedes the pending owner gate in sections 19–20 without erasing those earlier reports. **V-SDK4B Paint Studio / Classic MR Style / Crew Fitment is the next active milestone.** Full Audio Studio remains a required product feature and gets an explicit four-layer user-replacement acceptance gate below. No D3D9 preview or automated test alone is proof of native gameplay parity.


## 0. Product contract

**Vision:** a Windows-oriented, free Vehicle SDK / **Rally Workshop** for creating new cars and editing stock Master Rallye (2001) vehicles without hand-editing native resources. A user should be able to open a car, examine its in-game-like appearance, edit materials/textures/geometry/physics/audio/cameras, validate, build, test and revert.

**Core principles**

1. Original `MRallye.exe`, existing graphics `d3d8.dll`, and retail files on disk remain unchanged. Use the qualified external runtime and reversible, isolated resource overlays.
2. **Stock car edit** and **new CarID addon** are distinct installation types, managed by one project model and Studio UI.
3. Every transformation is non-destructive, reproducible, testable, and traceable to input resources and configuration. Immutable input + editable layer(s) + generated output.
4. GT3/GT4 resource extraction is optional and local. Never include/distribute proprietary models, textures, audio, icons or game binaries. User-created/licensed assets also work.
5. `Randomizer & AI Extender` remains a separate project; no unapproved integration.
6. **Owner-authorized local commits after each completed and validated phase** (with clear scope and passing tests); existing earlier phase commits are retained. Never push, release or publish without separate explicit authorization. Do not reconstruct fictitious intermediate historical snapshots. No claims of in-game verification based solely on synthetic tests.
7. Features that are not supported by the verified Master Rallye engine must be marked as **approximation / unsupported**, not silently simulated or advertised as native.
8. **GUI must be an actual working editor** calling existing SDK services, not a disconnected mockup or a rewrite of the proven conversion pipeline.
9. Source authenticity and target style are **independent authoring choices**. Preserve an untouched GT/MR source reference, plus optional author-edited texture/material/paint/scale layers; no destructive automatic "style conversions".
10. Preserve the distinctions between **source model proportions**, **rendered model scale**, **physical wheel/contact/collision dimensions**, **camera framing**, and **native damage behavior**. A scale operation must disclose what it changes and verify the affected systems.
11. Source and target formats are managed through a **capability-tested adapter registry**. Advertise only tested input/version/feature combinations. Unknown formats and semantics must fail with useful diagnostics, not silently degrade.

## 1. Verification vocabulary

- **GAMEPLAY-VERIFIED:** user launched the exact relevant candidate and reported the described result. Specify candidate ID and test conditions.
- **OFFLINE-VERIFIED:** automated tests or deterministic binary/asset checks passed; runtime behavior remains unconfirmed.
- **IMPLEMENTED-UNQUALIFIED:** code exists but cross-vehicle or native game behavior needs testing.
- **RESEARCHED:** formats/addresses/behavior partially mapped; production feature not built.
- **PLANNED:** scope agreed, no verified implementation.
- **DEFERRED:** deliberately outside current release, or subject to new research.

At release time, maintain both per-feature and per-car statuses, plus a test evidence path. Never upgrade a status without evidence.

## 2. Capability and gap ledger

| Area | Existing achievement / evidence | Remaining gap / next acceptance |
|---|---|---|
| GT3 import | Subaru Impreza Prototype visual import, wheels, materials, lights, UI; first reference baseline `V-MESH4.13` | Document supported GT3 source profiles; generic extraction diagnostics and non-Subaru regression |
| GT4 import | Mitsubishi Evo IV (`mits0015`) and GT4 Pajero imported; Lancer geometry/materials/crew/damage/light pipeline; GT4 Beta source adapter | Ensure another GT4 source with different topology can be imported through the shared path; flag unhandled source effects, version differences and supported LODs |
| Vehicle registry | Extra CarIDs and per-class slots; SCALE1 configurations with **29 and 30 cars gameplay-verified** in the reported tests, including race loading, AI, finish and re-entry | Qualify the **specific combined production roster** of real Subaru, Evo and Pajero; maximum total/per-class capacity remains unknown |
| Multi-addon builds | V-SDK1 combined-resource construction, CarID reservation, conflict checks, UI composition and experimental independent audio/hook composition | Full native regression on combined current candidates; one project must never reset another's resources or audio actor state |
| Model output | `car.dx`, `complete.dx`, `wheel.dx` + per-vehicle DXT, structural validation, source traceability | Expose editing and rebuild services to UI without hardcoded donor/source assumptions |
| MR materials | Conversion rules, paint reflection zoning, glass/decal, diffuse-alpha/reflection/damage interplay, brake glow, native damage mitigation | Interactive selectable Material Inspector, per-group/source-to-MR diagnostics, editor/undo, native material capability warnings |
| MR Previewer | Working Win32/D3D9 standalone viewer with race/frontend models; rendering close enough to diagnose many issues | **Middle mouse pan** + orbit/zoom/focus, material picking, selectable debug overlay, bookmarks, layer toggles; calibrate known D3D9-vs-D3D8 differences |
| Textures | DX/DXT read/write, PNG/other user inputs, CarSheet/smallcarsheet generation; PERF2 fixes DXT loading bottleneck; adaptive source-fidelity options developing | Texture Browser/Replace/Restore, alpha and UV previews, resolution and memory-cost warnings, hot reload, non-destructive override layers |
| Frontend performance | User reports near-instant model selection after PERF2; source analysis identified pathological small-chunk texture reads | Instrument reproducible cold/warm/re-entry timings; verify no cache leaks/stale resources at scale |
| Wheels and fitment | Stock-informed rim shelf, new rim texture rules, GT4 wheel transform, physics wheelbase/track/radius profiles | Unified visual hub/brake disc/wheel assembly editor; statically vs dynamically loaded stance distinction; physical suspension and source geometry fitting |
| Native damage | Corrected GT4 body tearing via compatible opacity/damage handling; Lancer user gameplay report | Automated deformation compatibility warnings on newly edited meshes; stock/addon regressions |
| **Broken/cracked glass** | **User-reported issue on Subaru:** breaking a window can make glass disappear; no systematic native glass-break study or accepted repair yet | Research stock MR intact/cracked/shattered transitions, per-pane state and vertex/texture ownership; implement and validate damage-aware broken-glass layer/state **only as supported by actual engine behavior** |
| **Existing texture reassignment** | V-SDK4A Inspector enumerates draws and native texture slots, resolves associated DXT and permits replacing pixels in existing texture resources; native slot IDs are presently **read-only** | Add verified, draw/slot-scoped **Assign Existing Texture** workflow. Select a DXT already present in the opened project, validate slot semantics and dimensions/UV/alpha/reflection, guard shared native table entries; persist edits, preview, build, undo/restore. Distinguish a slot pointer reassignment from replacing the pixel payload shared by many draws. |
| **Offline user help** | V-SDK3/V-SDK4A has diagnostic labels and tooltips/status text but no complete novice-oriented reference verified | Dedicated local Help/F1 and contextual help for project types, Open/Save/Validate/Build/Undo/Restore, viewport mouse controls, F3 debug, Raw/Assembled Race, wheel fitment, original-vs-edited texture, texture slot reassignment, native D3D9 preview limitations; update help alongside controls. |
| **Classic MR style matching** | Stock MR texture/material resources can be inspected; existing source-fidelity/balanced texture authoring | Optional locally sourced stock-MR material/texture equivalents with UV/scale/alpha adaptation, visual A/B, provenance; no bulk blind swapping |
| **Whole-car scaling** | Native source dimensions/mesh transforms, fitment and camera bounds partially mapped | Non-destructive scale/fit profile, synchronized source↔MR comparison, dimension targets, wheel/crew/light/collision/damage/camera dependency checks; no automatic physics claims |
| **Repainting / base paint** | GT material zoning and color/paint classification partly implemented; no qualified general paint editor | Editable base color and paint masks where source semantics permit, preserve liveries/decals/highlights; refuse unsafe hue shifts across shared atlases |
| **Audio substitution and presets** | Existing engine WAV plus synthesized whine/spool/BOV and per-CarID routing; preview/audition code | User-selected per-layer sound replacement, format conversion/loop analysis, gain/trigger presets, reversible A/B and fallback; never promise GT sample equivalence |
| **Format compatibility** | Known GT3/GT4 local conversion profiles; MR DX/DXT output, optional PNG/WAV authoring inputs; Blender round-trip not qualified | Published per-format/per-version matrix for geometry/material/texture/audio/UI capabilities, importer diagnostics, tested adapters, pluggable future sources, safe unknown handling |
| Lights/effects | Lancer and Subaru brake light features; V-PAJERO3 adds native `blight` case1/case2 switching with a source-qualified GT4 cutout/lens split; owner reports Pajero rear brake lighting works in game | Inspect halo containment/after-damage/re-entry on exact candidate; generalize pane/lens tagging and build Studio controls |
| Crew | Stock driver/co-driver injection for Lancer, per-car transforms | Editor for crew visibility/seat position, named crew source presets, collision/intersection preview where possible |
| Physics profiles | Independent editable `physics-profile.json`, Lancer AWD/engine/suspension profile, ride-reference fix and per-CarID family isolation | **Physics Studio** with parameter provenance, constraints, restore, save versions; safe live/static preview vs actual race data; final user balance remains user-driven |
| Engine audio | Per-CarID custom GT4 engine sound, multivoice whine/turbo spool/BOV architecture and user-confirmed tuned audible sound | **Audio Studio** with audition, per-layer controls, RPM/state visualization, source management, safe multi-addon identity tests |
| Authentic GT audio | Optional research extraction from GT3/GT4, GT4 engine sound sourced; correct whine/spool/BOV samples not fully qualified | Private local sample browser with waveform audition and evidence-backed source mapping; no mandatory proprietary sample |
| Gameplay cameras | V-SDK2 **experimental per-physical-CarID follow-extent override** for Lancer ID28 and stock Megane ID18; owner confirms camera visibly changes on two cars in-game | Validate no cross-car leakage, rear-view/split-screen/replay/re-entry; extend beyond follow extents only after native proof (no qualified per-ID FOV/smoothing/look-at API yet); Camera Studio later |
| Stock vehicle authoring | V-SDK2 copy-on-write stock projects implemented for **qualified Pajero ID1 and Megane ID18**; zero-edit emits no overrides; reversible Megane whitepaint DXT edit built, with no noticeable difference in owner test | Expand verified stock family registry; edit physics/audio/camera via shared typed backends; GUI editing, undo, stock/material visibility A/B, runtime tests |
| Blender | Blender used as separate manual modeling environment | Reliable export/reimport bridge with stable object IDs, material semantics, preserved patches, UV edits, topology-change conflict resolver |
| Packaging/installation | Generated launchable candidates, private output and multi-addon manifests | One-click reversible Build/Test/Install, conflict UI, capacities and save compatibility warnings, rollback/backup and diagnostic bundle export |
| Graphical Studio | Discussed **Rally Workshop** layout | Build working shell, viewport and panels; deliver vertical slices end to end, then complete editors |
| Docs/distribution | Extensive research/phase docs, private asset separation | User guides, onboarding, supported format matrix, testing matrix, privacy/licensing disclaimers, reproducible public asset-free SDK demo |

## 3. Baseline preservation and known bugs

**Freeze and back up** verified versions of Subaru `V-MESH4.13`, Lancer `V-LANCER6` visual plus latest user-approved physics/audio, Pajero `V-PAJERO3` visual/light pass over `V-PAJERO2` / PERF2, and successful SCALE1 29/30 capacity tests. Exact hashes and source commits must be extracted from the real checkout, not invented here.

**Separate low-priority backlog:** V-PAJERO3 replaces a generated four-sided black headlamp housing with a rear-only cap (offline evidence for removing the unilateral protrusion; owner has not specifically qualified that exact front angle). Native rear Brake Glow **is owner-confirmed**; check release/after damage/halo containment under real gameplay. Any later small visual issues should be filed with exact candidate/screenshots and severity, not silently re-open large phases.

**New glass-damage bug report:** user observed on Subaru that after breaking a window, glass disappears rather than leaving an appropriate damaged/cracked state. Record exact model/runtime version, damage action, affected panes and screenshots in a reproducible test. **Do not assume merely adding a decal layer resolves the problem**: first distinguish native global glass-hide behavior, per-pane switches, alpha/material state and geometry ownership. This is **GAMEPLAY-OBSERVED, CAUSE UNKNOWN**, not an implemented fix.

**Known uncertainties:** SCALE1 maximum capacity; full multi-addon roster gameplay with all current GT imports; GT Beta/Online version-specific mappings; full camera-mode coverage (only per-CarID follow extents experimentally implemented); native vs Previewer material parity; native broken-glass behavior; Blender topology round-trip semantics; authenticity of optional GT audio source samples; user saves compatibility. V-PAJERO3 synthetic four-addon texture budget reportedly stays within ~12 KiB of 32 MiB under its assumed world reserve: treat as a **fragile estimate, not measured runtime margin**; protect PERF2 and profile memory use during Studio changes.

## 4. Proposed main window: Rally Workshop

Three-panel layout with resizable docks; default dark graphite UI, restrained amber accents, neutral technical typography.

- **Left:** Vehicle Library (Stock / Addons; T1/T2/T3; search, status, source badge, revisions); optionally scene hierarchy/material list.
- **Center:** always-visible native-resource MR Previewer. Race/Frontend/Stock, material debug overlays, comparison mode, diagnostics.
- **Right:** context Inspector controlled by tabs `Model | Materials | Textures | Physics | Audio | Camera | UI | Build`; contextual subtools include **Glass Damage**, **Paint/Recolor**, **Dimensions/Scale**, **Style Match** and **Format Diagnostics**, without overcrowding top-level navigation.
- **Bottom:** collapsible Problems & Diagnostics, build logs, provenance, undo history, comparison and install health.
- **Top:** project selector, Save, Import/Edit Stock, Preview, Validate, Build & Test; advanced diagnostics toggle.

**Viewport controls**

| Action | Default |
|---|---|
| Orbit around focus | LMB drag on empty viewport |
| Pan camera / move focal point | **MMB drag** |
| Zoom/dolly | Scroll |
| Select material/mesh | LMB click (distinguish click from drag) |
| Focus selected item | `F` |
| Reset camera | `Home` |
| Front/right/top orthographic presets | Numpad 1/3/7 (configurable) |
| Debug overlay modes | `F3` and toolbar |
| Optional free-fly mode | RMB + WASD, provided it does not clash with selection |

Add camera bookmark Save/Recall; mouse sensitivity and invert settings; pan moves camera **and its orbit focus**, so orbit stays centered on the selected inspected region. UI viewport controls are distinct from **per-car gameplay Camera Studio**.

**Overlay tiers**
- Basic: vehicle ID, source, model variant, triangles, draw calls, textures and memory, FPS, current preview mode.
- Materials: hovered/selected mesh and material stable ID, source provenance, texture and UV set, blend/depth/alpha semantics, reflectivity weight, damage ownership, render pass.
- Diagnostic: wheel hubs/brake disc transforms, bounds (raw vs filtered, important for chase camera), crease/normal visibility, transparent layers, LOD and hidden pieces, missing textures, texture-cache/budget and compatibility warnings.
- Explicit banner when D3D9 approximation differs from qualified D3D8 runtime behavior.

## 5. Editor modules and MVP acceptance

### Model Studio
- Open `car.dx`, `complete.dx`, `wheel.dx` from stock or addon; grouped mesh/layer hierarchy, parts/LOD show-hide, materials and texture provenance.
- Stock crew, wheel interiors/rim shelf, lights, decals, shadow bounds, collisions are named semantic components with fallback unclassified groups.
- Side-by-side synchronized Source GT vs MR output and before/after render if available. No forced LOD fusion.
- **Scale/Fit subtool:** preserve source baselines and show real-unit overall dimensions, uniform render scaling and optional verified selective dimension adjustment. Compare overlays against a selected stock MR reference with matched camera/projection; source size, target size and auto-recommended transform must be distinguishable.
- Scale pipeline must inspect/preserve wheel anchors, tire dimensions, brake-disc centers, crew seats, lights, shadow bounds, collision proxies, deformation groups, camera bounds and frontend/race model consistency. Never silently scale physical behavior with visuals. Reject incompatible changes until acknowledged/repaired.
- MVP: select specific source mesh; inspect actual MR output; save/reload a harmless project-level setting without altering original.

### Material Studio
- Click a face/group → see material including alpha semantics; show `Normal`, `Diffuse Alpha`, `Reflection Weight`, `Paint/Non-paint`, `Blend/Depth`, `Material IDs`, `Wireframe`.
- Assign qualified native material types; visibility of effect and debug coverage updates without destructively editing base.
- Warn on reflective continuity across adjacent painted draw groups, glass/decal alpha conflicts, damage/reflection alpha collisions, missing brake switch dependencies.
- **Glass damage inspection:** show intact, cracked and broken/shattered render states where the engine and assets support them. Validate independent pane/material ownership so a break in one window does not wrongly hide unrelated panes; preserve damage-related alpha use and transparency/depth order. New crack textures/geometry are authored as optional derived overlays, not assumed to be sufficient alone.
- **Paint/recolor:** identify truly recolorable base coat versus baked GT source coloration and decal-containing atlas regions; expose color/tint masks and paint material controls only where verified, with undo/A-B and safeguards for logos, glass and shadows.
- MVP: repair a selected **stock** car material and an **addon** material in independent projects; validate builds and restore defaults.

### Texture Studio
- Browser of file name/hash, native DXT wrapper format, source resolution, resized resolution, alpha, UV users and estimated memory budget.
- Import a local PNG (plus BMP/TGA/DDS only as decoder support is qualified), show alpha/UV preview; non-destructive override and Restore.
- **Stock MR texture matching:** browse compatible original textures from the user's own retail install, compare to the imported texture and map candidate native substitutes. Show UV mismatch, transparency, texel density and material expectations, and offer resize/reproject/manual UV repair. Never assume a filename or color resemblance makes textures interchangeable.
- Offer distinct `Source Fidelity`, `Classic MR Style` and `Custom` style profiles. The native-style profile is an **opt-in non-destructive edit recipe**, not an automatic promise to transform every GT asset perfectly; preserve source images and editable user changes.
- Reload Previewer and recompile only changed assets; disclose full rebuild when unavoidable.
- MVP: one stock texture override and one imported car texture replacement with verified references, no damage to shared atlas.

### Glass Damage & Paint / Style workspaces (shared with Materials and Textures)
- **Glass:** independent windshield/side/rear pane IDs; intact/cracked/shattered state audit; source mask/material preservation; authored crack overlay options; native damage trigger mapping; per-pane regression after collisions and frontend↔race parity. Study stock MR behavior before declaring a correct implementation; unknown behavior is flagged.
- **Repaint:** solid-color paint materials and source-baked paint/livery require different workflows. Offer masked tint/recolor that preserves decals, shading and reflections where possible; otherwise provide a texture-edit fallback with explicit warning. Multiple color variants should be author-owned presets, not new hardcoded CarIDs.
- **MR aesthetic profile:** compare imported GT and stock MR car in synchronized 3D framing; selectively replace locally available stock-style materials/textures, normalize shading and optionally dimensions. Always show before/after and keep original source intact.
- **Gate:** a stock car and a GT addon can independently toggle/revert a paint/texture/material change; broken glass is qualified with per-window runtime testing before calling it a native feature.

### Blender Bridge
- Export editable intermediate interchange with persistent IDs and a manifest linking object/material/semantic tags and source DX draw groups; prefer a supported open format with tested Blender importer/exporter rather than assuming FBX/GLB/OBJ guarantee lossless round-trip.
- Reimport modifications: geometry, UV and material reassignment; preserve **author-authored overrides** across future GT source re-conversion via layered changes, not in-place base overwrite.
- Reimport explicit object/scene scaling with a source→target transformation ledger and validation of wheel/crew/collision/damage dependencies; warn if Blender object-unit changes make physical dimensions ambiguous.
- Detect renamed/lost IDs, topology changes, material reordering, reflection/glass/crew/lighting dependencies; ask for remapping rather than guessing on conflicts.
- MVP: export, move one detail, edit UV, add a small piece, reimport and rebuild without losing existing materials/hand adjustments; unchanged round-trip must be visually/structurally equivalent within documented bounds.

### Physics Studio
- Per-CarID stock + addon profiles: mass, CG, drivetrain, engine/torque, gearbox, brakes, tyres, steering, suspension, anti-roll, fitment, collision supported fields.
- Validated units/ranges, original/provenance vs manual values, controlled A/B presets, Undo/Redo and Reset to Original.
- Static wheel/anchor gizmos with warnings: source hubs != dynamic equilibrium != physical collision; no claims of live physics simulation.
- MVP: change a stock value without altering shared donor; independent Subaru/Lancer/Pajero profiles; rebuilding an addon doesn't reset user-tuned settings.

### Audio Studio
- Native engine loop, whine, turbo spool and BOV layers with independent audition/mute/solo, RPM/load approximations and trigger plots; stock tuning fallback.
- Import local user audio, provenance/hash/gain/sample processing, safe voice ownership, resource limits.
- **Per-layer replace/preset workflow:** engine, whine, turbo spool and BOV each offer own `Replace / Audition / Reset to Default`; process loops, fade/crossfade, pitch and triggers independently. Current self-created/synthetic SDK sound layers can be initial demo defaults **after license/source verification**, with user-owned GT extracts as optional local replacements. No GT audio bundled.
- A preset captures chosen files/hashes, per-layer levels, speed/RPM/load response and event settings; a missing audio file produces clear fallback/repair rather than silent playback.
- MVP: stock car audio override + two addons audible concurrently including AI, independent assets, no leakage or crash in race re-entry.

### Camera Studio (in-game)
- Per-CarID/mode native camera height, distance, look-at target, FOV/smoothing **only where supported**. Stock baselines, editable presets, reset.
- Inspect sanitized render/bounds contributors (antenna, spoiler, collision extents) and physical CG coupling; don't infer cause of high camera without runtime evidence.
- Preview has a distinct in-game-camera gizmo and known approximation label.
- MVP: stock sedan, stock off-roader and imported Lancer independent camera changes in-game; no effect on unrelated cars or shared replay modes.

### UI Assets
- Vehicle Select `carsheet` + `smallcarsheet` / race thumbnail, IDs, cropping/framing profiles, icon custom source and GT3 local extraction.
- Automatic conflict-free bank extension and resource mapping for multiple addons; preserve stock records.
- MVP: two/three new cars with unique correctly positioned icons and working race UI simultaneously.

### Format compatibility and import adapters
- Keep a **supported-format registry** with explicit status per product/version (`GT3 source layout`, `GT4 Beta source layout`, other tested GT4 variants, `MR DX/DXT`, intermediate Blender formats, source images, PCM audio, icons). Do not imply one GT4 Beta profile proves every GT4 version.
- For each adapter record: data types handled (geometry/UV/material/LOD/wheels/lights/audio/UI), required user-supplied extractor/decoder and licensing restrictions, validation checks, observed lossiness/fallbacks, round-trip guarantees and example fixtures.
- Multi-stage import diagnostics: **recognize → inspect → preview → convert → validate**. Unsupported/unknown data stays marked unresolved instead of being silently dropped or substituted.
- Future plug-in importers for other games, hand-authored Blender meshes and other open formats are **extension points**, not beta deliverables without tested evidence.

### Build / Install
- Validate → build → launch test → inspect reports; isolated retail resource overlay, no EXE or graphics DLL modification.
- Compatible manifest composition (camera/physics/audio/material/crew/UI), deterministic naming and identity with reserved CarID, collisions/fail-closed validation, safe uninstall/revert.
- Add compatibility warning for existing saves; record project version and source hashes.
- MVP: reinstall/revert stock override + three addons, no conflicts; successful native race complete/re-enter check.

## 6. Main roadmap and stop gates

### COMPLETED FIRST PASS: V-SDK2 / V-PAJERO3 (25 Oct 2026)
- V-SDK2 supplies **per-CarID follow-camera extent experiments**: Lancer ID28 and stock Megane ID18; user reports visible camera change on two cars. This is **not** a complete Camera Studio or a native per-ID FOV/distance/replay API. Preserve selected-ID isolation and continue mode/race re-entry testing.
- V-SDK2 supplies **copy-on-write stock model authoring** for qualified Pajero ID1 and Megane ID18. Zero edits produce zero resources; reversible parsed DX/DXT changes are supported. A Megane red-channel-only texture control was too subtle to establish noticeable visual impact in user's test; demonstrate a clearly visible but safe future GUI override.
- V-PAJERO3 implements a source-qualified taillight core/blended lens, native `blight` switch and rear-only headlamp backing profile. User confirms rear stop lighting works. Front black-protrusion removal is supported offline; precise gameplay-angle qualification remains pending.
- Archives reviewed: `vsdk2-source.zip` (13 manifest file hashes, 10 parseable Python files), `vpajero3-source.zip` (8 hashes, 5 parseable Python files); both ZIP CRC clean. Each is a **source overlay**, not a full reproducible checkout or runtime candidate. Repo-level test reports and in-game qualification remain independently bounded.
- **Gate reached for beginning V-SDK3**, with qualified features frozen and residual camera/stock-family gaps explicitly carried forward.

### HISTORICAL V-SDK3 REQUEST (delivered in source; see sections 11–12)
- Define SDK core services and stable project API (`open`, `inspect`, `override`, `validate`, `build`, `revert`); stop using independent one-off scripts as GUI backends.
- Create Rally Workshop shell, Vehicle Library (stock/addon), native-resource preview embed/dock, pan/orbit/zoom, Basic+Material debug HUD, persistence of camera bookmarks.
- Add **cross-cutting data schemas** now for pane IDs/state, paint masks, user texture overrides, dimension/coordinate transformations, sound preset references and import adapter capabilities, even if their complete editing UI arrives later. No speculative game-native claims.
- Implement end-to-end **two thin tasks in the GUI**: (1) inspect an addon and visibly adjust or replace one material/texture override using actual SDK semantics; (2) open a stock Megane/Pajero copy-on-write project and visibly adjust one supported stock resource, then Validate/Build/Restore from GUI. Keep native camera experiments separately qualified; do not promise unsupported controls.
- Ensure there is a real visible artifact and functional UI; not just design mocks. Keep headless CLI fully operational for CI and power users.
- **Gate:** user can discover/open Subaru, Lancer, Pajero and a qualified stock car, pan with MMB, toggle actual runtime-derived debug data, inspect real material IDs (click/pick if qualified), visibly edit one supported item and build/revert it via real SDK services. The CLI and previous launchers still work.

### V-SDK4 — Material & Texture Studio
- Material picking/highlight, alpha/paint/glass/decal/damage/reflection diagnostics, safe presets and editable overrides.
- Investigate Subaru's window-break disappearance against stock MR and create an isolated, tested **per-pane intact/cracked/shattered workflow**. If actual runtime cannot support all three states, label the supported subset instead of simulating functionality without warning.
- Texture browser, import/replace, alpha/UV details, Source Fidelity/Balanced/Performance options, reload and budget warning.
- Add **native texture-slot assignment** of an existing project DXT to a qualified selected draw/slot. This must NOT be confused with editing every usage of a shared DXT pixel payload; validate native pointer/name table ownership and conflict behavior.
- Provide **offline Help/F1** and discoverable view-control explanations for the editor. Keep docs synchronized with implemented functions.
- Add stock-MR texture/material substitution, `Classic MR Style` A/B, and masked body-color editing with persistent override/preset metadata.
- **Gate:** demonstrate repeatable repair of a visible import defect without hand-editing code; stock and addon changes independently reversible.

### V-SDK5 — Blender Bridge / edit preservation + Scale/Fit Editor
- Editable interchange + stable provenance IDs; round trip real GT car and stock MR car; conflict UI for changed topology.
- Implement reversible, source-to-stock reference-based overall scaling, visually qualified side-by-side size comparison and optional safe dimension recommendations. Keep mesh scale distinct from wheel fitment, physics and collision changes; surface dependencies and author approval.
- Source reconversion preserves user patches or stops with actionable conflict; no silent deletion.
- **Gate:** Blender geometry/UV edits persist through successful rebuild and optional upstream reconversion.

### V-SDK6 — Physics, Camera and Audio editing UI
- Connect qualified profile backends to readable controls, ranges, A/B/undo/default restore.
- Make per-layer audio substitution and self-created default whine/spool/BOV presets available through GUI; validate provenance/licensing and native trigger behavior. Add explicit manual import repair for sample-rate/loop mismatches.
- Audio audition and layer mixer; camera in-game-mode controls and Previewer gizmos; physics fitment and donor-vs-custom separation.
- **Gate:** user performs common physics/audio/camera changes without editing JSON or asking Codex. Game verification for each independent change.

### V-SDK7 — Fleet Builder, hardening, release readiness
- Merge stock overrides and addons; CarID allocation and bank frame composition; capacity limits and conflicts; installer/rollback; private-asset stripping.
- Repeatable automated + game tests on stock/varied addons; performance budgets, crash reporting, dependency and version checks, source docs.
- Publish a concrete **format and version compatibility table** and native glass-damage qualification (or transparent limitation). Include stock-style texture replacement, paint/recolor, scaling dependency and audio replacement regression cases.
- **Gate:** coherent multi-car roster, stable racing/AI/re-entry and full restore; no raw GT game content in distributable artifacts.

### Public beta: v0.x Vehicle SDK Studio
- Free downloadable tooling, source and license/docs as chosen by owner; sample **originally created or explicitly licensed** demo car/assets; step-by-step onboarding.
- Native-compatible features labeled clearly; unsupported advanced cases exposed through manual workflow.
- Sponsor links optional and unobtrusive after project eligibility; no donor-only functionality, no paid copies of GT assets.

### Post-beta (not a blocker for first useful release)
- More car families (GT3/GT4 variants, other games and Blender models), broader fully qualified source formats, more native capacity research, advanced replay camera controls, fully accurate D3D8 parity, advanced animation/interior authoring, possible sound provenance enhancement and community plug-ins.
- **Release boundary:** `Classic MR Style`, basic masked recolor and reversible scaling should be considered beta-target usability requirements where feasible; perfect automated semantic texture substitutions and fully automatic nonuniform scaling for arbitrary models may remain post-beta, with explicit limitation.

## 7. Per-phase working rules for Codex / Claude

1. Read this plan and the current repository baseline. Update the capability/gap ledger; do not repeat earlier research when existing qualified implementations can be reused.
2. For each track record **source → hypothesis → code change → tests → candidate → user gameplay result → status**. Use exact hashes and reproducible commands.
3. Continue through independent safe subproblems; do not stop for an intermediate report when implementation can continue. Do stop for any decision requiring human gameplay/permissions or unsafe/unproven native patch.
4. Implement smallest shared SDK core change first. Do not create vehicle-specific copies of existing pipelines; isolate true source differences in config/adapters.
5. Preserve proven baselines and run regression checks, especially stock cars, Subaru, Lancer, Pajero, UI assets, game-loading latency, deformation, cameras, crew, lighting, audio and expanded roster.
6. Keep separate isolated candidates for independent native experiments. Never combine multiple unqualified hooks and then attribute a result to one.
7. If UI is implemented, every visible control must be wired to a real action, validated state and persistable project changes. Expose human-readable errors and safe defaults.
8. At the close of every phase update these **three files** in the repository (to be created if absent): `docs/sdk/MASTER_PLAN.md`, `docs/sdk/CAPABILITIES.md`, `docs/sdk/REGRESSION_MATRIX.md`; keep the master document's existing objectives stable unless a documented decision changes scope.

## 8. Minimal regression matrix for the beta

| Test | Required cases / evidence |
|---|---|
| Safe source preservation | EXE, `d3d8.dll`, retail archives unchanged after build, install, launch, uninstall |
| Stock zero-edit | Original stock car resource and behavior match; edited stock override reverts cleanly |
| Addon independence | Subaru, Lancer, Pajero distinct mesh/UI/physics/audio; stock identity unchanged |
| Multi-roster | At least one user-qualified combined 29/30 config using real addon cars; player+AI, launch, finish, Results, reload, re-entry |
| Material/rendering | Frontend/race, glass/decal order, reflection mask seams, headlights, brake glow, crew, both reflection states, damage |
| Cracked/shattered windows | Stock pane damage behaviors vs Subaru regression; smash one window then examine all other panes; intact→damaged states, alpha/depth/reflections, race/preview parity |
| Style/material substitutions | Local stock MR texture replacement with visible before/after, verified UV adaptation, no unrelated shared atlas mutation; undo/restore; texture-memory and license/source checks |
| Native texture-slot reassignment | Same loaded project texture assigned to two or more eligible draws; verify only intended slot references change, shared native descriptors protected, preview/build/reopen/undo/restore; unsafe cross-pass alpha/env swaps rejected |
| Offline Help and F1 | Open context help in stock/addon project, inspect F3/hotkeys and material slots; verify links, correct current shortcut labels, native-preview qualification notes, navigation without internet |
| Repaint | Recolor a car's actual base coat while preserving baked logos where feasible; fallback UI and no wrong recolor when paint is baked into same pixels as decals |
| Scaling | Uniform scale and explicitly qualified dimension fit; Source vs MR reference view, correct wheel/brake/crew/light/collision/shadow/camera dependency reports; restore source and retain patch layers |
| Wheels/fitment | Four corners, front/rear brakes, tyre/rim layers, static stance vs loaded race stance, turns/bumps/jumps |
| Physics | Defaults, edited profile, steering/braking/reverse/landings; verify no cross-car donor mutation |
| Audio | Engine, whine, spool, BOV, AI and player, stock passthrough, cleanup/re-entry, mute/solo diagnostics |
| Audio replacement | Replace each engine/whine/spool/BOV layer independently from local user PCM; sample/preset conversion, loop/trigger checks, audition, sound ownership, A/B, Reset to Default, no bundled GT audio |
| Camera | At least one stock and one imported sedan and one off-roader, all relevant modes where supported; no global changes |
| Previewer | Orbit, MMB pan, zoom, selectable material, overlay, source-vs-MR warnings, reload, texture override |
| Blender | No-edit export/import, changed topology with conflict handling, UV/mesh edit persistence |
| UI assets | Correct icons for all addons; new frames don't corrupt stock or other projects |
| Performance | cold/warm/re-entry choice for 3 imported+stock; baseline vs after; memory/cache pressure and leak checks |
| Packaging | Manifest collisions, private asset exclusion, missing source handling, cleanup, rollback, backup, duplicate CarID prevention |
| Source-format coverage | Qualified GT3/GT4 profiles, known unsupported variants, MR native output, PNG/WAV support by exact type, Blender intermediary; unsupported input fails with actionable diagnostics, no silent loss |

## 9. Practical next prompt outline

With V-SDK2 first-pass controls accepted, start **V-SDK3 Studio Foundation**. Preserve the newly added cross-cutting requirements: pane-level breakable glass, optional stock-MR texture/style substitution, validated scale/proportion comparison, base-coat recolor, customizable audio presets, and an explicit versioned format-support registry. Instruct the agent to implement the actual Rally Workshop shell and an operational viewer + two full GUI→SDK→build vertical slices. Do not attempt every editor in the first Studio pass. Require exact demo launch instructions, brief issue backlog, successful CLI regression suite and a tested end-to-end UI action. Maintain this master plan, capability status ledger and regression matrix after the phase.

**Decision rule:** improve the *repeatable authoring workflow* before importing a fourth vehicle; new models are validation fixtures for generalized tools, not the next standalone polish project.


## 10. Review handoff — V-SDK3 starting baseline (25 October 2026)

**Source-grounded accepted deltas:**

- `V-SDK2`: bounded camera follow-extent overrides only, keyed to the current physical CarID with model and original 44-byte bounds guards; two independent gameplay camera changes reported. Camera manager getter mutates scratch state; do not incorrectly treat it as side-effect-free. ID0 follow override is deliberately unsupported. No global XML changes.
- `V-SDK2`: retail stock copy-on-write authoring, only pinned qualified Pajero/1 and Megane/18, changed DX/DXT resources, no-edit passthrough and restore. Stock physics/audio remain outside newly verified scope. Current tiny Megane whitepaint edit was inconspicuous, **not evidence that stock override failed**.
- `V-PAJERO3`: rear-cap generated lamp housing (rear plane retained, sidewalls dropped); native `blight` switching for a GT4 alpha-test core and separate blended lens. User has qualified rear lighting in game; precise black-front artifact angle still awaits targeted screenshot check.
- V-SDK1 frontend bulk DXT read optimization and working three-import roster must not regress. V-PAJERO3 cache estimate for synthetic sequence is close to its assumed limit; do not introduce permanent duplicate texture copies for previews/editing without measuring actual peak use.

**First GUI phase guardrails:**

1. **Inventory real modules and exact callable APIs** before choosing UI framework. The source archives are overlays; they are not the full repository.
2. Preserve one shared project and undo/override model for stock and addons; stock uses pinned retail ID/resources, addon uses distinct CarID allocation. Avoid coupling editor widgets directly to research-specific Python scripts.
3. Expose only backed-by-code edit fields as editable; future Glass Damage / Style Match / Repaint / Scale / Blender Bridge UI may be disabled with actionable explanation until implemented.
4. Build an actual working Windows UI, not just static visuals. Center viewport reuses the existing D3D previewer where safe. MMB pan and F3 actual data are must-have. If embedding the existing device is unsafe, use a reliable managed standalone viewer while working toward docking; do not fake a preview.
5. Run full repository regression in the agent's **own complete checkout**, and provide original build/launch commands, machine-readable errors and evidence, plus a small human validation checklist.
6. **Do not begin V-SDK4–7 automatically in this phase.** Keep the entire plan as a living specification; implement V-SDK3 to its own acceptance gate before prioritizing the next vertical slice. Continue through internal V-SDK3 fixes without pausing after an intermediate report.


## 11. V-SDK3 implementation ledger

The complete user-supplied v3 specification above is preserved. Imported SHA256: `29453cdf1ac9fb891524f44fb7faee0490052d1f92a7070753eed29613c50178`.

Studio Foundation adds a GUI-independent Workshop service, a real Windows Tk shell, managed D3D9 Previewer navigation/inspection, and texture edit/build/restore vertical slices. See CAPABILITIES.md and REGRESSION_MATRIX.md for actual validation status. The central image is a labelled GPU capture; interactive 3D runs in a managed native window, not a fake embedded viewport. No native gameplay feature was reimplemented for the GUI. V-SDK4 through V-SDK7 remain planned and require separate authorization.


## 12. V-SDK3 source review and V-SDK4 execution gate (25 October 2026)

**Current status:** V-SDK3 Foundation source-delivered, owner Windows acceptance and edited-candidate gameplay tests pending. V-SDK4 has not started. This section supersedes the earlier historical V-SDK3 prompt outline.

### Independently reviewed (source archive `rally-workshop-vsdk3-source.zip`)

- 728 tracked source files match SHA256 entries in `SOURCE_MANIFEST.json`; ZIP CRC clean and no unlisted archived files. Manifest claims `research/vehicles` commit `2a42ee769b5a2f014fbe414f6eea11bbe4afe3d7`, not independently verifiable without `.git`.
- 413 Python source files AST-parse cleanly. All 11 `tests.synthetic.test_workshop` tests passed under an isolated Linux environment.
- Cross-platform full suite attempt: 760 discovered tests, 76 skips, seven environment-dependent errors (six tests require missing `unicorn` x86 emulator, one requires the Windows MSVC x86 compiler). These are **not** proven product regressions. Windows agent reports 790 passing / one skipped; that Windows run was not reproduced in this review.
- Source establishes actual Tk GUI, project library, managed Win32/D3D9 interactive Previewer, orbit/MMB pan/zoom/focus/bookmarks/F3, draw selection, material semantics inspection, texture-wide RGB multiplier, qualified dimension-preserving RGBA PNG replacement, project undo/restore, stock copy-on-write and addon builds via prequalified roster.
- UI's central pane displays a labelled GPU *capture*, not live embedded 3D. Interactive Previewer opens a separate native window. Picking is triangle intersection, not alpha-texel-aware shader picking. Preview fidelity is approximate, not D3D8 parity.
- Existing qualified stock COW families remain Pajero/CarID1 and Megane/CarID18. Generic DX family inspection does not allocate a registered runtime CarID.
- Current color multiplier affects whole atlas and painted logos/decals. No general per-material native reassignment, UV editing, masked paint, crack/broken-glass logic, Classic MR Style mapper, Blender round-trip, geometric scaling, audio or gameplay camera GUI is implemented. Metadata reserved for future editors does not imply runtime behavior.
- Agent's Windows GUI tests/reports and launchable candidate paths are referenced in `.research-output` but neither private evidence nor candidate binaries ship in this source archive. Original EXE/DLL unchanged is claimed in agent report; cannot re-hash absent original binary inputs.
- Source history docs claim owner authorized 43 earlier local commits and a V-SDK3 commit. Confirm authorization and **no push** before any public release; archive alone cannot validate Git history.

### Immediate owner acceptance gate (before declaring Studio user-ready)

1. In the real Windows checkout run `Rally-Workshop.cmd` (build requires Python with Tk, CMake and MSVC for native Previewer on clean checkout). The review ZIP is source-only and has no retail or GT resources.
2. Open one addon and one qualified stock car. Check Race/Frontend/Wheel variants, material information, correct selections, missing-texture behavior and rest-pose/wheel positioning.
3. Interactive 3D: test LMB rotate/select, MMB pan without orbiting, wheel zoom, F focus, Home, Ctrl1–6 save/Shift1–6 recall, F3 overlay, reload without losing camera.
4. Apply an obviously visible local RGB edit or dimension-preserving PNG to one deliberately selected DXT. Check GUI capture and separate 3D viewer, Undo/Restore and project reopen persistence. Do not test on the canonical frozen finished cars themselves: work in a private Workshop project copy.
5. Configure the qualified roster and build a candidate. Launch it in the game and check menu, race, AI, sounds, damage/glass, brakes, cameras, Results and re-entry. Verify unrelated cars unchanged; restore and rebuild a zero-edit stock candidate.
6. Record Windows screenshots, exact candidate path/manifest, steps to reproduce problems and reported time/load/memory regressions, if any. Mark acceptance `OWNER-VERIFIED` only for runs the owner performs.

### Next implementation: V-SDK4A — Material/Texture Studio (bounded first vertical slice)

- Promote diagnostics into a real hierarchical mesh → draw → material → texture inspector with stable IDs/source provenance, selected/highlighted surfaces and reversible edit layers. Preserve race/frontend/wheel variants and stock/addon symmetry.
- Add supported real material reassignment/authoring only where native DX semantics, shader flags/texture slots and current writer can round-trip safely; otherwise show read-only fields and specific diagnostics. Do not call an RGB texture multiplier material authoring.
- Texture editor: diffuse/alpha channel views, previews, local PNG replacement with dimensional/alpha/orientation/UV warnings, resource-usage budget and non-destructive history. Keep existing DXT bulk loader and 32 MiB native cache behavior intact.
- Provide one **visible, selected-surface-scoped** edit demonstrated on a qualified addon and one qualified stock vehicle. If the render format forces shared-texture changes, disclose all affected draws and require user confirmation; do not silently alter decals/glass.
- Add before/after A/B and precise source-vs-renderer approximation labels. Avoid fake 'live D3D8 parity'. Preserve CLI and file provenance.
- Validate project reload, Undo/Redo/Restore, byte-stable zero-edit, asset ownership, edited candidate build and regressions for Subaru/Lancer/Pajero, cache/performance, AI/camera/audio/UI and native materials.
- Implement V-SDK4A end to end rather than expanding into all planned modules. Follow with separate V-SDK4B masked paint/Classic MR Style and V-SDK4C glass damage **research first**, preserving the existing Subaru symptom as cause-unknown.

### Remaining product roadmap (unchanged)

V-SDK4B: qualified basecoat/repaint masks and Classic MR style/stock material matching with UV adaptation. V-SDK4C: native cracked/broken-glass state research and reversible authoring. V-SDK5: Blender Bridge, topology conflict handling and coherent scale/fit, source/stock comparative overlays. V-SDK6: Physics, Audio (engine/whine/spool/BOV user presets) and gameplay Camera Studio. V-SDK7: Fleet Builder, format adapters, reversible install, public beta readiness. Existing planned work on lighting, crew, damaged state, UI icons, shadow and wheel fitment remains explicitly in the broader master-plan/regression matrix.

**Invariants:** original MRallye.exe untouched; existing d3d8.dll untouched; Randomizer separate; proprietary GT3/GT4 resources private; do not create or push commits without explicit authorization; no false native qualification or unsupported new CarIDs.


## 13. V-SDK3.1 owner acceptance findings and preview assembly gate (25 October 2026)

**New direct owner reports from the running Windows Rally Workshop (screenshots supplied):**
- Texture replacement **succeeded**. The dark Rally Workshop GUI is generally liked and must be preserved.
- Texture preview in Inspector is **unacceptably small and cannot be expanded**. Source `workshop/gui.py::show_texture()` uses hardcoded PhotoImage subsampling toward ~280×110 and a compact fixed-height texture label. Provide resize-aware main/right-pane texture preview and an independent resizable popup/dockable texture viewer with 1:1/fit/zoom/pan/alpha or checkerboard display; retain original/edited A/B. Preserve VRAM/CPU resource budgets and native FEED BGRA/alpha semantics.
- Subaru `car.dx` Race in live GPU preview and Workshop capture **appears to have left wheels whose facing/visibility follows camera azimuth**. This is a user-observed symptom, not a proven root cause. Produce fixed-camera multi-angle captured evidence; inspect `preview_scene.py` staging and `preview-profile.json` source transforms, left/right mirrored wheel winding, normals, outward-facing surfaces, culling and D3D9 draw state. Verify world-space wheel/hub vertices do not change under camera orbit. Do **not** silently edit the qualified Subaru runtime DX or wheel assets to hide a Previewer bug.
- Pajero Race displays wheels while other Race body views do not. Determine whether wheels are baked into `car.dx`, added as provenance-bearing `wheel.dx` rest-pose instances, or duplicated/incorrectly filtered. Existing `preview_scene.py` conditionally adds wheel instances to model kind 1; this must be inventoried and presented explicitly. **A raw Race DX can legitimately differ from an assembled race appearance**; never strip authentic geometry without evidence.
- Standalone Wheel preview currently shows a back/inner wheel face; default should show the actual visible exterior/rim face using per-side/per-rig verified outward-axis conventions. Support switching outer/inner side, no global hardcoded reversal.
- Provide a separately labeled **Preview Car + Wheels** toggle in Race variant, with optional rest-pose wheel assembly and explicit authoring of X/Y/Z position, yaw/rotation and qualified size/scale per wheel when the source-profile permits. Persist it in reversible per-vehicle preview metadata. Display wheel centers, body reference and physical/reference hubs when available; offer comparison to frontend rest pose. **These are preview-only transforms**, not native race physics/wheel installation, unless separate evidence and full end-to-end qualification exist.
- User expressly authorized Codex's previous local commits. This is not blanket authorization for future commits or pushes; obtain scope-specific authorization or obey the current direction. All other repo safety/publication constraints remain.

### V-SDK3.1 completion gate before V-SDK4A expansion

1. Compare original `car.dx` Race, assembled Race + Wheels, complete.dx Frontend and isolated wheel.dx for Subaru, Lancer, Pajero and one stock model. Document which family includes or omits baked wheels. Label source-vs-assembled mode and provenance in UI/HUD/captures.
2. Capture fixed frontal/rear/left/right/three-quarter views under camera orbit and cull-mode changes; show correctly oriented outside faces on all four wheels. Demonstrate no camera-dependent wheel pose, no phantom duplicate wheels and no accidental wheel geometry removal. Treat culling/faces vs transforms as distinct root causes until established.
3. Open a large texture and inspect it at full resolution (or a zoomable crop), navigate without clipping controls, resize the Inspector/preview and restore the last UI layout. The image is an actual supported texture, not a placeholder.
4. Persist a preview-only rest-pose wheel layout for a qualified vehicle, reload it deterministically, then build an unmodified vehicle and verify no game-resource change occurred. If user requests actual fitment authoring, gate that work behind explicit validated native controls.
5. Preserve successful texture replacement, visible material selection, GPU capture, F3 data, navigation, stock overrides, undo/restore, project save/build and PERF2 performance. Ensure preview changes do not become runtime edits accidentally.
6. Update `CAPABILITIES.md`, `REGRESSION_MATRIX.md` and this Master Plan with implementation evidence; owner executes final Windows/game checks. **V-SDK4A material authoring remains the next planned vertical slice; fix these rendering/UI issues before building advanced editors on top.**


## 14. V-SDK3.1 → V-SDK4A implementation ledger (25 October 2026)

The v4.1 owner specification above remains intact. Imported source SHA256: `59dd6361c1f0fc25b7975d403efc287048c06256aab7abae508ee6289f08cfb6`.

**V-SDK3.1 OFFLINE/WINDOWS-VERIFIED:** viewport-sized RGBA/RGB/Alpha image inspection, detachable resizable viewer, checkerboard, fit/1:1/zoom/pan, Original comparison and window/split persistence. Mirrored wheel transforms now reverse staged triangle winding while preserving inverse-transpose normals; frozen Subaru DX remains untouched. Raw Race excludes injected wheels/attachments; Assembled Race includes qualified profile instances. Exact embedded-wheel matching suppresses duplicates where provable. Lancer profile uses unchanged source wheel plus 87 matching body-frame draws. Wheel rest-pose editing is preview-only metadata, explicitly separate from game physics. Outside/inside camera uses dominant axial source normals, with an ambiguity fallback; not a global mesh flip. Six-angle captures for four families and configuration roundtrip evidence are private under `.research-output/vehicles/vsdk31/`.

**V-SDK4A IMPLEMENTED; exact checks in VSDK4A_RESULTS.md:** hierarchical source model/draw/material/texture inspector; per-draw native vertex diffuse RGB through the existing attribute writer; disable/restore an existing environment pass. Alpha/depth, unknown flags, UV and texture-slot assignment remain read-only. Shared vertex conflicts refuse selective edits. Whole-image texture changes list every referenced draw/slot and ask for explicit impact confirmation. Image alpha/orientation and native damage alpha ownership are preserved by scoped RGB edits. Save/reopen, Undo/Redo/Restore, hash-pinned surface layers and isolated stock/addon candidate builds use shared SDK APIs.

**Boundaries:** no semantic paint mask or selective texture cloning is claimed; a selected draw's RGB also modulates baked content on that draw. Preview wheel coordinates are not gameplay wheel positions. Original-game appearance and edited-candidate regressions remain owner gameplay gates. No new stock CarIDs, capacity, physics, audio, camera policy, glass-damage states or GT reconstruction were introduced. Owner subsequently authorized a local commit per completed and validated phase; push/publication remain separately prohibited. V-SDK4B/V-SDK4C and later roadmap remain deferred.


## 15. Owner V-SDK4A acceptance + source review (25 October 2026, revision 4.2)

**Source archive examined:** `rally-workshop-vsdk4a-source.zip`. Its 735 ZIP entries pass archive integrity, all 734 manifest-tracked files exactly match SHA-256, and all 418 Python sources parse. An independent targeted run of `tests.synthetic.test_workshop`, `test_workshop_stabilization` and `test_surface_authoring` passes 20 tests; the claimed 799-test/one-skipped full Windows suite is reported in `VSDK4A_RESULTS.md`, not independently reproduced in this review environment. Private compiled evidence and native gameplay remain user-side checks.

**Owner Windows observations:** previous Subaru wheel and raw/assembled Pajero issues are now resolved; texture replacement succeeds. Remaining 2D texture viewer issue: zoomed/fitted images visually break or distort, while exact 1:1 view is correct. This affects the texture image inspection canvas only, not 3D model textures or persisted DX/DXT assets.

### Immediate bounded follow-up: V-SDK4A.1 — Texture Viewer Resampling, UI Identity, and History

1. **Texture viewer only:** `src/master_rallye/workshop/texture_view.py` currently maps fractional zoom to `Fraction(...).limit_denominator(1024)` then `tk.PhotoImage copy -zoom n,n -subsample d,d`. This is integer pixel replication/subsampling, not proper area-filtered downscaling or bilinear interpolation. It can produce aliasing and misleading pixel/color appearances at non-1:1 scales. Replace with a well-tested **display-only** viewport rasterization path: exact original texels at 1:1, pixel-sharp integer zoom if selected, readable filtered reduction at fit/0.25/0.5/0.75, sensible fractional enlargement; premultiplied-alpha resampling and checkerboard correctness; zoom focal-point anchoring, smooth pan, clipping and bounded memory. Preserve actual texture byte payload, `encode_png` row orientation, alpha and existing source/edited/Undo/Build contract. Do not automatically change DXT resolution or texture source pixels.
2. **Zoom regression:** exercise actual TK images / screenshots, alpha edges, diagonal lines and lettering, 64², 128², 1024×256 and 2048² examples at 0.25×, 0.5×, 0.75×, 1×, 1.25×, 2× and 4×; verify Original/current in RGB/RGBA/Alpha, detached and embedded viewer, pan near edges, output byte-for-byte unchanged. Document filtering choices.
3. **Distinctive Rally Workshop application icon:** author a NEW original stylized off-road rally prototype silhouette reminiscent of the **Schlesser Renault Megane** shape, rather than extracting or distributing Master Rallye/other-game renders, logos, livery or screenshots. Graphite + restrained amber, high contrast at 16×16. Keep source SVG/vector art plus generated Windows multi-resolution `.ico` (16, 24, 32, 48, 64, 128, 256). Apply it to Tk main window, detached/dlg windows as appropriate, Windows taskbar where the launcher supports a real app identity, future executable/package, and optionally native Previewer if cleanly supported by the build. No proprietary image in the public asset bundle.
4. **Local history policy:** owner explicitly approves one local commit after each validated phase, with tests and artifact/evidence summary. Earlier 43 phase commits and the V-SDK3 baseline are already documented; do not manufacture historical versions or rewrite prior verified commits. Commit V-SDK4A only after confirming the real checkout status; subsequently commit V-SDK4A.1 as its own bounded change. No push, remote publication, release or unrelated repository operations.
5. **Owner acceptance:** ask the owner to verify corrected zoom on their actual Windows installation, legible app/taskbar icon and no regressions to surface RGB, mirrored wheel views, raw/assembled Race, native imports, existing texture replacement/build, stock restore and addon candidates.

### Historic V-SDK4A.1 review outlook (superseded for ordering by §16 below)

- **V-SDK4B:** Paint/Recolor Studio and Classic MR Style, starting with source-qualified opaque paint materials, mask-aware recolor that protects logos/glass, existing-texture reuse from *user-supplied* retail MR resources, original vs edited comparison, UV/provenance diagnostics, explicit non-destructive choices.
- **V-SDK4C:** Subaru damaged-glass root-cause research against original MR native states before implementing any cracked-glass authoring; don't assume the symptom proves a missing overlay.
- **V-SDK5:** Blender round-trip and qualified visual Scale/Fit + stock geometry comparison.
- **V-SDK6:** Physics/Audio/Camera Studio; preserve current synthesized whine/spool/BOV and allow independent user-supplied replacements with presets.
- **V-SDK7:** full fleet, format compatibility, release safety, installer, docs, and voluntary sponsor information after appropriate legal review.

**Definition of success for V-SDK4A.1:** both embedded and detached texture views display predictable, visually faithful images at arbitrary zoom, 1:1 remains pixel-exact, resource bytes remain identical, the app has a coherent legally distributable icon, and local Git history is clean and scoped.

## 16. Owner roadmap decision — V-SDK4A.1 completion → V-SDK4C damage-first (revision 4.3, 25 October 2026)

**This section supersedes the sequencing in §15 and earlier roadmap summaries, but does not delete or weaken their requirements.** The owner wants native vehicle completeness and physical/damage behavior investigated before cosmetic Paint Studio/Classic MR Style work. The next Codex run after V-SDK4A.1 is **V-SDK4C**; V-SDK4B is postponed, **not canceled**.

### A. Close V-SDK4A.1 cleanly

- Finish and verify Texture Viewer display-only fractional zoom/fit resampling (1:1 still pixel exact; actual DXT/PNG bytes unchanged); create the original Rally Workshop icon, preserving copyright boundaries.
- Run relevant Windows checks, isolate unrelated changes, create a **local** `V-SDK4A.1` commit only on acceptance; retain prior `V-SDK4A` commit and previous genuine history. No push or publication.
- Record owner acceptance, build hashes, tests and any remaining display issues. If this subphase has not yet been implemented, do not falsely mark it complete.

### B. Next run: V-SDK4C — Broken Glass & Native Damage Fidelity (primary mission)

**Observation, not yet diagnosed:** owner reports that when **one** window on the imported Subaru is broken, the car's glass disappears. It is **not established** that a separate cracked-glass texture or overlay is the correct repair; investigate actual stock native game behavior first.

1. Establish source-qualified stock MR glass baseline: intact, damaged/cracked if the engine supports it, broken/absent; multiple separate panes and which vertices/materials/flags/resources/damage groups own their state. Examine installed stock `car.dx`/`complete.dx`, original texture alpha, damage transitions, geometry and renderer ordering; isolate unknowns.
2. Reproduce Subaru regression in the actual game under controlled conditions: break left window only; observe all other panes, from several angles, before/after and after race re-entry. Compare with at least one stock sedan and one other import. Preserve exact candidate/provenance and capture proof. Offline Previewer cannot be asserted to simulate game damage unless a real mechanism is added and qualified.
3. Determine root cause rather than implementing an unqualified decorative cracked-glass decal. Candidate categories include shared damage indices/state, draw grouping, shared vertex alpha, blend/depth/alpha-test state, hidden geometry and texture ownership; these are **hypotheses**.
4. Implement the **smallest native-compatible correction** with independent per-pane intact/broken behavior as far as engine actually supports it. A cracked intermediate state or separate overlay is optional only if backed by evidence. Preserve intact glass appearance, UV, reflection, collision/damage effects, race/frontend distinction and other damageable body parts.
5. Provide appropriate semantic `Glass / Damage` diagnostics and future editor extension points, not fake glass authoring controls. If proof or in-game user testing is required, stop at an honest research status with a specific targeted Windows test recipe; do not claim the native fix is gameplay-verified without a tested candidate.

### C. In the same next development run: V-SDK4A.2 targeted Material/Texture UI gap

**Already supported:** selected native model/draw/material inspection; editing vertex RGB and disabling a qualified environment pass; replacing pixels in an existing `.dxt` changes **every** draw using that texture. **Missing:** reassigning a selected draw's slot to another texture already loaded in the project. This is not the same operation as changing image pixels.

- Add `Assign Existing Texture…` next to an actual selected **model/draw/texture slot**, not to the global image replacement control alone. Populate choices from project-owned resolvable DXT resources; show original binding, target, usage count, size/alpha/format, variant and native slot ID, preview difference and risk warnings.
- Research actual DX texture reference representation and `r4e_writer` behavior before writing. Support a slot/pointer/name reassignment only when exact native write semantics and sharing are proven. If a native string table/material descriptor is shared by other draws, either implement a validated copy/split or **refuse with clear diagnostics**; never silently rewrite all shared users.
- Verify that the target resource is available in the built addon/stock candidate, with correct resolver naming, no bank/resource collisions and proper alpha-test/blend/reflection semantics. Reject or warn on incompatible glass/lamp/environment use. Do not assume that replacing a `.dxt` file name in JSON patches the `car.dx` binary.
- Changes must be **reversible and composable** with existing vertex RGB, environment-pass, PNG replacement and undo/redo; survive Save → Reopen → Validate → Build → Restore. Test across at least two draws sharing one input texture, one target shared by two draws, and a deliberately unsupported native sharing case.
- If a safe native writer cannot be qualified within this milestone, deliver the researched binding map plus a disabled reasoned UI action and independently tested API instead of advertising a functional button.

### D. In the same next run: Rally Workshop Offline Help / User Guide

- Add an unobtrusive **Help** menu/button and **F1** shortcut plus contextual `?` near complex controls, preferably local searchable Markdown/HTML rendered by a readable help window (no network required).
- Explain: start/project library, addon vs stock projects; what `car.dx`, `complete.dx`, `wheel.dx`, `DXT` and CarID mean; Open DX family; Save/Validate/Build/Restore, Undo/Redo; Original/current and per-texture pixel replacement versus per-draw slot reassignment; RGB/alpha and native material limitations.
- Document viewport controls **MMB pan**, orbit, wheel zoom, `F` focus, `Home` reset, **F3 diagnostics**, Ctrl+1/Ctrl+6 view shortcuts if still current, Raw versus Assembled Race and preview-only Wheel Fitment. Explain how to show the detailed debug overlay and which figures come from D3D9 approximation versus actual MR.
- Include troubleshooting (missing source/private assets, build inputs, preview mismatch, performance, unsupported material/glass behavior), a short first-project walkthrough and keyboard-shortcuts quick reference. Cross-check against code so that no documentation tells users to click a control that does not exist.
- Keep help and program labels in English initially if that matches implemented UI; structure files so localization/Russian translation is straightforward later. Package help and icon with local Windows builds.

### E. Sequencing, commitments and gates

- Prefer **two scoped local commits** if both workstreams qualify: `V-SDK4A.2` (slot rebinding + offline help) and `V-SDK4C` (glass research/fix). Committing a verified research report is acceptable, but do **not** label an unverified gameplay fix as complete. Always inspect working tree and preserve prior actual commits.
- The owner authorizes local version-history commits after completed validated phases, **not** push, release, public asset upload or publication. Retain private GT/MR data local. Keep original `MRallye.exe`, `d3d8.dll`, retail archives unchanged; Randomizer separate.
- Owner **Windows acceptance gate**: texture zoom and app icon first; then native broken-window behavior, safe existing-texture reassign on a named draw, functional F1/help, Undo/Restore, and normal Subaru/Lancer/Pajero/stock game behavior. No regressions to PERF2/physics/audio/cameras/lights/30-car capacity.
- **Later:** V-SDK4B Paint & Classic MR Style, V-SDK5 Blender/Scale, V-SDK6 Physics/Audio/Camera Studio, V-SDK7 Fleet/release as already specified. Prioritize native completeness before cosmetic adaptation but preserve full product scope.


## 17. V-SDK4A.1 implementation boundary

Imported v4.3 source SHA256: `97d134bf1f0a5ad33022c8c8af40ab66f057bc054c2162608d7baaea222fdb8d`. V-SDK4A was locally committed after a fresh799-test run (one skip). V-SDK4A.1 adds display-only premultiplied Pillow resampling, exact1:1 and nearest mode, bounded viewport output, cursor anchoring, original SVG/ICO identity and safe versioned Previewer builds. Full805-test Windows result and56 zoom captures are documented in VSDK4A1_RESULTS.md. Owner gameplay/display acceptance remains separate. V-SDK4C is next by explicit owner direction; V-SDK4B remains deferred.
# Implementation update: V-SDK4C tracks B/C

## V-SDK4C delivery boundary

All three tracks have an implemented bounded result. Subaru's whole-car glass
ownership defect is source-confirmed; an isolated native two-case/four-zone
candidate and diagnostic per-zone inspection are ready for owner testing.
Intact geometry/UV/material multisets and native deformation are preserved;
stock crack-texture UV projection is an explicit approximation. A separate
third-state glass system remains unqualified. Full release suite: 814/1 skip.
V-SDK4B and later modules remain deferred. See VSDK4C_RESULTS.md.

V-SDK4A.1 is committed as `8085800`. Existing-texture slot rebinding and offline
Help are implemented in a separate following phase. Binding scope is deliberately
limited to existing slot-0 resources with equal encoded name length, dimensions,
format and alpha; no general descriptor allocation is claimed. Native glass
work proceeds separately. V-SDK4B/V-SDK5 have not been started.



## 17. 2026-10-25 owner review — V-SDK4C and V-SDK4C.1 decision (current)

### Source provenance / independently observed review

- Owner supplied `rally-workshop-vsdk4c-source-review.zip` and six supporting screenshots. ZIP CRC passed. `REVIEW_MANIFEST.json` lists **1,046 content files**, all **1,046 SHA256 hashes** match. The extra archived file is the manifest itself. **430 `.py` files** parse as Python. Nine targeted synthetic tests (`test_texture_binding`, `test_glass_authoring`) passed in the independent review environment. No full Windows/gameplay suite was independently reproduced.
- Archive reports branch `research/vehicles`, snapshot commit `bbc1f8aa4146ad9d488a4001272e1c0806cb6a96`, clean working tree. These fields cannot be authenticated without `.git`. Ledger names separate commits V-SDK4A.1 `8085800`, texture binding/Help `c3c0b12`, native glass `b22f83f`. The development agent reports 814 passed / 1 skipped on Windows; treat as **agent-reported**, not independently replayed.
- `texture_binding.binding_patch` **really changes only the selected physical draw's inline diffuse slot-0 ASCII bytes**, and retains identical byte offsets. It permits only same encoded stem length, same FEED dimensions/native header format and *identical every-pixel alpha plane*; other slots and Null-to-texture transitions are forbidden. These limits are implementation constraints of the current safe patcher, **not proven absolute MR engine restrictions**.
- `MaterialSemantics.from_draw` extracts native alpha blend/test state and an environment capability bit. The UI currently permits **environment ON/OFF**, not a verified continuous reflectivity value. Existing GT4 material code already treats some source texture alpha as reflection weighting; do not blindly edit opacity-alpha as reflection strength.
- V-SDK4C reauthoring **implemented OFFLINE** for baseline Subaru race `car.dx`, behind explicit source SHA256 and optional `base_glass_profiles`. It maps four logical native groups (`screenfront`, `screenrear`, `screenleft`, `screenright`) and relocates static lamp glass to an ordinary draw. The new cracked imagery is the **stock MR broken-glass texture mapped with new planar UVs**, not source GT art or a verified third state. Only this Subaru race `car.dx` differs in the author's 368-resource candidate comparison. Glass damage **still requires owner gameplay acceptance** against the isolated candidate.
- Stock Navara shows independent native glass-zone cases in research and owner's screenshots. Four **logical** zones do not imply one damage controller per physical pane; front/rear side panes can share one side-zone state.

### Owner-observed defects, not yet fixed or game-qualified

1. **Texture-slot picker is practically unusable for general substitution.** Most visible rows carry long incompatibility warnings and the only enabled row is commonly the currently assigned texture. Make the UI show 'compatible N / available M', prioritizing actual eligible alternatives; summarize exclusions rather than appending long reasons to every asset name. The fundamental writer limitations must be removed by a *verified structural DX rebuild* where safe, or documented and broadened through other sound native alternatives (never by silent truncation/padding).
2. **Pajero Nikon-side surface shows unwanted see-through/alpha and lacks expected reflections** in affected areas. Treat as two independently diagnosed problems: transparency/alpha/depth and paint/environment coverage. Owner screenshots and overlay show Frontend `complete.dx` material selection near the area, but cannot establish exactly which native draw/texture owns every pixel without source-qualified geometric picking and material audit. Audit Race `car.dx` and Frontend `complete.dx` separately.
3. **Pajero splash guards and frontal guard/bar vanish from one viewpoint/side.** Investigate real source triangle winding, normals, culling, mirrored transforms and missing backside geometry. Previewer `K` can switch CW/CCW/NONE as a diagnostic, but global `D3DCULL_NONE` is **not** an acceptable general fix. Require both D3D9 captures and owner game test.
4. **Subaru and Navara glass discrepancy.** The owner reports stock Navara gives convincing damage while Subaru still has a combined-looking cracked texture. Differentiate group-controller switching from *crack-texture UV tiling/coverage*. Check the precise V-SDK4C isolated candidate, one zone per fresh race, repeat race, individual vs adjacent panes. Do not promise physical per-pane independence beyond native four-zone evidence.
5. **Reflectivity editor needs a source-qualified intensity control.** Where native reflection is controlled by a proven reflection-weight mask/alpha or other source-qualified value, expose a controllable strength and preview comparison, retaining opacity, cutout, DATE/alpha-test, native damage alpha and other textures. Otherwise provide inspect-only/explicit unsupported state. Never invent an arbitrary shader constant or patch retail executable.
6. **Crew fitment and occupant placement** is scheduled for V-SDK4B alongside Classic MR Style/visual fitting, using already qualified Subaru crew work as a reference. It is not silently included in V-SDK4C.1.

### Next bounded milestone: V-SDK4C.1 — native material/visibility quality gate

**Track A — Texture Binding v2:** map DX inline strings, lengths, offsets, owning draw record, resource lookup and loader compatibility; add safe variable-length reconstruction or alternative proven general reference writer, independently qualify diffuse and (where possible) other stage slots; qualify alpha and resolution rules by actual stage usage, not a blanket whole-texture-alpha equality; preserve all owner resources, descriptor independence, undo/redo/reopen/build/restore and native byte invariants. Reject truly unsupported cases with one actionable reason. UI picker compatible-first, compact reasons, search/filter and accurate counters.

**Track B — Pajero material and reflection fidelity:** source-qualified isolation of the Nikon-side draw(s), log blend/test, depth-write, texture/vertex alpha, render ordering, environment stage/mask. Fix unwanted transparency and missing reflections conservatively in Race and Frontend. Reflection-strength control may be per material/surface only if real MR semantics are verified; protect intentional glass, livery and native damage. Compare environmental reflections ON/OFF.

**Track C — One-sided geometry and culling:** exhaustively locate splash guards and guard/bar using opposite-side screenshots + DX draw/triangle provenance, with culling modes and both fixed camera directions. Repair source winding or mirror transform, or add necessary explicit backside geometry using qualified topology writer; no global two-sided state hacks. Preserve materials, normals, UV, damage, collision, other vehicle baselines.

**Track D — Subaru glass acceptance:** reproduce owner-observed combined-looking glass, verify exactly which V-SDK4C Subaru candidate was launched, correlate native control-case changes with each glass zone, isolate broken-texture UV orientation/scale separately, and repair if source-qualified. Compare stock Navara, Subaru and untouched Lancer. The owner must explicitly validate the final candidate in MR under isolated impacts; offline captures are not a substitute.

**Gate:** close A–C with real GUI/native-resource before-and-after/build checks and regression. Provide one isolated Pajero candidate and one isolated Subaru glass candidate rather than bundling unrelated experiments. Keep tests, CAPABILITIES, REGRESSION_MATRIX, Help and COMMIT_LEDGER current. Authorize only **scoped local commits after validation**, no push/publication. Do not begin V-SDK4B until this bounded quality gate is reviewed or qualified blockers are documented.

### V-SDK4B after this gate

Paint/Recolor, Classic MR Style matching from locally installed stock textures, semantic masks, A/B geometry/appearance comparison and **crew/driver/co-driver seat orientation/position fitment**. Reuse successful Subaru occupant workflow without assuming GT model topology. Material/texture fixes in V-SDK4C.1 are prerequisites; keep V-SDK5 Blender/scale and V-SDK6 audio/physics/camera plans unchanged.

### Minimum owner game checklist for V-SDK4C.1

- Subaru: fresh isolated race, no damage, one **front** impact; restart then **rear**, then **left**, then **right**; inspect crack ownership and which glass/lamp stays. Re-enter race and repeat. Use exact candidate/build hash and state.
- Navara control: reproduce same broad damage-zone views; record whether two panes share a single side zone. Do not infer separate per-door controllers just from simultaneous cracked panes.
- Pajero: from front-left and front-right, rear-left and rear-right, verify mudflaps and bars against original source; repeat reflections ON/OFF and view the Nikon-side panel for transparency at all angles.
- GUI: choose a *different* existing texture (ideally different-length name and dimensions where stage-safe), bind selected surface, save/reopen, build, undo/redo, verify texture resource remains intact and unrelated draws remain unchanged.
- All changes: check Menu/Frontend, Race, AI/re-entry and wheel/crew/audio/light/damage preservation, PERF2 responsiveness and original EXE/DLL hashes.


## 18. 2026-10-25 owner follow-up — culling proof, discoverable hotkeys, glass authoring policy (revision 4.5)

**Evidence source:** two additional owner screenshots of Pajero Frontend `complete.dx` at identical close-up camera angles with Previewer `K` culling changed, and explicit owner testimony that the underside/backfaces of headlamp backing, frontal guard/bullbar and splash guards are missing **in the game**, on corresponding model variants. This is **owner gameplay observation**, not independently recreated gameplay by the reviewer. Do not confuse front-side legitimate opacity/alpha defects near Nikon with rear-face culling defects.

### 18.1 Culling diagnosis and target native repair

- `K` is confirmed in archived `vehicle_previewer/src/main.cpp`: `cull=cull%3+1`, cycling D3D9 `CW`, `CCW` and `NONE`; it changes Previewer rasterizer culling, not DX geometry bytes nor native game's culling mode.
- The new screenshots show that toggling cull changes visibility of the Pajero headlamp backing. The owner reports the same one-sided visibility for frontal guard/bullbar and mudflaps in Master Rallye itself. This **strongly implicates missing opposite-facing polygons, inconsistent winding/mirror transforms, or a native draw-level two-sided requirement**, but is not by itself proof of which specific triangles must be edited.
- **V-SDK4C.1 native geometry acceptance:** identify exact draw/triangle ownership and desired front/back visibility in `car.dx` and `complete.dx`; compare source geometry and qualified stock MR examples. Where two-sided visibility is genuinely intended, prefer repaired winding or complete/closed source topology; otherwise add a deliberate opposite-facing surface with proper normals/UVs, or use a qualified native per-draw two-sided state only if actually supported. Never fix by globally setting game or Previewer `D3DCULL_NONE`, disabling all opacity, or modifying original on-disk EXE/DLL.
- For the **headlamp backing**, distinguish internal occlusion from external panel visibility. Ensure no black rectangle protrudes, no artificial lamp bleed appears, and the lamp lens/reflector is correct from both intended viewing directions. Preserve lighting behavior, depth tests, intentional glass and body reflection passes.
- Provide fixed front-left/front-right/rear-left/rear-right previews with `CW/CCW/NONE` and reference stock render views; then a separately identified isolated MR candidate for owner gameplay acceptance. Do not call the defect fixed merely because `K` makes it visible in the D3D9 viewer.

### 18.2 F3 Overlay and F1 Help: complete actual control discovery

- Owner did not know about `K`; show the full set of currently implemented diagnostic keys in discoverable UI. In V-SDK4C code, `F1` already opens native Previewer help and offline Workshop help has a viewport guide, but the F3 overlay omits important keys. No need to add a second input system; expose the existing one.
- The source's `App::key` defines: `K` cull, `W` wireframe, `E` environment/reflections, `B` brake test, `D` composed/base/vertex, `C` alternate switch-case, `Z` instance depth write, `L` next layer, `0` all layers, `A` assembled/raw wheels, `Tab` Race/Frontend/Wheel, `F3` HUD, `I` resource dialog, `R` resource reload, `O` open DX, `F` focus, `Home` reset, `1..6` view presets, `Ctrl+1..6` save, `Shift+1..6` recall, `S/V` save/recall bookmark 1, and `F1` help. Document **only verified working actions** and their actual side effects; update when implementation changes.
- Include `F1 — all controls` in the normal viewport hint **even when F3 is off**. F3 HUD should show current values/labels for K/Cull CW/CCW/NONE, E/reflections, B/braking, W/wireframe, D/material mode, Z/depth and A/assembly; group remaining shortcuts compactly with an expandable cheat-sheet/help pane. Keep HUD readable at 1280x720, avoid covering model and expose color/selection labels with sufficient contrast.
- Use a single authoritative shortcut/action mapping where practical to drive interactive help, tooltip and HUD. Cross-check full English offline F1 Workshop help and native Previewer F1 text. Never advertise K=permanent game repair; if diagnostic `NONE` enabled, mark it `PREVIEW-ONLY — may mask single-sided faces`.
- Add regression tests for cycling `K` and for F3 state labels matching current controls and corresponding active render states; test both stock and imported geometry. Preserve owner-confirmed model preview navigation, editor help and build workflows.

### 18.3 Subaru broken glass — clarified intended origin

- Owner **explicitly confirms** that GT3 does not supply a suitable cracked-glass effect for this project and that **using/adapting locally sourced stock MR broken-glass textures is the intended approach**, not an undesirable source-fidelity compromise. Do **not** make recovery of nonexistent GT3 damaged-glass textures a blocker.
- Outstanding acceptance is **native damage-zone ownership/trigger behavior, pane-specific appearance, UV layout/coverage, and preservation of intact glass, lamps, materials and deformation**. Four native logical zones remain the proven boundary absent new evidence; do not advertise independent physical side panes beyond that evidence.
- Stock MR content is loaded only from the user's own installation; never redistribute stock MR textures or private GT assets in SDK source/build artifacts.

### 18.4 Scope/sequence and delivery

- These findings are **an explicit addendum to existing V-SDK4C.1**, not a new speculative rewrite. Continue Texture Binding v2, Nikon-side alpha/depth and reflection integrity, qualified reflection strength, one-sided Pajero geometry, and Subaru glass qualification as specified in section 17.
- First patch discoverability/HUD affordances (low risk), use K CW/CCW/NONE diagnostic views to isolate faces, repair actual DX geometry/qualified native materials with isolated Pajero candidates, then solicit owner gameplay validation. Keep glass separate from culling and from paint styling.
- Update `MASTER_PLAN.md`, `CAPABILITIES.md`, `REGRESSION_MATRIX.md`, `COMMIT_LEDGER.md` and F1/offline help. Local scoped commits permitted after validation only; never push/release without authorization. V-SDK4B remains deferred until this functional quality gate.


## 19. V-SDK4C.1 implementation ledger — 26 October2026

Implemented and offline/Windows validated: Texture Binding v2 structural native
references, material-specific compatibility, practical searchable picker;
qualified opaque reflection weights and mask diagnostics; source-cull-disabled
reverse faces; mixed GT4 frame opacity/alpha-only reflection translation;
owner-approved contoured headlamp housing; complete Previewer status/help;
UV-only continuation of the existing Subaru four-zone repair with stock-MR art.

822 tests passed, one optional skip. Actual Windows addon/stock picker and
reflection editing/build/history/zero-edit restore passed. Final Pajero and
Subaru candidates are separate. 64 final Pajero matrix captures plus64 glass
captures, original native CPU replay and sealed preflight pass. New gameplay
qualification remains pending; do not promote offline evidence to acceptance.
See VSDK4C1_RESULTS.md and COMMIT_LEDGER.md for scope, limits and reproducibility.
Existing private resources remain local; no old runtimes were removed after the
owner changed the cleanup instruction. No Paint Studio/crew phase started.


## 20. V-SDK4C.1 source-review acceptance and V-SDK4B handoff — 26 October 2026 (revision 4.6)

**Evidence tiers:** This is an independent source-only review, not a Windows gameplay or D3D8 result.
Review ZIP `rally-workshop-vsdk4c1-source-review.zip` contains 975 manifest-listed files, all
matching SHA256; 418 `.py` files parse. Independent focused Linux tests: 38/38 pass
(`test_gt4_layered`, `test_visibility_keepout`, `test_glass_authoring`,
`test_surface_authoring`, `test_texture_binding`, `test_workshop`). The author records
822 passing / 1 skipped Windows tests; the source-only Linux archive cannot reproduce
the complete Windows checkout (MSVC x86, private research artifacts, excluded Blender
add-on sources). Do not convert this limitation into a game-regression claim.

**Implemented and review-accepted (source/offline only):** safe length-prefixed
texture-binding record rebuild on qualified existing diffuse/environment stages;
source-aware alpha compatibility; searchable picker; source-relative opaque reflection
weight and diagnostic mask; D3D9 F1/F3 control visibility; source `cull=false`
backface reconstruction and headlamp contour housing on the Pajero; source-qualified
opaque Nikon trim split; UV-only stock-MR crack pattern continuation on the
existing four-zone Subaru glass candidate. Save/Undo/Redo/Restore and baseline
source pinning remain required. See `docs/sdk/VSDK4C1_RESULTS.md`.

**Do not silently treat as gameplay-qualified:** author-supplied isolated Pajero
and Subaru test candidates remain separate. Pajero must be checked intact/damaged
for the Nikon-side solidity/reflections, backfaces, bullbar, mudflaps, headlamps
and brake lights under native D3D8. Subaru must be checked under individual
front/rear/left/right impacts against stock Navara and across race re-entry.
Native support remains **four logical zones**, not one controller per physical pane.
Combined 30-car roster requires a new independent acceptance pass after candidate
integration.

**Next bounded milestone, owner-approved order: V-SDK4B — Paint Studio, Classic MR
Style and Crew Fitment.** Begin this stage after recording the V-SDK4C.1 verdict
and retaining the isolated gameplay candidates. Do not start Blender Bridge or
wholesale body scaling during V-SDK4B.

- Build a reusable **Style Profile** layered over the imported project's immutable
  originals: Source Fidelity, Classic MR Style, Custom. Preserve baseline
  shaders, damage groups and source provenance. Switching presets must be reversible.
- **Paint/Recolor:** semantic coverage masks based on qualified geometry, UV and
  texture analysis. Preserve baked livery, logos, racing numbers, lamps, glass,
  tires and cockpit. Support native-material colour where valid and mask-aware
  texture edits otherwise; refuse unsafe global tint as selective painting.
  Support civilian cars with a verified paint region, not an invented universal shader.
- **Classic MR Style:** select existing resources from the user's local retail
  installation, inspect UV and alpha/material compatibility, preview alternatives,
  opt into per-surface assignments and optional explicit re-UV/texture adaptation.
  No legal/proprietary textures or audio embedded in source archives or releases.
- **Crew Fitment:** bring the qualified driver/co-driver insertion/reuse workflow
  from Subaru/Lancer into GUI; qualified seat anchors, preview with occupants,
  XYZ translation/rotation/size controls and visibility/conflict checks. Keep
  native gameplay poses, animations, deformation and camera separate from an
  unverified pure-preview adjustment.
- **Comparison:** synchronised Original / Modified source geometry and material
  views; clearly label D3D9 approximation. Record provenance, project layers
  and undo/redo/restore. Highlight changes and data dependencies.
- **Validation:** stock zero-edit, one imported car style + paint change, one
  qualified stock reference and one crew adjustment through Studio, actual build
  candidate for owner verification, protected glass/brakes/reflections/damage,
  baseline UI/audio/physics/camera, PERF2 and 30-car roster invariants.
- **Deliverables:** Studio GUI and shared Core, full real Windows evidence, user
  acceptance checklist, source-only review archive, updated MASTER_PLAN /
  CAPABILITIES / REGRESSION_MATRIX / COMMIT_LEDGER / offline F1 Help, and a scoped
  local phase commit after testing. No push or public release.

**Longer-term untouched roadmap:** V-SDK5 Blender round-trip, precise geometry
scaling/stock size comparisons, V-SDK6 Physics/Audio/Camera Studio with user presets,
V-SDK7 Fleet Builder, format adapters, installation/restore and public beta QA.


## 21. Owner gameplay acceptance and explicit Audio Studio commitment — 26 October 2026 (revision 4.7)

### V-SDK4C.1 final owner verdict

- The owner reports **all their intended Windows/gameplay acceptance checks passed**; Subaru now shows functioning breakable glass and Pajero's appearance is considered fully polished.
- Update the per-car evidence ledger to **OWNER GAMEPLAY-VERIFIED for the specifically observed glass/visual defects** after recording the exact candidate hashes/IDs and conditions from the owner's local checkout. The user's sign-off is genuine gameplay evidence, but do not expand it into claims about unobserved damage transitions, unlimited roster capacity, or all GT4 source versions.
- **Close the V-SDK4C.1 owner gate.** Preserve the source-only and Windows test caveats in earlier sections as historical evidence, and retain isolated candidate records.
- The next implementation milestone is **V-SDK4B — Paint Studio, Classic MR Style and Crew Fitment** as scoped in section 20. Keep it bounded: mask-aware paint, style profiles, local stock material matching, crew/co-driver fitment, build/restore, regression and a local validated phase commit.

### Audio Studio is a release-blocking capability, not a vague future idea

The owner particularly wants to import or assign **a distinct engine sound plus independently replaceable transmission whine, turbo spool and blow-off valve (BOV)**, and then hear those four independent layers in the actual game. This expands the existing V-SDK6 Audio Studio requirements in section 11; do not overwrite or postpone them silently.

**Existing baseline:** the project already has qualified custom engine playback (including user-provided GT4 Beta content in private local studies), and independent synthetic/SDK-authored whine, spool and BOV layers in an existing Lancer candidate; native per-CarID audio work must be reused, not reimplemented blindly. The exact legal status of every sample/preset must be verified before redistribution. The owner has not yet approved a new fourth vehicle or an exact GT audio donor/source.

**Minimum Audio Studio vertical slice:**

1. Vehicle Library → Audio Studio: distinct slots for **Engine**, **Transmission Whine**, **Turbo Spool** and **BOV**. Distinguish continuous loops from one-shot events. Show current source/provenance and active per-CarID profile.
2. Each slot: **Import/Assign Existing**, **Audition**, **Mute/Solo**, **Replace**, **Reset to Default** and **Undo/Redo**. External audio is read from user-owned local files, with original assets kept immutable.
3. A user-facing import pipeline with explicit *actually tested* accepted file types and sample rates, decoding, conversion, clipping/DC-offset checks, channel layout and target-format diagnostics. WAV PCM is a safe initial target; do not claim arbitrary GT proprietary sound formats are accepted until a decoder is qualified.
4. Engine loop points and pitch/RPM response; whine speed/load/gear response; spool boost/load response; BOV throttle-lift/shift triggers; per-layer gain/envelopes. All trigger semantics must derive from observed project/native behavior and identify previews/approximations separately.
5. Named reusable presets with **file hashes/paths (portable handling), source provenance, levels, response curves, triggers and event cooldowns**, and per-vehicle overrides. Missing files must show an error and preserve a predictable default; no silent global sound substitution.
6. Interactive audition plus an *isolated real-game candidate* exercising all four replaced layers. Test idle, rising/falling RPM, up/down shifts, turbo transitions, throttle lift, race re-entry, simultaneous AI vehicles, per-CarID isolation and release of voices/resources.
7. Prove restoration is exact for the original profile and that changing one layer does not change the other three or other cars. Keep the existing SDK-generated sounds available as defaults if distribution rights are cleared; user-supplied extracted proprietary audio stays local.

**Test-car selection:** use an already imported and qualified car with four-layer plumbing (initially Lancer Evo IV) for the first audio substitution proof to minimize unrelated geometry/physics risk. A **new, characteristically sounding imported vehicle** is an excellent second acceptance scenario and product demonstration, but only after the format adapter and candidate are qualified; do not declare or bundle a specific donor/source without local evidence.

**Schedule flexibility:** V-SDK6 remains the canonical Physics/Audio/Camera Studio milestone. Because the owner is keen to exercise sound replacement, the Audio Studio vertical slice may be **advanced immediately after accepted V-SDK4B**, ahead of V-SDK5 Blender Bridge, with a separate bounded phase, without deleting/renumbering the rest of the roadmap. The owner should explicitly choose the order at that handoff.

**Audio acceptance gate:** A user can replace engine/whine/spool/BOV independently, audition them, save a preset, build and verify them in-game on a specific CarID, restore all originals, and observe no sound leakage to other cars or race re-entry crash.

## Repository implementation ledger — V-SDK4B, 26 October 2026

V-SDK4B implemented editable Source Fidelity / Classic MR Style / Custom
appearance snapshots, explicit hash-pinned paint masks and named colours,
local-stock material references with shared-owner impact and Binding v2 checks,
qualified existing stock crew rest-pose authoring, matched GPU comparisons and
updated offline Help. See VSDK4B_RESULTS.md, CAPABILITIES.md and
REGRESSION_MATRIX.md for exact limitations, private evidence and owner checklist.

The owner acceptance recorded in supplied v4.7 closes the prior Subaru native
broken-glass and Pajero appearance gates only for those tested candidates.
New V-SDK4B appearance/crew candidates are OFFLINE validated; actual gameplay
of these edits is a separate owner gate. No broader capacity/version acceptance
is inferred. No future Audio/Physics/Camera GUI, Blender/scale or Fleet milestone
is started by completing this phase. Local phase commits are authorized; no push.


# Owner design decision — 26 October 2026 — Master Plan v4.8

## V-SDK4B acceptance scope and limitation

Owner reports Paint Studio works. Source-review V-SDK4B confirms editable Source Fidelity / Classic MR Style / Custom snapshots, exact mask-pinned paint, local stock materials and explicit assignment, qualified crew rest-pose editing, and matched native D3D9 comparison. However, **Classic MR Style is currently a manually authored appearance recipe**, initialized from the original; **it is not yet a distinct automatic MR aesthetic conversion**. Neither polygon reduction, simplified liveries, optimized atlas topology, nor Subaru-like solid/recessed MR wheel construction is provided by switching profiles. Mark the UI capability honestly until implemented.

Review artifacts: `rally-workshop-vsdk4b-source-review.zip` (966 entries, 964 manifest-verified, 406 Python parses) and `rally-workshop-vsdk4b-changed-files.zip` (22 entries, 20 manifest-verified, 12 Python parses). Independently checked synthetic tests: 15 appearance, 6 texture quality and 11 Workshop tests PASS. Codex reports full Windows 837 PASS / 1 optional skip with private runtime evidence; that Windows run was not independently reproduced. Local V-SDK4B implementation commit is recorded in review ledger as `de1cd394294ee1b2fce381d70913fa07f8ff4748`; bundled archives lack `.git` for independent history verification. New V-SDK4B game candidates remain owner-gameplay-pending. No unrelated native gameplay qualification is inferred.

## The real meaning of Classic MR Style

An **opt-in, provenance-preserving, rebuildable conversion recipe** to make imported vehicles plausibly belong to *Master Rallye 2001*, inspired by the frozen successful Subaru rather than a blanket texture-resolution reduction. *Source Fidelity* remains untouched. *Custom* contains user-specific layers. All three use a common, explicit asset graph with original inputs immutable.

Target qualities, qualified separately:

1. **Body shape and geometry:** deliberate simplification toward a measured class-appropriate stock MR polygon/silhouette envelope; preserve distinguishing shape, arches, windows and wheel apertures. Measure class-specific original MR `car.dx`, `complete.dx` and `wheel.dx` distributions first. No invented universal 1,000-/2,000-triangle target. Retain damage/glass groups, lights, crew, wheel hubs, mirror/culling, attachments, UV and collision validity; never confuse visual simplification with a gameplay physics change.
2. **Paint and livery:** clean main paint color, only selected signature decals/sponsor/number details, optional more/less sponsor density. Classify direct paint, separately layered decals and decals baked into shared atlases. Reassign/paint/mask and regenerate clean diffuse maps **only when verified**. Never remove decals by blurring; never claim automatic text/logo detection without evidence. When ownership is ambiguous, offer an editable manual mask and clear preview.
3. **Wheel archetype:** visual opaque dark recessed inner backing/spoke gaps, retained tire, correct lip/rim profile and wheel-face orientation, per-side consistency, no fake transparency holes. Reuse source-qualified routines from Subaru V-MESH wheel work; do not apply a global alpha override because alpha may control reflections or transparency elsewhere. Preserve tyre/hub, brake glow and damage expectations.
4. **Materials and reflections:** native MR-compatible diffuse/reflective/black/rubber/glass/lamp/cockpit families. Reflections must have qualified masks, strength, matching draw ownership and no accidental window opacity. Existing local stock textures are reference material *from the user's own installed copy*, not a global substitute for mismatched UVs; permit repacking/new simple generated textures as appropriate.
5. **Texture layout and performance:** reduce needless source detail, avoid excessive atlases and shared alpha ownership, pack by semantic role, regenerate UV when qualified, track memory and upload/build constraints; protect intentionally retained text and visible logos. 'Fewer atlases' is a quality/budget goal, not permission to merge glass, body, decal and effect into unsafe shared surfaces. Preserve PERF2 bulk file reader behavior and native cache headroom.
6. **Rest-pose context:** preserve already qualified driver/co-driver fitment; display a report on passenger/window interpenetrations. Full arbitrary character rigging and gameplay camera/physics-scale coupling are not part of this style milestone.

## WHEN to apply style: a single reproducible build graph

**Recommended default: user selects Classic MR Style at import/project setup, before the first game build/installation**, because geometric/atlas changes are most reliable while source semantics and original GT model data are still available. This must *not* edit installed retail assets or modify a frozen current candidate.

**Also support later conversion:** open an existing SDK-authored imported car, choose `Rebuild as Classic`, restore a pinned pristine source-import baseline, regenerate a separate Classic candidate and review a diff, then opt in to build. Do **not** decimate or downsample an already-decimated Classic output again. If source provenance is unavailable, report it and offer only verified manual retrofits; do not pretend full conversion succeeded.

Dataflow: `local source inputs (immutable) -> source geometry/material semantic manifest -> style analysis/report -> author-accepted Classic recipe -> deterministic staged geometry/texture/material/wheel outputs -> visual Previewer A/B and diagnostics -> validations -> isolated Build -> optional Test/Install`. Manual author edits are separately versioned/reapplied as layers where source lineage remains compatible; conflicts must prompt remapping, not overwrite user work. Source Fidelity and Classic coexist. Keep CLI and UI on identical reusable Core APIs.

## V-SDK4B.1 — next bounded milestone: prove an actual Classic Style conversion

**Do not request a general universal one-click GT3/GT4 remaster in one run.** Prove on one qualified already-imported GT4 model (recommended **Lancer Evo IV**), comparing against stock MR classes and the frozen Subaru's visual principles. Existing Lancer game features remain qualified independently; do not change unrelated physics, custom audio, brake glow, cameras, deformation or mechanics. Deliver:

- A reproducible stock-MR class baseline report (triangle/draw/texture counts, wheel appearance, material/alpha/reflection role categories); note reference samples, no arbitrary hard caps.
- A semantic mapping of one selected Lancer's body, decal, wheel, glass and special draws; rejected/ambiguous surfaces and source hashes.
- A source-to-Classic recipe that actually removes/retargets chosen excess livery, assigns a clean primary color, simplifies at least one qualified **noncritical** geometric region with measured before/after triangle counts, and creates an MR-style wheel with an opaque recessed backing without fake black/transparent gaps.
- Qualified material normalization, atlas/memory report and preservation of window damage, light/glow, collision, driver, wheel hubs, physics and camera.
- Fixed-camera Original/Classic screenshots for all sides and wheel closeups, wireframe/reference silhouette and material-debug comparisons; Previewer evidence remains D3D9 approximation.
- Project profile persistence, no-op/rebuild determinism, intermediate output report, preview, undo/restore and isolated build from original pinned source, never from previous Classic result. A practical `Choose at import` path and `Rebuild existing car as Classic` path share the same backend; if adding full import UI is too wide, expose the exact project initialization flag and an honest GUI entry point to that backend.
- Explicit owner gameplay checklist and frozen Subaru/Pajero/Lancer regression comparison; dedicated owner D3D8 acceptance remains pending until tested.

If safe topology/wheel edits are limited by fixed-draw DX writer requirements, preserve draw grammar and document the exact boundary. Do not silently erase special buffers, damage/glass/light state, or collision. If a selective transformation is unsafe, keep the component as source fidelity and report its status.

## Subsequent milestones and preserved obligations

After V-SDK4B.1 owner review, generalize qualified transformations to other import classes (Subaru and Pajero as regression controls), add adjustable `Classic intensity`/decal-preservation choices and a useful interactive style recipe editor. **Do not label incomplete geometric/style conversion as one-click Authentic MR.** Carry over V-SDK5 Blender round-trip and scaling, standalone Audio Studio with independent user-replaceable Engine, Whine, Turbo Spool and BOV layers (with test/audition/loop/RPM/gain/presets), and full remaining Physics/Camera/Fleet roadmap. Audio is a priority, not forgotten, but outside the narrow V-SDK4B.1 scope. Each accepted phase gets a local commit; do not push or publish without explicit authorization. Private MR/GT art/audio remain local to user-owned installations.


## Repository V-SDK4B.1 implementation ledger

Implemented a bounded, exact-source Classic Lancer conversion: approved cover topology reduction, regenerated characteristic red/charcoal livery, stock-derived opaque recessed rim, measured material/texture normalization and independent source/Classic versions. CLI initialization and Studio Rebuild call the same Core; explicit report approval gates builds. Manual layers remain versioned with conflicts, and rebuilding resolves the immutable original. See VSDK4B1_RESULTS.md, CAPABILITIES.md and REGRESSION_MATRIX.md for measured counts, private Windows evidence and exact limitations.

The owner approved the final appearance/report before the isolated Classic build. This closes only that preview/build-input gate; actual D3D8 gameplay is pending. Stop V-SDK4B.1 for owner review. Do not automatically generalize recipes, start Blender Bridge or Audio Studio. Prior Audio Studio and remaining roadmap obligations remain unchanged. Local phase commits authorized; no push or publication.
