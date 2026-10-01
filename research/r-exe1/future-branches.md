# Evidence-driven future reverse-engineering branches

Difficulty estimates describe static analysis plus any controlled runtime work; they are relative within this project.

## QUICK WINS

### 1. Retail resource resolution and cache lifecycle

- **Question:** What exact precedence selects loose versus Data.sma entries, and what metadata makes a DX/GXI/GXM cache valid?
- **Current evidence:** `0064D530` loose-first/archive fallback, `006512F0` archive index scan, `00652570` member reader, stable GXM/GXI loaders in all builds.
- **Expected value:** High; answers how edited assets are discovered and where the game builds runtime caches.
- **Difficulty:** Low-medium.
- **Static work:** Resolve duplicate-name ordering, exact root matching, cache key/source timestamp inputs, and ownership/close paths.
- **Human runtime work:** One duplicate loose/packed sentinel test on a disposable retail copy; optionally invalidate a copied cache and capture loader branches.
- **Dependencies:** Hash-verified copied Data.sma/install; no edits to authoritative files.
- **Major unknowns:** Does every root allow loose override? Is archive resolution case-sensitive? Which fields invalidate caches?
- **First experiment:** Break at `0064D530` while requesting one path that exists both loose and packaged in a clone.

### 2. Generic broker parser and progress persistence

- **Question:** How do XML attributes populate the broker entry, and which entries reach the actual player-state file writer?
- **Current evidence:** 0x1c entry layout at `00601D00`, typed read/write functions, `Value Name/Type/Value` corpus, progress wrappers and save flags.
- **Expected value:** High; unlocks many systems and explains safe progress data experiments.
- **Difficulty:** Medium.
- **Static work:** Follow parser visitor, type conversion, serializer, and every `SavePlayerState`/`SaveOptions` flag consumer.
- **Human runtime work:** Normal play on a cloned profile, observe broker values and diff only generated save artifacts.
- **Dependencies:** Read-only parser context in R5T-D1 and archive-matched config baselines.
- **Major unknowns:** Writer entry point/file format, merge order, dirty tracking.
- **First experiment:** Static trace one Bool and one Float Value from XML through broker field and serialization dispatcher.

### 3. Alpha-test and environment material selection

- **Question:** Which material inputs choose alpha test, alpha blend, and environment/reflection stages in D3D8?
- **Current evidence:** 9.10 rewrite with new alpha-test families, stable 9.10-to-retail registry, existing R4D.1 material-state anchors, retail selector `00580360`.
- **Expected value:** High for faithful asset preview/rendering.
- **Difficulty:** Medium.
- **Static work:** Connect material fields to selector cases and exact render-state/texture-stage calls.
- **Human runtime work:** Breakpoint observation on existing cutout, translucent, and reflective assets; optionally capture screenshots from an isolated install.
- **Dependencies:** Existing material format findings; no preview code changes until exact consumer evidence exists.
- **Major unknowns:** `UsesAlpha` consumer and stage-state combinations.
- **First experiment:** Trace one existing cutout material and one translucent material through selector to D3D state setter calls.

## MEDIUM RESEARCH

### 4. Route markers, wrong-way state, and recovery

- **Question:** What updates LastMarker, SplitPoint, WrongWay, and pace-note ownership during a race?
- **Current evidence:** Formatted Race/CarN paths, RaceLine/finish/split/pacenote component factories, existing runtime confirmation of SplitTime0 only.
- **Expected value:** High for course modding and future experiments.
- **Difficulty:** Medium-high.
- **Static work:** Trace formatted path construction, all broker reads/writes near route classes, RaceLine progress and vehicle reset callbacks.
- **Human runtime work:** Watch one car across forward marker order, reverse travel, route departure, and recovery on a copied profile/course baseline; do not touch active R5T-C candidates.
- **Dependencies:** R5T-D1 SplitTime0 baseline; route-state candidate table.
- **Major unknowns:** Which state is per-car, which updates per-frame, and how course markers affect it.
- **First experiment:** Break on broker reads/writes for `Race/Car0/LastMarker` while crossing the next known RaceLine marker.

### 5. BuildData ownership and safe reachability

- **Question:** Is the retail cache builder reachable from a normal editor/menu command, and what is its real output set?
- **Current evidence:** Retail wrapper/walker/callbacks and method-pointer-like cluster; no earlier-build family found.
- **Expected value:** High if it permits safe rebuilding of cache outputs without reconstructing tools.
- **Difficulty:** Medium.
- **Static work:** Resolve table owner, vtable/callback registration, dispatcher and UI/menu entry.
- **Human runtime work:** Check ordinary retail UI; if reachable, use a disposable copied directory and audit output hashes/extensions.
- **Dependencies:** A disposable retail install and isolated input/output directory.
- **Major unknowns:** UI reachability, overwrite scope, accepted folder grammar, error handling.
- **First experiment:** Static trace all xrefs to `00692F8C` and the wrapper before runtime invocation.

