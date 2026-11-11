# R-MOD1-D implementation validation

The earlier sections are historical v4-v8 validation records. Current v9
R-MOD1-D results are at the end of this file; do not use older candidate
identities or counts as current status.

## Build identity and scope

- Branch: `research/r-mod1`.
- Source HEAD: `ea3012a1481cf1d2f8ed3401eedc995c96dbcfb9` (`fix: scope R-MOD1 review archive to project files`); the review archive index records the final worktree state.
- Supported retail image: I386 / PE32, 3,121,214 bytes, SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
- Human-test package: `.research-output/r-mod1/first-integrated-candidate-v4/` (ignored runtime output; never commit or include in the source archive).
- Candidate qualification marker: `STATIC_CANDIDATE_NOT_HUMAN_RUNTIME_QUALIFIED`.
- No game process was launched. Vehicle SDK files, the renderer proxy, the on-disk game EXE, game assets and user saves were not modified.

## Verification results

| Check | Result |
|---|---|
| Full synthetic suite, external writable TEMP/TMP | **616 passed, 0 failed, 0 errors, 0 skipped** |
| Focused R-MOD1 synthetic tests | **9 passed, 0 failed, 0 skipped** |
| Native shared-core MSVC x86 harness | **101 checks, 0 failures** |
| Python compileall | **passed** |
| MSVC runtime-core DLL build | x86, `/W4 /WX /Brepro`, passed |
| MSVC launcher build | x64, `/W4 /WX /Brepro`, passed |
| Exact-retail launcher `--verify` | passed; no game process created |
| Candidate package checker | passed: package hashes, plan regeneration, exact-build positive, missing/wrong-size/wrong-hash EXE negatives, altered DLL negative, invalid/oversized/missing INI safe defaults |
| Candidate reproducibility | independently built v3 and v4 manifests contain identical SHA256/size rows for all 7 package files |
| Generated native plan | 7 operations; exact preimages, no operation/code/data overlaps; deterministic plan/template hashes |
| `git diff --check` | passed; Git prints only its LF-to-CRLF working-copy notices |
| DInput proxy / renderer runtime matrix / game runtime | not run; human/runtime gates remain pending |

The successful full-suite run was:

```powershell
$env:TEMP = '<approved writable scratch directory outside the repository parent>'
$env:TMP = $env:TEMP
$env:PYTHONPATH = 'src'
python -m unittest discover -s tests/synthetic -v
```

That final run ended `Ran 616 tests ... OK`. An earlier attempt put the temporary
directory under `D:\Game\Master Rallye`; several strict Windows
`Path.resolve()` operations received `Access denied`, and one Observatory test
rejected extraction under the repository parent. That environment attempt
reported 615 run, 1 failure and 11 errors. Re-running with the approved
external scratch path passed all 616 tests; no product source was changed to
work around the path policy.

## v7 randomizer callback hotfix validation

The v6 randomizer-only crash is statically localized to the choice callback
gateway. The emitted gateway was `FF 15 08 00 01 70 C3`: it nested a `CALL`
around the four-argument `WINAPI MRChooseClassV1`, whose `RET 16` then returned
to the gateway and let its trailing `RET` consume AI slot 1 as EIP. The v7
gateway is `FF 25 08 00 01 70`, which tail-forwards the existing stdcall frame
so the native callback returns directly to the selector. The actual emitted
selector and gateway bytes are symbolically tested. A separate ABI correction
matches the audited no-argument cdecl progress-state singleton at `0x004B0310`.

The v6 decoded record reports Randomizer plus logging (`config_flags=5`),
Opponent Extender disabled, `start_phase=idle`, and `EIP=0x1`. This localizes
that captured exception to the randomizer selector path, before the opponent
Start guard. The supplied raw sidecar was not available for independent hash
verification. Its reported exception parameters `[0,1]` indicate a read at
address 1 and remain inconsistent with an instruction-fetch fault at EIP 1;
the discrepancy is preserved. The decoded register snapshot is
`EAX=FFFFFFFF EBX=0 ECX=94CAD48D EDX=30000 ESI=1 EDI=FFFFFFFF EBP=4
EFLAGS=10246 ESP=001AFC80 EIP=1`; its symbolic frame list is empty, while the
32 raw stack DWORDs are captured in the regression fixture. The earlier v5 Start report lacks a phase/EIP
record, so the opponent-extender-only and combined Start paths remain
unqualified. v7 does not change Start admission policy.

Candidate `first-integrated-candidate-v7` is at
`.research-output/r-mod1/first-integrated-candidate-v7/`. Its exact retail
source is `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`
(3,121,214 bytes). Candidate artifacts:

