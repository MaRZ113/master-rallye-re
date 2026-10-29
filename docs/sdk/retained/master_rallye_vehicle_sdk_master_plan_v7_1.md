# Master Rallye Vehicle SDK — Master Plan v6.7

**28 October 2026 — independent Source Garage phase-1 audit review, next bounded adapter qualification.** This update prepends a new checkpoint and preserves the entire previously authored v6.6 document **byte-for-byte below**. The changed-files archive's `docs/sdk/MASTER_PLAN.md` was separately observed to omit the v6.3–v6.5 addenda: restore those historical sections in the main repository rather than replacing them with a short status note.

## Source Garage phase-1 evidence

- Input reviewed: `changed-files.zip`, **26 entries** including 25 SHA256-pinned changes and one review manifest; ZIP CRC PASS, **25/25** SHA256 PASS, **9/9** Python AST PASS. Independently ran **50/50** supplied synthetic Source Garage tests. No full-source review ZIP, original donor games or private evidence were supplied for this review, so byte-level 16-game revalidation and the full Windows suite were **not independently rerun**.
- Research agent reports read-only inventory of **16** local donor roots, **38,762** files and **45,961,878,729** bytes; an external 11,047,585-byte full inventory SHA256 is recorded, but its content is not attached. The agent reports **1,017 complete synthetic/CPU tests, two skips** and unchanged protected assets; those claims are attributed to the agent's private evidence.
- Five PC representative structural/visual **diagnostic** probes: 4x4 Evo1/Evo2, Screamer 4x4, V-Rally 2 and Sega Rally 2. No source-game renderer parity and no new Master Rallye gameplay tests. Additional Revo SBF archive/DDS and DiRT1/DiRT2 PSSG dictionary probes do **not** qualify assembled vehicle import.
- **Paris-Dakar Rally (2001):** actual `PajeroRED.tc` and `PajeroSilver.tc` exist with `RallyCar 1.00`, `ArchList` and `Gex#MainBody.x` string observations. No verified mesh decode, Pajero V60/V20 identity mapping or direct connection to prerelease MR models.
- **Michelin Rally Masters:** static `Cars.BIN` plus script associations link `Toyota RAV 4` ID25 to `Car25A.PDO` and `Renault Megane F2` ID6 to `Car06A.PDO`. Five PDI1 directories were structurally validated; XO, `_VERTEX.BIN`, INDEX.TOC and TGA entries are *undecoded* payloads. Do not claim Mégane Maxi mesh confirmed or source model rendered. Retain personal priority high.
- **DiRT 2007 versus DiRT 2:** distinct PSSG type dictionaries are confirmed, with ambiguous duplicate attribute identifier in the early Neon example. No glTF car export or original shader equivalence qualified. Community tool availability is not a tested importer.
- **Universal Vehicle Scene** is currently a proposal, not an implemented universal source adapter. Current GT3/GT4 Classic v2 gates, accepted Heritage native MR passthrough and sound systems remain separate.

## Proposed next phase — 4x4 Evo2 Toyota 4Runner source adapter pilot

**After owner approval**, implement one conservative, deterministic read-only source adapter and fully assembled vehicle inspection for **4x4 Evolution 2, Toyota 4Runner SR5 Sport Package 2WD (2000)**, joined through `TRUCK/T4RSR52.TRK`.

1. Pin and validate the exact user-local `TRUCK.POD` and read selected POD2 members with bounded ranges and paths. This is a modified installation with TRIHook; do not present the content as untouched publisher retail.
2. Decode source body `MODELS/4RUNNERSR5.SMF`, material/UV streams and `ART/4RUNNERSR5.TIF`; preserve **33 objects, 2,089 vertices and 1,967 triangles** according to the original agent probe, along with original indices and evidence. Six wheel model variants (`08/12/16`, left/right) and all four source TRK wheel placements must be reconstructable. Validate actual components against source files; counts are not proof of successful assembly.
3. Determine coordinate axes, units, wheel rest pose and hierarchy with independent evidence. Existing Blender tool feet-to-metres convention is a hypothesis until source confirmation. A source TIFF alpha255 channel does **not** qualify glass opacity, lamp states or native MR materials.
4. Implement the minimal versioned Universal Vehicle Scene contract for this one format, including provenance/unknowns and private bounded sidecars. Save immutable source values and reversible derived transforms; do not silently normalize or delete ambiguous parts.
5. Produce an **assembled textured L2 diagnostic preview**, origin/axis/wheel fitment measurements, material/UV inspection and fixed-angle images, with documented renderer differences and source source-version hashes. Preserve unknowns, damaged-state, equipment, alternate source bodies/LODs/colorways as unresolved where not evidenced.
6. Test corrupted/oversized containers, missing members, transformed wheel variants, invalid UV/material references, source immutability and determinism. Re-run targeted and full available Windows regression suites. No external game or legacy binary execution without explicit approval.
7. Stop at a reviewed **neutral scene + preview**. Only after a new authoring approval should the neutral scene be mapped into a separate Master Rallye addon candidate and existing Classic MR Style transformations. Do not create a CarID, overwrite stock files or change accepted projects in this pilot.

### Historical research tracks preserved

- Paris-Dakar Pajero: bounded TC section/table/mesh decoding and two-file geometry comparison are a *separately authorized* research task; do not silently start a large RE campaign.
- Michelin RAV4/Mégane: next technical blocker is bounded wrapper TEA/LZSS8 decoding followed by XO/vertex/material research. Keep the catalog join and original F2 label. Do not claim finished or distribute source assets.
- Screamer Pajero remains second technical pilot option if Evo2 body/wheel binding blocks; V-Rally 2 and Sega Rally 2 remain diagnostic follow-ups, DiRT remains longer-horizon.

## Project protections and acceptance levels

- Current accepted native MR, GT and Heritage Subaru/Lancer/Pajero/Trooper projects remain immutable; Clio game testing is pending; accepted alternative CarID29 rosters remain mutually exclusive; **30 active entries** is the currently qualified limit.
- Never edit original `MRallye.exe`, clean `Data.sma`, existing `d3d8.dll`, original donor installations or unrelated Randomizer code. No bundled proprietary game source assets or unreviewed third-party scripts in distributable source archives. Observe licences and protect path/input budgets.
- Keep `L0` container discovery, `L1` structural assembly, `L2` human-inspected 3D preview, and owner-confirmed D3D8 gameplay evidence separately labelled. New donor gameplay is currently **NOT TESTED**.
- Local scoped commits permitted after verified tests. Do **not** push, publish, release or merge unrelated branches without explicit owner approval.

---

## Previous Master Plan v6.6 — preserved verbatim

# Master Rallye Vehicle SDK — Master Plan v6.6

**28 October 2026 — GT Garage Lab source-review closeout and Source Garage new-chat handoff.**

This is a non-destructive continuation of the complete v6.5 plan below. Prior roadmap, protected inputs, user-approved builds, and all earlier research remain intact.

## Current verified status — GT Garage Lab

- Supplied source-review ZIP: **1,253 source members**, manifest SHA256 **1,253/1,253**; changed ZIP: **68 members**, all byte-identical to the full ZIP and their own manifest. Zip CRC passed; Python AST **546/546**. No bundled `.dx`, `.dxt`, `.sma`, `.wav`, `.exe` or private extracted game resources detected. These are archive and syntax checks, not a full runtime or code-security audit.
- Independent Linux-targeted synthetic validation: **76 tests ran, 75 PASS and one skip**, no failures. The Codex report claims **967 tests with 2 optional skips** on Windows; that full result was not reproduced here.
- Review metadata: source snapshot commit `b9a24f7aadef6683a79a2d37bc03dea92a198706`; implementation commit `138df440709d1876080e852987da45a25267e3c7`; baseline `9416ddbc976da283964ab0ea621884b1789e0fe4`. Review ZIP has no `.git`; metadata is not an independently verified Git history.
- GT3 L0 local US `SCUS_971.02` result as reported by Codex: 5,333 RoFS entries, 574 day/night members, 572 structurally parsed, 2 empty/MISSING INPUT (`ho0100`), 562 unique model hashes. US/EU/JP catalog entries 244/244/242; exact source associations 244/231/242, including 13 EU source references missing in the examined US volume. These counts are **not playable-car claims** and private source corpus was not independently rerun in this review.
- Parallel automatic source-profile work reports **257 derived profiles / 287 GT3 day models**, 30 unresolved. Standard profile mode uses qualified approximations: donor scaling, MR rubber/crew and inferred glass/brake; Full mode preserves more GT imagery. Derived/compiled does not mean visually or in-game qualified.
- True original colorway source selection is implemented using GT3 carcolor IDs/records, not RGB tint. Non-Lancer pilot: **Renault Clio V6 `re0011`**, four authentic source choices: Iceberg Silver, Illiad Blue, Mars Red, Nocturne. Independent Source Fidelity and Classic pipelines exist; user edits persist separately per original-color project.
- Classic v2 is explicitly opt-in, semantic-role and hash guarded, preserves unclassified surfaces; v1 Lancer reproduction is retained. Clio includes separate MR-like rims, rubber and glass, corrected presentation hubs and reflections. **No generic automatic vehicle-wide polygon reduction or sponsor removal is proven.** CLUT, VU lighting, source rig and some effects remain unresolved, with L1/L2/owner gate differences preserved.
- The isolated Clio Source Fidelity and approved Classic candidates use an **alternative 30-slot** roster (Subaru27, Lancer28, Clio29). They cannot be simultaneously installed as CarID29 with accepted Pajero or Heritage Isuzu projects. According to source reports, candidate resource differences are Clio-only. Owner D3D8 gameplay for Clio is still **NOT TESTED**.
- Preserve accepted prior Isuzu owner gameplay evidence, Subaru/Lancer/Pajero accepted changes, clean retail `Data.sma` SHA256 `03c2b52d451b378c7ec634132ebfab706616e33c57fea2985b83db66d3fd4b2f` and protected MRallye.exe/d3d8.dll originals.

See `docs/sdk/GT_GARAGE_RESULTS.md`, `docs/sdk/AUTO_IMPORT_RESULTS.md`, `research/vehicles/gt-garage/SYNCHRONIZATION-2026-10-28.md` from the reviewed source tree for exact evidence and limitations.

## Next active milestone — Source Garage (new Codex chat)

**Purpose:** Research donor-game formats, tools, source editions and model readiness before writing the first new importer. This is **not** a command to import every vehicle, add new game slots, or start a DiRT converter.

### Donor game scope

1. Paris-Dakar Rally (2001): Pajero V60 and Evolution V20 historical lead; model identity with prerelease Master Rallye remains an unproven hypothesis.
2. Michelin Rally Masters: Toyota RAV4 and Renault Mégane Maxi; personally important elevated research priority, not an implied easy or first implementation.
3. V-Rally 2; 4x4 Evolution 1 & 2; Screamer 4x4: potentially easier technical probes with existing tools, subject to local validation.
4. Sega Rally 2 Championship and Sega Rally Revo; Rally Championship Xtreme; V-Rally 3: independent format/tool audits.
5. Colin McRae Rally 3, 04 and 2005; Dakar 2: The World's Ultimate Rally (verify platform-specific game files).
6. Colin McRae: DiRT (2007) and DiRT 2 (2009): late-era special vehicles, with first DiRT/Neon independently qualified rather than assumed equivalent to later EGO/PSSG.

### Required Source Garage process

- Audit only locally user-provided game installations/images and independently verify exact editions/platforms, archive signatures, hashes, model files, texture paths and source asset licenses. Configure **external paths**, not gigabytes of bundled files or guessed absolute locations. Inventory missing inputs explicitly.
- Research and verify community extractors, QuickBMS/Noesis/Blender tools and their exact versions, capabilities and licenses. Avoid running unknown legacy binary tools blindly; prefer source review and bounded reproducible tests. Link legitimate research/documentation only; do not download or redistribute proprietary game assets.
- Test separable gates: container opened → vehicle located → geometry/UV/materials → textures → wheel transforms → LODs → frontend preview. Record per-build L0/L1/L2 results as PASS/WARN/FAIL/UNSUPPORTED/NOT TESTED/MISSING INPUT with logs and hashes; **never equate archive extraction with 3D reconstruction or D3D9 preview with D3D8 gameplay**.
- Produce a tool/format matrix and prioritized importer decision based on **two independent axes**: owner `personal_priority` and evidence-backed `technical_readiness`. Paris-Dakar and Michelin are both high-interest; first implementation may rationally use a simpler source.
- Reuse a future source adapter interface feeding the common geometry/material/texture/wheel scene into existing MR authoring and Classic stages. Do not mutate frozen GT or Heritage candidates or overwrite package initializers/old branches.
- Maintain source-only outputs, ignored private extracted directories, immutable source handling, scoped local commits after validation, and no push/publication/branch merge without user permission.

### Source Garage phase deliverables

`DONOR_FORMAT_MATRIX.md`, `DONOR_TOOL_AUDIT.md`, `DONOR_CORPUS_MANIFEST.json` (no proprietary bytes), `DONOR_FIRST_PILOT_DECISION.md`, selective read-only smoke-test scripts and evidence, explicit unknowns, updated existing SDK plan/capability/test ledger, and a small new-chat continuation summary. Stop after audit for review before starting first cross-game adapter.

---

## Full prior Master Plan v6.5 (preserved verbatim)

# Master Rallye Vehicle SDK — Master Plan v6.1

**27 October 2026 — owner-confirmed Heritage Isuzu race closeout; upcoming Vehicle Presentation Polish.** This is a non-destructive update to the existing v6.0 roadmap. **Gameplay Camera 2.0 remains in progress at the main Codex**, and this addendum does not interrupt or alter that active work. The complete earlier plan follows unchanged below.

**Current implementation status:** Camera2.0 and the bounded Vehicle Presentation
Polish are now implemented and validated offline/Windows. The original owner
roadmap text below is retained as received; final status is appended at the end.

## Owner's new in-game acceptance evidence — Isuzu Trooper Demo 9.3.1

The owner provided three original game screenshots: Isuzu Trooper Vehicle Select, Isuzu as `DEMO TROOPER` in the Race Time/Results list, and a stock Reece Pickup (RAV4 comparison) Vehicle Select framing reference. The owner explicitly confirms the following for the Heritage Trooper test roster: vehicle appears in game with source wheel placement, usable native physics, working brake lamps, breakable glass, sound, menu/Results icons, stable race completion and return to the menu. These items are now **OWNER_CONFIRMED_GAMEPLAY** for this tested candidate, not merely source/offline qualifications. No automatic inference about untested split-screen, campaign, all race types, the alternative Pajero roster, unlimited capacity or other Demo cars. Keep independent Pajero and Isuzu configurations separate at CarID29.

## A. Results driver/participant name — existing capability, UI clarity

**Already present:** `Vehicle Details / Race HUD` in `src/master_rallye/workshop/vehicle_ui.py` exposes `Race Results display name (64)`; `src/master_rallye/workshop/vehicle_authoring.py::details_update` updates `addon.json -> results.display_name`, validates printable ASCII length <=64, and persists it through project authoring. `addon_sdk/manifest.py` requires `{policy: fixed, display_name: nonempty ASCII}`. The Results screenshot shows `DEMO TROOPER`, consistent with the configured fixed display name. The editor therefore does NOT need a second duplicate Results naming pipeline to satisfy the basic user request.

**Next UI polish:** rename/explain the field as **Driver / Results Name** or **Results Participant Name (fixed per vehicle)**; optionally add distinct project metadata `Driver Name`, `Co-driver Name`, `Crew / Source`, and a Results-row mock preview. Provide safe autofill `Use Driver Name for Results`, without silently overwriting the vehicle model/manufacturer fields or actual native DriverID. Build, reopen and reset should verify the fixed participant label changes in the isolated candidate. Note: this is a vehicle-bound display override, **not** a change to AI driver identity, original competition driver selection, player names or localization behavior. A future true per-participant/dynamic naming policy requires separate native research, not a misleading claim.

## B. Frontend 3D vehicle framing — new separate editor

The owner's screenshots show the **large live 3D model in Vehicle Select** sits noticeably too low for Trooper and several imported cars relative to the selected stock Reece Pickup/RAV4 reference: Isuzu's tyres extend below the lower panel baseline, while the reference vehicle sits visibly higher within its scene. This is NOT the separately generated 128x128 car-sheet thumbnail, NOT the 32x16 Results icon and NOT the gameplay Follow camera. The source scene uses `DataScene/FrontendScreens/VehicleSelect.xml` with a selected `CarModel`, `gaFrontendCarMoverAI`/spinner scene logic, and a distinct frontend presentation camera (see `research/r5v_a/frontend-vehicle-selection.md` and `research/vehicles/vsdk1/camera.md`). The precise error source is **unresolved**: possible frontend camera pose/target, presentation animation/transform, mesh origin/pivot, physical bounds or vehicle-specific calibration. Do not infer that the physics ride-height or stock body/wheel geometry is wrong.

Implement **Frontend Presentation / Menu Framing** after the current Camera 2.0 milestone, ideally as a small independent Vehicle Presentation Polish pass before broader Demo import. Required features:

1. Inventory and source-qualify the retail/frontend presentation path: selected CarID -> `complete.dx` (with integrated frontend wheels) -> presentation mover/spinner -> position/pivot -> frontend camera/projection. Verify whether pose and offsets are global, per-CarID, scene object, model transform or model-origin data. Do not confuse frontend with gameplay camera presets.
2. Calibrate at least three source-qualified examples: accepted Heritage Trooper, a stock Reece Pickup/RAV4 reference and one GT addon (Lancer or Subaru), with same display resolution/aspect, animation phase and UI scene. Measure projected bounding boxes, lower tyre baseline, visual center and margins in actual game screenshots. Check different viewport aspect ratios and low/high vehicle sizes.
3. Introduce a **Frontend Menu Preview** in Rally Workshop showing `complete.dx`, wheels and accurate overlay guides for original-style Vehicle Select content area, baseline and clipping. Distinguish renderer approximation from exact D3D8 frontend parity. Offer **Auto Frame / Manual Offset / Reset Original**, with live vertical offset and optional horizontal/framing scale adjustments only if proven compatible and safely scoped. Support before/after images and source reference comparison.
4. Author a qualified **presentation-only** per-vehicle correction: no change to race model `car.dx`, hub transforms, physics ride height, suspension, collision, shadow, damage, crew or source geometry. Avoid globally moving stock vehicles, blindly shifting vertices, altering shared frontend camera for every vehicle or mutating original scene files. If per-vehicle native isolation is not proven, return a source-qualified research blocker and preview-only capability rather than a hack.
5. Integrate with existing project authoring, independent candidates, Save/Undo/Redo/Restore, front-end menu re-entry, source hashes and QA. Validate stock zero-edit unchanged and Trooper correct race/world rest pose. Provide user owner checklist and exact resource/native-diff reports.
6. Do not assume that regenerating car-sheet artwork raises the actual big 3D Vehicle Select model. Those are separate channels.

## Sequencing and governance

- **Now:** Codex continues and completes Gameplay Camera 2.0 (five player-selected views, research-backed FOV ownership, real live D3D9 editing). Do not interrupt this phase.
- **Next small bounded pass:** **Vehicle Presentation Polish — Driver/Results label UX + Frontend Model Framing**. Reuse existing fixed Results display-name implementation; spend implementation effort on the true frontend 3D framing issue.
- **Then:** Resume **MR Heritage Garage breadth** with additional Demo vehicles and safe alternative roster mapping; preserve accepted Isuzu and Pajero pilots. Continue **GT Garage Lab, Classic universalization, Blender Bridge and Fleet Builder** as in v6.0.
- Preserve source-only private-asset policy, local validated commits, no push/release or retail EXE/DLL/original archive changes. Do not claim game visual parity until owner compares isolated candidate in D3D8.

---

# Master Rallye Vehicle SDK — Master Plan v5.9

**Decision: Game Camera Lab reviewed; begin MR Heritage Garage.** 26 October 2026. This revision adds a current status and new phase acceptance criteria **without deleting or replacing the entire preceding v5.8 and older plans**. The prior canonical plan follows this new checkpoint verbatim.

## 1. Current evidence checkpoint — Game Camera Lab

- Source-only full review archive: 1,052 ZIP entries; 1,050 hash-manifest entries all matched; 461 Python sources passed syntax parsing. All 28 nonmanifest changed-files entries match the full archive.
- Independent local synthetic run: **31 tests passed**, covering game camera lab, marker, player state, vehicle identity, camera profiles and Workshop regressions. A broader attempted run had two review-environment/import errors in legacy tests (`tests.helpers` and a direct native tool import), not a demonstrated game-camera regression. Codex reports **901 tests with two optional skips** on its full Windows tree; this full run was not reproduced here.
- Stage commit declared: `7e0ed2ba29d3ba4b0d25aa5841c40768d5fc14eb`; ZIP lacks `.git`, so this is documented rather than independently verified Git metadata.
- Camera research reconstructs the **flat, upright, pitch-disabled initial update** of one native Follow camera (eye, target, up), replaying original x86 code and the matrix-writer path. D3D9 gameplay-style pose viewing is **static and approximate**, not a verified D3D8 dynamic camera simulation.
- Three source Follow presets (`FollowCamera 0/1/2`) and normal/split configuration are inspected read-only. **The owner's five in-game camera types need an exact type → constructor → parameter owner → runtime switch map**; they are not equivalent to the three Follow preset indices.
- Current per-CarID authoring changes **follow half-length and height extent only**; native FOV, DistFront/Back/Up, pitch, smoothing and mode-specific state remain read-only or unqualified. Existing extents may influence multiple viewing modes if reused by camera construction; individual mode independence must be proved before controls are exposed.
- Camera Lab launches a standalone D3D9 Previewer for a selected precomputed pose; **not a live, continuously synchronized editing viewport**. `G` switches between Free Inspection and static Gameplay-style pose when available.
- Race progress marker tint authored via `race_colour_rgba`, original alpha retained, local qualified HUD image or labeled synthetic fallback, project history and isolated candidate emission. The owner confirms the marker and camera changes actually apply in the game. Native five-mode/FOV fidelity is not thereby established.
- Lancer `Softened Whine` preset from current milestone lowered gain and response, but owner still reports pitch subjectively high; retain accepted original, prepare a further mild pitch-only comparison later without changing successful Spool/BOV.
- Candidate A marker-only, B extent-only, C Whine-only kept separate. Owner game tests of those features noted; detailed stock/AI/camera-mode checks remain distinct validation gates.

## 2. New immediate milestone — MR Heritage Garage: Demo Vehicle Pilot

**Goal:** import an actual owner-supplied Master Rallye Demo/other-edition vehicle as a **new independent vehicle**, not a retail replacement. Reuse the separately maintained `master-rallye-re-rdemo` research worktree/branch and its Cooker evidence. That worktree's contents are **not present in the reviewed camera archives**; the main implementing agent must inspect its actual source, commits, documentation and source hashes before invoking or integrating it. Do not guess Cooker compatibility.

**Track A — Source audit and edition catalog**
- Locate the owner's read-only Demo and retail installations or unpacked archives and the correct Demo Cooker research; inventory exact builds, hashes, vehicle identities, DX/DXT/SMA, thumbnails, overlays, UI records, archive paths, animation/crew, audio and physics references.
- Build a Demo↔retail vehicle crosswalk with absent/different/identical/unverified status; distinguish engine support from source-file availability. Select one actually qualified candidate absent from or materially different to retail; do not invent a model name if local evidence is insufficient.
- Integrate only reviewed Cooker read paths or compatible outputs; preserve the independent branch, no blind merge or destructive copy.

**Track B — Import as new car identity**
- Copy-on-write immutable source baseline with version, hashes and provenance; choose available CarID within the currently qualified roster, namespace all dependent resources, generate distinct names, race HUD tint, select/menu/results images and thumbnails. Never replace a stock CarID or assume capacity >30 has been proved.
- Reuse the known SDK Core and vehicle library/Previewer, native loading and build infrastructure; avoid writing separate Demo-only packers if existing qualified code can be adapted.
- Include physics selection from qualified user-local retail `Data.sma` donor families with independent addon identity; check collision/visual wheelbase/radii/ride, camera extents and shadows. Preserve Demo semantics where qualified. Stock physics is not presumed portable without matching structures.
- Preserve existing Demo glass zones, lamps, damage and crew if working; add missing verified MR glass-control/damaged-texture and rear-brake ON support only where necessary. Never conflate rear brake lamp state with rotor glow. Avoid global alpha/culling patches.
- Preserve or explicitly qualify engine and supplementary audio sources; absent/unsupported source mappings require warnings and opt-in donor selection, not silent replacements.

**Track C — Validation and deliverables**
- At least one actual qualified Demo model parsed, visually staged, converted and compiled into an **isolated** independently identified 30-entry-or-fewer candidate (subject to local roster allocation) with reproducible manifest/sha checks, exact resource differences and zero stock mutation.
- Unit/synthetic, original-loader compatible parser checks, GUI/Previewer capture reports, integrity/restore, repeated candidate build, AI/roster initialization and first gameplay launch checklist. No claims of successful in-game Demo play without owner validation. If private source corpus missing, finish useful adapter/library/fixture validation, report precise dependency and do not fabricate a successful candidate.
- Document per-feature PASS/WARN/FAIL/UNTESTED and source build identity; no bundles of copyrighted Demo/MR files in source-only review deliverables.
- Preserve original `MRallye.exe`, `d3d8.dll`, stock retail/Demo sources, existing Audio/Camera/Physics/Classic work, PERF2 and working stock/addon records. Randomizer remains separate. Local validated commits authorized; no push/publish/release.

