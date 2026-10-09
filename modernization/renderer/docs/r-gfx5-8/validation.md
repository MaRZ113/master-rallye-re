# R-GFX5-8 validation and acceptance boundary

**READY_FOR_DIAGNOSTIC_RUNTIME**. The Windowed initial-resize defect has a causal source correction. True Exclusive startup is preserved, but restore/Error 2010 is still unresolved: this pass adds the missing owner/readiness/order observations. No real game session was launched or deployed. R-GFX5 is not closed.

## Source identity and worktree

- Repository: `D:\Game\Master Rallye\master-rallye-re-general`; branch `master`.
- Starting HEAD: `88bf3decd411b8b65e11e8b801650867097d186b` (R-GFX5-7).
- PC-VISUAL-PILOT1 source `f43d720e08961791ad46875af0d15430ed555e02` is a verified ancestor of the starting HEAD.
- Previous R-GFX5-7 DLL: SHA256 `dd07359719a71f6b64fe56d49f384d9dd75cc04121831adb539f338c6abe140d`, 1,502,720 bytes, recovered from its existing `docs/r-gfx5-7/validation.md`. Its handoff manifest inventories sources and does not contain a DLL hash. The old DLL identity was not recomputed from a surviving binary here.
- Pristine game SHA256 remains `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`, verified against `D:\Game\Master Rallye\MRallye.exe` after the work.
- No branch/worktree creation or switch, no push, no EXE/assets/PS2 research edits. Ghidra 12.1.4 queried the exact program read-only; new scratch is ignored.

At the recorded R-GFX5-8 preflight, unrelated Observatory files were left unstaged: `README.md`, `tests/synthetic/test_observatory_release.py`, `tools/runtime/broker_observatory.py`, `tools/runtime/observatory_version.py`, `docs/releases/observatory-0.2.3-beta.md`, and `tests/synthetic/test_observatory_remote_anchors.py`. Renderer source was clean at that preflight.

## Causal Windowed regression

`CONFIRMED_BY_SOURCE`: the old planner removed a previously overridden, unchanged dimension before testing the Reset against actual HWND geometry. A genuine first 1447×720 request became 1447×480 for admission after logical 640×480 → configured 1280×720 startup. Maximize/restore incidentally refreshed the logical baseline, explaining why later resizing worked.

`CONFIRMED_BY_SYNTHETIC_TEST`: `windowed_startup_order()` was first added against unchanged R-GFX5-7 source and failed on that first horizontal resize. With original-request admission and both logical axes updated together, it passes without any maximize workaround. Explicit startup, auto-size startup, horizontal/vertical/corner/extreme/narrow drags, bogus requests, latest-normal maximize/restore, minimize/restore, startup echo then genuine drag, and success-gated target updates are covered.

`native_display_ordering()` also uses a real hidden Win32 HWND and original WndProc dispatch with a mock D3D device. It verifies an immediate configured-startup drag and a Reset nested between the before/after message hooks, including AutoHideCursor=0 and shutdown unhooking. This is Win32/synthetic coverage, not hardware D3D8 or Master Rallye runtime confirmation.

## Build and test results

`CONFIRMED_BY_SYNTHETIC_TEST`:

| Check | Actual result |
|---|---|
| Current renderer Python suite | **118/118 PASS**, final run 66.536 seconds |
| Native CTest | **9/9 PASS**, final run 4.41 seconds |
| Compileall, entire `modernization/` | PASS |
| Git diff whitespace check | PASS; line-ending conversion warnings only |
| Proxy PE/export/import verifier | valid=true, no errors; details below |

All available native suites ran: foliage_probe, compatibility, native forwarding/COM, visual policy, classifier, reflection, FOV/culling, quality, and identity contracts. Existing assertions were retained. Python capture selectors were updated from R-GFX5-7 to R-GFX5-8 while retaining executable SHA matching; stale native captures do not supply evidence for the new build.

The auditor's new-device/stale-readiness, missing device ID, absent event sequence, and unchanged native-result tests are included in the final full Python run. The last production hardening records a single observer-install attempt even if both Win32 hook calls fail; failures cannot produce hook-install work every ordinary frame.

Canonical `python modernization/renderer/tools/build.py` configured the current Win32 tree successfully, but its parallel-4 MSBuild call stalled at the banner with no compile progress and was interrupted. The same configured tree was then built successfully with sequential MSBuild, including the final hardening. The canonical wrapper is therefore **not** reported as having completed; the actual Win32 Release build and all native suites did complete:

```powershell
cmake --build modernization/renderer/.build-msvc --config Release --parallel 1
ctest --test-dir modernization/renderer/.build-msvc -C Release --output-on-failure
python modernization/renderer/tools/verify_proxy.py modernization/renderer/.build-msvc/Release/d3d8.dll
python -m unittest discover -s modernization/renderer/tests -v
python -X pycache_prefix=modernization/renderer/.analysis/pycache -m compileall -q modernization
git diff --check
```

For Python, TEMP/TMP/TMPDIR pointed to the existing ignored `modernization/renderer/.analysis/tmp` directory because the sandbox restricts system-temp writes. Build/test logs remain ignored in `.analysis/`; no raw logs or generated native files are committed.

The compiler emitted existing SDK/mock/conversion warnings and no build errors. No ABI/ownership failures occurred in the native suites. This does not establish driver-level reset success.

## Final DLL

Path: `modernization/renderer/.build-msvc/Release/d3d8.dll`.