| Artifact | Size | SHA256 |
|---|---:|---|
| `MRallyeRandomizerLauncher.exe` | 377,856 | `e617e6ebdb2a83b5a464d751bafe5acf1f1692f37698ebe0d56f6ba3f754109d` |
| `MRallyeRandomizerRuntime.dll` | 129,024 | `a2365afaa4adabd59414ee74d286b1a1d3c827ef124d7b31963d58d60f691cea` |
| `MRallyeRandomizer.ini` | 197 | `beacb9bf79e98167efdeb41b4ea77c19e43f7f85bc71a495645c8d4eaf1c3c9d` |
| `native-patch-plan.json` | 6,068 | `ebd8bf254ac93e0c1c8ee8dd3b507fb603f3e5bf8aa2a546c3c930a897506fa0` |

The seven-operation plan identity is
`aa23bde77e221899645cd4c6e7893ce8d6bb801ef743dcf034c1c71ffb325ac9` and its
manifest SHA256 is
`0af5cf92e5fc895015c09fe86fce5327f40f93a7a1d6876e9fa9f477b861576a`.
Candidate verification checked package hashes, native plan boundaries and
regeneration, exact-build acceptance, and missing/wrong-size/wrong-hash EXE,
altered DLL, and malformed/oversized/missing INI rejection. Its status was
`CANDIDATE_STATIC_AND_NEGATIVE_PATHS_PASS`. The Windows suspended-process
preflight reported `SUSPENDED_PREFLIGHT_PASS`, verified image base `0x400000`,
size `0x311000`, `MEM_IMAGE`/`MEM_COMMIT` and executable-section bytes, made
zero native writes, and terminated the child before resume. v7 has not been
resumed into the game and is not human-runtime-qualified.

| v7 check | Result |
|---|---|
| Full synthetic suite | **625 run; 624 passed, 0 failed, 0 errors, 1 skipped** |
| Focused composition/native-plan/diagnostics/preflight suite | **17 run; 16 passed, 0 failed, 1 skipped** |
| Native shared-core MSVC x86 harness | **118 checks, 0 failures** |
| `python -m compileall -q src tools tests` | **passed** |
| `git diff --check` | **passed**, with only Git LF-to-CRLF notices |
| Exact-build/package/negative-path candidate checker | **passed**, 7 operations |
| Real Windows suspended-image preflight | **passed before native writes; child terminated before resume** |
| Independent MSVC candidate rebuild | **passed; all 13 package file SHA256/size rows matched v7** |
| v7 in-game runtime | **not run; human retest pending** |

The full-suite output is retained at
`.research-output/r-mod1/full-suite-v7.txt` in ignored local research output.
The focused command was:

```powershell
$env:PYTHONPATH = 'src'
python -m unittest tests.synthetic.test_r_mod1_composition tests.synthetic.test_r_mod1_native_plan tests.synthetic.test_r_mod1_diagnostics tests.synthetic.test_r_mod1_suspended_preflight -v
```

The complete checkout suite was:

```powershell
$env:PYTHONPATH = 'src'
python -m unittest discover -s tests/synthetic -v
```

The one skipped test is the opt-in live game suspended-child test; its purpose
is to create and terminate the exact retail child, not to launch gameplay. The
candidate checker did run the suspended-process preflight on this host and
passed. The v7 runtime candidate is ready for the bounded human Randomizer-only
Quick Race retest in [`runtime-handoff.md`](runtime-handoff.md), using only
one to three AI. Do not interpret the prior v6 UI human pass or v7 preflight as
a v7 gameplay pass.

Other final commands:

```powershell
$env:PYTHONPATH = 'src'
python -m unittest discover -s tests/synthetic -p 'test_r_mod1_*.py' -v
.\tools\r_mod1_core_tests.ps1
python -m compileall -q src tools tests
python tools/test_r_mod1_candidate.py `
  .research-output/r-mod1/first-integrated-candidate-v4 `
  --retail-exe 'D:\Game\Master Rallye\corpora\retail\MRallye.exe'
git diff --check
```

The candidate checker regenerates `native-patch-plan.json` from the exact
external retail bytes and packaged DLL, then exercises read-only launcher
verification and its negative paths. The plan and DLL are pinned by the
candidate manifest. The launcher executable's `--verify` is not evidence that
`CreateProcess(CREATE_SUSPENDED)`, remote memory installation or game startup
works.

## Candidate identity

The manifest in the ignored package is authoritative for per-file hashes.
The generated native plan template SHA256 is
`1fd069633eae8713aa8cf2fbb0740a61170db57d36bf4683cdc30a1d79b9bc4f` and
contains seven operations. The launcher/runtime/plan file hashes are copied to
[`patch-plan.status.json`](patch-plan.status.json). No patched executable is
produced.

## Evidence boundary and status