## 3. Required dedicated follow-up — Gameplay Camera 2.0

This remains a high-priority feature but **is not a hidden second major task inside Heritage Pilot**.

- Enumerate **all five owner-observed in-game camera modes**, map mode-switch dispatch and exact FOV/projection owner, whether each has vehicle-local or shared parameters, and identify which actually use the common follow extent initializer. Inventory normal/split/replay modes separately.
- Prove a per-CarID / per-mode native override of FOV and, where safe, distance/height/target/smoothing without leaking to other camera types or vehicles, and always support original/donor/custom reset. Do not expose speculative native sliders.
- Upgrade Game Camera Lab to a genuine **live preview editing workflow**: persistent D3D9 viewport process, responsive bidirectional settings transport (e.g. defined local IPC), mouse/on-screen manipulators for qualified eye/target/frustum inputs, visible current mode and FOV, before/after synchronized comparison, preview-only changes clearly marked, Apply/Reset and source hash guards.
- Calibrate static and dynamic camera outputs against owner-provided fixed-condition D3D8 screenshots/videos. Dynamic behavior without sufficient evidence remains labeled approximate.
- Independently validate five camera-mode isolation, stock/addon source guard, undo/reopen and no cross-CarID leakage. Do not globally edit `Cameras.xml` to simulate per-car control.

## 4. Queued usability/audio follow-up

- Optional new `Lancer — Lower Pitch Whine` A/B preset; adjust tone gently, preserve already liked Spool, BOV and engine and accepted original preset. Compare game hearing, not just numerical gain.
- Continue original source-colorways, GT Garage Lab corpus validation, generalized Classic MR conversion, Model Studio/Blender Bridge + Model Doctor, and Fleet Builder on the existing roadmap. Do not drop those features when prioritizing Demo restoration.

---

# Historical and retained Master Plan — v5.8 and earlier

# Implementation checkpoint — Game Camera Lab completed offline

26 October 2026. Shared native-informed static camera reconstruction, separate
Gameplay/Free Previewer modes, source-pinned per-CarID extent editing and Race
Progress Marker RGB authoring are implemented. Original follow updater AND
matrix writer pass controlled CPU replay; final D3D8 projection and dynamic
terrain/speed/history/smoothing remain approximate/unknown. No per-car global
FOV/distance/smoothing authoring is claimed.

Three isolated 30-entry Classic Lancer candidates change marker28, camera28,
and optional Softened Whine28 independently, with zero sealed game-resource
changes. Accepted source paint, tyre/glass corrections, frozen cars, physics,
crew, wheel hubs, lights/damage, UI and Engine/Spool/BOV remain intact. Every
fresh runtime now copies the owner's original PlayerState.xml byte-for-byte
when available, using the existing mutable-state exception. No fabricated
unlocks. Old verified runtime leaves moved to an owner-deletable quarantine.

See GAME_CAMERA_LAB_RESULTS.md and research/vehicles/vsdk2/game-camera-lab.md.
901 full synthetic tests / two existing private-fixture skips; actual Windows
Camera/HUD, Material/Binding/stock builds, Physics/Camera/art, Audio, Paint/Crew,
stock reference, texture zoom and native audio/roster regressions are recorded.
Real gameplay camera/HUD and Whine listening remain separate owner gates.
No next milestone, push, publication or release.

---

# Master Rallye Vehicle SDK — Master Plan v5.8

**Review checkpoint: 26 October 2026 — Vehicle Fidelity source accepted; Game Camera Lab next.**

This is an additive decision update to v5.7. The complete previous plan follows unchanged. When an older historical roadmap conflicts with this checkpoint, the checkpoint is current. Do not mistake source/Windows qualification for gameplay verification.

## Vehicle Fidelity: source-review results and owner feedback

- Owner reports BOV and Spool sound ideal, authentic to the intended GT sound; Whine appears pitched too high and slightly too loud. Preferred balancing action: lower Whine pitch and gain via the existing per-vehicle Audio Studio; leave BOV and Spool unchanged until an A/B listening comparison shows otherwise. Do not globally change other vehicles or rewrite samples to address a per-preset mix.
- Owner reports the latest model's appearance is an excellent match for Master Rallye. This is visual owner feedback, not blanket native qualification of each newly changed shadow, tyre and glass path.
- Source archive `rally-workshop-fidelity-source-review.zip`: 1,038 entries, ZIP CRC clean, 1,036 SHA256 entries matched, 450 Python modules parsed. Changed-files archive: 26 entries including manifest and review metadata, 24/24 reviewed content entries match full source tree.
- Local independent tests: 50/50 qualified focused synthetic tests passed using src/tools/tests PYTHONPATH. Separate original x86 camera tests could not be reproduced without Unicorn; they are not included in this clean focused count.
- Codex fidelity report: 894 full synthetic Windows tests with **two optional skips**; these numbers are reported by the developer, not independently rerun. The source manifest names local commit `59becef67db940e0c9d300ae96b62c9ebdddc4b0`; `.git` history is not bundled in the ZIP.
- Implemented and review-supported: Shadow Studio Original/Donor/Auto/Custom with source-pinned bounds and diagnostic overlays; qualified Lancer Classic tyre/glass optics and preservation rules; source-paint preservation option; responsive action rows and original pictographic icons, including Undo/Redo.
- Fidelity report measurements for Source to approved Classic Lancer: Race 2649→2379 tris (119→111 draws), Frontend 6333→4563 (186→178), wheel 745→370 (16→16), 77→77 referenced textures, estimated native RGBA cache 12,199,936→11,508,736 bytes. The existing topology/wheel reduction was preserved from the previous phase; do not attribute it all to this last change.
- Three isolated fidelity candidates: A Source/Original Shadow, B approved Classic/Auto Shadow, C same Classic/Custom Shadow. Auto versus Custom has **zero resource-byte changes by design** because the source-guarded external native shadow-bounds adapter uses a separate profile. Native D3D8 shadow rendering remains an owner gate; Previewer shadow guides are not terrain-projected game shadow evidence.
- The approved Classic retains source paint to avoid abrupt flat-shading seams; stock-derived tyre/glass optical semantics are source-qualified approximations. Exact game appearance, damage and shadow remain independently testable.
- No original MRall​​ye.exe, stock Data.sma, existing d3d8.dll, original GT/MR assets, or Randomizer changes are permitted. Private runtime/capture/audio payloads stay out of source-only deliverables. Completed validated phase local commits authorized; **no push, release, or publication**.

## Next milestone: Game Camera Lab + HUD Progress Marker Tint

**Main objective:** research and implement a source-qualified preview of how the game follows a car, without confusing it with the existing freely movable D3D9 camera. Integrate a small, real per-vehicle race-progress marker color authoring workflow.

### Camera Track A — Native reconstruction

- Inventory and cross-reference existing camera research, native hook for source-qualified CarID follow extents, bounds transformations, stock car behavior and replay/alternate paths. Identify exact matching-build code, source pointers and update stages for camera position, look-at/target, up-vector, FOV/projection, smoothing/inertia, terrain/speed effects and camera switches. Record proven versus inferred values.
- Do not expose FOV, distance or smoothing as working game settings until the native ownership, safe authoring path, regression and game evidence exist. The existing follow half-length/height extents are not camera distance or height controls.
- Keep original/donor/custom per-CarID baselines, reset to immutable original, isolated candidate builds, strict source hash and family guards, no effects on stock or other add-ons.

### Camera Track B — Preview in the existing renderer

- Add a clearly named **Gameplay Camera Preview** mode alongside free orbit. Reuse the existing D3D9 Previewer/model resources, stage vehicle plus wheel/ground guides, and render original versus edited at matched conditions.
- Render using recovered native geometry/projection logic to the extent it is supported; display camera pose, target and FOV only when evidence permits, with explicit labels **Native-Qualified**, **Approximate**, or **Unknown**. If only follow bounds are known, show qualified bounds and an illustrative—not falsely exact—chase framing.
- Support meaningful static snapshots and speed/terrain scenarios only when backed by evidence, with before/after and reset; provide calibration targets for D3D8 in-game screenshot comparison when the owner can test.
- Do not confuse a Previewer camera bookmark with the actual in-game camera. Do not claim D3D9 preview parity without real-game comparisons.

### HUD Track — Per-vehicle progress-bar marker tint

- Previous source/runtime research proves the bottom progress-bar marker uses a shared `hud-template_003_000.dxt` (16×8) image frame; its visible tint comes from `Race/CarN/Colour`. `VehicleRecord` carries RGBA at offsets +0x24..+0x30, and prior owner-runtime ID25 red A/B confirmed independent marker coloring.
- `addon.json` already has the typed/validated `race_colour_rgba` array ([0..1] floats). Implement a GUI control **Race Progress Marker Color** in Vehicle Identity & Presentation and a matching shared SDK Core service method. This is **not** a recolor of Vehicle Select, SmallCarSheet, Race Results, vehicle paint, or the generic shared HUD texture.
- Add RGB picker, preset palette, precise hex and normalized-channel display; preserve alpha=1 by default until alpha authoring is independently qualified. Preview the actual white marker tinted over representative dark/light progress-bar backgrounds using user-owned local HUD art if available; otherwise label a synthetic reference clearly. Preview and game rendering must remain distinguishable.
- Save, undo, redo, reset to donor/source, project reopening and actual native candidate emission; verify source guard, CarID mapping, no cross-vehicle/AI/stock leakage, generated record bytes, no unintended HUD XML modifications.

### Whine feedback / optional small polish

- In the existing per-car Audio Studio preset for Lancer, prepare **Original vs Softened Whine** profiles. Tune qualified gain and pitch conservatively, without touching successful Spool or BOV, preserving custom engine and GT audio sources. Prepare audition clips and exact WAV/profile differences where appropriate. Owner listening chooses preferred balance later; do not unilaterally change universal defaults.

### Acceptance/deliverables

- Native-camera research report with exact function ownership, verifiable field map, unknowns and ABI boundaries; qualified gameplay preview or conspicuously labeled approximate fallback; Windows captures with multiple modes and unchanged original/other-CarID behavior.
- Reversible per-vehicle progress marker tint: real GUI picker, genuine runtime fields, screenshot preview, stock/source reset, isolated candidate and per-CarID color-isolation tests. Race HUD tint gameplay checks queued but nonblocking for source/offline completion.
- Explicit optional Whine balancing candidate with preview; no new sound engine redesign.
- Complete available regression suite, repeat shadow/Classic/audio/physics/art tests, direct source/resource diffs, updated CAPABILITIES, REGRESSION_MATRIX, offline F1 Help, COMMIT_LEDGER, and a source-only review ZIP. Include notes of unqualified native camera parameters.
- Stop after this milestone for source/owner review. Do not start MR Heritage Garage, GT Garage Lab, Blender Bridge, new car import or automatic broad Classic generalization during this task.

## Later milestones, retained

- **MR Heritage Garage**: read-only Demo/retail/edition imports into independent CarID; verified Data.sma physics donors, new race glass/brake ON layers, original provenance and reversible builds.
- **GT Garage Lab**: optional full user-supplied GT3 corpus scan, source colorways and Classic recipe generalization with regression samples; do not claim universal support from the current Lancer pilot.
- **Model Studio & Blender Bridge**: editable geometry/UV, scale and fitment, persistent reimport, defect explanations (culling/alpha/reflection) and safe repair paths.
- **Fleet Builder & release prep**: large catalog versus qualified simultaneously active roster, install/revert, dependencies, documentation, license/provenance and packaging.

---

# Preserved Master Plan v5.7

# Latest implementation checkpoint — Audio Import 2.0 + GT adapter

26 October 2026. Physics/Camera/Vehicle Presentation completed first in local
commit `53fa708ed1e1a2290fe50ddc3a1286c1488faf28`. Audio Import 2.0 and the optional
GT Audio Source Adapter are now implemented and Windows/offline validated.
Ordinary local import remains independent of GT ownership; qualified PCM and
optional local FFmpeg decoding feed the original native-resource compiler.

The independent GT Sound Lab worktree remains clean at `1dc5b16`; actual package
initializers and identical shared GT4 geometry/database modules were preserved.
Catalog/bank/loop/RPM/pitch/event evidence survives explicit source-to-layer
assignment and presets. Missing program15 / fourteen unsupported INST entries
remain errors; no automatic replacement or full GT multi-band player is claimed.

See AUDIO_IMPORT2_RESULTS.md, CAPABILITIES.md and REGRESSION_MATRIX.md. Full suite:
894 tests / one optional skip. Five isolated builds change only 1/1/1/1/4 named
WAVs with unchanged native patch bytes; Windows GUI and complete SDK regressions
pass. Source, Core, parser and conversion hashes remain private provenance.
Original EXE/DLL/retail assets, frozen cars and Lab tree are unchanged.

Gameplay/DirectSound listening, prior Classic A/B and dynamic follow-camera
checks remain owner gates. This milestone stops for review; do not automatically
start Heritage Garage, GT corpus/model work, Blender Bridge, Fleet Builder or
native multi-band audio. The user v5.6 plan and earlier checkpoints below are
preserved historical specification; this checkpoint overrides their stale NEXT
labels. No push, publication or release.

---

# Implementation checkpoint — Physics & Camera Studio completed offline

26 October 2026. The scoped Physics / Camera / Vehicle Identity / Vehicle Art
implementation is complete. Shared Core, Windows GUI, typed independent physics,
source-qualified follow extents, display labels, hash-associated aliases and
explicitly applied MR-style artwork are functional. Full suite: 862 tests,
one optional skip. Three isolated candidate paths and exact differences are
recorded in PHYSICS_CAMERA_RESULTS.md and REGRESSION_MATRIX.md. Native/device
and D3D8 owner tests remain pending; no gameplay qualification is claimed.

The owner's v5.6 handoff is preserved below. Audio Import 2.0 and optional GT
Audio Source Adapter are next, in a separate validated local phase. Independent
Lab worktree/provenance and real package initializers must be preserved. Its
reported private corpus results are not yet revalidated by this main checkout.

---

# Master Plan v5.6 — GT Sound Bank Lab handoff accepted for integration planning

**Date:** 26 October 2026. **Current active main-agent work:** Physics & Camera Studio + Vehicle Identity & Presentation. **Independent research result:** GT Sound Bank Lab has completed a source-only handoff and synthetic validation. The Audio Import 2.0 milestone remains next for the main agent; GT sound-bank integration is an additive source adapter, not a prerequisite for arbitrary user-file import. Original game playback parity remains unproven.

## GT Sound Bank Lab — source-review checkpoint

Reviewed archive: `GT-Sound-Bank-Lab-source-20261026-final.zip`. Archive CRC clean; **33/33** content files match `source-manifest.json` (34 ZIP entries including the manifest); all **18 Python files parse** and independently **30/30 synthetic tests pass** in the isolated package. The researcher reports additional corpus/native verification using the private GT source files, which are **not** in the source-only archive and thus cannot be independently replayed from it. No live GT3/GT4 game/PCSX2 audio capture or listening test is claimed. The independent worktree and main Codex workspace remain separate; no merge or push evidenced by the ZIP.

### Qualified source-chain and bank findings (researcher-reported corpus analysis)

- **GT3:** US CAR244, ENGINE235, referenced sound numbers118; EU244 and JP242 CAR rows in other regional DBs. **1,215 banks**, **8,554 entries**, **8,501 bank-local spans** structurally audited. GT3 native CODE/GTSE routes `b_off`, `turbine`, `turbine2` into specific original INST voices; leaf pitch words are source-derived. Original event labels are not independently verified real-world acoustic descriptions. Short mesh code `sb0097` is not proven to join directly to a CAR row; do not invent that association.
- **GT4 Beta extracted corpus:** 723 GENERIC_CAR labels, 384 sound numbers, **3,572 numerical banks** fully decoded (21,439 band records and 21,433 bank-local spans). Default parts mapping requires DEFAULT_PARTS muffler key **+152** (not +136); category and turbo eligibility select `normal0..3` or `turbo0..3` under the supplied CORE. Lancer `mits0015` → `lancer_evo4_wrc_97` → ENGINE row1605 → Sound ID22601, **shared by 11 ENGINE rows**. Static default-part interpretation selects `turbo3`; available asset pairing with supplied Online-US CORE remains comparative, not proven historical playback.
- **Playback architecture:** GT4 supplied CORE loads **base engine**, **tuned engine/normal/turbo**, and **roadnoiz.es** as separate control streams. RPM banks mix up to two neighboring entries. GT4 native `turbine2` event has a continuous source-sample path tied to drivetrain/gear and speed controls (substantially stronger evidence than filename-only guessing); `turbine` has a separate controlled stream; `b_off` is an event-triggered one-shot. The full BOV state producer/trigger thresholds remain unproven. `shift_change` has a named token but is missing direct program15 in the sampled Beta race2 bank.
- **GT4 INST/JAM:** original native address shift is 3 (8-byte address units) for supplied main race banks, correcting an earlier *16-byte* interpretation. 24 INST banks, 107 entries, 93 supported for PCM export and 14 explicitly unsupported due to unresolved loop/SSA policies. Never guess or silently substitute absent programs or unsupported entries.
- **Source-only explorer:** `tools/gt_sound_lab.py`, `gt_sound_lab_server.py`, `gt_sound_lab.html`, `gt3_sound_lab.py`, `gt_sound_jam.py`, native verification tools, JSON schema and PowerShell startup. Provides private GT3/GT4 catalogs, source-qualified bank lookup, RPM/loop inspection, comparison and explicit mono PCM WAV audition/export with source/rate provenance. Local loopback browser; original inputs read-only; no assets, extracted audio, executables, native dumps or catalogs in distributable archive.

### Main Codex integration rules after Physics & Camera

1. Complete Physics & Camera Studio and Vehicle Presentation as already scoped. Do not redirect active worktree mid-milestone.
2. Implement **Audio Import 2.0** independently: friendly source file import (qualified decoder adapters), preview before apply, per-layer assign/loop/trigger treatment, gain/clipping, safe conversion and reversal for Engine/Whine/Spool/BOV. Do not require GT original-bank solution for user-owned WAV/FLAC/MP3/Ogg import.
3. Add an **optional GT Audio Source Adapter** consuming machine-readable lab records and private local source folders: `Find sounds for this car` → bank variants → entry / RPM / loop / evidence → audition → explicit source-to-layer selection → Audio Studio conversion → isolated build. Distinguish candidate default, statically source-associated, dynamic runtime-qualified and user-chosen sounds. Never identify `turbine2` as an acoustic transmission recording with certainty until listening/gameplay validation.
4. For Engine, initially permit an explicit source band as **single-loop MR approximation**; show all available original RPM bands as inspectable. Genuine GT multi-band engine mixing requires a separate source-qualified native/ABI/AI/reentry/performance implementation before it can be advertised.
5. **Integration caution:** the source-only ZIP includes **generated minimal `src/master_rallye/__init__.py` and `src/master_rallye/addon_sdk/__init__.py` shims**, not the original Workshop package files. **Do not copy those shims over the main repository's package initializers.** Review/merge shared files `gt4_spec.py`, `gt4_source.py`, `gt4_audio_extract.py` and tests deliberately. Use a separate adapter layer instead of overwriting active main-Codex changes.
6. Preserve source build SHA256, bank hash, sample-offset semantics (GT3 compressed member offsets versus bank-decoded sample offsets), sample ID, explicit rate provenance and unsupported statuses in project metadata. Private generated catalogs and extracted samples must stay ignored/local. Provide error messages for missing banks, unsupported entries and ambiguous model-code associations; do not guess replacements.
7. Add regression against existing Lancer ID28 audio, stock vehicle passthrough, AI/CarID isolation, lossless reversibility, native sound-hook safety, candidate diffs, CPU/memory budgets and real-game listening later. Label researcher-reported private corpus runs separately from locally reproducible synthetic tests. Local validated commits permitted; no push/publication.

### Outstanding research, deliberately nonblocking

- Matching GT4 Beta assets to the supplied Online-US CORE during actual gameplay; full gain envelopes, source controls, spatial/Doppler/ADSR/LFO and actual audible mix.
- GT4 BOV event producer and thresholds; the missing `shift_change` program15; fourteen unsupported JAM entries; sequence-mode dispatch.
- GT3 full in-race sound triggers and exact mesh short-code ↔ CAR label links (including `sb0097`); runtime/PCSX2 listening tests for any claimed acoustic identity.
- Multi-RPM GT engine playback in Master Rallye beyond today's qualified single-loop synthesis; do not change stock audio paths or the original executable/d3d8.dll without established safety boundary.

---

# Master Plan v5.4 — Audio Studio accepted offline; Physics, Camera & Vehicle Presentation next

**Date:** 26 October 2026. **Decision:** V-SDK4D Audio Studio is implemented and source/offline validated; D3D8 listening and V-SDK4B.1 Classic-Lancer gameplay A/B remain nonblocking owner gates. The next active milestone is **Physics & Camera Studio + Vehicle Identity & Presentation**. Keep older numbered V-SDK history below intact as historical planning; this decision overrides stale “Audio Studio next” and “GT Garage Lab immediately next” schedules wherever they occur in older sections. The user-facing milestone name is preferred over increasing numeric suffixes.

## V-SDK4D final status — evidence and boundaries

- Archive `rally-workshop-vsdk4d-source-review.zip`: 989 ZIP entries, valid CRC; 987 SHA256 manifest matches; 421 Python files parse; independent targeted Python tests **44/44 PASS** (31 audio/profile/integration/candidate and 13 Workshop tests) in a non-Windows environment. The complete Windows suite **854 PASS / one optional skip** and real Tk/dialog/build evidence are reported by Codex, not independently repeated here.
- Implemented shared authoring layer `src/master_rallye/workshop/audio.py`, user GUI `audio_ui.py`, CLI and offline Help; Engine, Transmission Whine, Turbo Spool, BOV; qualified PCM WAV import (original untouched, private SHA256-pinned copies), source assignment, response/bounds, audition with x86 original DSP + authored supplementary simulation, Mute/Solo, presets, Undo/Redo/Restore and isolated build.
- Five isolated Lancer experiments A–E reportedly change precisely **1/1/1/1/4 named WAV resource paths**, with unaffected models, camera, physics, UI and rest of fleet. This is resource-level evidence, not proof of actual DirectSound playback quality.
- Preserve the original native sound implementation and previous ECX/register/lifetime protections. **Stock/family-only audio authoring unsupported**; native engine cannot be disabled via candidates; “disable spool” retains silent native spool voice and estimator for BOV; provenance and supported PCM limits must be stated honestly.
- Native engine/AI reentry, SFX failures and real game mix remain separately evidenced. Game listening on A–E and Classic Lancer Source/Classic gameplay comparison are **PENDING, NONBLOCKING**. Local implementation commit reported in archive `COMMIT_LEDGER.md` as `4d38299362fdd6d2518829d8824ebda5b33ca5d4`; ZIP does not independently prove Git history. No push/publication authorized.

## NEXT — Physics & Camera Studio + Vehicle Identity & Presentation

**Goal:** the first complete GUI journey to edit a qualified addon’s real physics values and experimental per-CarID camera follow extents, give it a readable in-game name, label project textures, generate vehicle select and race-results art, and build/restore an isolated candidate. Use shared SDK Core, not GUI-specific parsers. When gameplay proof is unavailable, keep the gate pending and continue after qualified offline tests.

### A. Physics Studio (native initialization profiles, not an invented solver)

- Reuse `addon_sdk/physics_profile.py`, `addon_sdk/project.py`, existing `physics-profile.json`, stock donor clone, and exact hash-qualified local retail `Data.sma` members `DataGame/vehicles.xml` and `DataGame/Modifications.xml`. Never patch retail Data.sma or originals.
- Expose searchable, grouped qualified typed fields: dimensions, mass/inertia, powertrain/torque/RPM, drive type, steering, brake balance, suspension, dampers, wheel/tyre relationships and qualified per-player modifications. Show units, stock donor/source values, current overrides, bounds and provenance. Any path not covered by the backend schema remains read-only.
- Offer donor/source library (qualified stock family templates from exact retail corpus), presets, before/after diff and explicit copy-on-write family identity. **Do not copy an entire stock file blindly**; preserve namespace, wheelbase/track/radius, collision/hubs and actual ride-height distinctions. No speculative automatic balancing.
- Make at least one clearly observable physics edit on existing Lancer and show that only that vehicle’s typed override/resources change. Preserve audio across preset and project edits. Test reset, Undo/Redo, Save, reload, Validate, Build, Restore, zero-change equality and resource diffs. Provide future gameplay checklist for acceleration, grip, braking, reverse, collisions and AI.
- Display which properties affect **game initialization**, which are **preview-only**, and which require separate native research; physics sliders must not fake real-time vehicle motion simulation.

### B. Camera Studio (strict per-CarID capability boundary)

