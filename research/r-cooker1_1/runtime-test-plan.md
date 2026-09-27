# R-COOKER1.1 Trooper runtime test and closeout

**Status: PASS — CONFIRMED_BY_RUNTIME.** The project operator reports that
retail accepted the minimal rev131-derived Trooper candidates. The result
closes the R-COOKER1.1 runtime gate for these three tested resources only.

## Candidate package

The tested package consisted of the three generated files in the ignored
directory:

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

## Recorded runtime result

- Frontend complete model: works.
- Race car model: works.
- Wheel model: works.
- Textures/material appearance: correct.
- Geometry: appears correct; no visible model deviations were observed.
- Vehicle operation: remains operational in retail.
- Collision and damage behavior: not separately reported.

For these Trooper assets, retail compatibility does not require the official
9.10.0 local triangle reorder. This is `CONFIRMED_BY_RUNTIME` for the tested
`complete.dx`, `car.dx`, and `wheel.dx`; it does not establish universal
rev131 compatibility. The backup and restore procedure above remains the
reversible way to repeat the test.
