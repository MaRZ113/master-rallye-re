# Master Rallye Vehicle SDK — Master Plan

**Status:** active working plan
**Last reviewed:** 1 November 2026
**Canonical repository path:** `docs/sdk/MASTER_PLAN.md`

> **Keep this document current, not cumulative.** Edit sections in place; remove superseded tasks and outdated assumptions. Do not append dated checkpoints, paste old plans, create `v8.x` copies, or reproduce test-run diaries here. Git history, `COMMIT_LEDGER.md`, focused technical reports and issue records preserve historical details. This document contains only the current product direction, verified baseline, decisions, priorities and acceptance criteria.

## 1. Product goal

Build **Rally Workshop**: a responsive, attractive Windows vehicle editor and SDK for Master Rallye. Users should be able to import vehicles from supported source games, edit geometry and materials, create native MR effects, preview results, and install reversible mods **without writing Python or asking the developer to bypass source-fidelity checks**.

The visual objective of **MR Classic** is organic integration with stock Master Rallye—not emulation of an entire donor-game renderer. **Source Fidelity** is a separately preserved option. A faithful vehicle, a deliberately restyled vehicle, and a user-customized vehicle are all legitimate project outputs.

## 2. What currently works (baseline; confirm against checkout)

| Area | Verified baseline and remaining boundary |
|---|---|
| Native MR Workshop | Native DX/DXT preview/build, qualified stock edits, physics, camera, audio, shadows, crew, damage/glass, brake states, identity, frontend/results and reversible candidate builds exist. Do not regress them. |
| GT3 / GT4 | Subaru, Lancer, GT4 Pajero, Clio source/colorway and **GT Classic** work provide visual and authoring precedents. Current Classic backend is still GT-specific and needs donor-neutral integration. |
| 4x4 Evolution 2 | Toyota 4Runner runs in MR (owner-tested). Source geometry and wheels decode. Original nine-color CPU recolor and second TIFF sample's recoloring contribution have been researched; some source GPU/bump/gloss behavior remains uncertain. |
| PC Paris-Dakar Rally | RED and Silver Pajero source scenes decoded. Silver has run in MR; owner reported stiff suspension. The models are not proven to be the missing original MR promo assets. |
| Dakar 2 Xbox | Pajero, Nissan Pickup and Hino source models decoded and previewed. Original multistage shader semantics partly recovered. **Strict shader-equivalent native materials remain blocked**; do not let this automatically prohibit an explicitly adapted MR Classic project. |
| Michelin Rally Masters | RAV4 and Mégane F2 neutral scenes recovered. RAV4 runs in MR with working handling/body/glass damage (owner report); wheel-edge and brake-lens fixes exist as isolated candidates, **D3D8 owner verification pending**. Mégane native import is not owner-qualified. |
| Vehicle capacity | Owner accepts the32-record Forester/RAV4 reference (8/12/12). A separate33-record8/12/13 configurable-order candidate passes offline validation; its D3D8 lifecycle/save/AI remains pending. Alternative CarID29 configurations remain independent. No unlimited capacity claim. |
| Workshop UI | Legacy Tk remains supported. Source Garage has dependency-aware preview caching and asynchronous open/render with safe cancel. An optional PySide6 Widgets editing pilot is validated on Dakar2 Pajero and a GT-derived native snapshot; the remaining Studios have not been migrated. The reported15-second delay was not reproduced on the measured Pajero workload. |

Source-only review archives and automated tests do not prove original-game rendering parity or actual D3D8 gameplay. Use the detailed reports for evidence and exact build hashes; this plan deliberately omits historical test counts and commit-by-commit narratives.

## 3. Product decisions

1. **Three authoring modes:** `Source Fidelity` (immutable donor interpretation), `MR Classic` (reversible MR-native restyle), and `User Customized` (free editing of derived geometry/materials). Preserve the unmodified donor project.
2. **Editability is normal:** vertex moves, topology changes, new meshes, UV edits, wheel backings, spare wheels, material/Glow/reflection assignments and copying qualified stock MR effects are legitimate. Source hashes/triangle counts are not hard export gates for intentional edits.
3. **Validate the result, not obedience to the source:** reject malformed indices, unsafe binary/resource changes, incompatible controllers and destructive writes. Show warnings or request re-binding when source ownership becomes obsolete. Never silently retain stale face/material/controller IDs after topology changes.
4. **MR Classic is donor-neutral:** use explicit surface roles and reusable MR material references; no GT-only assumptions or rectangular UV-atlas shortcuts that create broken reflection islands.
5. **Compact installed mods:** target a small, compatible runtime DLL plus external resources and manifest, using existing reversible runtime/overlay research. The **editor's** distribution size is a separate concern from the **in-game mod's** footprint. No ordinary-user dependence on a full duplicate game installation.
6. **No unnecessary feature/research expansion:** improve the existing garage and conversion workflow before adding more donor games.

