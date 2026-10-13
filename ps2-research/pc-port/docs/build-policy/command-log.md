# Commands actually executed

Preflight: git status --short --branch, git rev-parse HEAD, renderer diff/status.
Initial public command:

```powershell
python ps2-research/pc-port/overlay/build_overlay.py
```

Correctly STOPPED: modernization/renderer has tracked working-tree changes;
staging refused. User approved old immutable Git objects only, preserving the
four concurrent HUD edits. Executed reviewed local one-off verifier wrapper:

```powershell
python ps2-research/pc-port/.analysis/approved_git_objects_build.py
```

Wrapper permits only those exact four working hashes, verifies pinned/current
renderer Git trees and rejects any other changes; it stages from Git objects.
Initial canonical build PASS; then repeated after exact third HUD patch was
approved. Both runs built baseline and PS2-enabled independently. Existing
canonical build trees were retained. Final same-input verification:

```powershell
python ps2-research/pc-port/.analysis/check_incremental_build.py
python ps2-research/pc-port/overlay/inventory_build_roots.py
git diff --check -- ps2-research/pc-port
```

Builder actually executed cmake -S .staging/<variant>/modernization/renderer
-B .build/<variant> -G "Visual Studio 18 2026" -A Win32 -DBUILD_TESTING=ON;
PS2-enabled additionally MRR_ENABLE_PS2_PORT=ON and staged MRR_PS2_PORT_ROOT.
Then cmake --build ... --config Release --parallel1, CTest, verify_proxy.py,
focused unittest discover and compileall. Logs are ignored under .build/logs
and .analysis/single-root-*.log. Compact reports included, raw logs excluded.

Future public command remains overlay/build_overlay.py. It requires clean
locked baseline; no persistent exception switch was added. Direct incremental
commands in overlay/README.md are examples for already verified staging.
Original renderer/SDK/game assets were never written by these commands.
Human cold-menu, Turkey3 and H A/B instructions are pending, not executed.