### 6. Ghost recording/playback data path

- **Question:** What creates replay data, where is it stored, and how is it consumed by GhostCar?
- **Current evidence:** `RecordReplay`, `RecordSpline`, `GhostPlayback`, `Ghost_StartPosition` in all builds; retail GhostCar setup.
- **Expected value:** Medium-high for replay and camera research.
- **Difficulty:** Medium.
- **Static work:** Trace broker setters, file APIs, sample buffers and the parser feeding the playback object.
- **Human runtime work:** Short race on cloned profile, record generated files and debugger state only if an existing option is accessible.
- **Dependencies:** Safe profile backup and build-specific function map.
- **Major unknowns:** Recording trigger, file extension/layout, deterministic update cadence.
- **First experiment:** Cross-reference RecordReplay/RecordSpline setters against file-open/write xrefs before launching the game.

## DEEP RESEARCH

### 7. AI/raceline target and recovery architecture

- **Question:** How do AI actors consume RaceLine samples, choose speed/steering targets, and recover when off route?
- **Current evidence:** `gaRaceLineAI`, driver parameter registrars, `Race/CarN/RecordSpline`, course marker families and AI vehicle classes.
- **Expected value:** High for course-route understanding, but broad.
- **Difficulty:** High.
- **Static work:** Identify AI actor vtables, per-frame update path, marker/sample lookup, and recovery/vehicle reset callers.
- **Human runtime work:** Observe AI on an unmodified known course, record target/progress values at matched frames; no route edits until a stable trace exists.
- **Dependencies:** Route-state branch and known AI race setup.
- **Major unknowns:** Spline representation, steering controller, speed policy, opponent difficulty.
- **First experiment:** Map `gaRaceLineAI` and AI-car vtable updates, then identify the first consumer that reads RaceLine markers.

### 8. Full course runtime registry and participant limits

- **Question:** How are course scene names registered, selected, and expanded into race setup, and what limits are genuine runtime capacities?
- **Current evidence:** executable course-name tables, RaceTest XML class names, `Race/NumCars`, own vehicle registry limits and separate six-row MasterRallye summary.
- **Expected value:** High for extra-course mod feasibility and correct capacity boundaries.
- **Difficulty:** High.
- **Static work:** Trace frontend selection -> course ID/name -> scene open -> race spawn loops; resolve each bounded array with surrounding semantics.
- **Human runtime work:** One known course selection and race start with debugger observations only; no extra-slot edits in this branch.
- **Dependencies:** Frontend and resource branch; existing R5V registry findings.
- **Major unknowns:** Registry storage, mode-specific counts, course registration path.
- **First experiment:** Decompile the frontend race-select selection handler and follow its chosen name into scene resource open.

## LONG-TERM / OPTIONAL

### 9. Network protocol and multiplayer capability

- **Question:** Does port 22222 carry race sync, discovery, or a different service, and what modes can reach it?
- **Current evidence:** stable UDP listener, Network/SyncState, per-car IP keys, race-sync enforcer.
- **Expected value:** Medium; useful only if multiplayer preservation is a target.
- **Difficulty:** High.
- **Static work:** Trace send/recv framing, handshake, packet types and indexed slot limits.
- **Human runtime work:** Two loopback-only copies on an isolated machine/network after static mapping.
- **Dependencies:** Network init and menu-mode map.
- **Major unknowns:** Protocol, peer roles, external endpoint behavior, supported retail modes.
- **First experiment:** Complete a static send/receive call graph and enumerate packet construction sites.

### 10. Player save container and unlock state

- **Question:** What file/container persists broker values, and how do campaign summary, unlock state, and selected car interact?
- **Current evidence:** Progress wrappers/flags, GameSaved/MasterRallye summary rows, cup selected car IDs.
- **Expected value:** Medium-high for preservation/modding.
- **Difficulty:** High until the writer is found.
- **Static work:** Identify serialization dispatcher and actual OS file write calls; trace saved-data load before frontend state selection.
- **Human runtime work:** Backup profile, change one normal progress item, compare only newly written files and validate re-load.
- **Dependencies:** Broker serializer branch.
- **Major unknowns:** Save file path, checksums, versioning, failure/fallback behavior.
- **First experiment:** Find calls that enumerate broker entries based on SavePlayerState flags and follow them into file APIs.