## 3A. Current priority: V-DEF3 roster/order owner qualification

**Accepted baseline:** the owner confirms corrected Demo Forester (ID30) and
Demo RAV4 (ID31), including the independent retail Newrav physics. Preserve
V-DEF1 owner-fixes/release and V-DEF2 physics-identity/release unchanged. RAV4's
121 historical Demo parameters remain inactive evidence; its known source versus
physics wheelbase difference remains documented, with no geometry/hub offset.
Full race/Results/save claims must still refer to actual specific owner evidence.

The common SDK/Workshop builder now separates physical IDs and canonical
reservation locals from a configurable selection permutation. Forester follows
retail WOOLDAND8; Demo RAV4 follows retail Newrav12 without renumbering30/31.
Per-project class assignment is explicit; non-T2 AI insertion remains unsupported.
Workshop saves private copies of roster settings rather than modifying accepted
configs. Source adapters, native models and gameplay Studios are unchanged.

An isolated33-record (8/12/13) CMD test package adds only a labelled technical
retail Wildcat clone at ID32 beside Wildcat14. This is not the full Demo vehicle
restoration. Original Demo8.4.1 registration/localization proves its future
historical display identity **TOMCAT / PRIVATEER TOMCAT**. Do not infer authentic
old geometry from the user-replaced current rebaked folder.

All33 forward/reverse maps, native publisher13/navigation, initializer/name/audio
ABI, resource/UI/physics preservation and two deterministic Workshop builds pass
offline. The explicit33 profile uses bounded512-KiB process storage; existing
profiles keep their earlier budgets. Original EXE, Data.sma, wrappers, Randomizer,
accepted projects and saves remain untouched. Configured-order packaging refuses
active saved championships; no silent migration or progress reset is permitted.

**Stop for owner review:** test adjacency, all T3 positions, selection, fresh race,
Results, re-entry, disposable championship save/load and Randomizer coexistence.
Do not call this33-record layout gameplay-qualified yet, begin full TOMCAT
restoration, expand AI pools or add another slot. See
`V_DEF3_ROSTER_ORDER_RESULTS.md` and `V_DEF3_PROVENANCE.json`.

Original RAV4 identity/marker remain UNKNOWN; editable **DANIEL NEBOT /
REAL_FALLBACK** and blue SDK marker remain labelled fallbacks. Newrav/Reece
Russell is not transferred to retired RAV4. Preserve the eight-case historical
matrix and original-source values in `DEMO_DRIVER_COLOUR_EVIDENCE.md`.

### Historical V-DEF1 implementation/qualification snapshot

The paragraphs below retain the state recorded before full owner acceptance;
the acceptance above supersedes their old pending status, not their evidence.

The complete Demo audit is retained in `DEMO_VEHICLE_AUDIT_RESULTS.md` and its
matrix/shortlist. The first authorized restoration now has a persistent Workshop
project and isolated CMD candidate: canonical9.3.1 Demo Forester geometry,
authenticated original CarSheet and separate Demo9.10.0 side mini icon,
owner-confirmed Darren Sutherland, independent RETAIL Forester physics and
bounded native glass/WOOLDAND ON-core/halo adaptations. Demo physics remains
historical evidence after the owner reported excessive tyre wear. The complete
model alone is rebased upward by the measured retail rest-frame difference
0.38971442m; race geometry and original source files remain unchanged.
See `V_DEF1_FORESTER_RESTORATION.md` and `V_DEF1_FORESTER_OWNER_TEST.md`.
Current private candidate: `vehicles/v-def1/owner-fixes/release` under
`.research-output`; previous `release-candidate` remains available for rollback.

**Owner-qualified capacity remains30 (8/10/12).** A separately gated31-record
candidate appends ID30/T2 local10 (8/11/12); automated checks and CPU helper
emulation pass. Owner screenshots confirm selection/race entry, and the owner
explicitly confirms the race driver name. Full race completion, Results, AI,
saves/re-entry and the FOUR corrected behaviors remain unverified. Existing
IDs,accepted projects and originals are unchanged.
No rear glass zone was invented; broken UV/shading and halo fit are explicit
adaptations. Incorporate owner feedback before promoting this layout or another
restoration. The unrelated Nov Wildcat collection drift detected against the
prior audit is preserved,not rolled back: the owner confirmed intentional
replacement of misleading Simmbugghini files with original9.3.1 Wildcat.
54 focused and1315 full Windows tests pass (2 existing skips);222 DX/DXT repeat
exactly and308 previous roster resources remain unchanged. DLL stays separate.

## 3B. Deferred priority: Definitive Edition vehicle runtime