- Distinguish **in-game follow-camera** from independent **3D Previewer orbit/pan/bookmarks**. Existing `addon_sdk/camera_profile.py` qualifies only hash-pinned per-CarID **follow-extents** (`half_length_m`, `height_m`) bound to observed DX collision bounds and runtime families; per-CarID field isolation has prior owner evidence on Lancer and Megane.
- Provide numeric controls and a diagnostic overlay/gizmo (source bounds, edited bounds), alongside source/model hashes, target CarID, reset, before/after and warnings when a bounds edit may affect visual camera framing. Do not claim that these numbers directly mean “camera distance” or “camera height”.
- Enforce current guardrails: verified qualifying model hashes and CarIDs only; CarID0 and unqualified cameras read-only, with clear reason. Do not silently mutate overall model scale, damage/collision or wheel fitment when editing follow-camera extents. Unsupported FOV, smoothing, focus, rear/replay modes remain read-only future work.
- Validate actual isolated candidate output and source-dependent patch selection; test **targeted CarID only**, multiple candidate composition, stock passthrough, re-entry and no other vehicle effects. Game D3D8 approval remains owner task.

### C. Vehicle Identity (user-friendly vs native identity)

- Provide editable manufacturer, model, full display name, and qualified race-results display name where SDK/native contracts permit. Display immutable/internal addon_id, runtime family, physical CarID, registry identity and resource namespaces separately.
- Tie edits to `addon.json`/existing manifest profiles without breaking physically assigned CarIDs or locally qualified runtime names; respect ASCII/name-buffer/font constraints and provide a character budget/preview. If a name is locked by a hashed runtime identity profile, show the blocker rather than changing identity quietly.
- Add reliable metadata-level **Friendly Name** for textures/materials (e.g., `Body Paint`, `Wheel Rim`, `Rear Lamp`) with stable resource IDs and contextual draw associations. Do not rename referenced on-disk `.dxt` files as if this were only a label; implement actual native resource renaming only in a later qualified writer pass, with full dependency rebinding.
- Make display labels searchable and persistent across project reopen, style versions and compatible conversion rebuilds. Preserve semantic aliases where identifiers remain stable and explicitly mark conflicts otherwise.

### D. Generate Vehicle Art — reuse existing MR generator

- Reuse `addon_sdk/ui_preview.py`, `ui_assets.py` and `tools/generate_vehicle_ui_previews.py`; do not author a second icon converter. Produce **Vehicle Select 128×128** and **Race Results 32×16** from a qualified source DX, both locally previewable. Keep `mr-native-v1` style/presentation and allow controlled orientation, framing, brightness where the renderer supports it; preserve source image provenance.
- Provide **Generate Vehicle Art**, separate rerender for each image, before/after, preview, explicit Apply, Undo/Restore. Generated PNGs must be project-owned and original source model remains immutable. Make generation from Frontend / Race variants explicit.
- Validate native texture/bank append-only limits, frame refs, DXT word0x08 CRC, cross-addon name/slot conflicts and that only intended UI resources changed. No private stock art in source distribution; use user’s local retail assets as templates.
- Clearly separate “preview generated” from “in-game icon actually installed” and show game-validation status.

### E. Regression, shipping and scope

- Preserve V-SDK4D four-layer Audio Studio and presets, Source/Classic Lancer separation, Subaru glass, Pajero visuals, wheel assembly and brake lights, true texture rebinding and reflection, Paint/Crew, stock copy-on-write, PERF2 bulk DXT loading and SCALE1 qualified 29/30 roster without claiming wider capacity.
- Use only local reversible candidate output; no on-disk modifications of `MRallye.exe`, original `Data.sma`, `d3d8.dll` or original game resources. Keep Randomizer unrelated. Private MR/GT resources and audio never enter source-only review archive.
- Implement/validate the full functional UI, not empty tabs. Use real Windows GUI evidence and owner checklist, focused and full automated tests, exact changed-resource/diff manifests, offline F1 Help. Complete bounded milestone, record one scoped local Git commit and result reports. **No push, releases or publication** without separate permission.
- Do not start MR Heritage Garage, entire GT3 corpus audit, Blender Bridge or Fleet Builder in this pass. Preserve their detailed historical requirements below, including later native MR Demo imports, physical stock profiles and AI/roster integration.

**Acceptance:** In one open Rally Workshop project I can inspect a verified Lancer, edit an allowed physics parameter and an eligible gameplay-follow extent, set a supported display label and friendly texture aliases, generate both MR-native UI images, compare and persist changes, validate/build isolated resources, Undo/Redo/Restore, and see an accurate summary of what changed and what still requires owner gameplay validation.

---

# Master Plan v5.3 — Vehicle Identity & Presentation in Physics & Camera Studio

**Date:** 26 October 2026. **Decision:** extend the upcoming **Physics & Camera Studio** pass with a bounded, real **Vehicle Identity & Presentation** workspace: editable vehicle display names, understandable texture aliases, and a one-click native-style vehicle icon/thumbnail generator. Preserve every requirement and historical decision in v5.2 and earlier. This is **planned work**, not a claim that a full GUI identity editor exists. The currently assigned **Sound Studio** remains first.

## 1. Reuse the existing qualified MR UI asset pipeline

- The source-reviewed SDK already contains `src/master_rallye/addon_sdk/ui_assets.py`, the `mr-native-v1` composer in `ui_preview.py`, and vehicle UI icon tools. It already supports bounded project-frame bank extension for **Vehicle Select CarSheet (128×128)** and **Race Results SmallCarSheet (32×16)**, using local owner-provided retail templates and validated manifests. **Reuse this pipeline**, and distinguish generating artwork from installing game UI bank frames. Do not create a second incompatible generator.
- Add an obvious **Generate Vehicle Art…** action within Studio; let the user generate **both** Vehicle Select and Results imagery from qualified race/frontend views, preview each at native resolution and as an enlarged nearest-neighbor inspection, adjust framing/background/lighting if supported, and regenerate either independently.
- Allow the user to choose/correct source variant, yaw and pitch, bounds/padding and original-MR presentation recipe. Match stock MR silhouette placement and alpha conventions; preserve exact role-specific output dimensions, source hashes and generated PNGs. Where automated alpha/background segmentation is unreliable, request explicit manual refinement instead of publishing a bad artifact silently.
- Use project-local deterministic recipes, metadata and owner-provided stock references. Save generated artifacts as overrides, support preview → accept → Save/Validate/Build → Undo/Restore, and report conflicts/capacity failures if the proper native frame cannot be added. Do not bundle original game imagery or GT source assets publicly.
- Scope is **vehicle-selection artwork and small results thumbnails**, not a redesign of the Rally Workshop `.ico` application icon, which already has separate branding.

## 2. Three kinds of names, each with explicit semantics

1. **Human-readable vehicle identity:** manufacturer, model, combined Vehicle Select name, Results label, optional Studio-only title/nickname, source/edition and display catalog grouping. Expose existing verified `addon.json` fields (`frontend.manufacturer`, `frontend.model`, `frontend.combined`, `results.display_name`) through GUI, keeping them synchronized only where the native UI semantics actually require it. Respect observed ASCII, NUL and UI width/presentation limitations; show a live preview and meaningful errors. For stock copy-on-write, do not rename retail IDs or mutate original game resources.
2. **Texture/resource friendly labels:** let the user give a texture a human-readable **alias**, e.g. `Body Paint`, `Front Glass`, `Left Door Decal`, while continuing to show the original internal filename, hash, atlas role and draw usage. Aliases are editable metadata and do not change game resource identities, material references, source provenance or build stability. Support search and sorting by friendly label **and** original name. A single shared atlas may have several different semantic usages: never claim that one alias defines all its surfaces.
3. **Actual internal resource rename:** a different, higher-risk explicit action if a qualified authoring need exists. It must safely update **all** references across DX draws/materials, project manifests, bindings, generated resources and UI banks where relevant, detect collisions case-insensitively and native length/character constraints, and support exact undo/restore. It must not silently rename opaque imported IDs or hashes. If full-safe rename is not proven, expose aliases only and mark native rename unsupported.

## 3. Integration with the Physics & Camera milestone

- Place the identity/presentation tools in a compact **Vehicle Details** / **Presentation** area, leaving Physics and in-game Camera as separate functional panels.
- Maintain the distinction between **D3D9 Previewer navigation** and **actual per-CarID native game cameras**; UI icon camera/framing is a third independent concept.
- Generate artwork for both addon and qualified Demo-as-new-CarID heritage projects where the existing native packaging permits it. Treat stock edits as copy-on-write and distinguish previewable from installable states.
- Expose validation status prominently: artwork generated vs UI bank frame built vs actual D3D8 game qualification. Preserve current roster and per-CarID isolation.

## 4. Acceptance and regression criteria

- Rename the Studio display title and qualified native addon manufacturer/model/Results labels; reopen the project and rebuild without changing CarID, slot ownership or other vehicles.
- Set readable aliases for several `.dxt` files, show their real native names alongside them, and prove alias-only edits produce **byte-identical DX/DXT and compiled game resources**.
- Generate, visually inspect and separately regenerate native-compatible CarSheet and SmallCarSheet outputs from an existing qualified vehicle; verify their 128×128 and 32×16 dimensions, alpha bounds, manifest hashes, deterministic reruns, source fidelity and original bank-frame preservation.
- Validate fully reversible UI asset/frame construction for an addon and one safely qualified stock/heritage path, documenting where unsupported. Confirm no generated thumbnail accidentally changes appearance, physics, game camera, audio or damage assets.
- Update Rally Workshop F1 Help, `MASTER_PLAN`, `CAPABILITIES`, `REGRESSION_MATRIX`, and the commit ledger. Make one validated **local** milestone commit; **no push or public release** without permission. Keep original `MRallye.exe`, `d3d8.dll`, retail assets and Randomizer untouched.

## 5. Execution order and boundaries

1. Finish and review **Sound Studio**, already assigned.
2. Execute **Physics & Camera Studio**, with **Vehicle Identity & Presentation** integrated as a scoped product deliverable.
3. Continue **MR Heritage Garage**, **GT Garage Lab**, **Model Studio/Blender Bridge**, and **Fleet Builder** as previously scheduled. Do not prematurely bundle all of their features into the Physics & Camera milestone.

---

## Preserved v5.2 and previous master-plan history

# Master Plan v5.2 — MR Heritage Garage: Demo and cross-edition Master Rallye vehicle restoration

**Date:** 26 October 2026. **Decision:** expand the product contract to encompass original Master Rallye vehicles from owner-provided Demo and other qualified releases as **new, independent playable car entries**, not merely editing existing retail IDs. Preserve all v5.1 and earlier requirements below. This is a **planned feature, not a newly validated implementation**. The exact structure and version compatibility of `Data.sma` have **not been reverified in this revision**; inspect real, user-supplied files before describing physics extraction as functional.

## 1. Product goal and prioritization

**MR Heritage Garage** is a first-class source family alongside GT3/GT4 and user-authored assets. The long-term goal is a library of all verifiably recovered and legally usable Master Rallye vehicle variants, with distinct source provenance (Demo, retail, version/build) and a safe optional installation into spare CarIDs. The vehicle library can contain more entries than are simultaneously installable in the game's proven roster; **SCALE1 validated 29–30 entries in specific test conditions, not an unlimited capacity guarantee**.

- **Sound Studio** remains the currently assigned phase, with a four-layer audio editor on existing Lancer.
- **Physics & Camera Studio** remains an early priority; its Physics Studio should supply shared parameter/preset infrastructure to Heritage Garage. If archive research uncovers critical prerequisites, the small heritage import research pass can run before the full Physics GUI milestone, but do not conflate either with completed features.
- **MR Heritage Garage** becomes a prominent early integration milestone **before broad GT Garage Lab/Classic generalization and public beta**, because native MR source vehicles and physics provide valuable baseline test data.
- **GT Garage Lab** continues systematic GT3 source audit, source colorways, incompatibility repairs and Classic MR generalization, based on qualified reference data.
- **Model Studio + Blender Bridge** follows with reusable geometry correction/validation tools; **Model Doctor** remains an explanatory diagnostic/UI layer, not a substitute for fixing known GT3 import defects centrally.
- **Fleet Builder** remains essential to install, select, remove and restore combinations safely.

Use friendly names in conversation, Studio and README; preserve historical `V-SDK...` stage identifiers in Git and previous documentation. Do not silently rename previously completed phases.

## 2. Data sources and archive provenance

- Require owners to select **their own local Demo and retail Master Rallye installations/archives**. Record source path, file hashes, edition/build fingerprints, archive entries, variant and extraction provenance without copying original archives into public project artifacts.
- **Inventory before conversion:** enumerate Demo versus retail car names/resources, class, model `car.dx` / `complete.dx` / `wheel.dx`, associated DXT, material and alpha variants, source CarID references, sound/UI assets, crew, light/glass/collision/control records, and physics candidates. Detect identical vs differing resources by content hash rather than filename assumptions.
- **Data.sma research:** first determine the actual archive structure and its physics entries (if present) in each supplied build. Map template files/records to game vehicle identities and physical parameter families; verify the native loader and field semantics with existing qualified stock and Lancer physics instrumentation. Do not assume every `Data.sma` entry is a complete, independently portable physics profile.
- Distinguish **unavailable source**, **unreadable format**, **source-version mismatch**, **candidate builds**, **Previewer pass**, and **confirmed native game pass**. Never advertise blanket Demo-compatibility from one model.
- Keep source assets read-only and private; public releases contain SDK code, manifests, schema/tests, and originally authored or permitted demo fixtures, **not redistributed MR Demo/retail models, audio or textures**.

## 3. Two different operations in the library

1. **Edit Existing MR Vehicle** (already supported as qualified copy-on-write work for selected retail CarIDs). Preserve its original identity/roster slot and zero-edit passthrough.
2. **Import MR Vehicle As Addon** (new Heritage flow). Choose a local Demo/other-edition car, allocate a **new, unique** CarID/slot under the existing capacity constraints, namespace model/textures/physics/sounds/UI resources, provide clear configuration and produce an isolated reversible roster candidate. No mutation of the source Demo, retail installation, original `MRallye.exe`, or existing graphics `d3d8.dll`. Do not overwrite a retail car because of an old source CarID conflict.

The same qualified vehicle editor and Studio viewport should operate on both types; they have distinct validation, source ownership and install behavior. Catalog/storage capacity must be decoupled from active roster capacity.

## 4. Physics template browser based on verified stock `Data.sma` records

- Add **Choose Physics Template**: list verified stock physics profiles by source edition, native identity, class/type, provenance and parameter coverage. Display source stock baseline vs editable values; preview/diff/reset, save a versioned per-new-CarID copy, and build safely using existing physics-profile/native mapping mechanisms.
- Require explicit warnings for donor wheelbase/track/ride/collision/wheel radii/camera mismatch, and an edit/fit workflow where supported. Never silently alias multiple addon CarIDs to one writable stock physics record, or carry over wrong registry names (previous Lancer bug).
- Permit user tuning with the future **Physics Studio**, preserving base donor bytes/semantics; game result remains subject to gameplay handling tests and AI validation. Do not claim arbitrary physics fields or formats are editable until verified.

## 5. Optional native-features completion for Demo models

- **Glass damage:** inventory source pane geometry and native controller/control-case ownership. For missing qualified features, use stock MR local crack textures and the already game-accepted four-logical-zone authoring approach as a candidate, mapping front/rear/left/right only where geometry/engine support exists. Do not promise independent breakage of every physical window beyond native evidence; test one-zone impact isolation and lights surviving damage.
- **Rear brake lights / Brake Glow:** independently inspect lamp/off + lamp/braking ON native passes/draws and source placement. Author a real MR-compatible *rear lamp braking emissive/glow ON state* where missing, using source-qualified mesh/UV and native switch logic. Keep it distinct from brake disc heating/glow; do not conflate the two systems. Test rear lamps by braking and reset; protect texture alpha, headlamps and culling.
- **Lighting, crew and native damage:** confirm working headlights, taillights, driver/co-driver, geometry deformation and transparent materials. Present these as optional specific authoring tasks with per-car evidence and safe fallbacks, not automatic guaranteed fixes.
- Maintain original source appearance as a non-destructive baseline, and enable the separate Classic MR Style profile where required without unknowingly double-processing native MR vehicles.

## 6. Heritage project workflow in Rally Workshop

**Vehicle Library → Import → Master Rallye (Demo / Other Edition) → Source Audit → Preview → Map Missing Dependencies → Choose New Slot → Choose Stock Physics Template → Complete Glass/Brake-Lamp Features (if qualified) → Validate → Build & Test → Add to Fleet.**

- Show a side-by-side edition comparison with provenance, optional UI CarSheet generated using existing MR-style tools, and clear source-version compatibility messages.
- Create a versioned, reusable *heritage project* that preserves an immutable input manifest and editable overlay. Reopen, compare, undo/redo, restore and rebuild without rereading/repacking original retail archives unless requested.
- Report all active roster conflicts and preserve stock save/unlock, AI, Results and repeated race loading; protect PERF2 cache performance and the already qualified combined-car composition hooks.

## 7. Qualification ladder and definition of success

**Heritage L0 — Inventory:** identify at least two distinct local MR edition/build inputs and produce an exact table of differences, or clearly report if only one edition is supplied; inventory `Data.sma` record types without making unproven physics claims.

**Heritage L1 — Independent addon:** source-qualified Demo car opens in Raw/Assembled/Frontend Previewer, imports to its **own new CarID** without overwriting stock, and produces a validated isolated candidate; chosen stock physics template is demonstrably bound to the correct addon namespace.

**Heritage L2 — Native feature authoring:** add or repair at least one actual glass-zone/state and one independent rear brake-lamp ON behavior on the qualified candidate where source features require it. Demonstrate deterministic reversible resource differences, preserved other cars and detailed diagnostics.

**Heritage Game qualification (owner):** actual Master Rallye selects and races the new entry; source/modified views, glass states, braking lamps, physical handling, AI, frontend, Results and re-entry verified. No offline test substitutes for this native qualification; do not block unrelated SDK phases while awaiting owner game testing.

Start with **one user-supplied Demo vehicle that is absent or materially different from the target retail roster**, not a speculative mass migration. Maintain a growing catalogue of Demo and other-edition entries with PASS/WARN/FAIL/NOT TESTED and evidence/hash per source build. Do not declare every known MR vehicle restored until individual evidence exists.

## 8. Required regression gates and engineering constraints

Retain the accepted Subaru native four-zone glass, Pajero native culling/material/reflection fixes, standalone Previewer wheel assembly, 30-entry SCALE1 test evidence, Source Fidelity/Classic Lancer split, PERF2, four-layer audio profiles, CarID isolation, stock edit copy-on-write, current Camera profile experimental bounds and private asset restrictions. Validate combined candidates only when actually assembled/tested; prior independent test results are not transitive.

For each completed, qualified phase, record source fingerprints, reports and **one scoped local Git commit**. Previous commits remain unchanged. **No push, public release or publication** without owner permission. Preserve unrelated Randomizer source and original game's executable, retail archives and `d3d8.dll` unchanged.

---

# Master Plan v5.1 — Owner clarification: readable milestones, Blender Repair Guide, Physics & Camera Studio

**Date:** 26 October 2026. **Decision status:** product roadmap clarification; not an implementation claim. This handoff supersedes the *scheduling order* of v5.0 wherever inconsistent; the original v5.0 requirements and evidence ledger remain below intact. The latest inspected code baseline is the V-SDK4B.1 source-review archive; no V-SDK4D implementation or later UI is assumed available.

## A. Human-readable phase names

Use names in the GUI, release notes, README and owner summaries; preserve existing `V-SDK...` IDs for historical traceability, research folders, regression cases and Git commit subjects:

| Friendly project name | Historical/internal milestone | Product goal |
|---|---|---|
| **Sound Studio** | V-SDK4D | Four editable audio layers (Engine, Whine, Spool, BOV), audition, presets, build |
| **Physics & Camera Studio** | New early editor milestone (do not overwrite prior IDs) | Native-qualified per-car physics editor and bounded experimental follow-camera settings |
| **GT Garage Lab** | V-SDK4E corpus and colorway work | Real source colorways, batch source audit, compatibility diagnostics and reusable Classic recipes |
| **Model Studio + Blender Bridge** | V-SDK5 | Round-trip geometry/UV/materials, scale/fit, source-preserving diff, guided repairs |
| **Fleet Builder** | V-SDK7 | Install/build/rollback, multi-car validation, release preparation |

Never rename old committed stage identifiers or fake past history. All feature status documentation must continue to distinguish game-verified, offline-verified, implemented-but-unqualified, researched and planned.

## B. Current reality: physics and gameplay camera authoring

In latest reviewed V-SDK4B.1 sources, `src/master_rallye/workshop/gui.py` exposes material, texture, wheel preview fitment, appearance/paint/crew, build/scope, but **no dedicated Physics or Camera Studio tabs**. `docs/sdk/CAPABILITIES.md` states existing `physics_profile`, `audio_profile`, `camera_profile` and native adapters are preserved in authoring/build, while dedicated GUI editing is deferred. `docs/sdk/RALLY_WORKSHOP.md` likewise states stock physics/audio authoring and Camera Studio UI are deferred.

**Physics (existing Core, not Studio GUI):** `addon_sdk/physics_profile.py` supports typed, family-scoped source-pinned `physics-profile.json` edits for known native families and qualified field types, with restrictions and validation. Prior Lancer physics has owner gameplay evidence; that does not imply all stock cars or arbitrary parameters can be safely changed. The planned Physics Studio must enumerate qualified editable fields from authoritative schema, show units/source defaults and per-CarID namespace, validate bounds and cross-parameter dependencies, and provide save/preset/diff/undo/rebuild. Keep preview wheel fitment distinct from *actual physical wheel positions/tyre/suspension/collision*.

**Gameplay camera (existing experimental Core, not Studio GUI):** `addon_sdk/camera_profile.py` has `diagnostic_only` comparison and an explicitly gated `native_follow_extents` binding of `height_m` and `half_length_m`, source-hash-pinned to a qualified `car.dx`. Owner earlier observed visible per-CarID camera changes for two cars. **FOV, smoothing, independent chase-offset editing, replay/front/other camera modes are not proven supported by this profile.** Camera Studio may initially expose those two qualified follow-extent parameters with exact limitations, preview bounds and before/after, while advanced camera tuning remains research-gated. Do not confuse D3D9 Previewer orbit/navigation with in-game camera edits.

**Roadmap priority:** Complete active Sound Studio first, then a *bounded* Physics & Camera Studio vertical slice rather than defer both until the end. Its acceptance requires an addon physics edit plus a qualified per-CarID follow-extent camera edit through GUI, source/target provenance, validate/build/revert and no unrelated vehicle leakage; stock and advanced camera fields remain read-only if unqualified. Subsequent GT Garage Lab and Model Studio order can follow practical dependencies: corpus inventory/colorway pilot first; Model Studio guided repair tools may be developed ahead of the exhaustive wide visual campaign; re-run Compatibility Lab after generic fixes. No phase may falsely advertise complete full-game camera authoring.

## C. Blender Bridge must include **Model Doctor** and guided repair

Model Studio is not finished merely by exporting OBJ/GLB and reading it back. Provide beginner-friendly **Inspect → Diagnose → Explain → Fix/Export Blender → Reimport → Compare → Validate/Build** as an end-to-end workflow. Every warning links to a relevant focused offline Help page, identifies source model/draw/material/texture and affected visual region, and distinguishes definite native incompatibility from approximate Previewer heuristics.

Mandatory diagnostic categories, each with source evidence, severity, conservative suggested fix, and regression fixture:

- **Backface culling and normals:** reversed triangle winding, mirrored transforms/negative determinant, truly single-sided mudflaps/guards/headlamp backing, missing back surfaces. Preview both sides, show face normals/winding and CW/CCW/NONE diagnostic, advise Blender normal reorientation or intentional rear faces/verified native double-sided semantics. Do NOT globally disable culling or duplicate all triangles.
- **Alpha and transparency:** distinguish diffuse alpha, vertex alpha/reflection weight, cutout/alpha test, blend, depth test/write and sorting, decal vs glass vs opaque paint. Display texture alpha and native material fields; repairs must preserve glass damage, reflective coverage and decal depth. Do NOT globally force alpha to 255.
- **UV/atlas/texture binding:** missing/incorrect texture, inverted UV, seam/disconnected island, shared atlas/decal ownership, source colorway, unsupported or oversize resources. Recommend targeted re-UV, assignment via existing Texture Binding v2, mask-aware paint and appropriate material conversion.
- **Wheels and physical fitment:** inward-facing rims, missing opaque recess/lip, reflected left/right instances, hub positions, visual radius versus physics/collision. Separate preview pose from game physics.
- **Native glass/damage, lights and crew:** source-qualified damage controllers/zones, two-sided glass, intact/cracked UV, lamp/brake glow, attachment bones/crew seat rest pose. Preserve native runtime ownership and animation rather than guess.
- **Topology/geometry budget:** nonmanifold or degenerate triangles, detached floating parts, excessive per-draw triangles, LOD, collision hull and scale. Distinguish recommendation based on measured MR ranges from real engine limits.
- **Environment/material intensity:** qualified reflection mask/weight, no universal shader strength without native evidence.

**Blender Bridge round trip:** Maintain stable object/draw/material IDs in a companion manifest, import/export axis/handedness/unit transforms, deterministic normals and winding, retained UV/material/texture references, cautious topology-diff and changed-draw revalidation, mapping conflicts requiring explicit human choice, and immutable source baseline. No silent loss of glass controllers, damage, collision, wheel/lights or author paint layers. Provide reproducible examples showing fixes for a backface and an incorrect alpha/depth surface. Blender add-on is optional; an intermediary asset format with manifests is permitted if native `.dx` round-trip is not yet verified, clearly labeled.

## D. Scope/priority after this update

