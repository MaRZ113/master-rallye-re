# R5V-E0.1 validation and provenance

## Scope

R5V-E0 was closed first in commit 21f8f65. This phase reads retail
configuration/assets and targeted retail Ghidra analysis; it does not alter
MRallye.exe, Data.sma, game assets, scene XML or registry capacity. No runtime
candidate, patch manifest, diagnostic redirect or Forklift activation was
created. Tracks were not examined.

The owner supplied the E0 P0/P1 FULL PASS report, including ID25 selection,
Trooper preview and race model, physics, collision, damage, stage completion,
results and return to menu. The report also says existing vehicles remain
available. The exact test executable hash and raw captures were not supplied.
See research/r5v_e0/findings.md for the attribution limits.

## Static evidence

Retail scene/resource inventory inputs:

| Input | Size | SHA-256 |
|---|---:|---|
| DataScene/FrontendScreens/VehicleSelect.xml | 148,236 | EC7FD6372FE5008B1039EB8E09890EF3B37396DAD1581568AF439CBB611B58E1 |
| DataScene/FrontendScreens/RaceResults.xml | 41,035 | 3CF61487CD54AA2E5FC03DED9C292F78320F00D0AD7BA39F184FD40DAA603818 |
| DataScene/Hud/Hud0.xml | 124,360 | 91616CAA529FB4762E8E263F58BFE0F35EE5AEBF127E8BA2FC3014A677EA4DBF |
| DataScene/Hud/Hud1.xml | 206,653 | 9146CB6832CD3FE70B9E1765019A20CE0EA886DA3DD035DAFAAA9DC195BEFFBE |

Targeted raw Ghidra observations used:

- FUN_00481950 and FUN_004819B0: button update, absolute selection ID,
  localization queries and direct stats loads.
- FUN_00481E20: class-local to absolute ID conversion.
- FUN_0045A3C0 and FUN_00458E70: registry accessor/object base and record
  layout, cross-checked with R5V-B.1.
- FUN_0047C840, especially 0x0047CB41–0x0047CB5E: Race Results producer and
  VehicleRecord +0x1C read.
- FUN_00530300, FUN_004E23E0 and FUN_004E1FF0: property-to-image-selector
  update.
- FUN_004A71B0, FUN_004A72A0 and FUN_004A74A0: progress marker setup/read/update.

Ghidra used the existing local 12.0.4 installation and a read-only project
copy. Raw exports and generated image inspections remain under ignored
.research-output/r5v_e0_1/ and are not committed. No ReAgent reconstruction
was used; conclusions above are based on raw Ghidra assembly/decompilation,
scene/resource inventories and the attributed human report.

## Automated validation

The repository synthetic suite is run at E0.1 closeout with the command below.
This phase adds research documentation only, so no new parser or unit tests
were introduced.

    $env:PYTHONPATH = 'src'
    & 'C:/Users/MaRZ/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -m unittest discover -s tests/synthetic -v

Result: **195 tests passed** in 11.098 seconds. The test suite does not
reproduce gameplay.

## Evidence limits

- The name lookup selector is raw-code supported; the final rendered English
  label is corroborated by the owner and retail EXE strings.
- Stat field reads and values are directly attributable to ID25 initialization.
- Vehicle Select mapping absence is established by the static retail scene.
- Race progress icon is a generic static resource. The separate 1P graphic
  described by the owner remains unidentified without a screenshot/object match.
- Race Results numeric frame selection is directly supported by the producer
  and consumer path. Frame 0 looking like Astero is visual corroboration.

No game binaries, proprietary assets, screenshots, Ghidra project or raw
analysis export are part of this documentation commit.