Static source analysis, compilation, native synthetic harnesses, package
verification and fail-closed negative cases are complete. They do not prove
the candidate can reach the frontend, that installed hooks execute correctly,
that a race is safe, or that a graphical `d3d8.dll` proxy coexists. The
external launcher candidate is **READY FOR HUMAN RUNTIME** only within the
five-total Track10/T1/ID0/Ghost-off/no-SplitScreen envelope documented in
[`grid-safety.md`](grid-safety.md). Counts above four AI remain refused at
Start. R-MOD1 is not a qualified public beta; DInput proxy and renderer matrix
remain unsupported/pending.

## Suspended image-mapping hotfix — v5

The v4 `CreateToolhelp32Snapshot(TH32CS_SNAPMODULE...)` preflight failed on a
suspended retail child with Windows error 299 because loader state was not
ready. The v5 launcher no longer enumerates modules before resume. It uses the
audited fixed PE image base and validates the full `SizeOfImage` mapping with
`VirtualQueryEx`, then checks mapped PE headers and complete executable
sections before native writes. No resume, wait/retry, or unverified-base
fallback is used. Original executable path/hash, x86, preimage,
protection/readback, and fail-closed termination checks remain in force.

The actual suspended-process test was attempted with the pristine retail
executable at `D:\Game\Master Rallye Pristine\MRallye.exe`. On this host,
`CreateProcessW(CREATE_SUSPENDED)` fails first with error 623
(`ERROR_ILLEGAL_DLL_RELOCATION`), before a child process or mapped image exists.
The test is therefore **BLOCKED_ENVIRONMENT_CREATEPROCESS_ERROR_623**; this is
not a mapping pass and the candidate must not be used for a game launch until
`--preflight` reports `SUSPENDED_PREFLIGHT_PASS` on a compatible Windows host.

The v5 package is `.research-output/r-mod1/first-integrated-candidate-v5/`.
Its source executable identity remains the exact 3,121,214-byte retail image
with SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
The launcher SHA256 is
`df22ff6f9e455977339358804f73112639686b798420d92baccb4acb7736a713`
(377,856 bytes). The runtime DLL is unchanged from v4 at
`432c72f4958bea4c9547799251e1c225df23a3e0ef032007fcebaa2f60a80fde`, the INI
is unchanged at `81d626ef74b0024ab4023a69084c47c7eb672a9db7fbde75b2650d66233212e7`,
and the seven-operation native plan is unchanged at
`e823fa7943f58aae16e8114c7ee46e11354d2d710f9eb8ec2ac32e80f8b83aaf`.
The v5 candidate manifest SHA256 is
`e6a631cca2188896b8e17915f78e8bfd23f6d11af0f5c5fc873f5a1bcc82e2bd`.

Verification for this hotfix:

| Check | Result |
|---|---|
| Full synthetic suite | **618 passed, 0 failed, 1 skipped** |
| Focused R-MOD1 tests | **10 passed, 0 failed, 1 skipped** |
| Opt-in real Windows suspended preflight | attempted; **1 skipped** because CreateProcessW returned error 623 before mapping |
| Native shared-core MSVC x86 harness | **108 checks, 0 failures** |
| `python -m compileall -q src tools tests` | passed |
| Candidate package checker | static checks passed; status `CANDIDATE_STATIC_PASS_SUSPENDED_PREFLIGHT_BLOCKED`; 7 native operations |
| `git diff --check` | passed; only Git LF-to-CRLF working-copy notices |

The focused test command is `python -m unittest discover -s tests/synthetic -p
'test_r_mod1_*.py' -v`. The full suite used an approved external writable
`TEMP`/`TMP` and `PYTHONPATH=src`. The opt-in live attempt used
`RMOD1_RUN_WINDOWS_PREFLIGHT=1`, the v5 package, and the pristine retail path
above. `--verify` passed but remains a file/package verifier, not a substitute
for the suspended-process gate.

**Current status:** v5 is packaged for preflight on a compatible Windows host,
but suspended mapping verification, human game launch, and runtime patch
installation remain unqualified. If `--preflight` fails or reports anything
other than `SUSPENDED_PREFLIGHT_PASS`, stop without launching the modded game.

## v6 Change Mode correction and race-start exception localization

The owner subsequently reported that v5 passed retail/runtime verification,
installed all seven native operations and resumed, then produced two distinct
failures: opening Change Mode hung with exit code `0xCFFFFFFF`, and Quick Race
start raised `0xC0000005`. The retail executable remained unchanged. This is
owner-reported runtime evidence for v5, not qualification of v6.

The Change Mode root cause is statically confirmed in the emitted helper. One
stack DWORD held the configured list upper bound while the enString constructor
used that same effective address as its temporary object. The v6 helper
allocates separate bound/object slots, preserves the historic StringList
object lifetime, balances native callee cleanup, and restores the entry stack
before replaying the displaced instruction. The regression test decodes the
actual emitted bytes, symbolizes ESP at constructor/destructor/insertion and
loop comparison, checks the bound is not overwritten, and verifies the labels
One through Seven are appended once.