**Active now:** Sound Studio / Audio Studio on existing Lancer; no owner D3D8 test needed to proceed with offline work.
**Next preferred:** bounded Physics & Camera Studio GUI using existing SDK Core and experimental camera follow extents; qualified fields only.
**Then:** GT Garage Lab source inventory plus verified real source colorway pilot; Model Studio & Blender Bridge with Model Doctor; comprehensive Classic generalization and GT3 scan/visual regression can be ordered against available source data and fixes.
**Later:** Fleet Builder and distribution QA. Preserve accepted Subaru glass, Pajero culling/materials, Lancer Classic pilot, 30-roster SCALE1 behavior, PERF2, Audio per-CarID, stock copy-on-write, private asset rules and existing original EXE/DLL protections. Local phase commits are authorized, but no push, publication or release without new permission.

---

# Master Rallye Vehicle SDK — Master Plan / Rally Workshop

**Working baseline:** 26 October 2026 (revision 5.0: V-SDK4D Audio Studio remains next; owner-approved GT3 compatibility corpus, source colorway research and cross-vehicle Classic MR generalization added as V-SDK4E. Historical sections intentionally retained.)
**Repository:** `master-rallye-re-vehicles` · **branch:** `research/vehicles`
**Purpose:** single living specification for development, review, acceptance and public beta planning.
**Status disclaimer:** this document summarizes previous source-review discussions and reported gameplay tests. It is **not** a new repository or binary audit; verify each item against the current checkout before implementation. Update the ledger after every development phase.


> **CURRENT DECISION — 2026-10-26 / revision 4.7:** The owner reports successful in-game tests of the V-SDK4C.1 fixes: Subaru glass now breaks correctly, and Pajero's visual corrections are accepted. This supersedes the pending owner gate in sections 19–20 without erasing those earlier reports. **V-SDK4B Paint Studio / Classic MR Style / Crew Fitment is the next active milestone.** Full Audio Studio remains a required product feature and gets an explicit four-layer user-replacement acceptance gate below. No D3D9 preview or automated test alone is proof of native gameplay parity.


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

---

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


---

# Owner handoff — 26 October 2026 — Master Plan v4.9 (V-SDK4B.1 review, Audio Studio next)

> **Supersedes the older “V-SDK4B.1 next” wording in v4.8.** Historical sections are retained intentionally. The next active implementation milestone is **V-SDK4D — Audio Studio Foundation**; V-SDK4B.1 is offline-validated and awaiting its separate owner D3D8 gameplay test, which is explicitly **non-blocking** for beginning V-SDK4D.

## V-SDK4B.1 evidence ledger

Artifacts inspected: `rally-workshop-vsdk4b1-source-review.zip` and `rally-workshop-vsdk4b1-changed-files.zip`. Full source archive has 978 entries (976 SHA256-manifest matches); changed-files archive has 28 entries (26 SHA256-manifest matches), and all 26 changed content files match the full archive byte-for-byte. All 416 Python files in the full archive parse. Independent Python synthetic tests for Classic, audio profile/integration, Workshop and turbo audio: **37 PASS**, after setting project `src`, `tools` and `tests/synthetic` on the Python path. Codex's Windows report claims **846 tests PASS / 1 optional skip**, not reproduced by this review. Both archives omit `.git`, private runtime candidates, private GT/MR assets, original EXE/DLL, and real-game evidence. Repository metadata records phase commit `e51d1d603d5adc00b7c12919ae980a4e561aed15`; independently verify in original checkout when needed.

`docs/sdk/VSDK4B1_RESULTS.md` documents the hash-qualified V-LANCER6 Classic recipe and these measured resource changes:

- Actual packaged race `car.dx`: **2625/107 triangles/draws → 2355/99**.
- Frontend `complete.dx`: **6333/186 → 4563/178**.
- `wheel.dx`: **745/16 → 370/16**; draw grammar preserved.
- Referenced texture resources **77 → 75**; native RGBA estimate **12,199,936 → 12,019,712 bytes** (~1.48% reduction). Do not market this as a major memory or FPS improvement.
- Deliberately simplified specified protective covers (48→16 triangles per affected draw), qualified sponsor overlay removal, rebuilt red/charcoal paint fields, retained signature numbers/marks, solid recessed Subaru-derived wheel backing, guarded opaque MR paint environment, protected cutout alpha.
- Stock MR class ranges were measured (IDs 0–20), but these are style references rather than engine limits. In particular, Classic Lancer Frontend triangles still exceed ordinary measured stock Frontend ranges; **one qualified Classic pilot is not universal full automatic MR-style conversion**.
- Immutable source → separate Classic output, deterministic report, explicit SHA256 approval before build, preserved Source Fidelity, qualified manual-layer replay and visible conflicts on topology/atlas changes.
- Source Fidelity and Classic 30-roster candidates exist as *alternative isolated builds* for CarID28, **not** simultaneous duplicate CarIDs. Preserved other vehicle resources, physics/audio/UI identity, stock resources and native runtime plan are offline-verified. No new game capacity claim.

**Status:** V-SDK4B.1 implementation **offline ACCEPTED for continuation**, D3D8 owner test **PENDING / non-blocking**. Keep a short deferred A/B acceptance checklist: launch `sf` then `cl` isolated candidates; compare body/livery/reflections/wheels all sides, brakes/glass/damage/crew, race/re-entry/Results/AI, menu loading. Preserve exact candidate paths and hashes from the owner's private checkout; do not infer archive-contained runtime files.

## Next active milestone — V-SDK4D: Audio Studio Foundation

The priority now is a **functional audio authoring UI** leveraging existing qualified independent per-CarID sound infrastructure, not adding a fourth vehicle or redesigning native sound systems. Existing `src/master_rallye/addon_sdk/audio_profile.py` already validates and compiles `audio-profile.json` v1 with engine plus optional `transmission_whine`, `turbo_spool`, `bov_release`; current native response logic has load/gear/RPM approximations. Existing tools include `vehicle_audio_import.py`, `vehicle_audio_audition.py`, `vehicle_audio_layers.py`, per-profile validation and native candidate builders. Existing Lancer was gameplay-heard earlier; new per-layer substitution and Audio Studio must still be tested per candidate. Preserve and integrate these functions through a shared SDK service; no duplicate CLI-incompatible GUI encoding.

**Required four slots:** Engine (native `wsDsFxRevs` source waveform), Transmission Whine (continuous native SFX), Turbo Spool (load/pressure proxy), BOV (release-triggered one-shot). Preserve correct event differences and guard syntax, source provenance, local hashes, per-CarID ownership, mute/solo, source diagnostics, bounds, reset, undo/redo, build/restore.

**Core vertical slice**:
1. Workshop Vehicle Library → Audio Studio for a qualified addon (pilot **Lancer Evo IV / CarID28**). Show current audio profile, four independently editable layers with source/provenance, active state, qualified response fields, loop/crossfade/trim controls only where supported.
2. **Import Local WAV / Assign Existing / Remove or Disable / Reset Layer**. Prefer explicitly tested RIFF PCM formats within existing decoder guards; never claim support for arbitrary GT3/GT4 proprietary banks or other compressed formats without a verified adapter. Convert to engine/SFX native mono PCM16/48k where the compiler actually does so, with warnings for DC, clipping, invalid/oversize sources, loop seams and gain.
3. **Per-layer audition**, mute/solo, RPM/load/shift/lift scripted preview and combined mix with audio measurements. The existing original-instruction Unicorn engine DSP audition is an offline diagnostic; native DirectSound device, event timing and in-race perceived loudness remain a distinct human listening gate. Do not pretend preview equals gameplay.
4. **Named audio presets** and per-car profile overrides with immutable source hash, relative private source reference or workspace-managed copy, authoring settings, provenance and controlled file-path portability. Preserve original synthetic whine/spool/BOV defaults if usage rights are confirmed. Import/export **metadata-only presets** freely; do not bundle private game-owned audio.
5. Isolated source-only/no-source A/B/C/D resource builds (engine-only change, whine-only, spool-only, BOV-only, then all four) using **existing Lancer**. Prove each independent layer change leaves other layer bytes, other CarID profiles, physics/material/glass/roster and normal game build identities unchanged. Ensure the build candidate is sealed, predictable and reversible.
6. Regression for audio allocation/lifetime: race enter/exit, multiple AI users, Results, optional source failure, mute/resume, BOV cooldown, resource namespacing, no global sound overwrite. Validate exact runtime constraints; avoid reintroducing past ECX sound-hook lifecycle fault.
7. Update GUI F1/Help, `CAPABILITIES.md`, `REGRESSION_MATRIX.md`, `COMMIT_LEDGER.md`, CLI examples and Master Plan. Commit completed/validated V-SDK4D **locally** only; no push/release without separate authorization.

**Explicit boundaries:** No speculative physical boost sensor, throttle-perfect signal, original GT audio decoder, new multi-bank engine playback, universal source bank import or unsupported stock audio overwrite. The v1 audio profile guards currently restrict the custom engine to qualified addon CarIDs; UI must show stock cars as unsupported/read-only unless native evidence expands support. Do not edit original `MRallye.exe`, `d3d8.dll`, retail files, frozen vehicle candidates or Randomizer. Do not ship private GT/MR audio.

**V-SDK4D acceptance:** Within Rally Workshop, using the **existing Lancer**, I can safely set a custom source for each Engine/Whine/Spool/BOV layer, audition one or all, customize qualified response parameters, save/load a preset, undo/reset, validate and build isolated candidates. The actual-game audio A/B and per-CarID behavior will receive owner listening confirmation later. Do not block next development on unavailable gameplay time; mark **OFFLINE / WINDOWS / OWNER GAME** separately.

## After V-SDK4D

Return to **V-SDK5 Model Studio / Blender round-trip / proportion and scaling comparisons**, followed by remaining Physics and Camera Studio, format adapters, fleet/install, public-beta QA. Keep **V-SDK4B.2 Classic generalization / interactive recipe editor** in the backlog, not silently declared complete. The owner wants a future distinctive-sounding **fourth test car**, but that is an independent vehicle-import decision once Audio Studio has a stable baseline; don't start a new import without chosen, permitted source materials. Maintain the mandatory glass/damage, native lights, wheel/crew fitment, source/Classic style, PERF2, 30-entry composition, stock copy-on-write and full regression matrix.


---

# Owner expansion — 26 October 2026 — Master Plan v5.0: GT3 Compatibility Lab, Colorways & Generalized Classic MR Style

## Decision and phase boundary

**Owner request:** Generalize the currently Lancer-specific Classic MR Style recipe to other GT-derived vehicles; test real source-car color variations using a qualified source that contains at least two usable stock colorways; run broad compatibility analysis of **all GT3 cars available in the owner's lawful local source corpus** without having to add every vehicle to the Master Rallye game. The aim is to discover conversion failures and incomplete coverage before public beta.

**Execution order:** Preserve active **V-SDK4D Audio Studio** (four independent Engine, Whine, Turbo Spool, BOV slots) and its narrow Lancer acceptance. After Audio Studio, start a separately budgeted **V-SDK4E Compatibility & Classic Generalization** series, before or as a prerequisite of larger Blender/Fleet work. Do not mix new GT3-car imports into V-SDK4D. Defer Lancer Classic D3D8 owner A/B as a non-blocking acceptance gate. The V-SDK4B.1 Lancer pilot is **offline-qualified for one hashed source recipe only**, not proven universal or gameplay-verified.

## V-SDK4E.0 — Source corpus inventory and coverage baseline

1. Inventory local, user-provided GT3 (and optionally GT4 comparison) input trees without copying proprietary content into source archives. Identify exact game/build/version/region/profile only when discoverable. Work with incomplete data without inventing vehicle totals.
2. Distinguish **catalog entries**, **unique model data**, **color/livery variants**, **wheel variants**, **LOD versions** and **licensed/source availability**. Do not assume one catalog ID equals one unique 3D mesh or one paint color.
3. Build a deterministic manifest (relative private input references, hashes, parser profile, classification, optional colorway and LOD inventory), with a scan resume/checkpoint mode and a lightweight resource-budget mode. Original asset files remain read-only.
4. Automatically group representative fixtures by evidence-backed source traits: road versus rally, open cockpit versus closed cabin, high-detail or unusual wheels, multiple body colors/liveries, unusual glass/alpha, decals, reflective split/islands, alternate geometry and possible damage-control constraints.
5. Maintain capabilities by **format version, vehicle source and subsystem**. Unsupported data receives a concrete explanation, never a false green PASS.

## V-SDK4E.1 — Genuine source colorway pilot

- Select **one source GT3 vehicle for which two or more actual color configurations are locally verified**, not a guessed GT3 model. If none is available, report the blocker and test with a qualified GT4 source rather than claiming GT3 proof.
- Research whether variants are alternate textures, livery/atlas sets, material-color records, material IDs or geometry-linked state. A user-authored recolor is **not** automatically proof that native source colorway selection is supported.
- Import source variants **A and B** through the same adapter, preserving body/material/decal associations, texture ownership, provenance and deterministic builds. Verify that wheels, glass, lamps, UV and unrelated assets are identical unless source evidence says otherwise.
- Expose `Source Colorway` (original GT palette/livery selection) **separately** from `Studio Custom Paint` and `Classic MR Style`. Do not flatten these into one RGB slider.
- Build and GPU-preview at least two variants offline, compare fixed-camera captures and resource manifests, reopen/save/restore, and explain any colorway state that cannot be reproduced in MR without a manual paint authoring workaround.

## V-SDK4E.2 — Reusable Classic MR Style pipeline

- Decompose the source-hash-pinned V-SDK4B.1 Lancer pilot into **reusable, evidence-gated stages**: semantic asset classification → MR class/style reference → protected topology simplification → livery simplification/mask planning → wheel reconstruction/lip/solid inner backing → MR-native material and reflection normalization → atlas/texture budget → validation/build/report.
- Use **separate GT3 and GT4 source adapters** and semantic intermediate contracts. Do not make the GT3 pipeline secretly depend on `mits0015` or GT4-only attributes, nor silently rewrite a GT3 asset as a GT4 profile.
- Classify mesh/material/texture roles explicitly: painted panels, trim, decals, glass/damage panes, lamps/brake glow, driver/co-driver, tires, rims, brakes, shadow/collision and environment passes. Ambiguous roles are held at Source Fidelity with a warning instead of destructively simplified.
- Geometry budgets must be **measured stock MR ranges**, segmented by vehicle class/role, not arbitrary hard polygon caps. Preserve silhouette, UV seams, glass/lighting/damage/control draws and culling. Report triangles/draws before/after per subsystem.
- For classic wheels, preserve proper outward facing orientation, side symmetry, rim lip and opaque recessed interiors without globally forcing alpha opaque or losing genuine reflections; leave explicit manual wheel-fit corrections available.
- Simplified liveries must select protected numbers/marks and use qualified semantic masks/texture adaptation. Blind blurring or downscaling original GT atlases is not a Classic conversion.
- Non-destructive `Immutable source + source colorway + style recipe + user overrides → sealed candidate` with stable IDs, change-provenance and explicit replay/conflict handling. Reapplying the same recipe to the same source must be deterministic and idempotent from the immutable baseline.
- Pilot beyond Lancer: **at least one non-Lancer GT3 representative** (Subaru as preserved regression, plus another available and structurally distinct GT3 input if qualified), and where useful Pajero as a GT4 regression. Do not change frozen gameplay-accepted sources as the test output.

## V-SDK4E.3 — GT3 Compatibility Lab: wide offline matrix

The **goal is breadth of diagnosis**, not installation of the entire catalog into MR.

Three progressively expensive levels, each separately counted in reports:

1. **L0 Inventory / Decode:** For every discoverable car and variant in the lawful local GT3 corpus, report parser availability, expected geometry/wheels/texture/colorway/LOD records, source hash, missing input and parser errors. No GPU or game required.
2. **L1 Conversion / Structural Validation:** For every uniquely decodable model within budgets, dry-run the canonical converter and optionally Classic recipe, emitting **temporary isolated output**. Verify DX/DXT structure, material/texture links, vertex and draw ownership, winding, UV bounds, alpha/culling, wheel dimensions, potentially dangerous per-car controls, resource and memory budgets. Do not install results into the game. Record clear failure categories and reproducible fixture IDs.
3. **L2 Visual / Targeted Runtime:** Generate deterministic Previewer fixed-angle captures for a stratified, manageable set of distinct complex cases (not necessarily every color or duplicate mesh). Select a smaller representative group for actual Master Rallye candidates / future owner D3D8 tests. Clearly distinguish D3D9 approximation from game proof.

Run the suite in **streaming/checkpointed batches** with bounded RAM/disk/CPU/time; support cancellation, retry, `--resume`, deduplication by source content, and extraction of diagnostics without retaining full proprietary rendered art in source-only archives. Prefer low-cost structural passes before costly rendering or gameplay.

Use one per-car/variant evidence row containing: `source profile; source ID; model/variant/LOD hash; discoverability; L0; L1; L2; Classic feasibility; source colorways; geometry; wheel/culling; materials/reflections; alpha/glass/damage; textures/UV; memory; errors; status; evidence path`. Status vocabulary **PASS / WARN / FAIL / UNSUPPORTED / NOT TESTED / MISSING INPUT** plus evidence tier. Do not aggregate a missing resource into a successful pass.

Offer sorted issue families for importer improvements (e.g. culling, decal blend, shared atlas, wheel side orientation, transparent pane, missing headlights, unsupported LOD). Fix underlying **generic importer behavior** before writing per-car exceptions. Record exception provenance and regression fixtures when exceptions are unavoidable. Re-run a representative baseline including accepted Subaru, Lancer, Pajero and stock MR editing after converter changes.

**Honest coverage claims:** `all GT3 cars tested` may only be used once the corpus version/region and denominator are documented and the specified L0/L1 levels truly covered each available entry; otherwise state `N scanned / M unique models / K converted / P visual-inspected / Q game-tested`, with exact exclusions and reasons. Never equate catalog-wide offline conversion to native D3D8 playability.

## V-SDK4E owner acceptance and constraints

- The user can choose among at least two **verified real source colorways** of one qualified car and distinguish source palette, custom paint and Classic style.
- Classic MR Style is a reusable semantic pipeline demonstrated beyond a Lancer-specific hash recipe, with demonstrably distinct simplified geometry, livery/paint, MR material roles and solid recessed wheels where safe. Unsupported parts are reported as fallbacks.
- Compatibility Lab produces a reproducible corpus-wide matrix and categorized failures without installing hundreds of cars into Master Rallye.
- Existing V-SDK4D audio authoring, per-CarID sound isolation, native glass damage, Pajero polished geometry, Subaru integrity, PERF2 frontend loading, 29/30 verified SCALE1 roster, stock copy-on-write, camera and UI editing continue to pass regressions. No unqualified max-car-count or universal GT3 compatibility claim.
- Nothing modifies original `MRallye.exe`, original retail files, existing `d3d8.dll`, unrelated Randomizer or frozen source models. GT3/GT4/MR assets remain private, local and excluded from released artifacts. Only owner-authorized scoped local Git commits; no remote push, release or publication.
- Each bounded subphase delivers a real implementation, quantitative coverage report, test/fixture summary, `CAPABILITIES.md`, `REGRESSION_MATRIX.md`, `COMMIT_LEDGER.md`, offline Help updates and source-only review archive. Leave owner gameplay checks open if unavailable instead of blocking independent development.

## Schedule handoff

**Now:** V-SDK4D Audio Studio on qualified Lancer.
**Next:** V-SDK4E.0/.1 corpus inventory plus a true source-colorway pilot.
**Then:** V-SDK4E.2/.3 semantic Classic MR Style generalization and checkpointed GT3 Compatibility Lab.
**Subsequently:** V-SDK5 Blender Bridge / scaling, remaining Physics and Camera Studio, Fleet Builder, public-beta QA. Keep future audio-based fourth-car demonstration separate from the corpus scan; do not silently add all discovered cars to the game.

---

# October 26, 2026 — Master Plan v5.5 addendum: Open Audio Import + GT Sound Bank Lab

**Priority update and source-of-truth precedence.** This addendum supersedes earlier statements suggesting that the existing narrow PCM guards or currently qualified Lancer audio are long-term product limitations. They are **current implementation bounds**. It does not supersede the native/runtime evidence boundaries or requirements to protect user assets, stock installations, and project reversibility. Active main-agent implementation remains **Physics & Camera Studio + Vehicle Identity & Presentation**. A separate GT Audio Research agent may work in parallel in an isolated worktree. The main agent shall integrate a more capable Audio Studio in the next bounded audio-improvement milestone once current work is safely checkpointed, independently of whether GT orchestration research is complete.

## Verified baseline from V-SDK4D source

- `src/master_rallye/addon_sdk/audio_profile.py`: one mono source through MR's `wsDsFxRevs` engine synthesis; stock tables preserved. **This does not reproduce GT4's original multiband engine orchestra.** Source WAV guards are SDK checks, explicitly not native engine maxima.
- `decode_pcm`: RIFF PCM only, mono/stereo, 8/16/24/32-bit integer, 11,025–48,000 Hz, 8 MiB file limit and 2,000,000 PCM frame limit. Non-PCM WAV, float WAV/WAVE_EXTENSIBLE, FLAC, MP3, Ogg/Vorbis and others have no qualified frontend importer. Existing trimmed continuous engine loop is bounded to 0.1–4 seconds; optional layers currently reuse several engine-source validations even when their playback semantics differ.
- `src/master_rallye/workshop/audio_ui.py`: a local `Import Local WAV…` file chooser, followed by trim/crossfade/gain dialog; existing separate Audition/Mix. There is **no pre-commit source/converted A/B playback in the import dialog**.
- Four current slots are independent: engine, transmission whine, turbo spool and BOV; whine/spool are continuous, BOV is a one-shot. Per-CarID isolation, source provenance, reversible presets and isolated builds have already been developed. Do not discard these.
- GT4 research `research/vehicles/vaudio1/gt4-source.md`: Lancer's source-car row maps through DefaultParts and Engine into **Sound ID 22601**, shared by other Engine rows. This bank has multiple RPM entries and source normal/turbo directory variants; the qualified current MR import uses **a single selected engine band**. Original GT4 loading, pitch, crossfade and gain clues exist, but historical build pairing and complete runtime mix are not fully qualified.
- GT3/GT4 events `b_off`, `turbine`, `turbine2`, `shift_change` are known from inventories. Event labels **do not establish actual sample/bank/program identity**. Original sustained transmission whine has not been authenticated. Never repurpose an unrelated event because of its name.

## Track 1 — Main-agent Audio Import 2.0 (independent of GT discovery)

1. **Choose nearly any ordinary user-supplied audio file without preparing PCM manually.** Support an extensible, safe, explicit decoder-adapter interface; target common RIFF PCM/float/WAVE_EXTENSIBLE, FLAC, Ogg/Vorbis and MP3 using verified local decode backends, dependency checks and transparent messages when an adapter is unavailable. Detect signatures, not only extensions. Reject malicious/malformed/decompression-bomb sources safely. Do not assert support until implemented and tested. Proprietary GT files enter through separate source adapters, not by pretending that arbitrary bytes are audio.
2. Retain originals unchanged and pinned by SHA256; convert decoded samples to qualified native output using deterministic controlled channel mixing, resampling and sample-rate/bit-depth conversion. Make length/cap limits **layer-appropriate**, allow long source files via streamed and bounded decoding, then derive smaller engine loops or one-shots as necessary. Keep final native resource budgets and explicit per-layer constraints. Do not remove all resource guards in pursuit of universality.
3. **Preview before import:** in the chooser/import dialog provide Source Play, Converted Play, A/B, Loop Preview where appropriate, waveform and selection/loop marker, Stop, gain/peak/clipping/loop seam warnings, and audible audition of the *selected destination layer* under a simple scripted RPM/load/gear event. Apply only after user approval. Clear distinction between approximate offline preview and actual DirectSound gameplay.
4. Allow assigning **any already imported compatible sound** to Engine, Whine, Spool or BOV, regardless of its previous source/role, with explicit layer semantics (looped vs triggered) and support for source-specific suggested trims and controls. User must not have to generate a special 4-second WAV. Keep per-layer source hashing, presets, Undo/Redo/Restore, CarID isolation and native build integrity.
5. Provide automatic loop detection/selection candidates, silence trim, DC removal, click-safe crossfade, loudness/gain and clipping diagnostics. Do not claim automatic musical/acoustic correctness. Expose manual override and audition; do not silently stretch one-shot BOV sounds into continuous loops or invert trigger ownership.
6. Make a clear status vocabulary `Decoded`, `Converted`, `Native buildable`, `Auditioned`, `Gameplay tested`, and distinct failure reasons. No blanket hard-lock from first-stage input format checks; retain actual native constraints.
7. Test source-only synthetic fixtures covering common codecs and difficult inputs, import-dialog preview, multiple source lengths, conversion determinism, four destination layers, presets, missing adapters, immutable originals, candidate-diff isolation and audio resource memory budgets. Avoid adding third-party binaries/licenses without review.

## Track 2 — Independent GT Sound Bank Lab research

**Goal:** source-verified vehicle→bank→sample→RPM band/event and activation map for lawful user-local GT3 and GT4 source trees. Investigation is research-only until qualified; no private sample or original game content bundled, published or copied into general source archive.

