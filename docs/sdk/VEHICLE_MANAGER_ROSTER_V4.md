# Vehicle Manager integration

Existing SDK changes were preserved first as commit b165e5a (Extra Options
SDK binding, native setup resources and documentation). This integration
then imports the accepted Manager from integration/base c0dd9d0.

Open **Vehicle > Vehicle Manager / native roster** in Rally Workshop 2 Qt,
or **Vehicle Manager** in the existing legacy Workshop. The Qt panel uses
the existing application and style; the legacy entry uses a child window.
`tools/Launch-VehicleManager.cmd [game-folder]` opens the same Qt panel.
`tools/vehicle_manager.py --game <folder> list` provides the CLI.

Choose a private game/candidate folder. Opening it is read-only. Import the
active roster once if there is no base snapshot. Move cars within T1/T2/T3,
remove/restore addons, or install/enable/disable DEMO `.mrcar` packages. Apply
validates a fresh active.new and swaps only MRMods/Vehicles, retaining the
previous active roster. Close the game before Apply. Stock moves the active
roster aside; Apply restores it. Retail IDs cannot be removed. Native IDs,
physics families and AI mode masks stay stable; removed IDs keep mask zero.

The original Manager operations, native class transform, RVP parser and
local-header archive reader live in `workshop/roster`. No sibling checkout,
external F3 compiler scripts or second runtime launcher is required. MRLP v1
is recomposed from the accepted base template: immutable ranges, allocation
and Challenge hooks remain owned by that template; final native checks and
digest are regenerated and hook preimages verified. Class edits cannot alter
the hook ABI. New physical vehicles still require the SDK registry builder
and an updated accepted base; this panel manages that base and variants.

MRVR v2, MRVC v1, RVP1, MRLP v1 and `.mrcar` v1 are preserved. Lamp catalogs
and model/texture resources are copied from the base, including the new
Forester PS2 geometry. Texture Studio and livery authoring are unchanged.
Game archives, EXE, proxy DLLs and saves are never overwritten by the panel.

Verification: `tools/test_vehicle_manager.py --source-host <candidate>
--work-host <fresh-scratch-folder>` exercises identity apply, reordering,
retirement/mask zero, restore, package disable/enable and Stock/restore.
Existing directories are refused by the test. The Qt panel was rendered and
its lists verified using the existing Workshop Qt environment. Game workflow
acceptance is separate from these offline checks.
