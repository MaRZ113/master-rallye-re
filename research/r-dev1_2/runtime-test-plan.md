# First safe developer-tool runtime observations

These are prepared instructions only. No game window was opened, no command was sent, and no runtime result is claimed.

## Shared setup

1. Use a **disposable retail install copy**, never the authoritative install or corpus directory.
2. Verify the copied executable remains retail SHA-256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
3. Hash the copied EXE and relevant DataGame config before and after. Back up any disposable config that may be changed.
4. If the native main window is not available, set only `Menues/Enabled=True` in the disposable config copy; record that change and restore the copy afterward.
5. Use `tools/runtime/dev_command_trigger.py` first without `--confirm`. Check that it reports one process/window, the expected image path/hash, and the native `Game → Reset / Exit` menu signature. It refuses to send if there are zero or multiple targets.
6. Do not use any other command injector, debugger, process-memory writer, EXE patch, or arbitrary `WM_COMMAND` sender.

## Test 1 — Flow Builder open-only

**Question:** Does retail command `0x30` open the Flow Builder window without running a tool action?

Run the helper in dry-run mode:

```powershell
py -3 tools/runtime/dev_command_trigger.py --tool flow-builder
```

If the single target checks out, run:

```powershell
py -3 tools/runtime/dev_command_trigger.py --tool flow-builder --confirm
```

Type exactly `OPEN FLOW BUILDER` at the prompt.

**Allowed:** observe the window/menu, take a screenshot, move or resize the window, close it normally, and reopen it once using the same allowlisted command if desired.

**Forbidden:** Build IDs `0–2`; Clear/Load Speed Matrix IDs `8–9`; FL→SFL ID `10`; any File New/Open/Load/Save/Save As, conversion, build, clear, or other local action.

**Collect:** screenshot; visible menu labels and enabled/disabled states; Debug-window text/log if available; whether the game keeps running; whether the window closes/reopens normally; before/after EXE/config hashes; any created/changed files in the disposable install.

**Interpretation:** one Flow Builder window and unchanged data files agree with the static open-only boundary. A helper refusal is a safe stop, not a failed game result. Any unexpected file change or crash ends the observation; preserve the disposable copy and record exact evidence before restoring it.

## Test 2 — Broker Editor open-only

**Question:** What read-only fields and live broker values does the Broker Editor display after its known in-memory key-metadata registration?

Run dry-run mode:

```powershell
py -3 tools/runtime/dev_command_trigger.py --tool broker-editor
```

After verifying the same retail hash/window/menu checks, run:

```powershell
py -3 tools/runtime/dev_command_trigger.py --tool broker-editor --confirm
```

Type exactly `OPEN BROKER EDITOR WITH METADATA REGISTRATION` at the prompt. This is intentionally distinct from the Flow Builder confirmation because open adds the two `__NO_SAVE` / `__NO_CHANGE` string-ID nodes to shared in-memory metadata when absent.

**Allowed:** observe, scroll, expand the tree/list, select entries, read displayed values, move/resize, and close normally.

**Forbidden:** edit values; Remove; Update; Commit Changes; Save Game; Save Options; Save Player State; or invoke any other menu action.

Inspect without modifying, when visible: `Race/*`, `Vehicles/*`, `Frontend/*`, `Progress/*`, `Editing/*`, `ModelCaching/*`, `DebugWindow/*`, and `Menues/*`.

**Collect:** screenshot; visible columns; key/path representation; type and scope representation; save flags; sample values from the named path families; Debug-window text/log if available; whether the game keeps running and the editor closes normally; before/after EXE/config hashes; any changed/created files in the disposable install.

**Interpretation:** successful display with unchanged on-disk files agrees with the static open-only boundary, but does not resolve the sentinel names' downstream policy meaning. Any value edit or commit would be a separate, unauthorized experiment and must not be inferred from this observation.

## Debug text capture

No passive `ReadProcessMemory` capture helper is supplied. Stable debug-buffer address/ownership has not been established; use the visible Debug window/log or screenshots. Do not add injection or write access for this test.

## Runtime status

**NOT RUN.** Both tests await human execution in the disposable install.
