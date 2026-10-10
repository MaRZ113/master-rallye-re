# R-CAM1-A3c validation — 2026-10-10

Status: **BLOCKED_ON_RACE_EPOCH_CORRELATION**. A Win32 Release lifecycle
observation DLL is available. Functional Freecam is **not implemented** and
in-game observation is **PENDING**. No new camera/frustum/VIEW writes occur.

Checkout: `D:/Game/Master Rallye/master-rallye-re-general`, branch `master`,
starting clean HEAD `0ed480712da532a66376da9bd5658166a7663c78`.
No new branch/worktree, deployment, game launch, or push was performed.

## Executed validation

| Check | Result | Scope |
| --- | --- | --- |
| Exact retail inspector | PASS, 86 instruction/context anchors | SHA-locked pristine EXE, 3,121,214 bytes, ImageBase `0x00400000` |
| Read-only Ghidra ledger | 71 function records | Five added lifecycle/pool functions; Ghidra 12.1.4; no project save |
| Full Python suite | **140/140 PASS**, 100.575 s | `python -m unittest discover -s modernization/renderer/tests -v` |
| Win32 x86 Release build | PASS | `python modernization/renderer/tools/build.py` |
| Full native CTest | **11/11 PASS**, 13.75 s | Final rebuild after Python generator tests |
| Actual observer bridge fixtures | PASS, 61 cases | Ten production x86 bridges, enabled/disabled repeated cases plus nested execution; not the proposed scheduler bridge |
| Native JSON serializer smoke check | PASS | Actual `race_epoch_tests.exe --snapshot-json` output parsed independently as JSON; unsupported host remains unauthorized |
| Compileall | PASS | `python -X pycache_prefix=modernization/renderer/.analysis/pycache -m compileall -q modernization/renderer` |
| Proxy PE verifier | PASS | PE32, I386, required direct exports, no recursive `d3d8.dll` import or delay imports |
| Git whitespace check | PASS | `git diff --check` |

The first full Python run exposed that interface regeneration removed the new
Device8 observer member. The generator was corrected, the full 140-test suite
passed, and all native targets were rebuilt and retested afterwards. Assertions
for previous camera/UI/display/vehicle behavior were not weakened.

Native tests exercise request/success/job/owner generations, stale/duplicate/
unknown callbacks, same-course restart, open/read/decode/fallback failure,
retirement and actor/job pointer reuse, thread/capacity/counter quarantine,
Reset/release revocation, guarded arrays and typed Broker storage, native context
signatures, batch rollback/readback/protection restoration and foreign-hook
ownership. The observer ABI fixtures exercise original-call counts, RET 0/4/8/12,
ECX/EDX, float bits, flags, stack alignment, nonvolatile registers, EAX/EDX,
x87, XMM and MXCSR preservation on the actual production bridges.

## Candidate identity

Build output: `modernization/renderer/.build-msvc/Release/d3d8.dll`

- Size: **1,671,680 bytes**.
- SHA256: `70992f4c1a8ea115f5bee942c7af781bab039740407eb30e85cc78073eb83cb4`.
- PE: **PE32 / I386**; DLL ImageBase `0x10000000`.
- Direct exports: `Direct3DCreate8` ordinal 5, `ValidatePixelShader` ordinal 2,
  `ValidateVertexShader` ordinal 3.
- Imports: `bcrypt.dll`, `USER32.dll`, `KERNEL32.dll`.

Ignored handoff artifacts under this renderer directory:

- `.analysis/handoff/r-cam1-a3c/`: candidate DLL, hash manifest and the exact
  bounded runtime instructions; no replacement INI or game assets.
- `.analysis/archives/r-cam1-a3c-observer-20261010.zip`: runtime handoff archive.
- `.analysis/archives/r-cam1-a3c-source-20261010.zip`: all changed source,
  documentation, tests and bounded research metadata, with SHA256 manifest;
  no DLL/PDB/OBJ/LIB, raw game logs, proprietary binaries or Ghidra database.

## Boundaries still open

The concrete unknown is RaceLimits attachment at VA `0x0048E717` / RVA
`0x0008E717` relative to completion of the corresponding scene-job callback
at VA `0x0052D620` / RVA `0x0012D620`. An owner created after that callback
gets no guessed job lifetime. France1 resource identity must also be reconciled
with the observed scene/source names. A reused job pointer remains unqualified.
Neither supporting RaceState2/offline context nor a diagnostic correlated-owner
candidate grants camera authorization.

Native **scheduler** completion ABI, temporary full-frame camera scope,
Freecam/input controls and restoration tests: **NOT IMPLEMENTED / NOT RUN**.
Existing GameFov interception is unchanged. Passing observer tests does not
prove a race certificate, camera movement, rendering quality, world streaming
or successful live restart. Exclusive remains deferred.

Next evidence is the [single France1 restart capture](runtime-test-plan.md):
offline Quick Race → frontend → the same Quick Race → F10 → normal quit.
No deliberately failed or corrupted load is requested. Close the observed
owner/job relationship before implementing the verified camera bridge.