The Start AV is still **UNLOCALIZED**. No v5 exception record, faulting EIP,
register context or call stack was available, and Windows Event Log inspection
was unavailable in this environment. The existing Start allow/block policy
remains unchanged. v6 adds an opt-in first-chance AV record and explicit phase
markers around guard decision, the original Quick Race setup call and prepared
roster validation. A controlled x86 harness verified that an AV record is
captured while the exception remains catchable; this does not reproduce or
localize the game AV.

The v6 candidate is
`.research-output/r-mod1/first-integrated-candidate-v6/` and remains
`STATIC_CANDIDATE_NOT_HUMAN_RUNTIME_QUALIFIED`. Its launcher SHA256 is
`6021cb35e20bf0ff2f8d36f64f845ddb2168c19bf5be48ac5aa207cfde96404d`, runtime
DLL SHA256 is
`dfa4a67695450f7df545cb5d59f1d6367b18a2abaafe152b2eba81f3f067d07b`, native
plan file SHA256 is
`b2edd225257a53bbe24c6c83a944f8907934ebab5549933850e0259a4c2277cb`, and
runtime plan identity is
`ffd84c04d94552a7af2673b57dd7fba775f6420ee33cbf4e9dfb30bf367cbae9`. The
candidate retains seven operations and the v5 suspended `VirtualQueryEx`
mapping hotfix. The local v6 `--preflight` attempt again received Windows
error 623 from `CreateProcessW` before child creation; it did not verify a
mapped child and did not install operations. The package verifier completed
with `--allow-preflight-blocked` and reports
`CANDIDATE_STATIC_PASS_SUSPENDED_PREFLIGHT_BLOCKED`.

The v6 human handoff first checks Change Mode with a menu-only Seven profile,
then compares four separate configurations at three AI or fewer: both
features disabled, randomizer only, opponent extender only, and both enabled.
It requests preservation of `MRallyeRandomizer-crash-v1.bin` if the AV recurs.
Do not change Start code until this evidence identifies the failing phase and
faulting instruction.

### v6 verification results

| Check | Result |
|---|---|
| Full synthetic suite | **624 run; 623 passed, 0 failed, 0 errors, 1 skipped** |
| Focused native-plan / diagnostics / composition / preflight suite | **16 run; 15 passed, 0 failed, 1 skipped** |
| Native shared-core MSVC x86 harness | **118 checks, 0 failures** |
| Controlled x86 runtime exception harness | **passed:** first-chance AV record captured and remained catchable |
| Python `compileall` | **passed** |
| `git diff --check` | **passed after removing Markdown trailing whitespace** |
| v6 exact-build/package checker | **passed static and negative paths; `CANDIDATE_STATIC_PASS_SUSPENDED_PREFLIGHT_BLOCKED`** |
| Real v6 suspended-process preflight on this host | **blocked:** `CreateProcessW` error 623 before child creation |
| Independent v6 deterministic rebuild | **passed:** every packaged file matched SHA256 and size |
| Review-archive deterministic/hash-index test | **passed** |

The skipped test is the opt-in real Windows suspended-child test; it requires
`RMOD1_RUN_WINDOWS_PREFLIGHT=1`. The package checker was run with
`--allow-preflight-blocked`, which records the host's error 623 while still
running package, exact-build, plan-regeneration and negative-path checks. It
does not convert the blocked preflight into a pass. The full suite used
`PYTHONPATH=src` and an external writable `TEMP`/`TMP` directory to avoid this
Windows sandbox's temporary-directory ACL failures.

The focused command was:

```powershell
$env:PYTHONPATH = 'src'
python -m unittest tests.synthetic.test_r_mod1_composition tests.synthetic.test_r_mod1_native_plan tests.synthetic.test_r_mod1_diagnostics tests.synthetic.test_r_mod1_suspended_preflight -v
```

The authoritative full-suite command was:

```powershell
$env:PYTHONPATH = 'src'
python -m unittest discover -s tests/synthetic -v
```

The v6 build used `tools/build_r_mod1_candidate.py` with the exact external
retail input and `--package-on-preflight-error-623`. The second build was
written to a separate ignored output directory; recursive file SHA256/size
comparison returned no differences. Candidate hashes and the exact human
sequence are recorded in [`runtime-handoff.md`](runtime-handoff.md). The v5
rows above remain historical; v6 still requires human runtime testing.

## R-MOD1-C v8 numeric INI and combined feature candidate

