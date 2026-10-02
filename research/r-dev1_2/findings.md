# R-DEV1.2 findings

Status: **static closeout complete; controlled runtime observations are prepared but not performed.**

## Main results

1. **R-DEV1.1 correction:** retail `005AF970` is the producer of the four editor-open flags. It clears bytes `+0x44..+0x47`, checks the Marker/Particle/Broker/Egg HWND predicates, closes currently open tools, and sets the matching bytes. `005AF9F0` consumes and clears them.
2. **Lifecycle:** the snapshot is called by Game and Scene open/reset/state-reinitialization paths, as well as by application teardown. Open Game/Scene paths validate a selected `DataGame/` or `DataScene/` XML path before taking the snapshot and applying the new state. Reset paths take it after confirmation and before their state operation. Retail restoration is called from a separate foreground callback that then calls `SetForegroundWindow`; the exact event-dispatch trigger and whether each state path guarantees that callback remain unknown.
3. **`Editing/EditorsOpen`:** it is a typed integer counter, not a bool/list/bitset. Its direct paired update paths belong to Marker and Egg editor-view initialization/cleanup; the helpers also save/restore camera/view data. Particle and Broker do not call those integer updater functions directly.
4. **Broker sentinels:** retail Broker Editor registers `__NO_SAVE` and `__NO_CHANGE` as interned broker key IDs in a shared linked-list registry. A direct-reference census separates literal/static-initializer references from the opener's pooled-object call sites; the insertion code performs duplicate detection and appends a key-ID node, but does not itself filter saves or prevent broker changes. The labels' intended policy effects remain unknown. `__IGNORE` is not passed by the Broker Editor opener, and no other direct retail code consumer was recovered.
5. **Broker Editor open-only:** it builds and populates UI, reads existing broker records, and mutates shared in-memory key metadata when those IDs are absent. No typed broker setter, XML serializer, save writer, or disk-write open is on the mapped first-open path. Classification: `LOW_RISK_BUT_METADATA_MUTATION`.
6. **Flow Builder open-only:** the `0x30` route creates the window/layout/menu and shows it. No automatic load, conversion, build, clear, or output write was found before user input. Classification remains `SAFE_OPEN_CANDIDATE`, open-only.
7. **Runtime preparation:** the helper's exact retail hash gate and dry-run default remain. Its allowlist now contains only `flow-builder` (`0x30`) and `broker-editor` (`0x27`); the latter requires the separate phrase `OPEN BROKER EDITOR WITH METADATA REGISTRATION`. BuildData and all write-capable commands remain excluded.

## R-DEV1.1 corrections recorded here

- The prior claim that no producer existed for `+0x44..+0x47` is superseded: `005AF970` is the producer, and `005AF9F0` is the consumer. The original R-DEV1.1 files retain their historical text with a visible correction notice.
- The initial tentative `Editing/EditorsOpen` owner attribution to Particle is corrected. Retail caller chains map the counter to Marker and Egg editing-view contexts.
- The previous Broker Editor `DO_NOT_RUNTIME_TEST` decision is superseded by `LOW_RISK_BUT_METADATA_MUTATION`; only the open-only observation is prepared, with a separate strong confirmation. Editing/commit remains outside scope.

## Evidence and analysis environment

- **CONFIRMED_BY_CORPUS:** all four pristine executable hashes match `research/corpus/executable-provenance.md`.
- **CONFIRMED_BY_EXE:** retail and pristine 9.3.1 were imported/analyzed in isolated Ghidra 12.1.4 projects. Targeted Ghidra Bridge decompilation covered lifecycle callers, snapshot/restore, broker manager/insertion, Broker Editor open/population, and counter helpers. Retail lifecycle instructions were checked against assembly. Pristine 9.10.0 was checked through hash-verified function byte/call patterns. Pristine 8.4.1 did not establish the later snapshot/restore object layout.
- Ghidra 12.1.4 path: `D:\Game\Master Rallye\_reverse-tools\ghidra-bridge-main\ghidra_12.1.4_PUBLIC`.
- Ghidra projects, bridge exports, and profile are scratch under ignored `research-output/r-dev1_2/`. Shared Ghidra projects were not opened or modified. No raw database is committed.
- No full-program pseudocode export was generated.
- No runtime game launch, UI interaction, editor open, memory write, EXE patch, or game-data modification occurred.
- Validation before commit: the 10 targeted command-trigger unit tests passed; both phase JSON files parsed; `function-map.csv` parsed with 26 rows; all four executable hashes and sizes matched the authoritative corpus; `git diff --check` passed. These checks do not constitute runtime validation.

## Artifacts

See:

- `editor-lifecycle.md` / `.json`
- `editor-state-structure.md`
- `broker-sentinels.md` / `.json`
- `broker-editor-open-path.md`
- `broker-editor-safety.md`
- `flow-builder-safety.md`
- `runtime-test-plan.md`
- `known-unknowns.md`
- `function-map.csv`

The exact human observations remain pending as described in `runtime-test-plan.md`.