1. Inventory exact user-local GT3/GT4 source builds/volumes, table layouts, car identifiers, sound banks, container formats, metadata, sample counts and hashes; report missing/inaccessible prerequisites separately. Preserve user files read-only.
2. GT4: reproduce and generalize the known car→DefaultParts→Engine→`soundNum` association (Lancer 22601 is the oracle); map shared sound IDs, engine/normal/turbo bank variants, possible tuning profile selection, RPM windows, base pitch, gain and crossfades; qualify sample duration, loop flags and required decode provenance. Do not assume path `turbo*` is an isolated spool/BOV sample.
3. GT3: expand the present RoFS `sound/se.inf` GTSE event inventory and five known INST banks into source-qualified container/dispatch evidence; trace runtime event token→bank/program/split/sample/pitch/gain where matching executable evidence is available. Unknown mapping remains UNKNOWN, not a guessed match.
4. Both: trace `b_off`, `turbine`, `turbine2`, `shift_change` event dispatch and actual triggering rules; distinguish one-shot effects, synthesized behavior, engine bands and any true transmission whine. Separate source data facts, comparative external implementation hints and matching-build native evidence.
5. Deliver a private sound-bank explorer/index and source-only code that reports car identity, sound ID, sample table, RPM ranges, loop points, and playable auditions of explicitly decoded samples with confidence annotations. Never claim a GT sample's acoustic role solely from filename, numeric ID or subjective timbre.
6. Contribute a **candidate mapping contract** consumable by Audio Studio: source game/build hash, car ID/name, bank path/hash, program/split/entry, validated playback rate, loop region, inferred/verified role, confidence, conversion method and user acceptance. Prototype `Find sounds for this car` with explicit recommendations; uncertain suggestions stay manual.
7. Run synthetic tests and replay known Lancer reference mappings. Use dedicated scratch/worktree and written handoff. Give a precise blocker report and next experiment if an event dispatch relationship remains unproven rather than fabricating a 'complete orchestra'. Do not modify the main agent's live files or merge without review.

## Future research dependent on runtime evidence

- To reconstruct GT's **full multi-RPM-layer engine orchestra**, investigate a source-adaptive multi-band engine runtime or source-aware offline simplification. The existing MR `wsDsFxRevs` single-loop path remains a working fallback. Exact GT playback may be impossible without further verified runtime extension. Each approach must state real differences and costs; native hooks require isolated ABI/lifetime/race-reentry/performance qualification.
- Support AI and multi-car simultaneous audio, race re-entry, Results and no cross-CarID sound leakage. Preserve existing proven native sound hook register/lifecycle fixes. No original EXE or d3d8.dll on-disk modification.

## Work order, naming and acceptance

- **Now — Main agent:** complete Physics & Camera Studio and Vehicle Identity as previously scoped; update existing audio requirements in the capability ledger so `PCM WAV only` is shown as *current adapter coverage*, not a permanent limitation.
- **Now — Separate agent:** GT Sound Bank Lab research in a separate worktree or separate notes, with read-only original game sources. Deliver evidence and a handoff contract, not unreviewed changes to the main branch.
- **Next audio enhancement — Main agent:** Audio Import 2.0, pre-commit audition and arbitrary compatible source-to-layer assignment independently of source game; integrate the GT adapter afterward when the independent research delivers evidence.
- **Later:** full GT multi-band engine proof of concept only when audio data and necessary native capabilities are actually qualified. Do not delay ordinary user sound imports on an unresolved GT mystery.
- **Acceptance:** a user can select ordinary supported source audio, audition original and converted versions *before applying*, assign that sample to any of four layers with appropriate looping/triggering, adjust and build a reversible candidate. For GT source exploration, user can identify verified bank-to-car/sample relationships and see unknown areas honestly labeled. Audio remains private and source-only archives contain code and synthetic fixtures, not commercial game data.
- Validated phases may be committed locally with documented test evidence. No push, release or publication without explicit separate authorization. Maintain `MASTER_PLAN.md`, `CAPABILITIES.md`, `REGRESSION_MATRIX.md`, `COMMIT_LEDGER.md`, and offline Help.


---

# October 26, 2026 — Master Plan v5.7: Audio Import acceptance, Vehicle Fidelity, Game Camera Lab

**Source of truth / supersession.** This additive update follows the canonical source review at commit `1eeb45f584c5ef82be878e110a3e2c23d4d350c8`, preserving every earlier requirement, research hypothesis and previously accepted game test. Older schedule handoffs referring to Physics/Camera as "not started" or Audio Import 2.0 as "future" are superseded by the current status below. The working branch and local-Git-commit discipline continue; remote publication always requires separate authorization.

## A. Reviewed status and evidence boundaries

- **Physics & Camera Studio / Vehicle Identity & Presentation:** implemented and Windows/offline validated, `53fa708ed1e1a2290fe50ddc3a1286c1488faf28`. Native gameplay camera edit currently controls source-qualified *follow extents* (half-length and height), **not** camera position, distance, look-at, damping, FOV or replays. Vehicle labels/aliases and UI artwork have native build integration; 33 donor physics families qualified under existing schema. Owner game test of latest candidate still pending.
- **Audio Import 2.0 / optional GT Sound Bank Lab:** source-review commit `1eeb45f584c5ef82be878e110a3e2c23d4d350c8`; 1026/1026 manifest file hashes, 443 syntactically correct Python files; changed-only source files 43/43 match; available synthetic test groups were independently run on the review machine (Audio Import 9, GT Lab 6, shadow 6, camera-profile 3). The author's Windows report states 894 tests OK with one optional skip. Do not conflate the latter with locally reproduced all-Windows validation.
- Audio import supports source PCM WAV, optionally local ffmpeg/ffprobe for admitted MP3, FLAC, Ogg Vorbis/Opus and float or alternate PCM WAV; the reported source caps remain 64 MiB and 30 seconds, and current engine/native authored interval is 0.1–4 seconds. These are *current implementation bounds*, not an engine-wide theoretical limit. Source/converted playback occurs before Apply; all four output roles and source provenance remain independently reversible. Full GT engine multiband orchestration remains unsolved; one chosen band uses the MR native synthesis fallback.
- Source-qualified private GT bank inspection has real RPM/event/record provenance; `turbine2` drivetrain evidence and separate `turbine`/`b_off` relationships do not constitute full acoustic playback parity. Missing `shift_change` program 15 and 14 unhandled INST entries remain explicit blockers.
- **Audio audition warning:** the combined scripted near-listener four-layer candidate E reports **2747 clipped PCM samples** across test segments. Individual layer compile guards pass; owner should inspect actual gain/headroom and listen in-game. DirectSound/device settings and physical attenuation are not reproduced by the offline sum.
- No new D3D8 gameplay qualification is inferred for the latest Audio/Camera/Classic candidates. Previously accepted Subaru glass and Pajero material/visibility gameplay observations remain accepted.

## B. Next phase: Vehicle Fidelity (shadows + Classic MR rubber/glass + UI usability)

### Shadow Studio / Auto Fit

- Reuse `addon_sdk/vehicle_shadow.py`, `tools/vehicle_shadow_native.py` and existing hash-bound profiles, not a new unverified renderer. Expose **Auto Fit** from the exact Race body X/Z envelope and transparent-shadow texture alpha support; show physical units, source/candidate profile, computed footprint, margins, scale, offset and effective alpha threshold. Distinguish the body bbox from rendered footprint and from collision bounds.
- Provide **manual width/length scales, X/Z offsets, margins, alpha threshold** with original/donor/current Reset, Undo/Redo/Restore and explicit Save/Build. Use source-qualified native shadow-only bounds dispatch; never rewrite collision or model spatial bounds in place or alter shared shadow textures.
- Add Previewer **shadow-projection guides**, top-down overlay and Original/Modified comparison, clearly marked as D3D9 approximation. Test small passenger, long rally prototype and tall offroad fixtures; ensure source pin mismatch or absent qualified marker fails closed. Performance, menu UI and independent CarIDs must not regress.
- Review earlier Evo shadow fitting provenance; do not assume a global shadow texture fits every vehicle or force identical offsets for different classes.

### Complete Classic MR Style material semantics for tyre and glass

- The qualified Lancer `classic_style.py` explicitly states that original **glass/rubber/light materials are retained**. Therefore current Classic is not yet a complete MR-material normalization stage. Diagnose relevant physical draws, native DX render flags, opacity/alpha-test, environment pass, normal/decal ownership and source GT texture provenance. Distinguish inherited GT *visual textures and source semantics* from actual executable "GT shaders" (MR renderer consumes native-converted DX semantics).
- Introduce qualified, versioned **MR Tyre/Rubber** and **MR Glass** semantic transformations with local stock reference inspection, preview/compare and per-role Reset. For tyres, qualify opaque black sidewalls/tread, tint/diffuse, UV texture substitution and solid wheel inner recess without hiding brake/disc geometry. For glass, qualify optical appearance/alpha/environment and keep each of the four native logical damage-controller groups, Subaru-style crack adaptation, intact glass, lights and depth/sorting intact.
- **Never** make every GT source surface opaque or remove alpha globally. Do not overwrite donor/project originals; unclassifiable material remains source faithful with a machine-readable warning. Check race `car.dx`, frontend `complete.dx`, standalone `wheel.dx` and assembled views, including near/far and direct/oblique camera angles. Keep generated Classic deterministic/idempotent with manual overrides and source SHA guards.
- Follow-up broad Classic generalization and original GT3 colorway support remain in GT Garage Lab after this selected-vehicle material pilot; do not claim universal GT materials fixed from one car.

### Readability / UI polish

- Add meaningful icons to Undo, Redo, Save, Restore, Validate, Build, audio Play/Stop and camera controls, with readable accompanying text/tooltips and accessible keyboard accelerators. Use legally distributable original/icon-font-optional assets; do not embed proprietary fonts/assets.
- Fix clipped labels/buttons at common Windows DPI/scaling and smaller app window sizes: responsive toolbar groups/overflow or wrapped action rows, resizable workspaces, minimum supported dimensions, visible scroll handling and persistent layout. No inert decorative icons; ensure actions, disabled states, shortcuts and offline F1 Help remain synchronized.
- Do not initiate wholesale GUI toolkit replacement just to address these layout problems.

**Vehicle Fidelity acceptance:** stable saved/restored shadow fitting, qualified MR-style tyre/glass appearance visibly different from Source Fidelity without damage/opacity regressions, actual isolated candidate, UI usable without clipped action labels, deterministic test evidence, and owner D3D8 checklist. Owner D3D8 may remain pending while independent next research continues.

## C. Following phase: Game Camera Lab + Gameplay Camera Preview

- First reverse source-version-matched native **camera pose pipeline**: update timing, active camera modes, player vehicle/model bounds, world/view/projection matrices, follow target and offset, jump/speed/reverse response, FOV and smoothing if independent controls truly exist. Capture exact offsets/functions/constants and compare multiple stock MR cars and known user-confirmed per-CarID follow-extents edits. Do not infer camera distance simply from modified model bounds.
- Implement a **real 3D Gameplay Camera Preview** inside or alongside established D3D9 Previewer, with vehicle and ground reference, camera frustum/target guides, Source/Edited view switch, numerical profile inspector, saved test poses, motion playback/reference trajectory only when justified. Use an *approximation* label until full D3D8 camera matching is proven; do not call static manual orbit the game camera.
- Treat default/stock and donor camera profiles as immutable provenance. Provide **Original / Donor / Custom**, one-action Reset and safe per-CarID binding. Expose FOV/smoothing/distance etc only after native semantics and safe source/CarID-bound patch paths are qualified. Unsupported controls must be read-only, not sliders to nowhere.
- Deliver actual D3D8 screenshot matched-pose comparisons when owner can test; document projection/rendering differences and quantify camera-space error, not just one visually similar screenshot. Keep first prototype independently testable and nonblocking on owner timing.

## D. Remaining product roadmap, preserved in full

1. **MR Heritage Garage:** user-local Demo/retail edition import, independent new CarIDs, Data.sma qualified stock physics selection, preserved original looks, native glass and brake-lamp completion, identity/assets and full vehicle catalog separate from installed fleet. Retain 29/30 proven SCALE1 boundary unless expanded with new evidence.
2. **GT Garage Lab:** real source-colorway pilot, qualified Classic material/general geometry/wheel/livery generalization and batch GT3 L0/L1/L2 compatibility audits, with explicit denominators, failures, resume/budgets and no mass in-game installation requirement.
3. **Model Studio + Blender Bridge:** stable IDs, round-trip geometry/UV, normals/winding, culling, alpha and reflection diagnoses, collision/wheel/crew attachment preservation, scale/Fit original-versus-modified reference, targeted Model Doctor guidance (primarily for unfamiliar future imports).
4. **Fleet Builder:** reversible multi-vehicle project/CarID management, conflict detection, game resource-bank/UI checksums, install/rollback, re-entry/AI/Results qualification, packaging and release notes.
5. **Long-term audio:** optional verified GT multi-RPM orchestrator, further direct event-to-sample research, arbitrary qualified source input improvements beyond current 30s budget, tuned mixed headroom and stock audio support only if native evidence permits. Keep baseline MR single-loop as fallback.
6. **Public beta:** F1/help and tutorial, meaningful UI and self-explanatory errors, catalog provenance, stock zero-edit passthrough, sustainable plugin/format adapters, regression matrix and source-only distribution. Monetization remains optional and never conditions access to code or copyrighted game assets.

## E. Near-term owner checklists and regression gates

- **Audio candidate**: source/native preview; engine RPM sweep, drive/coast Whine, load-driven Spool, release BOV, E headroom with actual in-game Engine/SFX volumes; stock/addon AI, Results and race re-entry. Log anything clipped or overbearing before rebalancing. Do not overwrite accepted baseline.
- **Physics/Camera/Paint/Classic candidate**: validate separate builds, identity/art/results, per-CarID follow-extents isolation, physics only on intended family, Classic paint/tyre/glass vs Source Fidelity, no driver/crew, damage or shadow regressions. Missing gameplay checks remain explicit.
- **All future source code phases**: isolated candidate and restore, unchanged original `MRallye.exe`, `d3d8.dll`, retail `Data.sma` and private game sources, source hash lock, native ABI/lifetime, no unrelated Randomizer changes, 29/30 previously verified roster expectations, PERF2 load speed, and prior Subaru/Lancer/Pajero fidelity. Local commits authorized for completed phases only, no push/publication/release without specific permission.

---

# 27 October 2026 — Master Plan v6.0: Heritage Trooper closeout and Gameplay Camera 2.0

## Source-review baseline and owner evidence

The reviewed scope is `rally-workshop-heritage-source-review.zip` and its matching `rally-workshop-heritage-changed-files.zip` delivered 27 October 2026. Source manifest: 1062/1062 SHA256 files matched in a 1064-entry ZIP; 469 Python files parsed; the 24 changed payload files matched the complete source archive byte-for-byte. Independent targeted reviewer replay: 47 PASS across Heritage, Camera, Workshop, Audio Workshop and presentation-related tests. Broader test selections encountered the missing `tests.helpers` private/legacy fixture, which is not treated as a Heritage failure. Codex's reported Windows/full synthetic suite: 910 tests, two optional skips; independent complete Windows replay not performed here. REVIEW.json declares phase commit `7412f1571270cc8539810978a7126604cc5502ff`; absent `.git` history within source-only ZIP, this is report evidence, not independent Git verification.

The owner confirms **Isuzu Trooper appears in-game with its original correct wheel placement**. Count this as owner-supplied gameplay evidence for vehicle availability and visible wheel alignment, not as a full D3D8 race lifecycle/damage/audio/AI/results/re-entry pass. Detailed native glass, brake and collision behaviors for this exact candidate need explicit verification as described in `docs/sdk/HERITAGE_GARAGE_RESULTS.md`.

This is the first genuinely imported Demo 9.3.1 Trooper in an independent `HeritageTrooper` project, runtime CarID29 / T2 local9, with an isolated 30-record roster keeping Mercedes26, Subaru27, Classic Lancer28 and omitting Pajero's installed slot only in this candidate. The separate Pajero project and builds are retained. Original geometry, driver/copilot, source wheel transforms and collision remain; native MR donor physics `Vehicles/Trooper` is cloned into `Vehicles/HeritageTrooper` with explicit source provenance; Navara stock audio profile7 is an acknowledged donor fallback, not recovered Demo engine audio. Source glass logic has qualified front/left/right triangles, no fabricated transparent rear pane; brake-light states are bounded to native lens draws. All authoring is read-only toward Demo/retail assets; no 31-slot gameplay claim.

The separate `master-rallye-re-rdemo` investigation was reused after inspecting branch `research/r-demo-pipeline` at recorded HEAD `a48afa147ef984e809f1f065299985aefaad6091`, not wholesale merged. Inventory covers 33 Demo family directories, including alpha/duplicates, and 26 retail model families: demo 8.4.1 has 14 directory families and zero stageable under current rev127 policy; 9.3.1 has 13 with five structurally stageable; 9.10.0 has six with five structurally stageable. These are not guaranteed unique or playable-car counts. Rev131→135 upgrades are qualified, rev135 passthrough is qualified and rev127 remains deliberately unsupported until researched, not solved by changing a version word. Original Trooper files match known R-BRIDGE hashes; generated Cooker caches must not be confused with shipped source models.

Native class-slot research identifies a 12-position UI-key publisher comparison, separate class-count handling and other unqualified resource/AI/save boundaries. Owner-confirmed active fleet is still 30, not 36. Hypothetical 13/16 publisher CPU tests and T1/T2 spare arithmetic do not authorize an automatic capacity increase. Do not enable >30 by default until separately tested and specifically requested.

## Next active milestone: Gameplay Camera 2.0 (five real camera views, FOV and live authoring)

The pilot Heritage Garage objective is achieved. Return to the owner-requested camera extension before the next mass Demo/GT work. Keep the next milestone bounded: investigate and implement the qualified parts of *five actual switchable in-race views* and live edits in the D3D9 Previewer; determine safe FOV authoring; do not invent five independent sets of controls from three XML Follow profiles or claim a fully native simulator from a static preview.

### A. Source-qualified five-view camera research

1. Reuse `docs/sdk/GAME_CAMERA_LAB_RESULTS.md`, `research/vehicles/vsdk2/game-camera-lab.md`, the exact retail matching-build EXE evidence and tools for native CPU replay. Map the player's five visible in-race camera choices to actual native camera object class, mode switch dispatcher, camera manager index, source XML `Cameras.xml` presets, split variants and renderer camera/FOV assignment. Explicitly distinguish five UI/player camera modes from three Follow XML profiles and their split variants; map rear/replay/special cameras separately if present.
2. Trace mode initialization, per-frame update/lifetime, eye-target-up, camera world/view/projection math, aspect-ratio behavior, FOV copy/conversion, distance/height/focus/pitch, temporal smoothing and speed/terrain branches. For each, identify source/version hashes, instruction/data addresses, records, guarded owners and evidence grade. An unknown value remains read-only; no speculative native hooks or silent global camera change.
3. Determine whether FOV is global shared configuration, per-mode/per-instance, per-vehicle or renderer-wide; if it is shared, prove safe vehicle+camera mode isolation before adding authoring. A globally applied FOV change must never be presented as independent per-CarID/per-mode authoring. Compare normal, split, reverse, replay, race re-entry and AI camera owners where relevant.

### B. Live D3D9 Gameplay Camera Preview and direct manipulation

1. Evolve the existing Previewer, not a second renderer. Users should select the source-identified camera mode, view the real assembled model, ground/wheels/driver, switch Original/Modified, and *drag* qualified camera eye/target handles, or interact with qualified FOV controls with immediate visible results **without restarting the viewer or rebuilding resources**. An explicit Apply persists changes; Cancel/Restore reverts preview-only changes. Keyboard entry, numeric fields and wheel/scrub should stay synchronized with viewport, with reasonable throttling and robust process/session cleanup.
2. Support viewport aspect ratio, projected camera frustum/target overlay, editable vs read-only indicators, original/current numerical inspector, screenshot A/B and saved reproducible camera state. Do not silently alter physics, shadow, collision, source mesh or other cars while adjusting preview. If the mathematical model only covers first-frame flat static Follow, label the simulated view accordingly; more modes require actual reconstruction before claiming parity.
3. Provide Original / Donor / Custom for each *qualified independent camera scope*; one-click Reset with undo/redo/history, reopening and deterministic native candidate compilation. If native ownership is shared, visibly show that scope and warn about cross-mode coupling. Restore must never overwrite camera presets of unrelated vehicles.
4. Reuse the already working Race Progress Marker color; do not regenerate or rewrite the common icon texture. Preserve accepted Lancer Softened Whine and the accepted Spool/BOV. A separate future Lower Pitch Whine preset can be tested without replacing accepted sources or interrupting this milestone.

### C. Isolation and test qualification

- Deliver an evidence table for all five visible camera modes: source identification, original parameter owners, supported live Previewer calculations and genuinely safe native editable fields. No arbitrary fake FOV/distance/smoothing sliders.
- Provide at least one real controlled per-CarID/per-mode FOV or other extra-camera native experiment **if research proves isolation and ABI safety**. Otherwise deliver the fully functional read-only or approximate live viewer and a clear bounded blocker; do not claim independent authoring success without the native proof.
- Include frame-by-frame controlled native x86 playback or source-matched trace tests where possible, with D3D8 owner screenshot comparisons at fixed window aspect ratios and source model. State numeric projection/pose deviations and unknown dynamic terms rather than just a visual impression.
- Test cameras of one qualified original retail car, Lancer, Subaru, Pajero and Heritage Isuzu in independent source/roster configurations. Avoid transposing Pajero and Isuzu into the same CarID29 simultaneously. Verify owner binding and lifecycle for scene switches, Alt+Tab, menu re-entry, split-screen, owner teardown, failed resource loading and stock fallback.
- Protect retail MRallye.exe, data archives and original D3D8 DLL. Source-only ZIP must not include private model, audio, textures or runtime candidates. Local validated commit authorized; no push, publication, release or unrelated Randomizer modifications. Update capabilities, regression matrix, help, commit ledger and Master Plan.

### Acceptance gate

The Workshop selects the source-mapped real camera mode, opens a *responsive live 3D view*, permits qualified camera changes and compare/reset directly in that view, and builds an isolated reversible candidate whose written camera scope is fully explained and tested. Five camera modes and FOV are explicit research targets; do not assert five independent editable sets unless real native evidence supports it. D3D8 gameplay parity is owner-confirmed only where actually tested.

## Immediate owner Trooper verification (nonblocking for Camera 2.0)

The owner has confirmed Trooper appears and correct original wheel fitment. When convenient, verify actual race suspension/grounding, intact and cracked front/left/right glass, brake ON/OFF confined to lenses, deformation/collision, audio donor, new AI roster, stage completion/Results/re-entry. Distinguish confirmed items from pending in the acceptance ledger. Test the new Heritage roster separately from accepted Pajero roster; preserve both.

## Subsequent milestones after Gameplay Camera 2.0

1. **MR Heritage Garage — catalog breadth and independent fleet slots:** create additional 9.3.1/9.10.0 vehicles through the reviewed adapter; add qualified rev127 8.4.1 only after real revision research; donor physics/art/audio/light/glass ownership and source-family identity are explicit. 31/32 roster research is an independent gated capacity experiment, not an assumption.
2. **GT Garage Lab:** GT3 breadth L0/L1/L2, exact source colorways, semantic Classic MR Style generalized beyond Lancer, transparent documented failures, limited game installs.
3. **Model Studio + Blender Bridge:** source-preserving round trip, stable mesh IDs, normals/winding/culling, UV/alpha/material repair, collision, scale/fitment, future Model Doctor.
4. **Fleet Builder:** project collection, configurable alternative rosters, safe slot allocation, conflict detection, installs and rollback. Preserve all historic accepted Isuzu, Subaru, Lancer and Pajero projects.
5. Optional audio Lower Pitch Whine A/B, original GT multi-RPM research, longer input support and release-quality QA remain visible future work; preserve accepted BOV and Spool source/gain unless separately tested.


## Implementation status — Gameplay Camera 2.0, 27 October 2026

Source-qualified three Follow + two Fixed cycle, per-object FOV/aspect ownership,
per-CarID/per-mode guarded copy overrides and continuously running D3D9 camera
drafts are implemented. Normal/split override scope is explicitly shared. Fixed
position, dynamics and replay controls remain read-only. Owner-requested lower
clipping correction is an explicit unsaved Follow framing draft; the bonnet view
has a neutral rest-pose floor/grid and height reference. See
`GAMEPLAY_CAMERA2_RESULTS.md` and current regression evidence. All new D3D8 camera
behavior remains pending owner; the full separate Heritage Trooper acceptance
reported with v6.1 is confirmed and preserved. After validation/commit of this
camera phase, proceed only to the requested bounded Vehicle Presentation Polish.


## Implementation status — Vehicle Presentation Polish, 27 October 2026

Gameplay Camera2.0 completed and committed first (3919a7e / fc3c97d).
Results naming reuses the qualified fixed display path, adds actual icon preview
and targeted history/Restore. Frontend Presentation is a separate addon-scoped
private camera-target adapter, not model or gameplay physics translation.
Trooper/NewRav/Lancer source measurements, stock-like vertical matching, live
D3D9 drafts, source/reference comparisons and isolated name/framing candidates
are implemented. Stock reference remains read-only; unsupported frontend
FOV/distance/scale controls are not advertised. Exact capability boundaries,
source addresses, regressions and owner checklist: VEHICLE_PRESENTATION_RESULTS.md.
Accepted Heritage gameplay remains owner-confirmed. New camera/presentation
D3D8 behavior remains pending; stop here for review, no subsequent imports.