Candidate `first-integrated-candidate-v8` is at
`.research-output/r-mod1/first-integrated-candidate-v8/`. It is built from the
exact pristine 3,121,214-byte retail image with SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
Candidate status is `STATIC_CANDIDATE_NOT_HUMAN_RUNTIME_QUALIFIED`.

| Artifact | Size | SHA256 |
|---|---:|---|
| `MRallyeRandomizerLauncher.exe` | 385,024 | `04655e39b4c07ed0d30bf48ec343188b82b65adbf18e5965409f3fc29d1e7197` |
| `MRallyeRandomizerRuntime.dll` | 135,168 | `8dc8a75944773918dba726cf356263b11fe3fd7ed96c36606cf74efefd6a906a` |
| `MRallyeRandomizer.ini` | 1,620 | `aabb713a528456a027c7f44b88c4d55cd704537f2a8548e7fd4fd06b73549e9b` |
| `native-patch-plan.json` | 6,068 | `f4621735a7afcf29788d2d900bb92aac049b9d5eed4172e063962b21f3710d6b` |

The runtime plan identity is
`b9ff8520d1927439c0783a12bbc6300b65b9d31e73c05537639b3b2520a629ba`; the
candidate manifest SHA256 is
`dbd0bdd46db5603cace2e87944528e4f8a2b1ba69d97d9ffeeeb6f56f8b310a85`.
The native plan still contains seven non-overlapping operations: four shared
bootstrap operations, one Randomizer operation and two Opponent Extender
operations. Numeric INI selectors 0..6 map to Stock, Full, T1, T2, T3, Mixed
and Diverse. Boolean and duplicate policy numeric values are strict, and
malformed/missing/oversized configuration falls back as a whole to the safe
stock defaults. The launcher `--verify` was exercised with the safe defaults
and each of the six non-Stock numeric policy profiles.

### v8 validation results

| Check | Result |
|---|---|
| Full synthetic suite | **625 run; 624 passed, 0 failed, 0 errors, 1 skipped** |
| Focused R-MOD1 suite | **18 run; 17 passed, 0 failed, 1 skipped** |
| Native shared-core MSVC x86 harness | **158 checks, 0 failures** |
| Python `compileall` | **passed** |
| `git diff --check` | **passed**; only Git LF-to-CRLF notices |
| Exact-build candidate checker | **passed**, including seven-operation ownership/range checks and wrong/missing build, DLL and INI cases |
| Windows suspended-image preflight | **passed before native writes; child terminated before resume** |
| Deterministic candidate rebuild | **passed; all 15 package files matched SHA256 and size** |
| Original retail EXE | **unchanged; exact pinned SHA verified** |

The one skipped test is the opt-in real suspended-child test in the synthetic
suite (`RMOD1_RUN_WINDOWS_PREFLIGHT=1`). The candidate checker separately
performed the Windows suspended-process preflight and passed the fixed-base
image mapping validation before any native writes. The full-suite command was:

```powershell
$env:PYTHONPATH = 'src'
python -m unittest discover -s tests/synthetic -v
```

Focused R-MOD1 tests were:

```powershell
$env:PYTHONPATH = 'src'
python -m unittest tests.synthetic.test_r_mod1_core tests.synthetic.test_r_mod1_diagnostics tests.synthetic.test_r_mod1_native_plan tests.synthetic.test_r_mod1_composition tests.synthetic.test_r_mod1_suspended_preflight -v
.\tools\r_mod1_core_tests.ps1
python -m compileall -q src tools tests
git diff --check
```

The package checker command was:

```powershell
python tools/test_r_mod1_candidate.py .research-output\r-mod1\first-integrated-candidate-v8 `
  --retail-exe 'D:\Game\Master Rallye\corpora\retail\MRallye.exe'
