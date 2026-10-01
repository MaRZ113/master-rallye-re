# R-EXE1 whole-program reconnaissance

## Scope and evidence rules

This is architectural reconnaissance across the four read-only executable corpora and the retail `Data.sma`. The R-EXE1 checkout is based on committed HEAD in `research/r-exe1-whole-program`; no binary patching, asset writing, game execution, or runtime claim was made. The original checkout's in-progress R5T work was consulted read-only for context and was not copied or changed.

Evidence labels follow repository convention:

- **CONFIRMED_BY_EXE**: direct instruction, control-flow, data-reference, import, or string-xref evidence.
- **CONFIRMED_BY_CORPUS**: bytes or semantic structure observed in a corpus file; archive-backed XML observations include CRC/size validation.
- **CONFIRMED_BY_RUNTIME**: prior human runtime evidence, cited to the existing R5T report; no new R-EXE1 runtime experiment was run.
- **SOURCE_EVIDENCE**: existing project implementation/documentation, not a new fact about the original game.
- **STRONG_HYPOTHESIS**, **HYPOTHESIS**, **UNKNOWN**: unresolved interpretation with falsification steps in the ledger.

Direct executable evidence is exact-build-specific. A missing literal/xref is not evidence that a dynamically formatted broker path or virtual call is absent.

## Architectural picture

The four builds form a tightly related PE32/D3D8 lineage, but the code base did not simply grow in place. The 9.3.1-to-9.10.0 shader registration path is a notable rewrite; retail then keeps that renderer path close to 9.10.0 while adding archive-backed `Data.sma` access and a retail-only `BuildData` command family. Several core helpers, including the resource-root constructor, UDP listener, default parameter-broker registration, and progress wrappers, remain recognizably stable.

The runtime architecture is organized around a broker-driven application and resource stack:

```text
CRT entry -> application dispatcher -> manager construction / settings
    -> window + D3D8 + input + audio + network
    -> frame loop: messages, timer/state, input, simulation/physics,
       audio, scene/render dispatch
    -> manager shutdown

DataGame / DataScene broker and scene configs
    -> named values and scene component factories
    -> vehicle / frontend / race objects
    -> DataGx model, image, texture, material and scene resources

retail resource open:
    loose requested path -> Data.sma central-directory lookup fallback
```

The broker layer is a shared bridge between configuration and runtime systems. Retail broker diagnostics expose 0x1c-byte value entries, type tags, save flags, and GLOBAL/SCENE/USER scopes; typed accessors share the entry vector. Existing `Data.sma` XML records use `Value` elements with `Name`, `Type`, and `Value` attributes and save flags. This connection is supported by independent corpus and executable evidence, although the exact generic XML parser implementation should be followed from the existing parser path rather than inferred from broker diagnostics alone.

## Strongest new architectural conclusions

### Startup and main loop

**CONFIRMED_BY_EXE.** Retail dispatches through `006766A0`, initializes managers in `005AFB20`, enters the frame loop in `005AFE30`, and releases application/device/audio state in `005AF920`. Window/device setup is in `00652F50`; D3D8 is created through `00558EE0` and configured in `00559340`, DirectInput8 setup is in `00570E00`, DirectSound setup in `0059A010`, and network manager initialization in `00653860`. The frame loop reads `Game/Quit`, updates messages, timing and input, then reaches simulation/scene/audio/render managers. This is an engine-style manager loop rather than a single monolithic race function.

The window starts from a 640x480 branch; DirectSound failure is logged but does not fail the whole graphics/input initialization path, whereas device/input failure does. This asymmetry is visible in the initialization control flow and should guide future error-path inspection.

### Filesystem and resource manager

**CONFIRMED_BY_EXE.** All builds import ordinary Win32 file enumeration/open calls and register `DataAudio`, `DataGx`, `DataGame`, and `DataScene` roots from the current directory; 9.3.1 onward also registers `DataVideo`. The shared root-constructor instruction sequence is 0.928 similar from 8.4.1 to 9.3.1 and identical by mnemonic sequence for later pairs.

**CONFIRMED_BY_EXE, retail.** `0064D530` first calls `CreateFileA` on the requested path. On failure, an enabled archive path normalizes slash direction, matches a registered virtual root, resolves its archive entry, and opens the member through `00652570`. `006512F0` scans backward through `data.sma` in 0x400-byte chunks for `PK\x05\x06` or the observed `SM\x05\x06` marker before locating the central directory. The member reader validates ZIP central-directory records and accepts stored (0) and deflate (8) methods. This establishes a useful loose-first/packaged-fallback candidate path, but not every root's search precedence or all archive error fallbacks.