---

# 27 October 2026 — Master Plan v6.2: Vehicle Presentation review and GT Garage Lab activation

## A. Source and owner evidence

- Review sources: `rally-workshop-presentation-source-review.zip` (1,079 ZIP entries, no CRC errors; 1,077/1,077 manifest SHA256 matches; 481/481 Python AST parses) and `rally-workshop-presentation-changed-files.zip` (26 entries including manifest and metadata; 24/24 changed source/document/test files match the full archive byte-for-byte). Both archives contain no `.git` history; `REVIEW.json` declares final revision `9416ddbc976da283964ab0ea621884b1789e0fe4`, scoped phase commit `5d389f1e1ae997c9a0a18926efb67b6c7bfb0a79`. These identities are metadata claims, not independently inspected commits.
- Independent reviewer targeted Python regression: **98 tests PASS** covering frontend presentation, camera mode authoring, camera profiles/replay, vehicle authoring, Heritage source, Classic style, Fidelity, Shadow Studio, Workshop audio, Paint/Crew, Workshop and vehicle selection UI. The reported **923 Windows tests / two optional fixture skips** come from the implementation report, not an independently repeated full Windows run.
- Implemented Results/Driver field is the **fixed per-vehicle `results.display_name`**, 64 printable ASCII, with real existing 32x16 resource in an illustrative GUI Results-row preview, Apply, Undo/Redo and Restore. Not an AI DriverID or participant/crew runtime identity editor. Owner confirms the name is editable; final native Results name behavior for a new custom value remains separately owner-testable.
- Frontend Presentation reuses source-qualified VehicleSelect camera and `gaFrontendCarMoverAI` path. The reference model is original **stock NewRav**. At 640x480, reported model bottoms were Trooper 432.96px, stock NewRav 401.09px, Lancer 412.27px, from exact source projection. Trooper Auto Frame chooses `+0.453632 m` as **private frontend camera target correction**; model vertices, wheels, collision, physics and in-race cameras do not move. This is vertical-baseline matching, not proven dynamic native panel fitting. Large VehicleSelect correction is unique-resource/scene/source-bound and reversible; stock comparison stays read-only. User confirms updated preview looks good; D3D8 presentation build parity remains a separate owner verification until observed.
- Previous Camera 2.0 has five actual player-selectable types mapped to **three Follow + two Fixed**. Source-qualified normal/split scope is shared for the chosen mode. Follow supports qualified FOV and Dist Front/Back/Up, Fixed supports FOV; pitch/smoothing/speed response, fixed geometry and replay remain read-only pending research. D3D9 live viewport and guarded native candidate exist. User reports improved camera appearance/editability, but untested native mode/split/lifecycle behaviors must not be overclaimed.
- The owner deliberately replaced the root `Data.sma` that had old track-build contents with an original clean retail archive. The phase records a current root hash beginning `03c2b52d...`, matching its retail baseline; previously recorded root hash began `7cc2be10...`. Treat this as an **explained external change**, not as a developer-phase write or a failure to preserve the build's sealed 313 vehicle resources. Keep before/after hashes, manifest provenance and owner attribution. Never replace or rewrite original game corpora as a repair strategy.
- Accepted full Heritage Trooper owner game results remain: model/wheel alignment, physics, sound, brake ON/OFF, broken glass, UI imagery, race completion/Results and menu re-entry. Trooper and Pajero are **alternative** CarID29 30-slot rosters; do not install concurrently in the same CarID. Other frozen accepted cars and Audio Studio remain unchanged.

## B. Immediate next user-facing milestone — GT Garage Lab: Classic MR Generalization and True Colorways

The next phase should create a real **reuse-first** conversion system and a measured GT3 corpus baseline, not manually install the entire GT3 catalog. Activate the previously deferred v5.0 GT compatibility obligations. Provide user-facing naming, not new opaque phase suffixes.

### Workstream 1: Read-only GT3 source corpus and deterministic compatibility baseline

1. Locate the actual owner-local, read-only GT3 sources (and optional separate GT4 comparison sources); verify build/region/version and source hashes before interpreting model IDs. If sources are missing, record `MISSING INPUT`, never synthesize a catalog.
2. Enumerate source vehicle records versus **unique model hashes**, LODs, wheel assets, materials, texture atlases, colorways and decodable variants. Do not equate vehicle database entries with unique complete 3D assets or count variant colors as wholly separate models.
3. Implement resumable, bounded `L0` scan for **every available catalog entry** and selectively representative `L1` dry-run conversion; store per-entry `PASS/WARN/FAIL/UNSUPPORTED/NOT TESTED/MISSING INPUT` and exact causes. Limit CPU/RAM/disk; hash-based deduplication, crash isolation, cancellation, repeatable reports and `--resume` are required. No bulk runtime candidates.
4. Create private scan outputs, a source-only compatibility schema/report generator, issue-family clusters and fixtures with proprietary content excluded. A coverage percentage must name its exact denominator and evidence level.

### Workstream 2: genuine source colorway selection

1. Find at least one **actually evidenced** GT3 car with two original color/livery choices (if none in local GT3 sources, report that and use a source-qualified GT4 comparator). Trace whether variants are textures, materials, palettes, database attributes or geometry associations.
2. Reuse existing model and texture import pipelines. Separate **Source Colorway A/B**, **Custom Paint** and **Classic MR Style** as independent non-destructive project choices. Source identity, hashes, material/UV ownership and untouched regions remain explicit.
3. Render two controlled before/after Previewer comparisons, show changed resource summaries, persist a project, reopen/undo/redo/restore, build only a small optional isolated candidate if qualified. Never present RGB tinting alone as source colorway support.

### Workstream 3: generalize authentic Classic MR Style beyond one Lancer hash

1. Audit `src/master_rallye/classic_style.py`, `classic_geometry.py`, `classic_wheels.py`, `classic_materials.py`, `tools/classic_vehicle.py`, `tools/vmesh_gt3_to_dx.py`, Lancer frozen recipes, Subaru glass/wheels, Pajero GT4 culling and texture fixes, stock MR class references. Preserve the current Lancer recipe as a **regression oracle**, not the universal recipe or an output overwrite target.
2. Introduce explicit source adapters (GT3 and separate GT4), a stable semantic intermediate model and qualified per-role classification for body panels/paint, decals, wheels/tyres, rim backs, glass/damage groups, lamps/brake ON-OFF, crew, collision/shadow, environment/reflection and UV/texture ownership. A source-only label never proves an opaque/alpha native material role.
3. Implement a **deterministic, recipe-compiled Classic** transform: source identity + selected original colorway + class/style preset + semantic role approvals + optional user overrides → immutable Source Fidelity and reversible Classic outputs. Make generic geometry simplification, clean-livery planning, solid recessed wheel design, native MR rubber/glass material mapping, source-color preservation and budget reporting reusable across classes. Each destructive operation must be source-scoped, explicable and individually reversible.
4. Preserve original mirrored wheel orientations, source hub transforms, DX/UV atlas seams, alpha coverage versus reflection alpha, correct culling/winding, native glass break/damage zones, brake lamps, driver/co-driver, collisions, physics and audio. Refuse unsafe edits on ambiguous draws; keep the original Source Fidelity with a human-readable diagnostic.
5. Demonstrate at least **two distinct source archetypes**, including an actually available non-Lancer GT3 model. Frozen Subaru can be read-only regression input; do not overwrite its gameplay-accepted candidate. Use stock MR style samples as calibrated appearance references, not uncontrolled native-file copying.
6. Build an isolated A/B for one newly qualified car, unless verified gameplay constraints make an offline result the only safe output. Compare geometry/draw counts, materials, UV, tyre/glass, lights, texture budgets, wheel baseline, deterministic rebuild and fixed D3D9 views. No general compatibility claim from one or two passes.

### Workstream 4: batch diagnostic path and future expansion

- After the generalized pilot works, execute `L1` for each **unique decodable GT3 model within stated budgets**, with resumable run logs and categorized exceptions. Plan `L2` D3D9 captures for a stratified group representing complex glass, backface culling, many colorways, unusual wheels, decals and high-detail geometry. In-game D3D8 testing is a smaller owner-selected group; count it independently.
- Every reproduced failure should add a small synthetic/metadata-only regression fixture and classify its cause before any vehicle-specific workaround. Build a prioritized issue list for the GT source adapters, style compiler and later Blender Bridge / Model Doctor. The first pass may deliver L0 coverage and representative L1 and L2; do not report full L1 coverage until it actually completes.
- Future MR Heritage batches are separate: rev127 Demo 8.4.1 and fleet expansion beyond confirmed 30 slots require independent native qualification. Original MR models should not be forced through GT Classic automatically.

## C. Deliverable and safety gates

- Working GT Garage Lab read-only corpus scanner with resumable manifest and explicit supported formats; true original source-colorway selection on one confirmed car; generalized semantic Classic Style on multiple model archetypes; reproducible preview/compare; source-only issue matrix, regression tests, GUI/workshop integration where qualified, and Help updates.
- Source-only and changed-files archives; report actual synthetic, Windows Previewer and owner game evidence independently. Provide SHA-pinned conversion recipes, package/resource diff reports and no false all-GT3-playable claims.
- Preserve Gameplay Camera2.0, frontend framing, Results names, Heritage Isuzu, Lancer/Subaru/Pajero baselines, qualified native glass, shadows, brakes, audio/presets, painting, Physics Studio, generated art, Race HUD marker and stock copy-on-write.
- Treat user local GT/MR game assets, model variants, textures and audio as **private**; no bundling in source-only archives. Never alter original MRallye.exe, original clean `Data.sma`, other archives, existing d3d8.dll, or Randomizer. Limit owner-authorized local commits to tested work; no push/merge/publication without separate request.
- **Stop for review after the qualified generalization/colorway/corpus-foundation milestone** rather than simultaneously starting Blender Bridge, Fleet Builder, a broad GT4 port, or mass Demo imports. GT3 catalog-wide L1/L2 work remains the next bounded phase if not completed safely during the initial milestone.


---

# Master Plan v6.3 Addendum — Cross-Game Rally & Off-Road Heritage (2026-10-28)

## A. Product direction: curated rally-raid history, not wholesale GT imports

**Strategic change approved for planning:** Master Rallye Vehicle SDK / Rally Workshop should evolve from a primarily Gran Turismo donor pipeline into a **game-agnostic, user-owned-source vehicle restoration workshop** centered on Master Rallye's original identity: turn-of-the-millennium off-road, rally-raid, expedition SUVs, trucks, buggies and historic rally/rallycross/hill-climb specials. GT3/GT4 retain their importance as the first, proven donor adapter and a compatibility stress-test corpus, **not** a commitment to import every available GT vehicle into the game.

The central experience remains the original 2001 Master Rallye. Curate historical/editorial vehicle collections rather than silently treating different model years as original MR content. Classify vehicles as: **original MR heritage / historically plausible period addition / later-era bonus / experimental non-four-wheel**. A car's existence in a community vehicle list does not prove the user owns its source file, that the 3D asset can be extracted, that it matches a pre-release MR asset, or that it can safely drive in MR.

**Maintain active Codex work:** complete the current bounded GT Garage Lab generalization/source-colorway/corpus work under v6.2 first, since its common semantic model, preview, classifier, validation and non-destructive Classic conversion will be reused by every donor format. Do not interrupt an active validated phase to begin unrelated reverse engineering.

## B. Donor game candidates — owner-curated research queue

| Donor | High-value candidates / role | Priority and technical qualification |
|---|---|---|
| **Paris-Dakar Rally (2001)** | Pajero V60 and Pajero Evolution V20 (as identified by the owner), Nissan Patrol, Mega Désert, Toyota Hilux, Mitsubishi L-200, 2000 Schlesser Mégane, Ford Ranger, Jeep Wrangler and buggies | **P0 — forensic pilot.** Compare 3D geometry, UV, texture paint, proportions and materials of both Pajeros to MR's pre-release screenshot/icon evidence; never claim identical original meshes until established. PC source preferred when actually available. First isolated non-GT donor candidate after assessment. |
| **4x4 Evo 1/2** | Diverse 2000–2002 civilian U.S./Japanese SUVs/pickups including Toyota, Nissan, Mitsubishi, Dodge, Chevrolet, Ford and Jeep | **P1 — breadth + configurable civilian/rally styling.** Many trims and variants; deduplicate actual model/mesh hashes, not catalog names. Create user-selectable stock civil, period rally and custom paint profiles, without inventing original game liveries. |
| **Screamer 4x4** | Mercedes-Benz Unimog, Toyota Hilux/Land Cruiser, Land-Rover Defender, Jeep, Pajero, Rába truck | **P1 — structurally different class pilot.** Unimog is a valuable heavy-utility contrast to original MR KamAZ. Validate physical dimensions, hubs, tyre radii, gearing and center of mass; source licensing and extraction as normal. |
| **Colin McRae Rally 04/2005 (and 3 where unique)** | Ford Transit Rally Van, Citroën 2CV, Land-Rover Freelander, VW New Beetle RSi, Mitsubishi Pajero, Nissan Pickup, MG ZR, Fiat Punto/Puma S1600, Rally 037 | **P1/P2 — period rally culture.** Verify actual playable model vs decorative traffic, versions and source format; first source audit before committing to candidate. Potential MR design lineage comparisons are hypotheses until supported by source evidence. |
| **Dakar 2 (2003)** | Tatra 815, MAN F90, Hino Ranger, Nissan Pickup D22, alternate Dakar SUVs and trucks | **P2 — console format research, not early importer dependency.** Inspect source/platform build boundaries and tool availability first; PS2/GameCube/Xbox archive, geometry and texture encodings may differ. Focus on trucks/pickup unique to this donor. |
| **DiRT (2007)** | Race Touareg, Desert Warrior, Pajero Evolution, BMW X3 CC, Fenomenon Stratos, Pikes Peak specials, CORR buggies, Kenworth/Freightliner, KamAZ and others | **P2 — high-value later-era premium collection.** Its later-generation assets require validated simplification of poly counts, LOD, shader materials, normal maps and texture sizes for MR's 2001 renderer. Not all vehicles are period-authentic; label accordingly. |
| **DiRT 2 (2009)** | 1993 Pajero T3, optionally Hummer H3 and distinctive off-road vehicles | **P3 — selective bonus**, not blanket roster import. |

IGCD/community catalogs and period game announcements are **leads** only; source-qualified local asset IDs and direct model review decide implementation. Some named variants may require correction after actual file examination. Preserve edition/platform provenance.

## C. Architecture: Cross-Game Source Adapters

Keep **GT Garage Lab** as a source-specific research and validation module. Build a higher-level, donor-agnostic **Source Garage** architecture on top of common Vehicle SDK Core:

`User-local source game/build → read-only source adapter → normalized semantic vehicle scene (geometry, materials, UV, hierarchy, wheels, crew, glass, lamps, original paint variants, physics/audio provenance) → Source Fidelity / optional Classic MR Style / custom authoring → validation → isolated MR candidate`.

Each adapter must declare exact supported editions, executable/archive/source hashes where necessary, decompression/mesh/texture capabilities, missing components and uncertainty. Never globally misinterpret a source-specific alpha channel or culling mode. Unknowns remain explicit. Preserve original donor geometry and materials in the project; generate separate native-compatible derivatives. Private licensed game content remains user-local and **must not** be distributed with the SDK or source-only review bundles. Any public release needs an independent rights review.

**Cross-game feature adaptation** uses existing studio layers: Physics donor/authoring from qualified MR sources, qualified gameplay camera, wheel fitment, crew, native glass damage, lamps/brake ON, shadow auto-fit, named Results drivers, frontend framing, icon generation, Race HUD color, Audio Studio, user colorways. Missing source features must be declared and added through reversible overlays only when MR adapter support is established.

**Fleet/catalog distinction:** catalog can list many locally discovered candidates, but the active build remains restricted to the qualified roster capacity (currently 30 in the known configuration). Do not invent stable 31+ capacity. Preserve alternative Isuzu/Pajero CarID29 build variants.

## D. First staged cross-game milestone after GT generalized foundation

**Step 1 — Source Archive & Model-Lineage Forensics:** select **Paris-Dakar Rally (2001)** as first new donor. Verify an owner-local source build, extract a read-only vehicle/texture inventory, identify both reported Pajero variants. Compare against original MR pre-release icon/screenshot evidence using fixed-angle outlines, geometric features, UV seams, wheel locations, texture patterns and hashes if file formats permit. Classify `visually similar`, `probable related asset`, or `direct asset match` with stated evidence, not enthusiasm.

**Step 2 — First PC donor adapter:** deliver minimum independently testable Paris-Dakar source adapter and local preview of one qualified vehicle. If Pajero files cannot be extracted or recognized, report blockers and choose another confirmed car from that owned source (not a fabricated placeholder). Add synthetic regression fixtures without private meshes.

**Step 3 — one isolated MR candidate:** import one qualified unique donor candidate as an alternative addon, with wheel/crew/physics/audio/glass/light/shadow/camera/identity/Results/menus checked using the established pipelines, and owner D3D8 validation distinctly marked. Source Fidelity first; Classic as a separate opt-in conversion after semantics are verified.

**Step 4 — donor matrix:** count actual local, supported, converted and D3D8-verified assets separately. Choose the next adapter based on highest benefit-to-cost ratio: 4x4 Evo 1/2 (civil SUVs), Screamer 4x4 (Unimog/heavy vehicle), or Colin McRae 04/2005 (period rally oddities). Defer Dakar 2 console reverse engineering and high-fidelity DiRT until PC adapters are proven.

## E. Vehicles on two wheels — separate engine feasibility study

Motorcycles and quads from Dakar titles are compelling, but MR's already qualified vehicle/physics systems are designed around four-wheel cars. A visually convincing motorcycle model in the existing car slot would **not** establish two-wheel stability, steering/leaning, contact dynamics, collisions, animations or appropriate AI. Do not promise a bike class, force two invisible wheels, or put motorcycle implementation into the initial donor-import milestone. Create a separate feasibility note only after the four-wheel cross-game importer is proven.

## F. Regression, provenance and workflow rules

- Preserve the previous **v6.2 GT universalization milestone** unchanged until independently reviewed; its output is infrastructure for cross-game compatibility, not a product commitment to mass GT installs.
- Keep the original game, clean Data.sma, d3d8.dll and all accepted standalone addon projects unchanged; isolated builds, deterministic manifests, compare/report/restore as before.
- Document owner-provided vehicles and external game rosters as research candidates; never convert community screenshots alone into claims of file-level compatibility or material equivalence.
- Main Codex receives this new scope **after** current work is reviewed. Proposed next milestone name: **Rally Archive — Paris-Dakar Source Pilot**. No automatic implementation, Git push, release, copyrighted asset packaging or parallel unrelated reverse engineering.

---

# v6.4 Addendum — Cross-Game Source Recon / Donor Tool Audit (2026-10-28)

## Decision and sequencing

The owner proposes a single **private, user-managed source collection** for the potential donor games, followed by an **audit of existing community tools and actual supported game revisions**. Adopt this as the next bounded milestone **after the currently active GT Garage Lab work**, not an immediate mass importer. Keep the new collection outside `master-rallye-re-vehicles` and all distributable archives. Link to user-owned installations or maintain immutable local working copies; neither sources nor their extracted proprietary assets enter Git.

### Sample private layout (paths illustrative, not assumed to exist)

```text
D:\RallyWorkshopSources\
  sources\
    4x4-evolution-pc\
    4x4-evolution-2-pc\
    screamer-4x4-pc\
    paris-dakar-rally-2001-pc\
    colin-mcrae-rally-3-pc\
    colin-mcrae-rally-04-pc\
    colin-mcrae-rally-2005-pc\
    dirt-2007-pc\
    dirt-2-2009-pc\
    dakar-2-2003-ps2-or-gamecube\
  manifests\
  extracted-private\
  previews-private\
  researched-tools\
  reports\
```

Game entries without an owner-local source are `MISSING INPUT`, never simulated. Console editions require platform-specific inventories. Use absolute configured source paths rather than assuming a drive letter. Use read-only source access, hash inventories, detect revisions, bound scan/extract size, preserve source provenance, and never execute newly downloaded legacy tools without independent provenance/security review.

## Preliminary outside-tool survey: leads, not verified on owner source files

| Source family | Tool/evidence found | Remaining work | Starting readiness |
|---|---|---|---|
| 4x4 Evolution 1/2 (PC) | 4x4 Evolution Revival Project documents POD utilities, Blender SMF importer/exporter, Z3D importer, RAW texture converters | Validate specific game edition, genuine car mesh, transforms, color variants, texture/alpha, wheel hubs, LOD and hierarchy | **Best established community workflow** |
| Screamer 4x4 (PC) | ResHax identifies `.cod` archive, `.dat` separate vehicle geometry, `.tex/.32/.32a` textures; QuickBMS and Noesis scripts/plugins are linked | Verify scripts work for owner's edition; preserve normals, material ownership, wheel transforms and texture binding | **Strong exploratory candidate** |
| Colin McRae Rally 3 / 2005 (PC) | RallyGamer documents iRipper for `.BIG` packages | Package extraction is not proof of usable mesh exporter; identify actual geometry and texture formats | **Archive path exists** |
| Colin McRae Rally 04 (PC) | Xentax historical jRipper support listing and RallyGamer community information | Confirm reliable tool availability, car mesh extraction and format version; do not assume iRipper works identically | **Needs version audit** |
| Paris-Dakar Rally (2001 PC) | Vehicle lists confirm interest, but no sufficiently verified model-specific extractor found in this survey | Identify actual packaging, mesh/textures first; compare both Pajeros to historical MR evidence only once decoded | **Priority forensic target; format unknown** |
| Dakar 2 (PS2/GameCube) | Platform-level disc extraction and historical GameCube SBB discussion exist | Game-specific car model decoder not established; GameCube `GBA.SBB` is **not evidence of a car archive** | **Research-heavy** |
| DiRT (2007 PC) | Original game uses early Neon technology; later EGO/PSSG tools are not proof of support for 2007 assets | Verify 2007 file signatures and one material+mesh open/export on the actual source before committing | **High-value, high-risk** |
| DiRT 2 (2009 PC) | Later EGO-era PSSG tools and community documents offer plausible starting points | Validate exact local build and complete mesh+material extraction; avoid extrapolating from DiRT 3 or Rally | **Provisional** |

External research pointers for the investigator (recheck availability/security and actual supported versions):
- 4x4 Evolution Revival Project: https://www.4x4evolution.net/doku.php?id=modding_tools
- Screamer research and links: https://reshax.com/topic/633-screamer-4x4/
- Colin McRae 2005 tools: https://www.rallygamer.com/downloads/cmr2005/tools/tools-and-hints
- Colin McRae 3 tools: https://www.rallygamer.com/downloads/cmr3/tools/tools-and-hints
- Later EGO/PSSG context: https://ego.fandom.com/wiki/Utilities
- 2007 Neon background: https://mcvuk.com/development-news/special-report-neon-a-codemasters-and-sonys-illuminating-next-gen-engine/

## Source Intake report contract

Produce `DONOR_FORMAT_MATRIX.md`, `DONOR_TOOL_AUDIT.md`, `DONOR_CORPUS_MANIFEST.json` (private path redaction for publishable reports), and `DONOR_FIRST_PILOT_DECISION.md` with machine-readable per-file scan data kept private. Required columns per exact local build:

- `source_game`, `platform`, `edition_region_build`, `source_hash`, `available/missing`;
- `container_format`, `mesh_format`, `texture_format`, `audio_format`, `texture_variants`, `vehicle_catalog_mapping`;
- `candidate_tool`, provenance, license, executable/source-only and security checks;
- `open/read`, `extract`, `view`, `export`, `retain_materials`, `retain_uv`, `retain_wheels`, `retain_lod`, `repeatability` with evidence status per feature;
- `gaps`, needed native reverse engineering, estimated adaptation complexity, first compelling candidate;
- `L0 inventory`, `L1 verified one vehicle`, `L2 preview` and *separate* owner D3D8 gameplay testing.

Explicitly distinguish community claims and generic tools from successfully tested support of these particular user-owned game revisions. A successful archive unpack is not a successful 3D/UV/material conversion.

## Pilot selection and limits

First perform metadata/format detection for every **available** source; use targeted reference-vehicle extraction on multiple donor families as the realistic gate. Selection criterion: **verified source ownership and extraction, completeness (mesh+textures+wheels+materials), perceived value to MR, complexity**, in that order. Prioritize **Paris-Dakar** as the historical/forensic target, but use **4x4 Evo or Screamer** as an alternative first end-to-end proof if their tooling is demonstrably ready sooner. Do not decide from catalog names alone. Keep DiRT as a separate challenging asset-upgrade test; first prove original Neon geometry/material reading before authoring Classic simplification. Keep motorcycles outside the initial scope.

The next milestone is a *source/tool audit plus one or more read-only extraction smoke tests*, **not** mass conversion, installation, runtime hooking, or an unbounded reverse-engineering commitment. No undocumented merge or Git push. After review select a bounded donor adapter pilot.


---

# v6.5 Addendum — Source Garage: Four Additional Game Families (2026-10-28)

**Nature of change:** expansion of the *future* read-only source/tool audit only. This is NOT a change of the currently active GT Garage Lab milestone, NOT an order to import these vehicles immediately, and NOT a change to the previously selected Paris-Dakar historical research objective. The owner particularly values Michelin Rally Masters as a childhood game: move it into an **early, elevated research lane**, but not above Paris-Dakar or ahead of an already active task. Previous v6.4 plan and safety/provenance/approval constraints remain in force.

