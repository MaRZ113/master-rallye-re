# R-CAM1-A3j.3a — Exact retail physics-probe context correction

## Finding and correction

The supplied runtime session `session-20261011-065112-40800.jsonl` recorded `requested=true`, `exact_retail_build=true`, `installed=false`, and `reason=exact_call_context_mismatch`. The local `D:\Game\Master Rallye\MRallye.exe` was verified as the pristine retail image: 3,121,214 bytes, SHA-256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.

The expected substep-tail context was truncated and incorrectly placed the final `CALL` immediately after `57 8B CE`. At VA `0x0043F8DC` / RVA `0x0003F8DC`, the retail `.text` contains this complete 25-byte sequence:

```text
57 8B CE E8 1C 03 00 00 8B CE E8 B5 04 00 00
8B CE E8 0E 05 00 00 4B 75 A6
```

The final call remains at VA `0x0043F8ED` / RVA `0x0003F8ED`, bytes `E8 0E 05 00 00`, target VA `0x0043FE00`. The controller context at `0x00443820` and substep-begin context at `0x0043F8A7` also match retail. Their calls remain at `0x00443827` to `0x00444AE0`, and `0x0043F8AD` to `0x0043F650`, respectively.

The three expected contexts now live in the shared physics-probe model used by production verification and native tests. The native regression pins the entire 25-byte tail sequence, checks the other two full contexts, rejects a mutated tail byte and a truncated sequence, and verifies a specific diagnostic for each context. Production now reports `controller_context_mismatch`, `substep_begin_context_mismatch`, or `substep_tail_context_mismatch` while retaining strict checks.

An independent PE `.text` read of the local exact-hash executable matched all three full contexts and all three five-byte calls and decoded targets. No address was borrowed from another build.

## Installation safety review

The fix preserves the exact pristine hash/build gate, image-base check, module pin, thread suspension and EIP-quiescence checks, all three original-call-byte checks in `RacePatchBatch::install`, rollback, and owned-hook restoration. A failed or foreign partial patch remains disabled and pinned for process exit. Thread quiescence failure now has its own `thread_quiescence_check_failed` reason, separate from the three context mismatch reasons. Inspection found no other immediate fail-open defect in this installation path.

The first build exposed a separate integration compile defect: `Device8` used `physics_probe_attached` for acquire/release but did not declare it. The field was added to the generated wrapper template, then the generator was run and its determinism test passed. This keeps the observer's device lifetime balanced across creation and release.

## Validation

| Check | Result |
|---|---|
| Exact retail SHA, PE `.text`, three complete contexts, three callsites and targets | PASS |
| Native CTest, including `physics_probe_contracts` | PASS, 16/16 |
| Renderer Python suite | PASS, 160/160 |
| Root synthetic suite | PASS, 630/630 |
| `python -m compileall -q modernization/renderer` | PASS |
| Proxy PE verifier | PASS; PE32/I386, required exports, no recursive `d3d8.dll` import |
| `git diff --check` | PASS |

Build artifact (local, ignored, and not included in the source archive):

- `modernization/renderer/.build-msvc/Release/d3d8.dll`
- 2,064,896 bytes
- SHA-256 `67b82fe57e22a74c0d687b858f359f1e9a9d4b0788b382907011848eda7fa050`
- PE32 / I386; direct exports `Direct3DCreate8`, `ValidatePixelShader`, `ValidateVertexShader`

This proves build and package structure only. The corrected observer has not yet been runtime-confirmed; the required next setup result is `installed=true`, `reason=exact_callsites_installed_read_only`.

## One-session runtime handoff

Use the exact pristine retail executable with the verified SHA above and the newly built DLL from this validation. In its renderer config set:

```ini
[Trace]
Enabled=1

[PhysicsObserver]
Enabled=1
```

Restart the game so settings are reread. Run one ordinary offline France1 race, drive on clear road, invoke the game's normal recovery/Reset once, let the car settle, drive briefly, then exit normally. Do not use teleport or any experimental relocation. The observer is read-only with respect to physics and Broker state.

Inspect the single new JSONL session in `MRRRenderer/logs`. First require:

```json
{"type":"physics_probe_setup","requested":true,"exact_retail_build":true,"installed":true,"read_only_game_data":true,"reason":"exact_callsites_installed_read_only"}
```

If the observer paths execute, the same session should also contain bounded `physics_probe_event` records and a `physics_probe_summary` on normal release; require `patch_restored=true` there. If installation fails, report the emitted per-context reason verbatim; do not relax verification. If installation succeeds but no events appear, retain that session for deciding whether the instrumented paths executed.

## Repository state

- Repository: `D:\Game\Master Rallye\master-rallye-re-general`
- Active branch: `master`; starting and ending HEAD: `676ed24b2d32543c3b9356ed359e280f2b36a309`
- Existing unrelated dirty work from prior camera/UI phases was preserved.
- No game executable was modified, no generated DLL was added to source control, and no commit or push was made.
- `research-handoff-a3j3a.zip` contains only the A3j.3a source/template/test/documentation delta.
