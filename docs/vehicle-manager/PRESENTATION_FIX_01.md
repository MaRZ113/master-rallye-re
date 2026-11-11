# Roster V4 presentation fixes

This candidate derives from the actual `host-roster-01/MRMods/Vehicles/active`
transaction, not its older `catalog.json/source_runtime`. Neither the source
host nor its EXE, DLLs, saves, options or original data is changed. The output
is a separate `host-roster-fix-01` under `.research-output/hosts`.

## Changes

* Trooper physical ID29 uses existing SIDE/Results frame **23**, identified by
  the owner. The shared image bank and all texture bytes are unchanged.
* Mercedes' initial CarSheet frame was already 40, but its
  `gaFrontendDisablerAI/True Value` was 3, a Landcruiser frame. Synchronize the
  unlocked frame with the widget's actual frame. The same defect affected
  Trooper (41) and ForesterSTI (42); these are repaired together.
* Forklift ID25's native unlock check requires `Progress/UnlockedCars/Bonus2`
  or the existing UnlockCars/UnlockAll cheats. The restored button had neither
  a disabler nor an unlock controller. Reuse the ordinary stock bonus-button
  controllers with Bonus2 and frame31, so a locked entry cannot be selected.
  No save flag is changed and no unconditional unlock is introduced.
* ForesterSTI, Rav4 and Tomcat each had an environment-enabled unlit brake
  core and halo (feature mask5). Disable that environment bit to obtain stock
  mask1, using Vehicle SDK `patch_dx_attributes(material_env=...)`. Exactly
  two bytes change per car. Geometry, UVs, indices, state selectors, blend
  flags, lens fitting, textures and collision are preserved. The unused
  secondary texture name stays in place, preserving the binary layout.
  Trooper already has stock-like mask1 brake materials and is preserved.
  Mercedes and Forklift do not have authored native brake switches; this fix
  does not invent lens geometry for them.
* Use the Vehicle SDK race-marker colour API to author the other added cars'
  progress-marker colours. **All stock ID0-24 and ForesterSTI ID30 retain
  their exact original float32 RGBA bytes**, following the owner's correction.
  Modified IDs:25,26,27,28,29,31,32,33,34. ID34 remains outside the current
  menu maps, exactly as in the source; its reserved record is not reactivated.
  Colours represent the default model/livery; runtime model/livery-specific
  marker switching is outside this presentation fix.

The editable palette and frame choices live in `presentation-fix-01.json`.
Physical IDs, family identity, stats, class maps/order, physics, AI, model
variants, courses and every unrelated native patch remain unchanged.

## Native evidence

Retail EXE SHA-256:
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.

* `0x4819CE`: active frontend unlock CALL, followed through the installed SDK
  bridge during emulation.
* `0x45A150`, case25 -> `0x45A282`: flag index15 via `0x4AFB70`.
* `0x4AFB70`: `Progress/UnlockedCars/` + table entry from `0x6F682C`.
* `0x4AFAF0`: unlock-flag writer. The resolved native call graph contains
  reset `0x4AFC00`, championship award routines `0x450310`, `0x453D10`,
  `0x45B5B0`, and menu setup `0x480B60`. In those inspected original paths,
  flag15 is reset but no normal competition award sets it true. This is a
  dormant Bonus2 gate, not evidence of a missing new championship reward.
* `0x45A0B0`: VehicleRecord initializer, 52-byte destination stride. Seven
  integer arguments, temporary native string and four RGBA float32 arguments.

REA/Ghidra confirmed the original unlock/writer functions. The current MRVR
transaction, its preimages and instruction encodings were checked separately.
The format remains MRVR1 / RVP1 / MRVC1. Payload size, descriptor and writable
ranges are unchanged. New immediate edits respect sparse previous ownership;
the candidate has no overlapping native operations.

## Reproduction and checks

Run from the BASE checkout with Python3.11, Pillow, Capstone and Unicorn:

```powershell
py -3.11 tools/vehicle_presentation_fix.py --source-host .research-output/hosts/host-roster-01 --output-host .research-output/hosts/host-roster-fix-01 --sdk ../master-rallye-re-vehicles --spec docs/vehicle-manager/presentation-fix-01.json
py -3.11 tools/verify_vehicle_presentation_fix.py --source-host .research-output/hosts/host-roster-01 --candidate .research-output/hosts/host-roster-fix-01 --sdk ../master-rallye-re-vehicles --spec docs/vehicle-manager/presentation-fix-01.json
```

The builder requires a fresh output directory. It copies mutable host files;
only the unchanged, read-only Data.sma is hardlinked. No game is started by
either script. The scripts deliberately target this reviewed 35-record
presentation specification; they do not introduce a registry capacity limit.

Automated validation executes the native callers for all35 initializers with
intercepted string and record sinks, checking names, IDs, class/stats, icon
indices and exact RGBA arguments. It also follows the installed unlock bridge
for four Bonus2/cheat combinations, verifies every menu true-frame binding,
checks all native preimages/overlaps and confines binary changes to colour/icon
fields. Three brake models retain identical geometry/UVs/collision; native
logical brake cases are unchanged. Host comparison admits only six modified
files: roster, catalog, VehicleSelect.xml, and the three car.dx files. EXE,
both proxy DLLs, saves, options and every texture stay byte-identical.

Reports, source/build hashes and the palette image are in the candidate root.
Status: **OFFLINE_VALIDATED**. The game has not been launched for this fix.

## Narrow owner test

Start `.research-output/hosts/Launch-roster-fix-01.cmd`.

1. Mercedes, Trooper and ForesterSTI: correct unlocked CarSheet before and
   after moving selection away/back. Other cars retain their existing icons.
2. Forklift: with Bonus2/cheats false the entry is locked and cannot start a
   race. Using existing UnlockCars/UnlockAll should enable both image and
   selection. Do not change the production save for this check.
3. Trooper: historical frame23 in the participant HUD and Results.
4. ForesterSTI, Rav4, Tomcat: compare brake released/pressed, including night;
   no reflected environment on the lit core/halo. Judge remaining halo size
   and brightness visually; no new lens fitting was performed.
5. Check the added cars' Progress Bar colours. Stock cars and ForesterSTI
   must retain their old colour. The palette image supplies a quick comparison.
