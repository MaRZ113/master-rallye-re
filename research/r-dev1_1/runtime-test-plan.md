> **R-DEV1.2 update:** Flow Builder remains the first `SAFE_OPEN_CANDIDATE`. Broker Editor is now `LOW_RISK_BUT_METADATA_MUTATION` with a separate confirmation and its own open-only human test. See `research/r-dev1_2/runtime-test-plan.md`; that plan supersedes the old Broker Editor exclusion.

# Prepared human runtime tests — R-DEV1.1

Static analysis is complete. The research agent has not executed the game or sent a command. Run only the test whose preconditions are satisfied, using disposable copies and preserving the original EXE/config hashes.

## T1 — Early-build menu inventory (highest information value)

**Question:** Did an original 8.4.1 or 9.3.1 development UI expose any tool sender not represented by the analyzed native menu builders?

**Build:** Start with 9.3.1, then 8.4.1, using only the pristine executable hashes in `research/corpus/executable-provenance.md`. The fresh corpus files are now eligible. Preserve before/after hashes and use disposable copies.

**Procedure:** Copy a verified build and its matching shipped DataGame files. Do not modify the original corpus. Launch with original shipped `dev.xml`; record the menu bar, all visible windows, and all menu item text/states. Do not activate any hidden ID or write-capable local menu item.

**Interpretation:** A visible editor opener would move that tool to B only if the exact originating menu/control/accelerator and target dispatch are recorded. Seeing only Game Reset/Exit agrees with static analysis but does not prove an external harness did not exist.

## T2 — Retail visible-menu inventory

**Question:** Does runtime menu attachment match the retail builder and do shipped false flags suppress the Debug window?

**Build:** Retail only, exact EXE hash `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. Use a disposable install copy. First launch unchanged shipped config and observe. If inspecting the enabled path, change only `Menues/Enabled` in a disposable config copy; do not change `DebugWindow/Enabled` or trigger a hidden command.

**Record:** visible menu bar/submenus, Debug window presence, window titles, and hashes of the disposable EXE/config before and after. This inventories presentation only; the owner has already isolated the gate, so do not repeat a flag matrix.

## T3 — Flow Builder open-only (only command-trigger candidate)

**Question:** Does global retail command `0x30` open the expected Flow Builder HWND without triggering file operations?

**Build:** exact retail binary hash above, in a disposable install. The shipped Menues key may need to be enabled only to expose the main native window; do not change any resource files.

**Procedure:** Use `tools/runtime/dev_command_trigger.py --tool flow-builder` first without confirmation to inspect its dry-run target. If its reported image hash, main-menu signature, PID, and HWND are correct, run again with `--confirm` and type `OPEN FLOW BUILDER`. Record the window and menu. Close with the window's Close command or normal close button.

**Do not invoke:** Flow local IDs 0–2 (Build), 8–9 (Clear/Load Speed Matrix), or 10 (FL→SFL). Do not click any local menu action during this test.

**Expected outcomes:** An `&Game` menu target receiving ID `0x30` should create one Flow Builder window; if the window already exists, the opener should activate it. If no unique verified target is found, the helper refuses to send. The helper prints the exact build identity and classification before sending.

## Explicitly excluded tests

- Broker Editor open: unresolved shared broker list mutations; **DO_NOT_RUNTIME_TEST**.
- Egg, Marker, Particle, generic tree/object editor: open-time shared-state effects not bounded; **DO_NOT_TEST**.
- BuildData: recursive resource/cache writes; never trigger.
- Game/Scene Save: create-always writers; never trigger.
- Game/Scene Open or Reset: applies state to live runtime and lacks a legitimate sender; not part of this safe test pack.

No debug text capture helper is supplied because stable buffer ownership/address was not proven. The existing OCR capture route may be used separately if desired, but it is outside this narrow reachability test.
