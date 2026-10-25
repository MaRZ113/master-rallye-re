# Master Rallye Vehicle SDK — Master Plan / Rally Workshop

**Working baseline:** 25 October 2026 (reviewed V-SDK2 + V-PAJERO3 source overlays, revision 3)  
**Repository:** `master-rallye-re-vehicles` · **branch:** `research/vehicles`  
**Purpose:** single living specification for development, review, acceptance and public beta planning.  
**Status disclaimer:** this document summarizes previous source-review discussions and reported gameplay tests. It is **not** a new repository or binary audit; verify each item against the current checkout before implementation. Update the ledger after every development phase.

## 0. Product contract

**Vision:** a Windows-oriented, free Vehicle SDK / **Rally Workshop** for creating new cars and editing stock Master Rallye (2001) vehicles without hand-editing native resources. A user should be able to open a car, examine its in-game-like appearance, edit materials/textures/geometry/physics/audio/cameras, validate, build, test and revert.

**Core principles**

1. Original `MRallye.exe`, existing graphics `d3d8.dll`, and retail files on disk remain unchanged. Use the qualified external runtime and reversible, isolated resource overlays.
2. **Stock car edit** and **new CarID addon** are distinct installation types, managed by one project model and Studio UI.
3. Every transformation is non-destructive, reproducible, testable, and traceable to input resources and configuration. Immutable input + editable layer(s) + generated output.
4. GT3/GT4 resource extraction is optional and local. Never include/distribute proprietary models, textures, audio, icons or game binaries. User-created/licensed assets also work.
5. `Randomizer & AI Extender` remains a separate project; no unapproved integration.
6. No git commit, push, release or publication without explicit authorization. No claims of in-game verification based solely on synthetic tests.
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

### NEXT ACTIVE: V-SDK3 — Studio Foundation / first vertical slice
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
