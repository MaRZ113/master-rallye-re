# Commands actually executed

From D:/Game/Master Rallye/master-rallye-re-general, master:
git status --short --branch; git rev-parse HEAD;
git rev-parse HEAD:modernization/renderer; git diff --check.
Separate Course SDK status/HEAD inspected read-only: clean research/r5t-course-
archaeology,4244fa0c4d878523c9947f54816bf377cdfb2589.

Original audit, both F10 captures and both sessions inspected read-only. SHA
and exact native sequence are retained in runtime-audit.md. No new REA/Ghidra
pass was needed; original REFL1 writer and live D3D8 evidence answered the
bounded implementation question. No proprietary image or mesh was rewritten.

Final clean staging/build invocation (both independent variants):

```powershell
$env:MRR_PS2PORT_BUILD_ROOT = '<port>/.build-overlay-reflection11-final3'
$env:MRR_PS2PORT_REPORT_PATH = "$env:MRR_PS2PORT_BUILD_ROOT/build-report.json"
$env:MRR_REFLECTION_TEST_GXI = '<port>/.assets/reflection/PS2EnvSource64x64.gxi'
$env:MRR_COURSE_OBJECT_TEST_ASSET = '<port>/.assets/course-objects/Turkey3Puddles.ps2obj'
python ps2-research/pc-port/overlay/build_overlay.py
```

Builder actually invoked Visual Studio18 2026 Win32 CMake configure, Release
cmake --build --parallel1, CTest, verify_proxy.py for each variant, twice-run
interface generators,44Python unittest cases and compileall. Raw local logs
remain ignored under the final build root and .analysis.

The final two-file null-COM identity guard was copied into the same verified
PS2 staging, then cmake configure/build --parallel1, all29CTest, proxy exports,
all44Python tests, compileall and generator checks were rerun. Baseline source
and DLL hash were checked unchanged; all final source hashes matched staging
before and after the rebuild. Report.final_rebuild identifies this explicitly.

Previous local attempts: first staging compiled an older test include-order and
failed CHECK macro compilation; second completed both builds but PS2 CTest failed
the original reflection_contracts getter assertion. Guards were corrected in
the overlay, with no frozen test/source edits. Third fresh staging passed;
final incremental guard/test rebuild also passed. Failures are not PASS results.

Packaging actually executed package_reflection11_handoff.py with current
source/test/patch/DLL hash validation, repeated deterministic serialization and
ZIP manifest/CRC verification. Extracted-bundle tests are reported separately
in validation.md. The following remains a HUMAN RECIPE, not executed here:
manual DLL installation, modes0–4 game comparison and PCSX2 visual confirmation.
