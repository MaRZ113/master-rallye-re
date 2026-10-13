# Validation

Both independent Win32 Release builds: PASS, serial --parallel1.
Baseline CTest:24/24 PASS. PS2-enabled CTest:30/30 PASS, including HUD cache,
grass camera/asset/lifecycle, object admission, native transactions, reflection,
pixel probe and state restoration. Python:72/72 PASS, no failures/skips.
Optional private grass/puddle/reflection inputs supplied to native tests.
Both proxy export/PE verifications PASS. Both interface generators repeated,
deterministic, locked outputs preserved. Compileall PASS. Port diff-check PASS.

Same-input full workflow rerun:33.744seconds including both CTest suites,
Python tests, generator/hash/export checks.143 existing OBJ timestamps unchanged;
all checked staged source timestamps unchanged; BOTH DLL hashes unchanged.
No new build configurations or full clean. See incremental-validation.json.

Baseline DLL:85244faa5c9fcc75d1351977cf8dfefd9ff35791274efaeaed740a342bc50a32.
PS2 DLL:aca86773b3417f8abc2a9e7e3370d3cae63d83e1a25112d3c755131787a8164f.
Final outputs:dist/current/<variant>/d3d8.dll. Source/patch/Git hashes and the
one-off authorized dirty-worktree exception recorded in the build report.
No original renderer file changed BY THIS TASK; four pre-existing/concurrent
HUD edits preserved byte-for-byte and adopted only as a staged PS2 patch.
Public build verification still rejects dirty baseline. No original asset,
CourseSDK modification, auto-deployment, push or legacy directory deletion.

Post-fix runtime: NOT_PERFORMED. Visible grass, cold-menu FPS improvement and
HUD stutter improvement must be tested in game. PS2 parity not claimed.
