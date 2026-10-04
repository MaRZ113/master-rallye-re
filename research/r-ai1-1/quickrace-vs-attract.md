# Quick Race versus Attract

| Boundary | Quick Race | Attract Type14 |
|---|---|---|
| Owner / chooser | `0x47B780 / 0x458090` | `0x449E90 / 0x4584F0(false)` |
| Human boundary | One human: firstAI1,count3; excludes human absolute ID | Zero humans, loop starts0 |
| Class policy | One requested Car0 class selects pool | Broad vehicle-first pool0..20; derive class later |
| Unlocks | Ordinary7 IDs per requested class; T3 bonus reward checks | Ordinary21 across all classes; same bonus reward checks |
| Drivers | Separate single0..9 pool; `0x458980` | Same |
| Vehicle shuffle | `0x450580`, CRT rand after game RNG seed | Same |
| Publish | Per-N CarID, registry class, DriverID | Same |
| Replay/lifecycle | Ordinary Quick Race rules retained | Demo lifecycle, record/playback disabled |

Shared helpers: vector init `0x411650`, clear `0x41FA50`, insert
`0x414920/0x411C90`, erase `0x416620`, size `0x4116A0`, vehicle shuffle
`0x450580`, driver shuffle `0x458A80`, game RNG `0x4D1E90/0x4D1DF0`, CRT
`0x5C37AB/0x5C37B8`, registry `0x45A3C0`, Broker wrapper `0x4ADA50`, setters
`0x4ACAF0/0x4ACC10/0x4ACCD0`. **CONFIRMED_BY_EXE**.

## Downstream delta only

The new loop still publishes each N=1,2,3 exactly once; Car0 is never passed to
a new setter. Driver construction runs once, not once per selected class.
The original model/physics preparation loops iterate the existing four slots
and read each participant's ID/family. Result collector `0x47D6D0` and HUD
`0x4AAE70` already read per-N ID/DriverID; no slot-specific Car1 special case
was found at these boundaries. No result/HUD/camera/network capacity patch.

The R-AI1 [downstream audit](../r-ai1/downstream-consumers.md) applies without
a new actor path. Car0-derived AI balance scalar (`0x42CFFA/0x42E020`) and race
description class (`0x4BBE8C`) remain normal T1 values. Fixed runtime validates
one T3 AI; Attract validates stock multi-slot mixed selection. Multiple mixed
Quick Race AI, results and frontend return still require the new human test.