## New donor candidates and owner-supplied highlights

| New donor / exact version to verify | Owner-selected vehicle interests | Preliminary external tool evidence (NOT tested on owner files) | Priority within Source Garage |
|---|---|---|---|
| **Rally Championship Xtreme** (2001 PC; investigate relationship/build labels with *Rally Championship 2002*) | 1998 Nissan Micra Kit Car, 1997 Honda Civic | PCGamingWiki documents installed `Data/` directory and settings, but no confirmed original-car 3D importer found in this survey. These cars appear in IGCD's *Rally Championship 2002 (2001)* list; edition/alias must be verified from owner source. | Medium, early file-signature audit |
| **Michelin Rally Masters: Race of Champions** (2000 PC; PlayStation is a separate format) | **Toyota RAV4** (owner suggests XA10, generation to be confirmed), **1997 Renault Mégane Maxi**; compare *visual style* to the MR Schlesser, never assume shared source geometry | IGCD confirms both cars. Contemporary setup discussions confirm a local `Rally/Data/RallyMasters.DTA` file; its proprietary contents and whether it carries usable vehicle meshes are **not yet proven**. No independently verified complete car extractor identified. | **Raised: early priority forensic lane immediately behind Paris-Dakar, alongside easier tool-backed probes** |
| **Sega Rally Revo / Sega Rally (2007)** (PC prioritized; PS3/360/PSP separate) | 1986 Lancia ECV, Peugeot 206 RCC, 1988 Peugeot 405 Turbo 16 Rally Raid, MINI Cooper S, 2005 Mitsubishi Concept-X, Ford RS200E, RUF Rt 12 | ZenHAX records `sega_rally_2007.bms` for SBF, reported successful texture extraction, and **incomplete car geometry capture** in a 2016 experiment. Steam PC depots list vehicle model/texture `.sbf` resources. Extracting SBF does NOT establish complete car geometry import. | Medium-high future exceptional-cars lane |
| **Sega Rally 2 Championship** (PC / Dreamcast / arcade formats must be separated) | Historical rally lineup; identify edition-specific standout cars during audit | `Spreit/SR2Tools` repository documents Python modding tools for Sega Rally 2. Public reversing index lists SAR extraction, texture tools and `sr2mdl`. Precise supported platform and vehicle completeness still require testing. | Medium; tool-verification pilot |
| **V-Rally 2** (1999 PC and PlayStation first; Dreamcast independent) | 1997 Seat Ibiza Kit Car Evo 2, Alpine A110, Fiat 131 Abarth, Renault 8 Gordini, plus Rally favorites | **Strong verified community-research lead:** `VR2 Asset Explorer 0.6.11` (Aug 2026) documents PC/PSX PAK, car inventory, textures, geometry and read-only export. The author explicitly lists remaining unknowns and platform limits. | **Elevated technical quick-win candidate** |
| **V-Rally 3** (2002 PC / console, version-qualified) | 2001 Seat Córdoba WRC and distinctive 1600/Kit Cars | IGCD identifies Córdoba and other playables. No source-qualified universal car extractor verified in this survey; do not assume V-Rally 2 PAK tool supports V-Rally 3. | Medium, independent format audit |

## Cross-game identification and provenance cautions

- *Rally Championship Xtreme* and *Rally Championship 2002* may denote region/build naming around the 2001 Warthog/Actualize release. Match executable/product metadata and actual vehicle folders before treating them as one proven binary format; the IGCD Honda Civic/Micra entries currently come from the *Rally Championship 2002 (2001)* listing.
- The owner's Michelin RAV4 XA10 generation and the MR Schlesser/Mégane Maxi visual comparison are **research hypotheses**. The donor game's nameplate and in-game model/texture provenance must be recorded before claims of identity or reuse.
- V-Rally 2 and V-Rally 3 are different source adapters until an actual matching format is demonstrated; differences among PC/PSX/Dreamcast/Xbox/PS2/GameCube builds matter.
- For Sega Rally Revo, **SBF archive extraction/texture extraction is not full car geometry extraction**. Extract mesh+UV+materials+wheels and verify model topology before declaring it 'ready to import'. Treat Sega Rally 2 separately from Revo and Sega Rally 3.
- An IGCD catalog entry is evidence for a *candidate game vehicle*, not proof that its unique playable model, all colorways, crew or high-res geometry exist in the owner's edition. Inventory the original user-local files.
- Cross-game visual similarities never by themselves establish common 3D source assets. Track source game, edition, exact file hashes, model hierarchy, materials and variants.

## Add directories to the private configurable source intake

Under the existing `sources/` collection, include (only if the owner has those legitimate local installations):

```text
rally-championship-xtreme-pc/
michelin-rally-masters-pc/
sega-rally-revo-2007-pc/
sega-rally-2-pc-or-dreamcast/
v-rally-2-pc-or-psx/
v-rally-3-pc-or-console/
```

No installation present => `MISSING INPUT`. No automatic downloads of copyrighted game assets or execution of untrusted third-party binaries. The initial audit can use read-only header inspection and well-reviewed open-source scripts.

## Updated audit order (priority is not implementation scheduling)

1. **Paris-Dakar 2001** remains first *historical* investigation because of the missing/pre-release Pajero connection. No change to GT Garage Lab in progress.
2. **Michelin Rally Masters** moves to an **early parallel forensic slot** directly behind Paris-Dakar for its owner significance. Attempt DTA signature/TOC inventory, vehicle name mapping, textures and one Mégane Maxi/RAV4 model before proposing a decoder; unknowns remain reportable.
3. **V-Rally 2**, **4x4 Evo 1/2**, **Screamer 4x4** are top candidates for the *first tool-backed end-to-end reconstruction* depending on actual local source and successful geometry+texture+wheel tests; do not equate emotional rank with format readiness.
4. **Sega Rally Revo** and **Sega Rally 2** each receive an archive/file-format smoke test and separate platform-qualified mesh study. Revo's 2007 complexity does not disqualify historic unicorns, but the case must be resource-budgeted.
5. **Rally Championship Xtreme** and **V-Rally 3** receive first-pass signatures and a tool search; escalate only with actual compatible extraction evidence. Existing Colin McRae / Dakar 2 / DiRT tracks remain preserved unchanged.

Additional acceptance fields in `DONOR_FORMAT_MATRIX.md`: exact title alias, build region, platform, community-tool source/commit/hash/license, container recognition, source-to-car mapping, geometry+UV+materials+textures+wheel pivots, car color variants, preservation of game-owned resources, L0/L1/L2 evidence, no-asset-publication readiness. Add `personal_priority` separately from `technical_readiness`, never combine them into a misleading single 'compatibility' score.

## Preliminary research references (verify exact releases and availability)

- Michelin IGCD vehicle list (RAV4 and 1997 Mégane Maxi): https://www.igcd.net/game.php?id=10000157
- Michelin file existence/compatibility discussion (`RallyMasters.DTA`): https://sourceforge.net/p/dxwnd/discussion/general/thread/e0af89e66d/
- Rally Championship Xtreme PC data layout: https://www.pcgamingwiki.com/wiki/Rally_Championship_Xtreme
- Rally Championship 2002 IGCD vehicle list: https://www.igcd.net/game.php?id=10000059
- Sega Rally Revo IGCD: https://www.igcd.net/game.php?id=10000103
- Sega Rally Revo SBF research / BMS: https://zenhax.com/viewtopic.php@t=1862.html
- Sega Rally Revo Steam PC file list: https://steamdb.info/depot/4792/
- Sega Rally 2 SR2Tools: https://github.com/Spreit/SR2Tools
- V-Rally 2 2026 VR2 Asset Explorer reference: https://vannacut.com/2026/08/12/v-rally-2-pc-psx-reverse-engineering-pak-exporter/
- V-Rally 2 IGCD: https://www.igcd.net/game.php?id=10000008
- V-Rally 3 IGCD: https://www.igcd.net/game.php?id=403646

**Next action:** when the main Codex finishes its active GT Garage Lab milestone, give it this *scope extension* alongside the existing v6.4 Source Garage audit instructions. Research and choose; do not automatically implement/import all candidates, expand the native roster, or distribute proprietary assets. Follow established local-commit/no-push rules.


---

# Repository implementation checkpoints retained from f2714b1

The following two repository-only checkpoints are retained verbatim from the
baseline Git blob, with its LF bytes. The complete shared history appears once
in the attached v6.7 plan above. These checkpoints record earlier evidence and
review gates; the current owner request authorizes the bounded Evo2 neutral-scene
pilot. Historical task text is not independent authorization for other work.
See [MASTER_PLAN_RECONCILIATION.md](MASTER_PLAN_RECONCILIATION.md) for exact
attachment, shared-history and section-preservation checks. Paris-Dakar and
Michelin personal/historical priorities remain in the retained roadmap.

## Repository Source Garage audit checkpoint (historical status)

# Master Plan v6.6 — Source Garage audit checkpoint

28 October2026. Actual clean baseline `b9a24f7` / `research/vehicles` matches the
attached handoff. Attached v6.6 was reconciled with the actual GT Garage and
automatic-import results; historical plans below are preserved.

Source Garage cross-game format/tool audit is delivered for review:16 actual
source roots,38762 hashed files, five representative PC structural probes,
historical Paris-Dakar/Michelin probes, separate DiRT2007/DiRT2 dictionaries and
one Revo archive/texture test. See [SOURCE_GARAGE_RESULTS.md](SOURCE_GARAGE_RESULTS.md)
and its matrix/tool/corpus/interface links for exact qualification boundaries.
50 focused tests pass; full synthetic/CPU suite1017 tests/2 existing skips.

Proposed first new adapter: Evo2 Toyota4Runner SR5 Sport Package2WD, subject to
review. Paris-Dakar Pajero provenance and Michelin RAV4/Megane remain independent
high-interest research tracks. No first importer has started. Universal Vehicle
Scene is a proposal; current GT compiler/Classic gates are not universal support.
**Stop for audit review before adapter implementation.** Existing accepted cars,
alternative CarID29 rosters,30-entry limit and original assets remain preserved.

---


---

## Repository GT Garage implementation checkpoint (historical status)

## Implementation status — GT Garage Lab, 28 October 2026

Read-only corpus coverage, exact model/color joins, bounded source adapters and
shared automatic profile integration are implemented. GUI/CLI original-color
versions preserve independent manual histories. The approved UV prerequisite
rejects face images on no-UV wheel texgen packets, including old profiles.
Clio is the owner-approved GT3 pilot; original silver/blue and semantic Classic
wheel/rubber/glass comparisons exist. Source Fidelity has an isolated30-slot
owner-test candidate. The corrected Classic report c38d712c was explicitly approved and its isolated
candidate built. This is not gameplay acceptance. Representative CLUT limitations, unknown native GT3
rig/lighting and donor fitting remain explicit. No bulk installs or new native
capacity claims. See GT_GARAGE_RESULTS.md, SYNCHRONIZATION-2026-10-28.md and the
current regression matrix. Preserve v1 Lancer, automatic-import work and all
accepted cars; no Blender/Fleet phase begins here.


---

## Implementation status — Evo2 source scene pilot, 28 October 2026

The owner accepted Source Garage phase 1 and authorized one bounded adapter:
4x4 Evolution 2 Toyota 4Runner SR5 Sport Package 2WD (2000), original catalog
TRUCK/T4RSR52.TRK. The historical audit stop gate above is fulfilled for this
pilot only; all earlier plans and repository checkpoints remain retained.

Implemented: hash-qualified read-only POD2/SMF/TRK/TIFF reconstruction, minimal
Universal Vehicle Scene v1, original body and all six L/R wheel detail variants,
four literal source placement records, exact resource provenance and complete
raw TIFF channel/palette preservation. Source values, derived transforms and
preview interpretations remain distinct. Workshop Source Garage provides real
assembled textured D3D9 inspection and six fixed views without MR authoring.

40 new focused tests PASS; complete Windows synthetic/CPU suite 1057 tests,
2 existing fixture skips. Native build, existing viewer GPU smoke and actual
Tk Inspect/Create/Capture/Reopen PASS. Two independent 59-file scene outputs
are byte-identical. Six original MR files plus 2426 accepted-project files
retain exact hashes; donor POD and executable are unchanged.

L0 PASS; L1 WARN; L2 WARN with neutral assembly preview inspected. Unspecified
TIFF channels, original alpha/reflection/lighting, dynamic auxiliary passes and
settled suspension remain unresolved. Static hub wheelbase 8.88ft differs from
catalog 8.78ft; preserve both. No source-game renderer or MR gameplay parity is
claimed. See EVO2_SOURCE_ADAPTER_RESULTS.md, EVO2_SOURCE_SEMANTICS.md and
UNIVERSAL_VEHICLE_SCENE_V1.md for exact boundaries and private evidence paths.

The complete v6.7 attachment is retained byte-for-byte as this plan's prefix
and in docs/sdk/retained/. Full v6.3-v6.5 history and all repository-only blocks
are preserved; see MASTER_PLAN_RECONCILIATION.md. Attached historical directions
do not expand the current owner's explicit scope.

Paris-Dakar Pajero provenance and Michelin RAV4/Megane remain high priorities,
with their identity/inner-payload uncertainties unchanged. Existing accepted
Lancer, Subaru, Pajero, Trooper/Heritage and Clio projects, isolated CarID29
alternatives and the 30-entry limit remain preserved. No push or publication.
**Stop for review after source scene and preview; no MR conversion, CarID,
compiler, bulk import, Blender Bridge or additional adapter begins here.**


---

# Master Plan v6.8 — Evo2 4Runner review and first MR-native Cross-Game pilot

**28 October 2026.** This checkpoint is appended to the complete current repository
Master Plan (including the exact retained v6.7 history, repository-only
checkpoints and accepted Evo2 source-scene implementation). All prior research
and approvals remain preserved. This is a planning decision following the owner's
neutral-scene screenshot and independent source-only ZIP review, not a claim of
new gameplay or new implemented features.

## Reviewed implementation and evidence boundaries

- Reviewed user-provided `changed-files.zip`: 28 members, ZIP CRC PASS;
  `SOURCE_REVIEW_MANIFEST.json` lists **27/27** matching SHA256 files;
  **14/14** Python AST files parse successfully. Manifest revision
  `c5bd91fc5dcb81e6e10c44ebbd9c0a6073b129ed`, baseline
  `f2714b1d50c5af18bdc4081010317fe3e4632922`; no `.git` history in
  the changed-only archive, so commit existence is manifest-reported.
- Independently ran **30/30 synthetic tests** for POD2/SMF/TRK/TIFF source
  parsing and Universal Vehicle Scene validation/persistence. Ten additional
  preview tests could not be imported from this changed-only archive because
  `master_rallye.workshop.branding` belongs to the unchanged codebase and was
  omitted. This is not evidence of a product regression and does not qualify
  those ten tests as passed. Developer's full Windows run is **1,057 tests,
  two skips** (reported only, not independently reproduced), with Windows
  D3D9/Tk native captures and preserved asset checks in private evidence.
- Qualified exact source: 4x4 Evolution 2 Toyota 4Runner SR5 Sport Package
  2WD 2000, `TRUCK/T4RSR52.TRK`, body `MODELS/4RUNNERSR5.SMF`;
  33 body objects, 43 total mesh records, 38 nodes, 2,773 total triangles,
  14 textures and 6 original L/R wheel-detail resources. Original four TRK
  wheel positions retained, normalised from feet with a documented axis
  reflection. Original stock BODY mask selects 11 components at detail 2;
  light/axle auxiliary passes remain separate and unresolved.
- Critical source-faithfulness caveats: static high-detail wheel pose is not
  verified gravity-settled running-game suspension. Source TRK catalog
  wheelbase 8.78 ft differs from 8.88 ft of literal hub positions, and both
  are preserved. `ART/4RunnerSR5.TIF` contains an unspecified extra channel;
  neutral opaque coverage is a preview choice, not recovered source alpha.
  Bump shading, native source reflections, nine color transformations,
  animations/dynamic lighting, and settled suspension remain unqualified.
  No original Evo2 game-runtime visual comparison or MR gameplay test.
- Source adapter **L0 PASS, L1 WARN, L2 WARN** (assembled neutral D3D9 model).
  Source Fidelity baseline and immutable private sidecars are preserved. No
  MR native car or roster entry has yet been created for this 4Runner.
- Master Plan documentation restoration is described in
  `MASTER_PLAN_RECONCILIATION.md`, with retained v6.7 attachment byte-for-byte.

## Next approved planning target — Cross-Game 4Runner: first playable MR pilot

The next bounded deliverable, upon owner's forwarding of a new Codex prompt,
should **reuse the Universal Vehicle Scene v1 as an immutable source** and
implement a reusable, qualified bridge into the existing MR addon build
pipeline. This should not be a one-off Evo2-to-DX script disguised as a
universal importer. The bridge must preserve mesh IDs, origin and transforms,
UV/material/texture bindings, unit and handedness conversion, LOD/equipment
semantics, source color provenance and every unresolved source field.

1. Establish stock-MR class/scale/style references and compare against the
   neutral source body, static hub centers, wheels, rider/crew envelope,
   collision and rendering constraints. Explicitly **separate source static
   ride pose** from proposed MR physics suspension; no blind 1.05 multiplier,
   global body translation or automatic hub adjustment. Provide measured
   L1/L2 comparisons and adjustable, reversible authoring decisions.
2. Build a qualified **Source Fidelity** MR vehicle using the user-owned
   Evo2 source scene. Use correct body/complete/wheel resource partitioning,
   texture bindings, culling/winding, UVs, opaque tyres and safe fallback
   transparency/reflection. Unknown bump/extra TIFF channels must not be
   interpreted as alpha without evidence. Reuse existing MR material,
   geometry, shadow, glass/damage and brake-light authoring services where
   the donor model and native contracts permit.
3. For glass, headlamps, brake-lamp ON/OFF, crew, collision and damage,
   distinguish actual source-supported assets from manually authored MR
   enhancements. Do not claim original Evo2 runtime semantic fidelity when
   creating new MR features. Keep unsupported roles explicit and prevent
   unsafe auto assignment. Preserve exact source resource sidecars.
4. Choose a **verified MR donor physics family** suited to a four-wheel SUV,
   including wheelbase/track/radius/chassis baseline; create independent
   copy-on-write physics, camera, sound and frontend profiles. Vehicle identity
   and Driver/Results name, vehicle art, Race HUD marker, shadow and frontend
   auto-framing should use the existing Studio modules.
5. Use a **separate alternative 30-entry roster**, allocating a qualified
   addon CarID only after conflict analysis. Existing CarID29 alternatives
   include Pajero, Demo Trooper and Clio; these must never be installed
   simultaneously into one slot or deleted. Do not claim 31+ roster capacity.
6. Produce deterministic isolated **Validate → Build → Restore** candidates
   with exact differences, original/target model A/B D3D9 captures, source
   hashes, full available Windows regression and a short owner D3D8 gameplay
   checklist for menu, spawn, wheel stance, suspension, textures, alpha,
   glass damage, brake lights, AI, results and race re-entry.
7. Stop after **one Source Fidelity gameplay candidate** and separate review.
   A new Classic MR Style 4Runner profile, all nine original colorways, a
   broader Evo2 fleet, Paris-Dakar/Michelin adapters, Blender Bridge and
   additional CarID capacity are separate future milestones. If authentic
   stance, native integrity or camera/runtime constraints cannot be solved
   safely, deliver a well-evidenced partial implementation and explicit
   blockers rather than faking a passed game build.

## User visual review and additional follow-ups

The user's neutral 4Runner image has a credible textured body, roof rack,
original wheel equipment and an unusually high body/wheel gap. This gap is
an **inspection question**, not proof of a transform bug: the current viewer
shows source static, non-settled pose. The glass looks near-black and is
currently a deliberately neutral opaque interpretation. Compare source-game
screenshots (when available) and actual MR materials before tuning.

Upon successful 4Runner native pilot, continue high-priority **Paris-Dakar 2001
PajeroRED/PajeroSilver** archive/geometry research and **Michelin Rally Masters
Toyota RAV4 `Car25A.PDO` / Renault Mégane `Car06A.PDO`** inner-payload
reconstruction; keep cross-game Universal Vehicle Scene shared. Build the
broader donor compatibility matrix and eventually Blender Bridge, Model Doctor
and Fleet Builder separately. Do not erase accepted original vehicles,
private resources, or the clean retail Data.sma; never push/publish without
explicit permission.


---

# Master Plan v6.9 — Cross-Game 4Runner: owner gameplay findings and Native Visual Fidelity

**Checkpoint:** 28 October 2026. Previous v6.8 retained exactly above. This addendum records the owner's actual in-game 4x4 Evolution 2 Toyota 4Runner test. It is a planning and screenshot review, not an independent audit of the newest native bridge source. The uploaded `changed-files.zip` contains the earlier neutral-scene adapter commit `c5bd91fc5dcb81e6e10c44ebbd9c0a6073b129ed` (the earlier L2 scene milestone), **not** the new Universal Scene → Master Rallye build changes. Do not assert this review has independently verified that later implementation.

## Owner-tested 4Runner status

- **Observed in actual Master Rallye D3D8 gameplay:** the Toyota 4Runner loads as a playable car, drives (with unusual tall-body/large-wheel handling), supports body deformation and breakable glass. Source visuals remain recognizable, and original source wheel design is present. This establishes an owner-tested first cross-game playable candidate, but is not proof of all gameplay qualification dimensions.
- **Not yet individually confirmed in this report:** exact CarID, source checksums and build isolation for the latest bridge revision, Race Results/reentry, AI, comprehensive frontend UI, audio, all glazing zones, all tail-light states, or long-duration stability. Obtain the actual latest native-bridge source-only review/changed-files manifests before attributing implementation details or claiming full regression.
- **Owner-provided evidence:** seven in-game screenshots show body-side glazing/door issues, brake lamp triangulation, reflections/mirrors, interior crew posture, tyres/suspension and an existing Master Rallye undercarriage reference. Preserve these private screenshots separately from redistributable source files if they contain proprietary assets.

## Visual defect matrix: preserve source fidelity, fix qualified MR adaptation

| ID | Observed issue | Investigation / targeted acceptance | Priority |
|---|---|---|---|
| `4R-LAMP-01` | Brake light illuminates only a sharp triangular part of the rear lamp; a separate little red triangle appears beneath the lamp on body/bumpers. | Inspect brake ON/OFF native draw ownership, triangle indices, winding, exact texture UVs, mirrored L/R faces and overlay geometry. Do not solve by an indiscriminate emissive global tint. Both rear lamps must have geometrically bounded ON coverage with zero leaks and unchanged OFF glass. | High |
| `4R-GLASS-01` | Front door/window appears to extend transparency onto the painted door/part of body; an extraneous opaque triangular original-glass fragment remains. Windshield already looks acceptable. | For each affected source part (especially GlassI/GlassE and shared body materials), inspect mesh faces and source-vs-converted UV/alpha/depth. Split and classify selected geometry along actual window boundaries rather than making entire body draws translucent. Remove duplicate or incorrectly classified overlays without harming A/B/C pillar opacity. Preserve accepted windshield behavior and native damaged-glass zones. | High |
| `4R-GLASS-02` | Rear side and rear hatch windows remain very dark/opaque by source appearance. | Offer *Source Fidelity* as immutable baseline and optional *MR-style Full Glazing* overlay where geometry and window masks qualify. Use conservative alpha, reflections and dark cabin backing; do not make an unmodelled interior an empty transparent hole. Damage behavior must be explicit per qualified native zone; do not promise independently crackable every pane. | Medium |
| `4R-REFL-01` | Body has little/no environmental reflection; side mirrors look flat, some faces look like opaque beige patches. | Reuse qualified MR material/environment-pass mechanisms, separate opaque body reflection strength from actual glass alpha. For mirrors distinguish shell, thickness and reflective inset; verify whether missing geometry, UV or material is the root cause before writing surfaces. Avoid glossy all-over appearance. | High |
| `4R-CABIN-01` | Crew hands float because the vehicle lacks a steering wheel/dashboard/interior. | Add a minimal, clearly labeled MR-style cabin presentation option with steering wheel, simple dashboard and dark backing/seat silhouettes. Validate wheel axis, crew hand pose and cockpit viewpoint. Do not fabricate original 4x4 Evo interiors or replace existing crew skeleton. | Medium |
| `4R-SUSP-01` | Wheels visually float with no rods, axle or braces visible; source model may intentionally omit the parts. | Optional **visual-only** underbody supports using original MR-class examples: appropriate rods/axle sections, not physics-bearing components. Preserve wheel hubs, track, travel and collisions; test steering/suspension motion, culling and clearance. Do not freeze a fake solid suspension mesh across dynamically moving hubs. | Medium |
| `4R-RIDE-01` | Source vehicle has high stance/large tyres and distinctive handling. | Treat as a separate optional Physics Studio and qualified ride-height task only if the owner wants it. Do not alter race physics to solve a presentation defect or assume source static hub pose equals gravity-settled pose. | Deferred |

## Next bounded milestone: **4Runner Native Fidelity Polish**