```

An independent build into
`.research-output/r-mod1/first-integrated-candidate-v8-rebuild/` produced 15
files with byte-identical hashes and sizes. The exact human procedure and
feature-isolation INI profiles are in [`runtime-handoff.md`](runtime-handoff.md).
The previous v7 Randomizer-only normal-count result and v6 UI checks remain
separate historical human evidence; no combined v8 race, Results, renderer
coexistence or four-AI runtime pass is claimed.

## R-MOD1-D v9 topology correction and five-total candidate

Candidate `first-integrated-candidate-v9-final` is at
`.research-output/r-mod1/first-integrated-candidate-v9-final/`. It is rebuilt
from the exact pristine retail image and retains the seven-operation R-MOD1-C
bundle. The only participant allowance is experimental Four AI / five total;
Five through Seven AI remain refused before native setup.

The v8 denial log's `Frontend/SplitScreen=1` did not contain post-setup
`Race/NumPlayers` or `PlayerType` evidence. Exact-retail Ghidra analysis shows
the flag is read in `FUN_0047B780`, but only the resulting native Race state can
prove active participants. Candidate v9 therefore logs the raw bit, defers
effective player count until native setup returns, reads `Race/NumCars` and
`Race/NumPlayers`, then inspects only active CarN slots. The experimental
transition requires exactly one human and four AI. It does not bypass an
unsupported topology; it measures the native topology and refuses the screen
transition when the result differs.

The five-participant path does not import R-AI2.1's separate six-to-eight
deterministic-roster patch. R-AI2.1 changed two frontend count reads and its
fixed-roster/chooser boundary; its manifest says participant arrays were not
expanded and loops were not widened. R-AI2 proved the five-car native
lifecycle, and R-UI1 proved visible Four publishes count 4 into the native
five-car setup. Candidate v9 keeps the retail CarID and DriverID selector and
uses the original count-driven participant pipeline.

| Check | Result |
|---|---|
| Full synthetic suite | **626 run; 625 passed, 0 failed, 0 errors, 1 skipped** |
| Focused R-MOD1 suite | **19 run; 18 passed, 0 failed, 1 skipped** |
| Native shared-core MSVC x86 harness | **163 checks, 0 failures** |
| Python `compileall -q src tools tests` | **passed** |
| `git diff --check` | **passed**; Git emitted only configured LF-to-CRLF notices |
| Candidate verifier | **passed**; seven operations, package hashes, exact-plan regeneration, six profile/config checks and negative build/DLL/INI paths |
| Windows suspended image preflight | **passed before native writes; child terminated before resume** |
| Deterministic candidate rebuild | **15/15 files byte-identical** |
| Retail executable on disk | **unchanged; SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`** |
| Human gameplay | **pending; candidate was not launched into gameplay by this validation** |

The single skipped test is the opt-in synthetic real suspended-child test. The
candidate builder and independent candidate verifier each separately executed
the Windows suspended-process `--preflight` successfully. The focused command
was:

```powershell
$env:PYTHONPATH = 'src'
python -m unittest tests.synthetic.test_r_mod1_core tests.synthetic.test_r_mod1_diagnostics tests.synthetic.test_r_mod1_native_plan tests.synthetic.test_r_mod1_composition tests.synthetic.test_r_mod1_suspended_preflight -v
.\tools\r_mod1_core_tests.ps1
python -m compileall -q src tools tests
git diff --check
```

The full-suite command was:

```powershell
$env:PYTHONPATH = 'src'
python -m unittest discover -s tests/synthetic -v
```

Candidate verification and deterministic rebuild commands:

```powershell
python tools/test_r_mod1_candidate.py .research-output\r-mod1\first-integrated-candidate-v9-final `
  --retail-exe 'D:\Game\Master Rallye\corpora\retail\MRallye.exe'
python tools/build_r_mod1_candidate.py `
  --retail-exe 'D:\Game\Master Rallye\corpora\retail\MRallye.exe' `
  --output .research-output\r-mod1\first-integrated-candidate-v9-final-rebuild
```

All 15 generated package files matched SHA256 and size between the primary and
rebuild candidate. `runtime-handoff.md` contains the final artifact hashes and
the minimal Four-AI human test. No six-to-eight race, SplitScreen-expanded
race, renderer-proxy compatibility or human gameplay result is claimed.

## R-MOD1-D v10 Start-button hotfix and five-total candidate

The v9 Start failure was caused by a post-setup roster validator returning
through the parent callback epilogue before the original state-10 transition.
The v9 `actual_race_numcars=0` and `actual_race_numplayers=0` fields were read
from the default `NativeRosterSnapshot` when validation failed; they do not
prove the native accessors returned zero. v10 removes this veto, keeps the
bounded pre-start checks, calls `FUN_0047B780` exactly once on the allowed path,
and continues at `0x0047AD11`. A read-only observer at the later native
NumCars consumer `FUN_00408660` logs raw counters and safely bounded CarN
identity values. It never mutates state or blocks Start.

The logger now uses append-only file access, process-local serialization, one
record per CRLF-terminated write and bounded 64 KiB rotation. Its x86 Windows
harness confirms CONFIG, START and ROSTER records remain intact and
chronological. The v10 candidate was built from the exact pristine retail
image; no research-patched executable was used.

| Check | Result |
|---|---|
| Full synthetic suite | **629 run; 628 passed, 0 failed, 0 errors, 1 skipped** |
| Skipped test | Opt-in real suspended-child synthetic test (`RMOD1_RUN_WINDOWS_PREFLIGHT=1`); candidate builder and independent package verifier each separately passed the real Windows preflight |
| Focused native-plan tests | **14 passed**; emitted Start and observer machine-code/ABI checks, exact retail call bytes and raw-count telemetry bounds |
| Focused runtime logger source test | **1 passed** |
| Native shared-core MSVC x86 harness | **163 checks, 0 failures** |
| Runtime exception x86 harness | **passed** |
| Runtime logger x86 harness | **passed**; CONFIG/START/ROSTER intact and chronological |
| Python `compileall -q src tools tests` | **passed** |
| `git diff --check` | **passed**; only configured LF-to-CRLF notices |
| Candidate verifier | **passed**; eight non-overlapping operations, profile checks, retail/DLL/INI negative paths, deterministic plan regeneration |
| Windows suspended image preflight | **passed before native writes; child terminated before resume** |
| Independent deterministic rebuild | **16/16 package files byte-identical** |
| Retail executable on disk | **unchanged; SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`** |
| Human Four-AI race | **pending; v10 has not been launched into gameplay** |

