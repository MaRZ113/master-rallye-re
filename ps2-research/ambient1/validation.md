# Validation and completion gates

**PS2-AMBIENT1 STATUS: COMPLETE — bounded static/executable reverse.**
**RUNTIME_VALIDATION: NOT_PERFORMED.**

The principal authored-route -> controller -> actual model-world-matrix
contract is recovered. PASS below describes its stated proof boundary;
it does not assert live loading, cadence, pixel visibility or PS2 float bits.

| Gate | Result | Evidence and boundary |
|---|---|---|
| 1 Git discipline | PARTIAL | Correct existing general checkout on master; no branch/worktree created, no historical research or unrelated tracked paths changed. Pre-existing untracked ZIP is absent at closeout; its preservation cannot be confirmed, cause UNKNOWN. See audit below. |
| 2 Provenance | PASS | Exact sizes and SHA256 of all four canonical inputs verified before reading and rechecked at regeneration/closeout; inputs opened read-only. |
| 3 Owner/factory | PASS | Name registration, 0x130 allocation/constructor, prototype lookup, fresh clone, config/init/update virtual slots traced from original ELF. |
| 4 Object layout | PASS | Fields, owned control/time/history containers and external entity/marker/Broker carriers mapped; unknown fields and first-init bank flag retained. |
| 5 XML parameters | PASS | Eleven names/types linked to typed source-order reader, actual field and consumer; missing-after-config zero distinguished from constructor defaults. |
| 6 Marker list | PASS | Exact interned named lookup, source order, 80-byte records and XYZ offsets recovered; Marker No/Dir do not drive this evaluator. |
| 7 Curve algorithm | PASS | Original scalar operations establish uniform Catmull–Rom and time-to-control-index lookup; independent original-word and analytic checks. |
| 8 Sampling/speed | PASS | Chord-derived vs equal-span knots, fixed 1/30 invocation increment, bank-history meaning of samples recovered. Real dispatch/display cadence and dormant unserialized mode remain outside the diagnostic. |
| 9 Loop/endpoint | PASS | Modulo controls, evaluator equality wrap, advance strict overflow/reset, discarded overshoot, open endpoint and extra constant-mode closing hold traced/tested. |
| 10 Trigger lifecycle | PASS | Literal Car0 Broker observer, model-relative XZ distance, strict squared hysteresis, freeze/resume and missing-observer return traced/tested. |
| 11 Rest | PASS | Signed low32 seconds*30, open-only counter/reset and closed precedence recovered; pause freezes counter. |
| 12 Orientation/banking | PASS | Displacement forward, fallback tests, turn-derived ring average, quaternion up and explicit right row recovered. Initial pre-bank +128 and platform libm bit fidelity UNKNOWN. |
| 13 World transform | PASS | Publisher 1aa308 writes all sixteen words of *(entity+50)+20..5c; loader/model binding, affine world consumer and scene submission independently traced. Platform renderer/PSM children/GS pixels not claimed. |
| 14 Cross-instance cases | PASS | Six mandatory named cases reconstructed and compared; all 24 selected authored owners structurally checked without claiming runtime population. |
| 15 Offline reconstruction | PASS | Executable-derived finite-input evaluator, explicit state/observer assumptions, original-word probe, deterministic controller timelines and labeled spatial sweeps. |
| 16 Evidence separation | PASS | Authored/executable/synthetic labels retained; no gameplay trajectory or CONFIRMED_BY_RUNTIME claim. |
| 17 Portability assessment | PASS | Read-only SDK study, minimal future descriptor/hook requirements and per-case duplicate-object hypotheses documented; no PC implementation. |
| 18 Scope discipline | PASS | No bird/rigid-body/grass/water/reflections reverse, PC renderer/hook, SDK edit, course write, asset change or ELF patch. |
| 19 Regression | PASS | Focused/full unittest, available pytest, compileall, diff-check, final input/SDK checks and byte-identical regeneration recorded below. |

## Repository and preservation audit

Primary checkout: `D:\Game\Master Rallye\master-rallye-re-general`, branch
`master`, starting HEAD `6dbf84997cbdef023fe133ee80471d6206c9e73b`.
Preflight tracked tree/index were clean. The only recorded unrelated file was
untracked `ps2-research.zip`, SHA256
`f70cba451793008ab04f3ec737759faa813e1ba6b9dc747b341826f3a38f1e25`.
It is absent at closeout. No phase command opened its contents, deleted or
moved it; disappearance cause is **UNKNOWN**. Do not infer preservation,
deletion by the user, or responsibility from that observation. This limits
Gate 1's preservation audit and does not change the executable evidence.