- SHA256: `fda771e03dc3bc5457d995ea755933f9a3982fc280ece061d5b6329ad9f3f543`.
- Size: **1,531,392 bytes**.
- PE32 DLL, I386 / machine `0x014C`, Win32 Release; ImageBase `0x10000000`.
- Required direct exports: `Direct3DCreate8` ordinal 5, `ValidatePixelShader` ordinal 2, `ValidateVertexShader` ordinal 3.
- Imports: `bcrypt.dll`, `USER32.dll`, `KERNEL32.dll`; no recursive `d3d8.dll` import.
- Full verifier output: [build-verification.json](build-verification.json).

The DLL contains the current integrated foliage CPU-upload implementation. It is ignored and remains in the build directory; it is not part of the source commit or source handoff archive.

## Recovery and resource contracts

`CONFIRMED_BY_SYNTHETIC_TEST`: three explicit Exclusive lost → incomplete restored/decorated window → failed Reset → later DEVICENOTRESET → successful Reset cycles preserve genuine native HRESULTs, true Windowed=FALSE/640×480, successful-reset epochs, reference counts, and zero proxy window-apply calls. INVALIDCALL/E_FAIL remain real failures. Diagnostic message output stops at its bounded limit.

The production Device8 wrapper contract additionally proves that a failed Reset and a suppressed renderer-commit echo do not invalidate CPU upload mirrors or resource generations. A real successful Reset poisons MANAGED diagnostic mirrors, retains their resource generations, and invalidates DEFAULT metadata. Conservative poisoning is not automatically revived for an old resource. Existing pool/COM ownership is unchanged.

Foliage mirror budgets remain 8 MiB per buffer, 32 MiB per device, 16 MiB frame capture, 4096 initialized intervals and 8192 shadow entries. Lock/Unlock forwarding, WRITEONLY upload observation, generation/revision tracking, QueryInterface safety and opt-in F10 diagnostics remain tested. Mode=0/Diagnostics=0 remain defaults; requested Mode=1 stays blocked/Stock, with **no new visual override**.

PreserveMargins v2 remains `CONFIRMED_BY_RUNTIME` from prior in-game validation. This build's synthetic tests preserve draw-local WORLD override/immediate exact restoration and zero persistent packet writes, including real-success/failed Reset contracts. Centered4x3, Borderless, AF stage0 MIN-only, MSAA, gameplay FOV/frustum synchronization, source45 preview, MenuFreezeFix, shadows, stable vehicle semantics/reflections/brake exclusions, cursor and quit remain in the recorded passing suites. They did not receive a new in-game verdict during R-GFX5-8.

## Unresolved Exclusive evidence

The supplied R-GFX5-7 trace summary records iconic/zero-client DEVICELOST, then restored style `0x16CF0000`, ex-style `0x108`, outer 640×480/client 624×441, GetFocus=0 and a failing normalized 640×480 Exclusive Reset. The original raw JSONL was unavailable for independent audit.

`CONFIRMED_BY_EXE`: mode byte +0x1C is zero for native fullscreen and nonzero for native windowed; two validated owner chains, vtable and HWND allow read-only observation on pristine retail. The windowed WM_SIZE Reset path has no prior cooperative query, whereas the separate readiness path distinguishes DEVICELOST/DEVICENOTRESET. See [VA/RVA and calling-convention evidence](exclusive-static-analysis.md).

`STRONG_HYPOTHESIS`: a live windowed game owner with a native Exclusive device can reset prematurely from restored WM_SIZE. R-GFX5-8 traces now establish the live mode mismatch, DEVICELOST immediately before an early failed Reset, later DEVICENOTRESET/S_OK readiness and subsequent native Reset success. The actual style writer, complete call stack, path responsible in every failing case, and causal sufficiency of the mismatch remain **UNKNOWN**. Raw R-GFX5-8 JSONL files are not included in the source repository; capture IDs and detailed sequences are recorded in [R-EXCL1](../r-excl1-deferred.md). No field write, original-mode function call, post-Reset restyling, HWND message suppression, HRESULT translation or new retry was added. Existing bounded MSAA capability fallback is preserved.

## In-game validation procedure and archive

[W1–W6 / E1–E6 procedure](runtime-handoff.md) defines the in-game acceptance criteria. Start with W1/W2 without an initial maximize/minimize workaround, then E1/E2 with conservative settings. If E2 fails, retain one shortest complete new session JSONL, the INI and the precise minimize/restore action; unrelated high-resolution/MSAA/race repetitions and large dumps are unnecessary at that point.

New markers: `windowed_resize_admission`, `display_window_message`, `display_native_begin`, `display_reset_readiness`, `display_native_attempt`, `display_cooperative_transition`, `display_message_budget_exhausted`. The read-only audit pairs readiness with native Reset by device lifetime; it cannot convert a trace into a visual PASS.

[Source/test handoff](R-GFX5-8-handoff.zip) includes current renderer source and small unchanged Python/recon dependencies needed by its suites, with per-file hashes in [handoff-manifest.json](handoff-manifest.json). It contains no game assets, native binaries, raw captures, reverse databases, scratch or older handoff ZIPs. DLL build identity is metadata only. The ZIP is checked for CRC and every listed payload SHA256; its external `.sha256` receipt identifies the archive. A phase-local `binary` attribute prevents the repository's default text policy from converting CRLF bytes inside the compressed archive; the staged Git blob is also verified byte-for-byte and by ZIP CRC. Rebuild native suites before running Python capture checks after extraction.

The R-GFX5-8 ending commit and worktree status were recorded in that phase's closeout. Only renderer paths belong to its commit; unrelated Observatory changes were left untouched. R-GFX5 closeout and camera/photo/HD-UI work remained gated on in-game acceptance of both display modes.