Candidate directory:
`.research-output/r-mod1/first-integrated-candidate-v10/`.

| Artifact | Size | SHA256 |
|---|---:|---|
| Launcher | 388,608 | `bba29dc661a2a43c40d518369d52f2125e31a560b7b94519c1d8f95c2b41a568` |
| Runtime DLL | 139,264 | `f31521d601e782544bce7c7f950bbafe346578c6a972c4a2ff0987e1e959e5e1` |
| Safe default INI | 1,919 | `1f3c4e34f397b27ca16fac8b878d9501b65e8a56e4342a4fc00352031df4684e` |
| Native patch plan | 6,634 | `5db960c417acb05b5a4ec89a31199d0c59ae9e8a3a0a14acd834897a483bcc8e` |
| Runtime plan identity | — | `e3e1a2778a0b9e0bb32cba08de111ebe9154132069a3200d6c849efdda7dc1a9` |
| Candidate manifest | — | `a6a31de7aa9de71204d047c597299a862a25cf342e81b3fdd1384144f0b7a2b4` |

Commands used:

```powershell
$env:PYTHONPATH = 'src'
python -m unittest discover -s tests/synthetic -v
python -m compileall -q src tools tests
git diff --check
.\tools\r_mod1_core_tests.ps1
python tools/test_r_mod1_candidate.py .research-output\r-mod1\first-integrated-candidate-v10 `
  --retail-exe 'D:\Game\Master Rallye\corpora\retail\MRallye.exe'
```

See [`start-button-v10-hotfix.md`](start-button-v10-hotfix.md) for the
historical v10 timing analysis. V10 was later **FAILED_BY_HUMAN_RUNTIME**;
the v11 section below is the current candidate status. Five active
participants, AI movement, Results and frontend return remain unproven until
owner testing.

## R-MOD1-D v11 observer ABI hotfix — runtime reference

V10 was subsequently **FAILED_BY_HUMAN_RUNTIME** with an Access Violation in
the new race-scene observer. V11 removes that observer and leaves the native
getter CALL bytes unchanged. It preserves the setup-once Start transition,
append-only logger, exact-build launcher and suspended-image preflight. The
owner later confirmed a live one-human/four-AI Quick Race with five active
participants in v11. This did not newly establish finish/Results/Replay.

| Check | Result |
|---|---|
| Full synthetic suite at v11 closeout | **629 run; 628 passed, 0 failed, 0 errors, 1 skipped** |
| Skipped test | Opt-in real suspended-child synthetic test; v11 candidate builder and independent package verifier both passed real Windows preflight |
| Focused emitted-code / ABI tests at v11 closeout | **14 passed**; direct `CALL` vs nested wrapper stack arguments, direct return address, `RET 4` cleanup, untouched retail preimage, seven-op bundle and Start ABI |
| Runtime log focused test | **1 passed** |
| Native shared-core x86 harness | **163 checks, 0 failures** |
| Runtime exception x86 harness | **passed** |
| Runtime append-only logger x86 harness | **passed** |
| Python `compileall -q src tools tests` | **passed** |
| `git diff --check` | **passed**; Git reports only configured LF-to-CRLF notices |
| Candidate package verifier | **passed**; seven non-overlapping operations, no observer, exact retail bytes, package hashes, profiles and negative paths |
| Windows suspended image preflight | **passed before native writes; child terminated before resume** |
| Deterministic candidate rebuild | **passed; 16/16 package files byte-identical** |
| Retail executable on disk | **unchanged; SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`** |
| Four-AI/five-participant participant presence | **owner-confirmed runtime pass; separate from Observatory compatibility** |
| Finish/Results/Replay lifecycle | **not newly evidenced in the supplied v11 runtime report** |

V11 candidate directory: `.research-output/r-mod1/first-integrated-candidate-v11/`.
It remains unchanged as the four-AI runtime reference.

## R-MOD1-E v12 generalized Quick Race candidate