The open/close wrapper neighborhood includes `0064D070` and `0064D1C0`; archive setup/teardown constructors are `0064CE80` and `0064DA20`. Decompilation exposes global candidates at `DAT_0070AD6C`, `DAT_0070AD70`, and `DAT_0070AD74` for archive/index/active state. These are retained as neutral global candidates because handle ownership and teardown order are not fully proven.

**CONFIRMED_BY_EXE.** GXM model and GXI texture loaders retain cache-aware source-loading paths in all builds. Their debug strings and direct xrefs map consistently across the four executables. Retail also contains cached DX texture reading; `BuildData` invokes the same model, texture, and image-bank paths used by runtime loading, so it appears to cook cache outputs through shared loaders rather than a wholly separate converter.

### XML and parameter broker

**CONFIRMED_BY_EXE.** Retail broker diagnostics at `00601D00` enumerate 0x1c-byte entries and report entry count/capacity. Type dispatch recognizes Bool, Float, Int, Matrix, String, StringList, MarkerListName, and XmlFilename among its cases. Scope values 0 and 1 print GLOBAL and SCENE; other values are reported separately. The partial entry layout is `+0x00` key/index candidate, `+0x04` value-storage pointer candidate (diagnostics dereference this for typed values), `+0x08` type tag, `+0x0C` save-flag bits, `+0x10` revision, `+0x14` scope tag, `+0x18` unknown. Only the observed offsets and operations are named. The generic typed accessors use this shared entry array. Type-specific getters return the correctly typed value when the entry tag matches and use a default on a mismatch; setters write through the same entry layout.

`004D8EC0` creates/returns a global collection candidate at `DAT_006F9410`; its begin/end/capacity fields and linked-list field align with the broker diagnostic's collection walk. This is recorded as the likely global broker instance, not as the only broker in the process; scene and user broker scopes are separately printed.

**CONFIRMED_BY_CORPUS.** Archive-matched retail configs encode named values with `Value Name/Type/Value` and `SaveOptions`/`SavePlayerState`. `DataGame/Progress.xml` contains 109 WinStatus, 16 UnlockedCars, 6 OpenedModes, 7 Cheats, and 46 BestTimes values. These records align with executable progress wrapper keys and broker types. The CRCs for sampled `Game.xml`, `MasterRallye.xml`, `Progress.xml`, `RallyeCup.xml`, and `DataScene/RaceTest/France1.xml` match the retail archive index.

**Existing static evidence, not newly rediscovered:** the Retail XML factory dispatches `EggLists_Version4` into the Egg/list parser (`0052ECD0`, `0053AD60`, `0053AE50`); the existing R5T-D1 document traces the `gaRaceSplitTimeAI` property loader and already runtime-confirms the France1 SplitTime0 center/radius path. R-EXE1 adds cross-build class-name xrefs and relates them to the shared application/config architecture; it does not revise R5T-D1 or R5T-C.

### Graphics and material pipeline

**CONFIRMED_BY_EXE.** Every build initializes D3D8. Shader/material registration expands and then changes shape: the 9.10.0 registry adds explicit alpha-test families and its normalized mnemonic sequence is only 0.447 similar to 9.3.1; 9.10.0 to retail is 0.992 similar. Retail has selector/compile-failure paths and retains the prior project's shader registry/selector findings. This is the best cross-build lead into alpha-test versus blend and environment-stage semantics; no new interpretation of `UsesAlpha` is asserted here.

**Existing project evidence:** R4D.1 has already materially reconstructed DX/DXT/GXM/GXI/GXB material and texture concepts, including alpha and reflection states. R-EXE1 uses those findings to bound a future consumer-level trace rather than repeat the format work.

### Vehicles and scene/race logic

The confirmed retail vehicle path anchors remain the established entry points: `0044EE69` ordinary-race family pointer; `00493E30` `Vehicles/<family>` load; `00493FD0` `<family>/Player1` modifications; `004938C0` publish to `Vehicles/CarN`; and `0044F343` post-writer checkpoint. Existing R5V research already establishes a 25-row registry, class capacities, and the current extra-slot boundary. R-EXE1 does not claim a new vehicle capacity or repeat the Vehicle SDK reconstruction.

**CONFIRMED_BY_EXE and CORPUS.** RaceTest component names and executable class registrations align for `gaRaceFinishAreaAI`, `gaRaceLineAI`, and `gaRaceSplitTimeAI` in all four builds. Retail constructors/factories for finish-area and race-line objects and the pace-note property loader are identified. The `gaRacePaceNoteAI` XML component family has corresponding retail construction and field-load code; the exact gameplay consumption of `PaceNoteOwner`/`PaceNote` remains unresolved. These facts map the parser-to-component edge, not route or AI behavior.

