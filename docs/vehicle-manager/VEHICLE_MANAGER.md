# Vehicle Manager v1

`tools/vehicle_manager.py` (CLI) and `tools/vehicle_manager_gui.py` (window, `... gui`). Phase 3 of DESIGN.md.
The game folder, Data.sma, MRallye.exe and both proxy DLLs are never modified; everything lives in
`MRMods/Vehicles/`. Loaders stay generic: dinput8 reads `active/roster.mrvr` v2 (native roster + MRLP loader
profile) and `active/variants.ini`.

```
MRMods/Vehicles/manager/base/        reference roster (imported once from an installed v2 roster)
MRMods/Vehicles/manager/packages/    *.mrcar packages
MRMods/Vehicles/manager/roster.json  selection: per-class order, removed IDs, enabled packages
MRMods/Vehicles/active/              rebuilt by apply (active.prev/ = previous, active.disabled/ = after stock)
```

## What it does

| Action | Effect |
|---|---|
| order / move | in-class order of Vehicle Select: MRVC class tables, reverse tables, Vehicle Select widgets |
| remove / restore | SDK vehicles (ID > 24) leave / return to their class; the ID becomes a tombstone (never reused), saves that use it fall back to ID0 through the loader save guard; class counts, selection publisher bound, MRLP SDK vehicle list follow. Retail IDs 0..24 can only be reordered. |
| packages | `.mrcar` (ZIP, `mr-vehicle-package/1`, kind `variant`): a DEMO model of a family (folder, names, physics clone). Enable/disable/install. |
| apply | builds `active.new/` from the base, verifies it (v2 format, digest, variant files) and swaps it in atomically |
| stock | renames `active/` to `active.disabled/`: the game runs stock; `apply` restores |

Every apply starts from the base, so the result depends only on the selection. Checks: `tools/test_vehicle_manager.py`
(identity apply reproduces the base roster byte-exactly; remove Rav4 + reorder T2 + disable Tata DEMO; restore gives
the original bytes again; stock and back).

## Usage

```
py -3.11 tools/vehicle_manager.py --game <game> import-base --names docs/vehicle-manager/presentation-fix-01.json
py -3.11 tools/vehicle_manager.py --game <game> list
py -3.11 tools/vehicle_manager.py --game <game> remove 31
py -3.11 tools/vehicle_manager.py --game <game> order T2 30,7,29
py -3.11 tools/vehicle_manager.py --game <game> uninstall tata-demo.mrcar
py -3.11 tools/vehicle_manager.py --game <game> apply
py -3.11 tools/vehicle_manager.py --game <game> gui
```

Test host: `.research-output/hosts/Vehicle-Manager-roster-v4-01.cmd` opens the window for `host-roster-v4-01`
(base already imported). Close the game before Apply.

## Not in v1

* New native vehicles (a new physical ID) still come from the Vehicle SDK registry builder (V-CAP): build a roster,
  install it, `import-base --force`. The selection is kept for IDs that still exist.
* Moving a vehicle to another class, adding a fourth class (CLASS-T4) and packages of kind `vehicle` need the
  registry builder inside the Manager; planned as v2 together with the Workshop integration (the Vehicle SDK worktree
  research/vehicles currently has unrelated uncommitted work, so the window is a separate tool for now).
* The Manager refuses to run while the EXE is not the retail one; it does not check whether the game is running.
