# V-LAUNCH1 validation record

## Candidate identity

* Branch: `research/vehicles`
* Starting HEAD: `86f5ac8` (`research: archive J2 addon runtime review package`)
* Retail executable: `D:\Game\Master Rallye\MRallye.exe`
* Retail SHA256, before and after verification: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`
* Vehicle runtime bundle: `.research-output/vehicles/vmesh4/v4-exp-001/runtime`
* Addon plan SHA256: `567a27a8f3c978bebd2a6600710b89779d16ddece7cd983630d286338490477b`
* Resource index SHA256: `aa26db6363c8d4e660b08eb9d96661e14d5fd21bcac848b185dfd95d69104171`
* Native patch manifest SHA256: `515277c4f414af39823a032ec5979a2b1551c8c12fca5fa10cb3b655520588f6`
* Launcher: `.research-output/vehicles/vmesh4/vlaunch1-final/mr-runtime-launcher.exe`
* Launcher SHA256: `f81d9b8b67d30cd0325eba2241dc91a4b41d312e5c9919652c8006a932e2e99d`
* Launcher size: `146,944` bytes; x64 launcher for x86 retail process.
* Runtime qualification: **STATICALLY VERIFIED / READY FOR HUMAN PROXY+LAUNCHER TEST**.

The bundle verifier reported 187 resource files and 246 native operations. No
bundle, renderer DLL, Subaru authoring source, or retail executable was changed
by V-LAUNCH1.

Static source inspection of the renderer's `provenance.cpp` confirms its INI
and `MRRRenderer\logs` paths are derived from the loaded proxy module path,
not the launcher's changed child working directory. The intended game
directory already has `MRRRenderer.ini`; the existing build-tree log folders
are not runtime dependencies.

## Launcher and proxy checks

* `python -m unittest tests.synthetic.test_addon_sdk_runtime -v` — **12 passed**.
* `PYTHONPATH=src python -m unittest discover -s tests/synthetic -v` (PowerShell equivalent: `$env:PYTHONPATH='src'; python -m unittest discover -s tests/synthetic -v`) — **482 passed, 0 failed, 0 skipped**.
* `python -m compileall src tools tests` — **PASS**.
* `git diff --check` — **PASS**; Git emitted only its existing LF-to-CRLF working-copy notices.
* MSVC 19.51 / Visual Studio 18 2026 x64 launcher build — **PASS**.
* Candidate `--verify` against the exact Subaru runtime bundle — **PASS**, 187 resources / 246 operations.
* Candidate `--verify-launch-environment D:\Game\Master Rallye\MRallye.exe <bundle>` — **PASS**, `graphics_proxy=absent`; confirms launcher-only startup environment remains accepted.
* Isolated temporary directory with the pinned retail EXE and approved `pc-port/.build/ps2-enabled/Release/d3d8.dll` — **PASS**, emitted `APPROVED_GRAPHICS_PROXY sha256=235aae55e077fca1e5b5208d4ac158b1a00dd80041fa5885bd06890a041b1eb8` and `LAUNCH_ENVIRONMENT_VERIFIED graphics_proxy=approved-d3d8`.
* One-byte-mutated proxy — **FAIL_CLOSED**, exit 1 with `adjacent d3d8.dll SHA256 is not an audited graphics proxy`.
* Isolated adjacent `dinput8.dll` — **FAIL_CLOSED**, exit 1 with `unqualified local graphics/input/audio wrapper is present`.
* Original retail EXE hash after these checks — unchanged.

The four accepted D3D8 files separately passed the renderer's `verify_proxy.py`
PE/export/import audit. The isolated positive launcher-environment exercise
used the PS2-enabled build; the other three exact hashes are covered by the
native allowlist regression and their individual PE/export verification.

No game process was launched with D3D8 and the Vehicle SDK launcher together
in this phase. Rendering, free-camera/HUD controls, and in-game Subaru
materialization under the combined setup remain human runtime gates.

## Human handoff

From an isolated test install matching the V-MESH4 handoff, first check the
existing `MRallye.exe` SHA, then ensure one approved `d3d8.dll` is beside it.
Do not overwrite an existing DLL unless its SHA is already one of the four
approved values in `graphics-proxy-compatibility.md`. Run, in order:

```powershell
$exe = 'D:\Game\Master Rallye\MRallye.exe'
$bundle = 'D:\Game\Master Rallye\master-rallye-re-vehicles\.research-output\vehicles\vmesh4\v4-exp-001\runtime'
$loader = 'D:\Game\Master Rallye\master-rallye-re-vehicles\.research-output\vehicles\vmesh4\vlaunch1-final\mr-runtime-launcher.exe'
& $loader --verify $exe $bundle
if ($LASTEXITCODE -ne 0) { throw 'Bundle verification failed' }
& $loader --verify-launch-environment $exe $bundle
if ($LASTEXITCODE -ne 0) { throw 'Proxy or wrapper verification failed' }
& $loader --integrated $exe $bundle
```

Confirm in the launcher output that it reports the chosen approved proxy hash,
then inspect normal frontend, Subaru preview/race, free camera, HUD-free
capture, and clean exit. Recheck the retail executable SHA after the game
closes. A different adjacent wrapper remains an intentional refusal.
