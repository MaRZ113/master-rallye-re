# Broker NULL Guard and Windowed Freecam

Status: **ready for human runtime testing**. This is a build and static/native-test result, not in-game acceptance.

Repository: master-rallye-re-general, branch master, starting HEAD 676ed24.
Pristine target: MRallye.exe, SHA-256 bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4, 3,121,214 bytes, PE32/I386, ImageBase 0x00400000.

## Track A — Broker Dump NULL guards

The exact retail formatter has two independently verified native hazards. REA evidence records used for this implementation were ev_02f730f95f5a794447a1870078af4f380172f701264a9af04d65b7b5f01432d4 (StringList) and ev_8da8bec10c568670663c230acc6760dba6f1fb89a73219c82384b239ce045b21 (XmlData).

At 0x0060201E, the exact bytes are 8B 7B 04 3B 7B 08 74 1A: mov edi,[ebx+4], cmp edi,[ebx+8], then the original je 0x00602040. The guard branches NULL EBX to the existing empty-list completion at 0x00602040. For non-NULL it executes the displaced MOV/CMP and resumes at the original JE (0x00602024), retaining the original comparison flags and traversal.

At 0x00602153, the exact bytes are 8B 10 8B C8 FF 52 0C 8B F8 85 FF 74 2E: mov edx,[eax], mov ecx,eax, and the original vtable call. The original je at 0x0060215E targets the NULL-safe next-entry path at 0x0060218E; non-NULL returns to 0x0060215A. The generated stub preserves the non-NULL this pointer, stack return path, and call target behavior; NULL skips the unsafe dispatch and continues through the verified native next-entry path. Both continuation contexts are checked against the retail image.

The implementation is in modernization/renderer/src/broker_null_guard.cpp and modernization/renderer/include/broker_null_guard.hpp. It is gated on exact retail identity, ImageBase, and expected D3D factory caller. Each site has its own byte/context checks and status. Installation suspends and checks peer threads around patching, changes protection only for the validated site, flushes the instruction cache, verifies readback, and rolls back on failure. Generated stubs are proxy-owned executable memory; the proxy module is pinned for their lifetime. The independent AttractMode guard remains at its existing site and is not reinstalled here.

A safe site mismatch leaves ordinary D3D forwarding available and reports the failed site. An unverified patch rollback refuses D3D factory creation because the original image may no longer be safe to execute. The second site is skipped only when the first site has an unverified rollback. The final wrapped Root8 release restores owned sites after quiescence and reports restoration status.

The broker_null_guard diagnostic records exact-build result, each context verification and installation result, per-site reason, null-branch counters, rollback state, and whether original bytes were restored. Runtime acceptance still requires the original in-game Debug → Dump path to complete after a NULL StringList/XML entry and continue to later Broker entries.

## Track B — Windowed Freecam after graphics Reset

The user's Windowed trace identified the failure boundary: Maximize/Restore caused a D3D Reset, which revoked the completed race lifecycle proof; a later Freecam admission therefore failed even though Windowed input was delivered. The prior Windowed log is D:\Game\Master Rallye Pristine\MRRRenderer\logs\session-20261011-105219-6404.jsonl. A successful Borderless comparison is D:\Game\Master Rallye Pristine\MRRRenderer\logs\session-20261012-001348-30264.jsonl.

RaceEpoch::device_reset() now retains only a fully completed owner/lifecycle proof when no native lifecycle callback is executing. A Reset during an in-progress lifecycle, with no completed proof, or after explicit cancellation still revokes it. The D3D Reset path separately cancels the camera frame scope. Freecam activation then rechecks the current race certificate, camera owner/course context, and known paused state; Reset does not itself activate or authorize Freecam. The pause gate was explicitly approved by the user.

Window input keeps the existing scoped game-window subclass and foreground ownership check. It does not add a global keyboard hook or relax focus requirements. The bounded freecam_window_input record exposes display mode, game/attached/focus HWNDs, foreground/keyboard focus, owning/current thread, WndProc ownership, window/client validity, focus acceptance, F8 observation/edge, live race proof, pause, camera admission, and activation/rejection reason.

The Reset policy is recorded as reset_policy with completed_race_proof_preserved and camera_scope_cancelled; the observer emits race_epoch_device_reset. Test coverage exercises completed proof retention, in-progress/no-proof revocation, live certificate revalidation, pause gating, and the real scoped Win32 focus/input sample.

## Validation

- Canonical python modernization/renderer/tools/build.py: passed; Win32 Release and CTest 24/24.
- python -m unittest discover -s modernization/renderer/tests -v: 193 passed.
- python -m unittest discover -s tests/synthetic -v: 630 passed.
- python -m compileall -q modernization/renderer: passed.
- Exact retail Broker context tests verify retail hash, PE identity, complete bytes, and branch destinations.
- verify_proxy.py: valid PE32/I386 DLL; required D3D8 exports present; no recursive d3d8.dll import.

These checks establish code/build correctness. They do not replace the two human runtime tests below.

## Human runtime handoff

Keep Broker and Windowed results separately attributable. Use the new DLL at modernization/renderer/.build-msvc/Release/d3d8.dll; back up the currently accepted DLL before installing it. Do not alter the retail EXE.

Windowed Freecam: Set [Display] Mode=1; maximize and restore the window, start offline France1, pause through the native game, press F8, and check movement/mouse look, focus loss/return, and stock-camera restoration. The log should show preserved completed proof after graphics Reset, then input_focus_accepted=true, toggle_edge_generated=true, race_certified=true, pause_verified=true, and camera_admission_accepted=true when activation succeeds.

Broker Dump: Complete an offline France1 race, open race results, invoke the original Debug → Dump action, and confirm the game remains responsive, Frontend/RaceResults/PointsList (StringList) has balanced empty-list output, and later Broker entries are present. Repeat Dump if available. Check broker_null_guard startup/teardown records; both exact sites must report verified and installed before considering the guard active.

Do not infer runtime success from a DLL build or synthetic tests. The task is complete at READY_FOR_RUNTIME until these checks are performed.