**Prior runtime evidence:** R5T-D1 confirms SplitTime0 Egg Row3 as its runtime trigger center and `Radius` as its 3D spherical threshold. That evidence is an existing conclusion. Other marker progression, finish, start-grid, SFL, and tag100 semantics remain subject to their documented boundaries.

### Progress, save data, and frontend

**CONFIRMED_BY_EXE.** Progress wrappers directly read/write `Progress/Won/` in 8.4.1 and `Progress/WinStatus/` in later builds, alongside UnlockedCars, OpenedModes, Cheats, and BestTimes. The setters/getters are near-identical across later builds. Frontend cup selection reads class lists and populates button/status/time entries; the observed five-button layout is a UI layout count, not a career-capacity limit.

The retail `MasterRallye.xml` broker schema includes six summary slots, `MasterRallye/Car0` through `Car5`, and code serializes/deserializes those records when `GameSaved` is set. This is a campaign-summary record count only. It does not establish the active-race car count or a universal save capacity. Editor dialogs that open/save `DataGame/*.xml` or `DataScene/*.xml` are development/editor paths and are not proof of the player save-file format. Player save filename, container, and full serialization lifecycle remain **UNKNOWN**.

### Networking, replay, and AI

**CONFIRMED_BY_EXE.** A UDP listener exists in all four builds and binds port 22,222 when enabled. Network broker keys include per-car IP addresses and sync state; a race-sync enforcer path exists. This supports an actual networking subsystem, but does not establish protocol framing, online play support in a given retail mode, or a player cap.

**CONFIRMED_BY_EXE.** `Race/GhostPlayback`, `Race/Ghost_StartPosition`, and replay-related keys survive in all builds. Retail constructs a GhostCar when ghost playback is active, initializes it at the configured start position, and clears the playback flag on an invalid start-position path. The replay file format and `RecordReplay` producer remain unknown.

AI class names and course components are plentiful, but broad target selection, overtaking, recovery, stuck handling, and wrong-way correction have not been reconstructed. `gaHudAiWrongWay` is a stable HUD component constructor; the actual wrong-way detector and the dynamically addressed `Race/CarN/WrongWay` consumer are unresolved. No behavior is inferred from names alone.

### Development tools and surprise

**CONFIRMED_BY_EXE.** Debug/editor registration and XML game/scene open/save paths survive all four builds. Retail alone among these four contains `BuildData` strings and a recursive directory walker. The wrapper at `005B2F80` normalizes a root path, resets counters, walks directories, dispatches model/texture/image-bank callbacks, and logs counts. A method-pointer-looking cluster at data `00692F8C` references this wrapper; it is evidence of indirect registration/reachability, not proof that the command is exposed or callable in an ordinary retail session.

The original Data.sma remains untouched. The likely next step is to establish the wrapper's owning object/menu dispatch and test availability on a disposable copy before attempting to characterize outputs.

## Cross-build outline

- **8.4.1 → 9.3.1:** the progress prefix changes from `Progress/Won/` to `Progress/WinStatus/`; resource roots gain DataVideo by 9.3.1; core broker registration/root/network code remains recognizably related while RTTI-like strings and binary size grow.
- **9.3.1 → 9.10.0:** renderer/shader registration is structurally rewritten and adds alpha-test variants; `ddraw.dll` appears among imports; app-setting registration layout changes materially in the decompilation.
- **9.10.0 → retail:** root and network functions remain identical by normalized mnemonic sequence and shader registration is nearly identical; retail adds archive-backed `data.sma` lookup and `BuildData`; application-setting registration changes layout again. Retail is not simply a universally larger version of every demo subsystem.

Exact correspondence evidence and similarity caveats are in [`function-correspondence.json`](function-correspondence.json) and [`build-evolution.md`](build-evolution.md).

## Read next

- [`subsystem-map.md`](subsystem-map.md): bounded architecture map with files, anchors, differences, and unknowns.
- [`data-to-exe-anchors.md`](data-to-exe-anchors.md): archive inventory and executable name/xref joins.
- [`string-catalog.md`](string-catalog.md): curated string/xref samples plus machine catalog.
- [`hypotheses.md`](hypotheses.md), [`future-branches.md`](future-branches.md), and [`runtime-test-candidates.md`](runtime-test-candidates.md): explicit uncertainty and next steps.
