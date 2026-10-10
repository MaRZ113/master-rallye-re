# R-CAM1-A3b validation and delivery

**Status: `BLOCKED_ON_LIVE_RACE_OWNERSHIP`. Functional Freecam: NO.**

The reviewed native camera-consumer extent ends after EndFrame at
`0x0065332C` / RVA `0x0025332C`. The remaining prerequisite is a read-only
certificate associating the current live race owner with successful scene
initialization, including pending/failed same-course requests. The native
completion bridge and pose writes were not installed while that admission
condition remains unproven.

## Repository

- Path: `D:\Game\Master Rallye\master-rallye-re-general`.
- Branch: `master`; starting HEAD `9e7b56c411923875137ba0e17c6d9a64ed61c55e`.
- Preflight status/branch/log20/diff-check: clean; no unrelated changes present.
- Accepted UI commit `7e866d7` preserved.
- Stage changes only under `modernization/renderer/`.
- No new branch/worktree, retired-tree writes, game deployment or push.
- Original EXE/assets and existing Ghidra projects remain read-only.
- Commit subject: `research: map full-frame camera scope and race epoch blocker`.

## Newly executed checks

| Check | Result | Evidence boundary |
|---|---|---|
| Pristine scope inspector | PASS, 68 anchors (original 17 + new 51) | Exact SHA, RVA mapping, bytes and specified relative CALL targets |
| Fresh Ghidra evidence | 47 new curated exports; 66 including retained A3 exports | Read-only project, rolled-back transactions, reviewed instruction operands; mismatched entries excluded |
| Focused scope tests | 11/11 PASS | Malformed/unknown inputs, every anchor mutation, independent CALL-target check, ownership map and uncertified-state contracts |
| Full renderer Python | 132/132 PASS, 82.854 s | Existing renderer contracts plus six additional scope-evidence tests |
| Canonical Win32 Release build | PASS | `python modernization/renderer/tools/build.py`; no sequential fallback needed |
| Native CTest | 10/10 PASS, 7.48 s | Existing native regression suites; no Freecam bridge exists to exercise |
| Compileall | PASS | `python -X pycache_prefix=modernization/renderer/.analysis/pycache -m compileall -q modernization/renderer` |
| Proxy verifier | PASS | PE32/I386, DLL, required direct exports/ordinals, no recursive D3D8 or delay import |
| Diff-check | PASS | Final source/documentation whitespace check |

Full Python used an ignored writable renderer TEMP/TMP. Previous assertions were
not weakened. Actual x86 bridge tests, guarded camera write/restore fixtures,
production race-predicate fixtures, Freecam math/input and four Freecam/FOV mode
tests are **NOT IMPLEMENTED / NOT RUN**. Tests of the proposed static ownership
map do not substitute for these missing implementations.

## Build

Ignored output:
`D:\Game\Master Rallye\master-rallye-re-general\modernization\renderer\.build-msvc\Release\d3d8.dll`.

- Size: **1,597,440 bytes**.
- SHA256: `f11a2c26c37c2dab23a8e4d19af13ebab762f946be3e61f37f1aea19e4850af4`.
- PE32, I386 `0x014C`, DLL.
- Direct3DCreate8 ordinal 5; ValidatePixelShader ordinal 2;
  ValidateVertexShader ordinal 3.
- Imports: bcrypt.dll, USER32.dll, KERNEL32.dll; no d3d8.dll import.

This is a rebuilt baseline renderer. Renderer implementation/configuration was
not changed by A3b; the recorded binary hash is the fresh build output, not a
claim of byte identity with the earlier A3 build. It is not deployed and is not
a working Freecam candidate.

## Scope, ownership and implementation report

| Requirement | Result |
|---|---|
| Native traversal | `0x00509680`, thiscall ECX per-camera list, two arguments, RET 8; static contract pinned |
| GameFov owner | Existing single hook at `0x006532DD`; unchanged tail-JMP |
| Post-traversal `0x006532E2` | Rejected: FinalizeCamera/particles follow |
| Post-Finalize `0x006532E9` | Rejected: late builder/debug path follows |
| EndFrame call `0x00653329` | Renderer virtual `+0x18`, `0x0056CD80`, zero stack arguments, plain RET |
| Late builder `0x0056CE38` | Confirmed; selected camera also passed to debug rendering |
| Native end `0x0065332C` | Reviewed native consumption ends; epilogue RET 4, caller continuation has no CameraFrame read |
| Completion strategy | Candidate CALL interception at `0x005B0166` → scheduler; return `0x005B016B`; not installed/ABI-tested |
| Owned field plan | Planes `+8`, Previous `+0x38`, Current `+0x88`; exclude source/flags/viewport/snap |
| Native viewport | Per-camera and camera-zero writes must survive; no full-object restoration proposed |
| Cache/order | Builder cache guard and earlier position sorting/cache documented; independent-camera behavior unvalidated |
| Restore failure policy | Future implementation must deactivate, report failed readback, and avoid stale-pointer writes; not exercised |
| RaceLimits | Interned registration, AI slot/type/arrays, retirement before unregister/destruction confirmed |
| Phase | Native participant 0/1/2/3 writes mapped; no approved current-scene epoch certificate |
| Offline/loading/replay/etc. | No combined live predicate; unsupported/unknown states remain unauthorized |
| Freecam / controls / mouse | Absent: no activation, visible-pose initialization, movement, WASD/Numpad/Custom parser or mouse ownership |
| Coherent Freecam endpoints/planes/VIEW/particles | Not implemented; native reader requirements mapped |
| Stock restoration/focus/transitions | No Freecam mutation exists; future implementation obligations retained |
| Native vehicle-input isolation | Not implemented/claimed |

The exact missing state fact and smallest observation are in
[race ownership](race-ownership.md) and [runtime plan](runtime-test-plan.md).
No first-flight INI/toggle, controls test or flight is advertised. In-game Freecam
validation remains pending implementation.

## Accepted renderer regressions

R-UI1 automatic carousel correction, PreserveMargins v2, Stock/Centered4x3,
Windowed live resize, Borderless, MenuFreezeFix, frontend preview, vehicle
reflections/semantic lifetime, GameplayFOV/CPU culling, camera-owner probe,
A2 pre-submission observation, F10, foliage upload provenance, forwarding and
COM/resource identity retain their existing native/Python contracts in the
newly executed suites. Renderer source/configuration remains unchanged.
No new human acceptance is inferred from automated checks. Exclusive is unchanged
and remains deferred under R-EXCL1.

## Sources and handoff

- [Full camera extent and ABI evidence](scope-closure.md).
- [Live race ownership blocker](race-ownership.md).
- [Implementation boundary](implementation.md).
- [One ownership verification](runtime-test-plan.md).
- [Extended exact-build map](../../research/r-cam1-a3/camera-scope-map.json).
- [Curated export digests](../../research/r-cam1-a3/ghidra-evidence.json).
- [Bounded instruction excerpts](../../research/r-cam1-a3b/scope-excerpts.json).
- Read-only inspector: `tools/inspect_camera_scope.py`.
- Tests: `tests/test_camera_scope.py`.

Changed-source archive (ignored):
`modernization/renderer/.analysis/archives/r-cam1-a3b-source-20261010.zip`.
It contains the stage's tracked source/tests/docs/data only. No DLL/PDB/OBJ,
proprietary binary/assets, runtime logs, raw memory, scratch exports or reverse
database is included. The ending commit SHA and clean worktree are reported
after the commit; no push is performed.
