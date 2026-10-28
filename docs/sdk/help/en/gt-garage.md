# GT Garage Lab

Open **GT Garage Lab** to scan a private local GT3 VOL or reopen its checkpoint
report. Scan reads original files; Stop leaves the last checkpoint. Resume
requires the same source and reader hashes. L0 inventory is not a playable-car
certificate. Missing and unsupported entries remain visible.

Select an exactly associated catalog row and **Create from selected**. Supply
that model (.gz or decoded), original carcolor.db/carcolor.sdb, a read-only MR
donor and a new private output directory. The shared automatic importer derives
the profile. Donor scaling and source-lighting approximations remain explicit.
No installed game files are changed. Unknown editions/palettes may be rejected.

**Original colorway** selects original palette/material variants. Each color
owns an independent Workshop version. **Source Undo/Redo/Restore** changes this
selection, while manual Paint history stays with each version. **Open selected
in Workshop** opens the current editable version. Missing or changed source
inputs cause diagnostics, never silent replacement.

Custom Paint is a manual edit. Classic MR Style is a separately generated,
SHA-pinned conversion recipe. These are not original GT colors. Unknown surface
roles remain intact; exact Classic report approval is required before its game
build. The Clio pilot has MR rubber, recessed opaque wheel interiors and selected
glass changes; it does not qualify automatic decimation/livery removal for all
cars. Preserve Source Fidelity for comparison and restoration.

CLI: `vehicle_sdk.py gt-garage`, `auto-import-gt3`, `gt-source-project`.
Source project creation supports explicit `--profile` or exact
`--inventory --region --car-key`. The GUI uses this same Core/CLI path.
Use separate candidate directories, not retail installation folders.

L1 checks structural conversions. L2 captures are diagnostic D3D9 evidence.
Only actual owner gameplay qualifies race rendering, fitment and AI behavior.