V12 generalizes the explicit experimental Start gate to selected counts 4..7
AI (5..8 total). It uses progressive `MaxOpponents` profiles, retains the
seven-operation patch plan, leaves the count-reader/caller and physical
CarID/DriverID/refill body in the native chooser intact, and refuses extended
SplitScreen topology. Ghidra and exact retail bytes show a count-driven native
per-slot loop and class-pool refill; this is static behavior evidence, not
repeated-ID gameplay qualification.

| Check | Result |
|---|---|
| Full synthetic suite | **630 run; 629 passed, 0 failed, 0 errors, 1 skipped** |
| Skipped test | Opt-in real suspended-child synthetic test; separate v12 builder/package verifier Windows preflights passed |
| Focused native-plan/emitted-code tests | **15 passed** |
| Native shared-core x86 harness | **221 checks, 0 failures** |
| Python `compileall src tools tests` | **passed** |
| `git diff --check` | **passed**; configured LF-to-CRLF notices only |
| Candidate package verifier | **passed**; seven non-overlapping operations, exact retail plan reconstruction and positive/negative paths |
| Windows suspended image preflight | **passed before native writes; child terminated before resume** |
| Deterministic rebuild | **passed; 20/20 package files byte-identical** |
| v12 gameplay counts 5–7 AI | **pending human runtime** |
| Repeated-ID race lifecycle | **static chooser pass; pending human runtime** |
| Renderer interoperability / DLL proxy | **not tested / not started** |

Exact v12 candidate and plan hashes are in
[`candidate-v12-manifest.json`](candidate-v12-manifest.json) and
[`native-patch-plan-v12.json`](native-patch-plan-v12.json). Commands and output
summary are in [`validation-v12.txt`](validation-v12.txt).

## R-MOD1-E v13 false SplitScreen veto correction

Human testing showed that v12 denied five AI because the raw frontend
`SplitScreen=1` flag was treated as proof of two active humans. The owner's
previous v11 race had the same raw flag and produced one human plus four AI.
V13 removes this single pre-setup veto. It retains the raw flag in diagnostics,
keeps the native count/setup and chooser paths, and does not add a post-setup
observer or roster veto. Actual topology is verified from Race/NumPlayers and
participant PlayerType after setup; the two-human synthetic roster fails the
one-human qualification oracle.

| Check | Result |
|---|---|
| Full synthetic suite | Final run recorded in [`validation-v13.txt`](validation-v13.txt) |
| Numeric INI and independent feature controls | **unchanged and package-verified** |
| Native count/Start ABI and seven operation preimages | **verified against exact retail build** |
| Package verification / negative paths | **passed** |
| Launcher `--verify` | **passed** |
| Windows suspended `--preflight` | **passed before native writes; child terminated before resume** |
| Deterministic rebuild | **20/20 package files byte-identical** |
| Five AI + one human in gameplay | **pending owner runtime** |

The v13 candidate uses the exact pristine retail SHA256 and leaves the on-disk
executable unchanged. Its first human test is five AI plus one human with the
`experimental-six-total-t1.ini` profile; capture six initialized participant
slots and verify `Race/NumPlayers=1`. V13 is not gameplay-runtime-qualified.
Candidate identities and test commands are in
[`candidate-v13-manifest.json`](candidate-v13-manifest.json),
[`native-patch-plan-v13.json`](native-patch-plan-v13.json), and
[`validation-v13.txt`](validation-v13.txt).

## R-MOD1-F1/F2/F3 separate static closeout

F1, F2 and F3 were built as separate, cumulative checkpoint packages and were
not merged into one candidate. Each passed package verification, exact-retail
plan regeneration, launcher `--verify`, and real Windows suspended
`--preflight` before native writes. Rebuild comparison matched all 17/17
manifest-listed file hashes and sizes for every checkpoint. Candidate runtime
testing remains pending; these checks do not establish new game-mode gameplay
passes.

| Validation | Result |
|---|---|
| Focused R-MOD1 modules | 25 run; 24 passed; 0 failed; 1 opt-in suspended-child test skipped |
| Native shared-core x86 harness | 257 checks; 0 failures |
| Full synthetic suite | 632 run; 631 passed; 0 failed; 0 errors; 1 opt-in suspended-child test skipped |
| Python compileall | Passed |
| `git diff --check` | Passed; configured LF-to-CRLF notices only |
| Candidate/package verification | F1/F2/F3 passed, 7/13/17 non-overlapping native operations respectively |
| Windows suspended preflight | F1/F2/F3 each passed before native writes; child terminated before resume |
| Deterministic rebuild | F1 17/17; F2 17/17; F3 17/17 package files matched |
| Retail executable | SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`; unchanged |

Exact checkpoint identities and reproduction commands are in
[`status.md`](status.md) and [`validation-f1-f3.md`](validation-f1-f3.md).