Reference-only SDK: `D:\Game\Master Rallye\master-rallye-re-course`, branch
`research/r5t-course-archaeology`, HEAD
`4244fa0c4d878523c9947f54816bf377cdfb2589`. Initial/final status clean,
HEAD unchanged. Phase writes are confined to this checkout's `ps2-research`
source, tests, compact metadata, documentation and ignored `data/ambient1`.
No staging/reset/stash of unrelated paths, no original-input writes and no
push. Ending commit identity is resolved in the ignored closeout JSON and
the user-facing closeout; it cannot be embedded as its own content hash.

## Automated checks

| Check | Result | Record |
|---|---|---|
| Existing baseline suite | 98/98 PASS on host | `../data/ambient1/baseline-tests-host.log` |
| Focused spline suite | 32 PASS, zero skips with canonical corpus enabled | `tests/test_spline_runtime.py`; 28 hermetic +4 optional integration |
| Full unittest | 130 PASS, zero skips | `../data/ambient1/full-unittest-host.log` |
| Available pytest | 130 PASS; 158 subtests PASS | `../data/ambient1/full-pytest-host.log` |
| compileall tools/tests | PASS | `python -m compileall ps2-research/tools ps2-research/tests` |
| Working/staged diff-check | PASS | `git diff --check`, `git diff --cached --check` |
| Original ELF basis execution | 24/24 host float32 bit matches | `case-evidence.json` basis_probes; independent original-word decoder |
| Original allocation/virtual slots/world writes | PASS | Canonical integration test decodes effective addresses, 13 SWC1 +3 SW zero and four entity+50 reloads |
| Six-case repeat generation | PASS | Exact SHA equality for metadata, six controller JSONs and six SVGs across consecutive builds |
| Input provenance at closeout | PASS | Full size/SHA checks in Corpus constructor and `case-evidence.json` |
| SDK unchanged | PASS | Same HEAD, clean git status |

The initial sandbox baseline had one `WinError 5` in the existing hardlink
test. A permitted ignored TEMP/TMP directory and automatically approved host
execution passed the unchanged test. That environmental failure was diagnosed,
not weakened or hidden. Canonical integration used
`MASTER_RALLYE_PS2_INPUT=D:\Game\Master Rallye PS2` and the existing UI fixture
root `PS2_UI_CORPUS=ps2-research/data/ui1/extracted/TNG/DATAPSM/HUD`.
Available pytest came from the existing ignored CDELTA1 Python dependency
directory; no package was installed into the repository or game.

Repeat attempts with the bridge's Python 3.11 environment lacked Pillow,
which an existing HUD assembly test needs. The missing-dependency log is
preserved as `../data/ambient1/full-unittest-missing-pillow.log`. Final full
unittest/pytest used the already installed primary Python/Pillow and passed;
no test or assertion was changed to accommodate the environment.

Independent numerical constraints include rational basis polynomials,
collinear interior coordinates, knot/end interpolation, XYZ finite output,
speed-mode contrasts, strict trigger equality, loop/rest precedence,
publish-before-advance, missing observer and independent history buffers.
Malformed/short/nonfinite/duplicate inputs fail closed in the diagnostic;
that is stricter tool policy, not a claim of safe original ELF behavior.

## Runtime and fidelity boundaries

No synchronized PCSX2 video/matrix/tick capture was performed. Existing
individual JPG screenshots provide no temporal owner-state oracle.
The offline runs supply synthetic fixed Car0 coordinates and explicitly
assume first-init bank flag +128=0. Host IEEE float32, sqrt/sin/cos and
original-word probes do not reproduce every R5900 numerical detail.
No actual first heap value, gameplay fault, 30-FPS display rate, visible
object count or matched PC model placement is inferred from those tests.

The one next research recommendation is [PS2-AMBIENT-RUNTIME1](next.md).

## Local research archive

After the research commit, fresh AMBIENT1 raw queries, diagnostics, logs,
metadata and source references are packaged as ignored
`../data/ambient1/ps2-ambient1-research-bundle.zip`. Its manifest records the
actual commit, canonical fingerprints, runtime boundary and each member's
SHA256. Temporary directories, dependency binaries, Ghidra projects and
original game containers/ELF are excluded. Archive integrity and member
hashes are checked after writing; the local closeout JSON records archive
path/hash. It is a local handoff artifact, not part of the Git commit.
