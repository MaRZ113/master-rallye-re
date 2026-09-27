# R-COOKER1.1 retail runtime test plan

**Status: PENDING.** This is one controlled test of the generated
rev131-derived candidate package. The project operator runs the game; do not
change physics configuration or use official 9.10.0 DX as candidate input.

## Candidate package

Use the three generated files in the ignored directory:

```text
.research-output/r-cooker1_1/runtime-candidate/car.dx
.research-output/r-cooker1_1/runtime-candidate/complete.dx
.research-output/r-cooker1_1/runtime-candidate/wheel.dx
```

Verify hashes against `manifest.json` before copying. The candidate package
was generated from the paired rev131 DX files by the research prototype; it
preserves their local uint16 index order. It is not copied from official
rev135 output.

## Procedure

1. Close the game. In the same retail setup that previously loaded the Trooper
   restoration, back up the current three files from
   `DataGx\Vehicles\Trooper\` to a separate scratch/backup folder.
2. Replace only `car.dx`, `complete.dx`, and `wheel.dx` in that working Trooper
   package with the three candidates. Keep the existing compatible DXT files,
   executable binding, and vehicle physics/configuration unchanged.
3. Launch the established Trooper restoration path and check the frontend and
   race behavior below. Do not edit the authoritative `inputs/` files.
4. After recording the result, close the game and restore the three backed-up
   DX files. No permanent executable or configuration change is part of this
   test.

## Record these observations

- Does the frontend Trooper model appear?
- Does race loading succeed?
- Is the race body visible?
- Are wheels visible?
- Are materials and textures correct?
- Is wheel placement normal for the existing Trooper physics?
- Does collision work?
- Does damage behavior work?
- Does the game crash during vehicle load or race entry?

The central result is whether retail accepts the candidate without the
official 9.10.0 local triangle reorder. A pass would be runtime evidence only
for these tested Trooper assets and this retail setup. A failure should be
reported with the exact point of failure; do not broaden into cooker analysis
before localizing the result.
