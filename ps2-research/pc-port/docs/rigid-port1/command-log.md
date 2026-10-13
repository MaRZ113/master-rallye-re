# Commands and evidence boundary

Executed from the primary master worktree:

```powershell
git status --short --branch
git branch --show-current
git rev-parse HEAD
git rev-parse HEAD:modernization/renderer
python ps2-research/pc-port/tools/rigid_lifecycle_probe.py verify --exe 'D:/Game/Master Rallye/MRallye.exe'
python ps2-research/pc-port/tools/rigid_lifecycle_probe.py script --exe 'D:/Game/Master Rallye/MRallye.exe' --output ps2-research/pc-port/docs/rigid-port1/native-logpoints.x32dbg --max-hits 16
python -m unittest discover -s ps2-research/pc-port/tests -p test_rigid_lifecycle_probe.py -v
python -m unittest discover -s ps2-research/pc-port/tests -p test_tumbleweed_contract.py -v
python ps2-research/pc-port/overlay/build_overlay.py
python -m compileall -q ps2-research/pc-port/tools ps2-research/pc-port/tests
git diff --check
git diff --quiet HEAD -- modernization/renderer
git -C 'D:/Game/Master Rallye/master-rallye-re-course' status --short --branch
git -C 'D:/Game/Master Rallye/master-rallye-re-course' rev-parse HEAD
```

The build script executed immutable object verification, exact staging patches,
two generator reruns per variant, two separate CMake Win32 Release builds with
`--parallel 1`, CTest, proxy verification and107 Python tests. Detailed output
remains local under `.build/logs`; the compact report is `dist/current/build-report.json`.
No full clean or new build root was used. New observer/serializer tests concern
read-only behavior and source wire validation, not physical contact.

REA/Ghidra and independent GNU objdump/PE mapping commands are recorded in
`native-pc-lifecycle-20261013.md/.json`. PS2 direct Ghidra EER/Rabbitizer and
source extraction commands are recorded in `ps2-source-contract.md`;
HUD-specific checks in `../hud-port0/validation.md`.

Final PSB test rerun used the already installed bundled Python/Pillow12.3.0,
with original ignored HUD corpus environment set;25/25 PASS. This addressed
the earlier optional dependency error without changing tests or installing
software. No sample/debugger/game run, spawn, contact or DLL install executed.

Runtime commands in `runtime-control.md` are **user examples not executed**.
Use the user's actual PID; never copy the example PID as a discovered identity.