Follow `MASTER_RALLYE_DEFINITIVE_ROADMAP.md` for the product direction. First qualify a small external-resource vehicle runtime that starts with compatible game versions, preserves installed wrappers and coexists with Randomizer. SHA is diagnostic evidence, not a universal executable allowlist: select version-specific profiles using verified PE layout, relevant code/data invariants and hook preimages. Reuse J.1/J.2 and the J.3 compiler. Retail EXE evidence supports loose-first resource reads and archive fallback; Workshop can prepare a non-installable resource draft from an existing bundle. Prove the complete original-game resource and startup path before calling it installable; installation, shutdown and conflicts must fail safely. Two Randomizer F3/J.2 Challenge instruction overlaps, a general loading seam, initialization timing and adapters for other retail variants remain unresolved. See DLL_EXTERNAL_RESOURCE_DEPLOYMENT.md.

The independent Demo/PS2 Forester is now prepared as the explicit V-DEF1 CMD test above, distinct from retail WOOLDAND. Do not reuse CarID29 or treat the automated31-record proof as owner qualification. Continue universal DLL/version/Randomizer work only as its separately reviewed milestone.

The editor work below remains supported and resumes after the separately reviewed runtime foundation; current Workshop functionality must not regress.

## 4. Workshop usability and architecture — subsequent priority

### A. Measure and fix responsiveness first

Implemented backend: versioned source-memory/staged-preview/image caches, manifest-local dependency checks, atomic commits, bounded LRU, Force Refresh, worker cancellation and explicit test tiers. See WORKSHOP2_PERFORMANCE_RESULTS.md and SOURCE_VS_AUTHORING_VALIDATION.md. Native builds still fully verify original resources.

- Instrument actual Windows startup, project opening, donor decoding, UVS evaluation, preview staging, D3D9 process startup/rendering and vehicle switching. Compare cold and warm paths.
- Implement versioned, dependency-aware **memory/disk caches** for parsed assets, evaluated scenes, staged GPU resources and previews. Unchanged vehicle reopen must be a cache hit; camera changes must not trigger source re-decoding.
- Invalidate only affected layers after geometry/material/texture changes. Ensure deterministic cache keys, bounded storage, safe atomic writes, stale-result protection, cleanup and Force Refresh.
- Keep the UI responsive during long operations; show meaningful status/progress, cancellation where safe and errors. Do not invent percentages.
- Aim for **sub-second warm reopen where measurable and technically feasible**; report actual before/after timings rather than claiming it in advance.

### B. Change UI direction: investigate Qt 6 / PySide6

- **Do not spend another major phase reskinning every Tk window.** Treat Tk as the supported legacy UI during migration.
- The optional **Qt 6 / PySide6 Widgets vertical slice** implements library, mesh/face inspector, dark controls, progress, editable journals and separate neutral/native D3D9 captures. See WORKSHOP2_QT_RESULTS.md. QML and embedded D3D9 are not introduced; keep the external viewer boundary explicit.
- Preserve working Python backends. First validate integration of the existing native Windows D3D9 viewer: embedding or coordinated external window, focus, input, resize, high-DPI, device loss and lifetime. **Do not assume embedding is trivial.**
- Benchmark startup/memory and verify packaging/deployment and Qt licensing obligations before committing to the migration.
- If the pilot succeeds, migrate Studio-by-Studio using shared panels/widgets and one design system; retire Tk views only when replacement workflows pass acceptance. If embedding is fragile, use an explicit preview-window boundary instead of delaying the entire editor.
- The style should be coherent across main window, Source Garage, Model/Material/Glow, Physics, Camera, Audio, Shadow, Frontend and Help: restrained dark motorsport visual language, legible typography, consistent sliders/buttons, strong selected/disabled/focus states, good DPI and keyboard support.

### C. Shorten development feedback

- Keep all meaningful tests, but use `focused`, `smoke`, `integration`, `full` tiers with change-based selection.
- For small UI/material edits, run affected tests and fast smoke; for shared bridge changes run relevant integration; run the **full 1300+ suite once per milestone or significant risk**, not repeatedly after every trivial patch.
- Reuse safe immutable fixtures, profile slow tests, report selected/omitted suites transparently and preserve reliable Windows GUI/native checks.

## 5. Next priority: make editing and MR Classic genuinely usable

