# Mercedes GXM authoring-path bridge

**Historical Mercedes T1 setup notes.** The completed T1 result is in
[oracle-t1-texture-miss.md](oracle-t1-texture-miss.md). Generic authoring-path
discovery and guarded-script generation are implemented in
`src/master_rallye/authoring_paths.py`; current jobs generate their own mirror
and helpers. The historic Junction remains absent unless an operator runs the
exact generated helper for an active job.

## Evidence and current setup

The selected Demo 8.4.1 Mercedes GXM embeds absolute GXI references under
`D:/projects/MRallyeTNG/DataGx/Vehicles/Mercedes/`. The exact complete source
reference used by T1 is `Underdash-tga.gxi` (SHA256
`c8e3578ac885531aad2dc8c56ba2b5edcdf35237b325a09452626b6ae436ded5`).

At preparation time, the historical link path
`D:\projects\MRallyeTNG\DataGx\Vehicles\Mercedes` is absent. A local copy of
all 25 hash-locked GXI files, their source manifest, and the fixed setup,
check, and removal scripts is staged under the current branch's ignored
`.research-output/r-cooker3/source-bridge/`. The prepared T1 retail workspace
is also in this branch's ignored scratch. The script's computed target is
`source-bridge/authoring-root/Mercedes`, so all created bridge state stays
inside this branch tree except for the exact Junction node at the historical
path.

The three copied helper hashes were rechecked from the prepared copies:

- `SETUP_MERCEDES_JUNCTION.ps1` — SHA256
  `d28084e3894bac8001b3f0ae189e3641d1f2e12d3b4cbb7c2f44744bc6846920`.
- `REMOVE_MERCEDES_JUNCTION.ps1` — SHA256
  `d31cc152aaaccaafd4d13e34cae7616e9709c8078c758fa793a0caee97a5b926`.
- `CHECK_AUTHORING_PATH.ps1` — SHA256
  `77bc4b7327a94d7b7d77226c1b1bbbcc2afba5853d2a8a6f5f86ae84b12c27cb`.

Do not hand-create a junction. Use the prepared helper pair, which checks the
ownership marker, target, reparse type, source inventory, and all 25 GXI
hashes. The setup helper refuses an existing leaf directory or unknown link.
The removal helper removes only the verified Junction node with
non-recursive directory deletion and rechecks that the target GXIs remain.
The optional `RECOVER_R5V-F.2b_MERCEDES_JUNCTION.ps1` was intentionally not
copied into this branch scratch. If setup or cleanup refuses, stop and inspect
the marker/link state rather than invoking a recovery path.

## T1 sequence

From the demo-cooker repository root, run the copied setup helper:

```powershell
& ".\.research-output\r-cooker3\source-bridge\scripts\SETUP_MERCEDES_JUNCTION.ps1"
```

Then inspect the returned
`Get-Item` data: `LinkType` must be `Junction`; `Target` must resolve exactly
to this branch's `source-bridge/authoring-root/Mercedes` copy. If anything
differs, stop and do not repair it manually.

After the T1 run, remove only the marked Junction with the copied helper:

```powershell
& ".\.research-output\r-cooker3\source-bridge\scripts\REMOVE_MERCEDES_JUNCTION.ps1"
```

Confirm the link is absent and all 25 GXI hashes still match.
If cleanup refuses, do not delete the path or target; report the marker,
LinkType, and target state for review.

## T2 sequence

T2 requires the historical link path to be absent. The previous cache-only
workspace removed the exact link safely and left the source target intact.
For T2, only verify absence. Do not run another removal helper against a
missing path, and do not create a link. If any entry exists at that path,
abort T2 until its type/owner is understood.