**Stage A: audit and save checkpoint.** First request/read the latest cross-game native bridge source archive and source hash manifests if not available; do not treat the older neutral adapter package as the new build. Snapshot one immutable playable candidate and all source/target resource hashes. Annotate screenshot observations by physical mesh/draw/texture/UV IDs, visible lights, intact/broken glass, source fidelity vs MR adaptation. Reuse Material Studio, Texture Binding v2, Glass/Light editor, stock materials, Previewer and native rendering logic rather than hardcoded per-car surface patches.

**Stage B: high-priority correctness fixes.** 1) exact rear lamp ON/OFF polygon geometry and UV coverage with no escaped red triangles; 2) door glass transparency bounded by actual apertures with no opaque leftover fragment; 3) sensible stock-MR reflection for body plus proper mirror shell/inset. Keep the functioning windshield and all existing working damage, physics, camera, wheels and roster behavior.

**Stage C: optional coherent style completion.** Add separate reversible presets for rear glazing, minimal cabin/steering controls, and underbody suspension *visuals*. Do not misrepresent added geometry as sourced from 4x4 Evo 2. If uncertain, leave an explicit warning and expose a direct Previewer adjustment instead of a destructive auto-fix.

**Stage D: reusable architecture.** Move repeatable mechanisms into `Universal Scene → MR` semantic roles and qualified project overlays: `window_aperture`/`glass_pane`, `lamp_emissive_on/off`, `mirror_shell`/`mirror_inset`, `body_env`, `crew_controls`, `suspension_visual`. Identifiers, geometry mappings and per-surface flags must be stable and source-provenanced. Unknown parts default to unchanged and are logged.

## Required verification

1. Visual A/B in D3D9 and owner D3D8 gameplay: fixed angles showing both tail lamps OFF/ON, all window borders intact/cracked, original vs qualified reflection and mirror appearance, front crew from inside/outside, and four-wheel underside views.
2. No red illumination outside lamp apertures, no large transparent body-paint patch, no extra opaque triangular window surface, no reflection/alpha cross-contamination.
3. Preserve source-provenance 4Runner baseline and deterministic Validate/Build/Restore; explicit exact resource-difference reports. Materials do not alter physics. Cabin/suspension visual additions do not modify collision, hubs, suspension travel or camera.
4. Regression: Lancer, Subaru, Pajero, Demo Trooper, GT3 Clio, accepted source/Classic profiles, original retail passthrough; alternative CarID29 projects never simultaneously installed.
5. Native Owner Game qualification remains separate from automated and D3D9 results. Current user's observed **load/driving/body and glass damage** counts as passed; other aspects require direct checks.
6. Keep private source/game assets out of distributable ZIPs. Original `MRallye.exe`, retail `Data.sma`, game donor data, existing `d3d8.dll`, and unrelated Randomizer files remain untouched; local scoped commits only, never push/publish without permission.

## After this milestone

When native 4Runner appearance and common semantic corrections are validated, resume **Paris-Dakar Rally (2001)** research (`PajeroRED.tc`, `PajeroSilver.tc`) and **Michelin Rally Masters** (`Car25A.PDO` Toyota RAV4 and `Car06A.PDO` Renault Mégane) with the strengthened shared scene-to-MR bridge. Do not automatically launch a full new-game source decoder, another mass importer, speculative roster expansion, or Blender Bridge as part of the focused 4Runner visual-fix milestone.


---

# Master Plan v7.0 — 4Runner D3D8 visual regression review and stabilization

**Checkpoint:** 28 October 2026. This version retains the complete provided v6.9 plan above (without replacing previous project history) and reconciles the reviewed final Visual Polish source archives. The prior Codex phase did not receive v6.9 and appended its work to a retained v6.8; reconcile this exact v6.9/v7.0 history into the repository without dropping any existing unique research records. All source ZIP assets reviewed here are source-only; actual gameplay observations come from owner screenshots, not automated tests.

## Latest reviewed source package and evidence

- Full `source-review.zip`: 1,316 members (1,315 hash-manifest entries), 1,315/1,315 SHA256 PASS, CRC PASS, 584 Python syntax parses PASS.
- `changed-files.zip`: 20 members (19 hash-manifest entries), 19/19 SHA256 PASS, CRC PASS; all 19 changed entries identical to the full archive; 10 Python parses PASS.
- Exact manifest revision `450eb5d08dcc4a73d104357fd250b64e35dc92d1`, parent `77bbe6f696bf8c882637ba7dd21c2ac15ee8a534`. The source-only review cannot independently inspect the .git DAG.
- Independent Linux/Python targeted tests: 54/54 PASS across `test_semantic_aperture`, `test_source_garage_pilot`, `test_workshop_universal_source`, `test_evo2_source_adapter`, `test_source_scene_preview`, `test_visual_fitment`. Windows full 1,102 PASS / 2 skips and 42 D3D9 comparison captures are **Codex-reported** and were not reproduced in the present environment. No newly revised D3D8 candidate has automated gameplay qualification.
- Owner directly reports D3D8 improvement in side-front glass and brake ON/OFF illumination, but rejects the newly authored optional paint reflections, mirror faces, rear glass/backing, duplicate cockpit wheel and disconnected fixed frame. The existing front windshield remains accepted. New third/high brake lamp remains a requested future feature, not a verified implementation.
- The report notes a historically protected `d3d8.dll` snapshot mismatch (2,492/2,493 match). Codex says this task did not modify the DLL. Treat it as a provenance/integrity follow-up: compare an owner-approved current proxy baseline and log the hash, without overwriting or restoring it automatically.

## Diagnosed failures in actual D3D8 rendering

| Subsystem | Reviewed code mechanism | Owner observation | Stabilization decision |
|---|---|---|---|
| Correct front side panes | `fourrunner_semantics.author_apertures`, source-plane polygon intersection, outside opaque conservation | Front side windows now good | **Preserve verified fix**, avoid unrelated global alpha/mesh changes |
| Lower rear brake lights | Reviewed atlas-island geometry masks, `Body292`, native OFF/ON states | Rear brake light regions now illuminate correctly | **Preserve verified fix**; investigate separate high-center lamp as future optional qualified geometry |
| Body reflections | `fourrunner_visual_kit.apply`, `paint_reflection`: four partial UV-atlas rectangles, removes qualifying full triangles from original draw and adds env-selected geometry at intensity46/255 | Visually torn and spotty patches instead of coherent paint | **Disable by default; reject current option as production quality**. Review exact base/env pass ownership, opaque-alpha behavior and coherent complete paint surfaces, not simply raise reflection strength |
| Mirror insets | Selects three triangles53–55 per source mirror node; changes texture/environment/alpha | Mirror geometry looks flat and torn, previous appearance regresses | **Disable by default; restore original side mirror source meshes**. Investigate normals, material boundaries, thickness, winding, culling and native draw order before any new reflective treatment |
| Rear glazing | Cuts three UV polygons from Body diffuse and makes them translucent; creates opaque dark cuboid interior backing | Wrong apertures, visible black protrusion/box, missing clean rear-view glazing | **Disable rear glazing and remove dark cuboid from default**. Prefer original dark rear glass unless a D3D8-qualified aperture+interior solution exists; no invented rear damage controller |
| Cabin | Appends Navara steering wheel triangles100–117, dashboard selection and backing while original source dash texture still depicts a steering wheel | Two visible steering wheels | **Select one wheel only**. Restore prior cabin default now; future 3D wheel must be paired with removal or remapping of the baked texture and verified driver hand geometry |
| Underbody frame | Four body-fixed black beams that intentionally stop short of wheel envelopes; no moving axle solver | Appears unconnected to wheels | **Disable by default**. Either develop truly qualified moving/connected visual supports using MR animation, or retain source underbody; do not fake rods to wheels or edit hubs/physics |

## Immediate next bounded phase: `4Runner Stabilization — Quality Gate`

**Primary goal:** user-accepted, clean D3D8 appearance with the previously successful front glass and rear lamps retained. Prefer one credible stable vehicle to several broken optional enhancements. This is a regression-fix phase, **not** a new game donor or automatic all-purpose Model Doctor milestone.

1. **Freeze owner-approved baseline:** preserve previous working pilot, the new `fixed-final` all-options-off candidate and current `adapted-final` as immutable named comparison states. Confirm the actual user-tested candidate path and manifest (do not infer from screenshot or commit alone). Never overwrite alternative CarID29 roster projects (Pajero, Heritage Trooper, GT3 Clio, 4Runner).
2. **Deliver safe default:** build a new `4Runner Stable` variant with the corrected front side apertures and corrected lower rear brake lights but all five optional visual-kit flags OFF. Keep the accepted windshield, intact/broken native glass, drive physics, wheels, crew, sound, camera, frontend and damage unchanged. Run D3D8 targeted owner A/B first. If a supposedly safe variant still exhibits a regression, bisect native draw/material changes rather than proceeding.
3. **Fix by independent opt-in gates:** first coherent body paint reflections without tearing; then true mirror shell/inset; then optional rear glazing (only if correctly bounded without protruding black box), then optional single-wheel dashboard, then suspension visuals. Each independently enabled candidate must be testable in D3D8 before merging it into a combined preset. It is acceptable to defer or omit a feature rather than ship an artifact.
4. **Technical acceptance for reflection:** diagnose whether selective draw removal, coverage, winding, alpha roles or environment/blend state causes patchiness. Preserve the complete diffuse base and apply environment as a qualified extra pass only if native semantics support it. Prefer coherent surface ownership to UV-only whole-triangle filtering. Never enable generic global alpha/two-sided fixes.
5. **Mirrors:** start by restoring source shell and mounts; don't split three disconnected triangles as a finished reflective mirror. Require closed-looking geometry and valid normal/culling behavior from all user viewpoints. Conservative stock material is preferable to broken reflective insets.
6. **Rear windows:** use original opaque/dark glass as stable fallback. Do not cut body atlas polygons based solely on 2D masks unless 3D window aperture geometry, backing visibility, render order and damage grouping are qualified. Never extend transparency over paint/window frame.
7. **Cabin and frame:** no duplicate 2D/3D steering wheel. If proper artwork remapping cannot be proven, omit newly attached steering. Static black bars do not count as wheel attachments; obtain real wheel/suspension-part binding or omit. Neither fix may change collision, hub rest locations, physics or accepted crew geometry.
8. **High brake lamp:** investigate the real source rear upper brake strip and exact MR light state dispatch. Add only if independently qualified, properly bounded and reversible. Existing lower lamps should never regress for this optional addition.
9. **Test gates:** exact model/texture source provenance and byte-hash manifests; lossless original source scene; topology/UV/material ownership checks; 360-degree D3D9 captures with both mirror sides, all body panels and undercarriage; isolated full D3D8 user check for each optional pass (including glass intact/broken and lamp OFF/ON); race Results/reentry separately. Log pass/fail by option; never promote D3D9 static PASS to D3D8 pass. Source-only review and changed-files archives; focused+full Windows regression; protected-files checks including approved proxy baseline.
10. **Project docs:** reconcile canonical `docs/sdk/MASTER_PLAN.md` with this complete v7.0 source, preserve all old history, update capabilities/regression matrix/commit ledger/help and disclose rejected adapted candidate. Local scoped validated Git commits authorized. No push, release, publishing, unrelated branch merge or modification to installed originals/proxy.

**Success criterion:** The stable 4Runner in actual Master Rallye retains the newly correct side glass and brake lights, has no body reflection fragments, torn mirrors, visible black box, wrong rear glass cuts, duplicate steering or unconnected decorative frame. Source dark rear glass and simple original chassis are acceptable. Individually validated optional features may be promoted later. The existing source-to-MR bridge and other vehicle projects remain intact.

## Continuing roadmap after stable D3D8 qualification

- **Historical Archive:** Paris-Dakar Rally 2001 `PajeroRED.tc` / `PajeroSilver.tc`, plus Michelin Rally Masters RAV4 `Car25A.PDO` and Mégane `Car06A.PDO` as high-priority source decoding and original-model identity research. Do not overclaim shared original Master Rallye Pajero geometry.
- **Cross-game adapter refinement:** use stable source semantic evidence, not per-model guessed atlas rectangles or renderer-specific hacks, to improve universal transforms/material authoring; expand to more donor formats after this car is qualified.
- **Model Studio / Blender Bridge:** offer future safe user-authored mesh and material fixes with original-vs-modified comparison, culling, alpha, UV and topology repair. A Model Doctor may explain such defects after real systemic bugs have been resolved.
- **Fleet Builder and expanded MR Heritage catalog:** remain on roadmap. Verified 30-entry roster capacity is not a proof of unlimited active vehicles. Proprietary donor assets remain user-local.


---

# Retained repository implementation checkpoints (historical)

These exact prior implementation records supplement the complete v7.0 plan above.
Their earlier missing-v6.9 and pending statements describe the previous phase; the v7.0 owner review supersedes them.


---

## Implementation status — first Universal Scene to MR 4Runner pilot, 28 October 2026

The owner approved the accepted Evo2 neutral scene for one Source Fidelity
MR-native integration. The complete303112-byte v6.8 attachment is retained as
this plan's exact prefix and in docs/sdk/retained/; no older history/checkpoint
was replaced. Earlier source-only stop gates are historical and fulfilled for
this newly authorized one-car conversion, not permission for a fleet.

Implemented reusable universal-scene-mr-profile/1 bridge to common ScenePart,
DX/DXT and addon services; no separate Evo2 compiler. Original UVS/source
adapter and six L/R wheel resources remain immutable. Four exact side-specific
rolling resources use the original native wheel entities/spin/controllers
through a bounded selector, composed with accepted Lancer mechanics.

One independent Toyota4Runner Source Fidelity Workshop author project and
isolated30-entry alternative CarID29 candidate are delivered. Clean retail
Terrano physics receives measured hubs/radius and source torque-backed MR RWD;
MR Navara audio/crew, source-mapped front/side glass, six rear-only brake lens
triangles, editable Shadow Auto Fit, identity/art/Results/marker and frontend
Auto Frame are explicit MR adaptations. No vertical stance correction or1.05
multiplier; common Z datum-0.10668m is reversible. Rear glass damage, native
source alpha/reflections/bump/animations and settled suspension remain unknown.

38 new focused tests PASS; complete qualified Windows suite1095 tests,
2 existing fixture skips. Actual Tk/D3D9 create/open/validate/provenance,
Studio persistence/Undo/Redo/Restore and source/native capture review PASS.
Deterministic10 SourceBaseline and21 enhanced DX/DXT files; four original
wheel resources differ by at most1.60e-8m after serialized native rest-basis
composition. Controlled original-x86 selector/lifecycle/mechanics replay PASS.
Candidate304resources/260operations and allthree launcher preflights PASS.
All2493 protected original/accepted/source input hashes are unchanged.

Final private delivery: .research-output/vehicles/cross-game-4runner/pilot-delivery.
D3D8 selection, actual model loading, race contact/animation, glass/lights/audio,
AI, finish/Results and menu re-entry remain NOT TESTED / PENDING OWNER. Existing
owner-confirmed Heritage Trooper gameplay and all accepted other projects are
preserved; old historical pending notes do not revoke the owner's acceptance.
See FOUR_RUNNER_NATIVE_RESULTS.md, FOUR_RUNNER_STANCE_AND_MATERIAL_DECISIONS.md,
FOUR_RUNNER_OWNER_CHECKLIST.md and the current regression matrix/Help.

**Stop after this one owner-testable native pilot for review.** No Classic
4Runner, bulk Evo2 import, Paris-Dakar/Michelin campaign, Blender Bridge,
roster expansion, push, publication or release is started here.


---

## Visual polish checkpoint — Toyota 4Runner, 28 October 2026

This is an appended implementation checkpoint; all retained v6.8 attachment
bytes and prior historical sections are preserved. The pasted task mentions
v6.9 but no v6.9 file was supplied; no missing plan is invented or substituted.

The owner confirms previous 4Runner D3D8 loading, driving, body deformation and
breakable glass. Earlier blanket pending statements are historical. Finish,
Results, menu re-entry and the new visual variant remain unqualified.

Implemented bounded source-atlas pane/lens partitions with exact composable
barycentric provenance; side glass no longer covers painted doors/pillars and
omitted upper faces are handled. The accepted intact/broken windshield stays
identical. Rear lower red lens geometry replaces the broad red-corner triangle
heuristic; original Body292 completes the opposite rear surface. No bumper,
clear indicator/reverse area or headlight inherits brake state.

Optional MR kit choices are independently selectable at creation: conservative
paint reflections, original mirror-cap insets, Navara steering/dashboard and
dark backing, static rear glazing, and body-fixed structural frame. All off by
default. No full moving axle reconstruction or original Evo2 renderer fidelity
is claimed. No changes to source arrays, wheel geometry/hubs, physics values,
ride height, fitted collision or30-entry alternative roster capacity.

1102 complete Windows tests PASS,2 existing skips;42 real comparison images,
actual Tk/D3D9 creation, Studio reversibility, exact wheel/physics/collision and
windshield conservation, deterministic full real DX/DXT regeneration and
launcher preflights are recorded in the phase reports. New D3D8 visual checks
remain for the owner. Original accepted pilot remains available unchanged.
See FOUR_RUNNER_VISUAL_POLISH_RESULTS.md and current capability/regression notes.

Stop after this one-car visual milestone: no fleet, other donor campaign,
Blender Bridge, capacity experiment, push, publication or release.


---

## v7.0 implementation checkpoint:4Runner Stable

Owner D3D8 accepts side glass/lower brake fixes and rejects all five optional
Visual Polish experiments. Stable generation refuses those flags and retains
all21 fixed-final model/texture outputs exactly. Original mirrors/paint/dark
rear glazing/cockpit/crew/simple underbody are preserved. Native windshield,
glass damage and lower lamps are unchanged.45 D3D9 comparisons,59 focused and
1107 full Windows tests(2 skips), actual Tk/Studio and launcher preflights pass.
A separate default-off upper brake test uses4 clipped triangles on original
Body595/596 with the existing blight controller. No combined adapted preset.
Both NEW candidates remain pending owner D3D8 approval; prior tested path is
UNKNOWN. Full v7.0 attachment is the exact canonical prefix; all4895 bytes of
unique earlier repository checkpoints are retained above. Current proxy
baseline33917452...960ea1 is preserved; historical mismatch is not restored.
See FOUR_RUNNER_STABILIZATION_RESULTS.md. Stop after one-car stabilization;
no other donor/fleet/Blender/capacity/push/release work.


---

## v7.0 research checkpoint: Paris-Dakar Source Lab —29 October2026

Owner-authorized next source milestone after4Runner stabilization; clean
research/vehicles ec87796. Both original Pajeros and one Nissan Patrol decoded
through bounded TC/Gex/PC TIM readers to existing Universal Vehicle Scenev1.
Original meshes, UVs/normals/material IDs, palette/alpha/mips, resource provenance,
part positions and shared wheel assembly preserved. Existing D3D9 Source Garage
opens all three; explicit CW exterior rendering,36 fixed/basis views, actual Tk,
deterministic repeat manifests and50 focused/1132 full Windows tests(2 skips).
No original or accepted project changed;4610 earlier protected files exact.

Michelin bounded secondary pass recovers38payloads,8XOBJ structural models,
20TGA images,8alternate vertex streams and2PTOCs. Complete assembly and alternate
vertex ownership unresolved. Source catalog remains RAV4/25 and Megane F2/6,
not an unsupported Maxi identification. Historical Silver/front screenshot
resemblance is strong visual evidence; exact MR asset lineage, V60/V20 and
prerelease capture build remain unresolved. Full source reports and manifest
are in PARIS_DAKAR_SOURCE_REPORT.md, PARIS_DAKAR_TC_FORMAT.md,
PARIS_DAKAR_PAJERO_COMPARISON.md, PARIS_DAKAR_SOURCE_MANIFEST.json and
MICHELIN_SOURCE_REPORT.md.

PajeroSilver is the recommended next reviewed source target. Original runtime
material dispatch and suspension pose/options need separate qualification before
any MR authoring. This checkpoint stops at neutral source research: no new native
candidate, CarID, roster expansion, fleet, Blender Bridge, push or release.
The complete retained Masterv7.0 prefix and every previous checkpoint remain
verbatim; this appended result does not replace earlier plans with a summary.


---

## v7.1 review addendum — Paris-Dakar source recovery and next MR import gate (29 October 2026)

### Owner visual review and historical classification

The owner inspected the recovered, textured side-by-side images of the original Paris-Dakar `PajeroRED.tc` number 256 and `PajeroSilver.tc` number 271, together with two older Master Rallye promotional screenshots. The visible cabin occupants, livery and proportional details are promising. The owner notes that they do **not** look like exact one-to-one copies of the early MR models. Maintain this distinction: the RED vehicle differs from the red promotional model in front treatment and rear equipment, while Silver has a strong frontal resemblance to the white/silver promotional vehicle. Historical vehicle naming and exact asset provenance are still unqualified. No recovered image is evidence of an MR-native gameplay import.

### Independent source-only package review

- Uploaded `source-review.zip`: 1334 entries, valid CRC, all 1333 payload SHA256 values match the supplied manifest, all 595 Python modules pass AST parsing.
- Uploaded `changed-files.zip`: 23 entries, valid CRC, all 22 payload SHA256 values match; its 22 changed payloads are byte-identical to the corresponding full review archive entries. All 11 changed Python modules pass AST parsing.
- Independent Linux focused synthetic and compatibility run: `tests.synthetic.test_paris_dakar_source`, `test_michelin_research`, `test_universal_vehicle_scene`, `test_evo2_source_adapter`, `test_universal_scene_bridge`: **68 tests PASS, 0 failures**.
- The Codex report says the full available Windows suite passed 1132 tests with 2 optional skips, and 36 source-geometry D3D9 images plus 3 Workshop screenshots were produced. These original Windows outputs and proprietary game source files are not in the source-only ZIP and were **not independently executed or rerendered here**.
- The repo Master Plan in the full archive starts with the exact bytes of the previously provided canonical v7.0 file and appends the source-lab checkpoint. Previous 4Runner stabilization remains preserved. Local scoped commit reported in both manifests: `3bbe991d34f75d470188c4480143f8e9b6f666b3`; a source-only ZIP contains no `.git` history to independently establish authorship.

### Recovered source facts

- Verified read-only local Paris-Dakar original targets: `Data/PajeroRED.tc`, `Data/PajeroSilver.tc` and `Data/NissanPatrol.tc`, with source-qualified hashes. They use the supported TC `DEAFBEEF` structure, `Gex#` resource geometry and PC TIM-like indexed RGBA palettes with four original mip planes. The `.x` suffix inside `Gex#MainBody.x` is **not** a DirectX XOF model. The decoder intentionally does not generalize to other unverified TC signatures.
- Both Pajeros contain 65 TC entries and 8 Gex members; their original main-body triangle counts are 1376 (RED) and 1446 (Silver). Whole unique resource totals are 1956 and 2002 triangles; separate original wheel instances and static source attachment data are preserved. Third-source NissanPatrol tests reusable decoding without proving all Paris-Dakar vehicles supported.
- Preview uses explicit CW exterior culling, source palette channels and static original attach points. This is a neutral source reconstruction, not exact Paris-Dakar runtime alpha, material, suspension physics, lighting, lamp/glass damage or split-mode proof.
- Historical tests found no exact whole-image RGB match between 56 decoded image resources for each Paris-Dakar Pajero and 41 retail MR Pajero textures, including row-inversion checks. This does not settle derivative ancestry. The white/red car-sheet 022 appears byte-identical in local retail and demo 9.10.0 resources, but its corresponding separate 3D mesh is not qualified.
- Michelin has advanced to a genuine structural decoder: 38 selected PDI1 payloads (8 XOBJ meshes, 8 alternate `_VERTEX.BIN` streams, 20 indexed TGAs, 2 PTOCs) from the source-qualified local RAV4 Car25A and Mégane F2 Car06A. Wheel/hub placement, alternate pose ownership, exact runtime materials and neutral full-vehicle assembly remain unresolved. Do not call the Mégane F2 a verified Mégane Maxi model without further evidence.

### Decision: one PajeroSilver native pilot, only after this source review

The next bounded *proposed* milestone is a separate, isolated **PajeroSilver Paris-Dakar → Master Rallye Source Fidelity pilot** using the already qualified Universal Vehicle Scene → MR bridge. It is an independent adaptation of an original Paris-Dakar source asset, **not** an alleged exact recovery of a missing prerelease MR model. RED remains a second source variant and Nissan Patrol a structural regression; no bulk fleet installation.

Gate the pilot on (1) qualified source-material and palette transparency handling; (2) original runtime wheel pose/options versus the neutral attach point, and native MR wheel/hub/physics mapping; (3) source crew, lamps and glass identification without invented independent original behavior; (4) exact original rear/front source textures and trim preserving stock 2001-era look; (5) one reversible isolated alternative CarID29/30-car roster (do not overwrite existing accepted projects); and (6) independent valid frontend, results name, UI art, brake lights, damage, sound, camera and shadow bindings using explicit **MR donor** choices. Gameplay evidence remains pending until the owner tests the isolated D3D8 candidate.

Preserve 4Runner Stable and previous successful Native MR features; no experimental reflected mesh, mirror patch, rear blackout box, duplicate wheel or body-fixed suspension visual kit. Do not edit original game files or distribute donor proprietary assets. Local commits after tests, no push/publication. Stop after a single playable candidate for the owner's review.

### Roadmap remains intact

After first Silver pilot review, evaluate whether to import RED separately, or resume Michelin assembly and Paris-Dakar wider catalog; historical MR geometry provenance stays a parallel research question, and Blender Bridge is the future safe manual editing path.