- The versioned editable derived-scene journal is implemented above immutable UVS, with stable face IDs, transactions, undo/redo/restore, save/reopen, geometry/material edits and common-bridge native fixtures. The Qt pilot now demonstrates editing/material references/Glow/save/reopen and deterministic fixtures; legacy native-project migration remains explicit, not an automatic rewrite. See EDITABLE_VEHICLE_SCENE_ARCHITECTURE.md.
- Provide working UI controls to select faces/meshes, move/add/delete geometry, duplicate parts, adjust UVs and create or move a rear spare/wheel backing; these must survive compilation.
- Implement shared **Material & Glow Studio**: copy a stock MR material/effect onto selected *derived* faces; change opaque/cutout/glass/tyre/rim/reflection/Glow roles; edit brake OFF/ON separately; inspect exact output coverage; revert independently. Original MR glow and reflection behavior is a reference, not an unchangeable source hash gate.
- Split native material/draw groups where needed for intentional edits. Preserve the opaque base and correct window/paint boundaries. Disallow truly invalid MR output, not artistic deviation.
- Make GT Classic recipes available to non-GT scenes by **semantic roles**, preserving accepted legacy GT builds. Compare imported vehicles against stock MR visual references, not only donor-game shaders.
- Demonstrate the core owner scenario on a **Dakar 2 Xbox Pajero derived project**: add/reposition a spare, author wheel backing, apply MR paint/reflections/Glow, save/reopen and produce isolated native output. Strict Xbox shader Source Fidelity may remain BLOCKED without blocking reviewed Classic material substitutions.

## 6. Native mod delivery and engine capabilities (after the editing pilot)

**Deployment:** prove one reversible real-game launch with a small runtime DLL + external vehicle resources/manifest; version/conflict checks, no replacement of the installed `d3d8.dll`, no modification of original executable or clean retail archive. Development sandbox builds may remain isolated; ordinary installation should not require launching a duplicated game tree.

**Fleet limits and class research:** establish the actual max vehicles per class and total across selection, race, AI, Results, saves and UI. Examine the known 12-position frontend publisher separately from engine capacity. Test 31st/32nd entries only in isolated reversible builds. Research a **new class** as a distinct end-to-end operation, not just a menu tab. Do not state an unmeasured maximum as fact.

**Color presets:** prototype one vehicle-select control to cycle **multiple liveries per vehicle identity**, with frontend/race consistency and persistence. Prefer this over spending a physical CarID on each paint. Keep the main roster unchanged until real gameplay confirms the feature.

## 7. Existing source backlog — bounded, not blocking the product refactor

- **RAV4:** owner-test the combined wheel/lamp correction in D3D8; retain baseline and A/B/C/D comparison. No unrelated retuning.
- **Dakar 2:** retain full source-shader research and strict fidelity status; start with an explicit MR Classic authoring proof, not a forced full Xbox renderer recreation. Separate future truck physics validation for Hino.
- **Evo2:** preserve nine recolor variants and partial renderer unknowns. Do not reopen the already-working 4Runner for cosmetic experiments without user request.
- **Michelin Mégane:** use the shared edited/Classic pipeline after the authoring layer is proven; do not copy RAV4-specific lamp face IDs.
- **PC Paris-Dakar Silver:** owner-reported stiff suspension belongs to later Physics Studio tuning, not source parser research.
- **Historical MR lost vehicles:** red Citroën ZX #206, silver Ranger #205 and ambiguous early Pajero/SUV appearances remain evidence projects, not proof that their original meshes have been recovered. No new game-search phase now.
- **Blender Bridge:** planned later. Design stable editable scene IDs and mesh/material round-trip now so Blender integration can be added without another foundational rewrite.

## 8. Delivery and acceptance

Each development milestone must show a **usable owner workflow**, not just a test count:

1. Repeat-open an unchanged car and demonstrate a measured cache hit with responsive UI.
2. Change geometry and materials in the editor; save/reopen and preview the correct result.
3. Assign native MR reflection and Glow to user-selected derived surfaces without hardcoded source triangle IDs.
4. Build one safe reversible native project with meaningful errors only for real incompatibilities.
5. Keep existing accepted vehicle projects unchanged; provide targeted automated checks plus actual Windows GUI and D3D9 evidence. Record D3D8 game validation only when the owner performs it.
6. Deliver a compact documented change summary, exact remaining blockers, and update the **same** `docs/sdk/MASTER_PLAN.md` in place.

**Protection:** preserve original `MRallye.exe`, clean `Data.sma`, installed `d3d8.dll`, original donor installations, Randomizer, accepted projects and source-scene evidence. Keep private copyrighted assets out of source-only packages. Scoped validated **local commits** are authorized; **no push, publication, release or unrelated merges** without explicit permission.

## 9. How to maintain this plan

- This file is the **only current Master Plan**. Do not create chronological copies or paste older versions below it.
- Edit current decisions, baseline, active priority and blockers **in place**. Delete superseded instructions; move extensive historical evidence to focused `docs/sdk/*_RESULTS.md`, qualification matrices or Git/`COMMIT_LEDGER.md`.
- Keep individual milestone reports short: `changed`, `owner-tested`, `remaining`, `next`. Do not paste entire prompts or test logs here.
- If new evidence contradicts this baseline, correct it with a citation to a repository report or a test, rather than preserving both incompatible claims.
- Prefer clear scope and a small number of completed vertical slices over enormous all-at-once refactors.
