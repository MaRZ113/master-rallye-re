# Per-vehicle availability

## Native gate

Retail source SHA-256:
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.

Ghidra 12.1.4 identifies `FUN_0045A150` as the availability helper. Its
Vehicle Select caller passes the native record in ECX. The helper reads the
physical ID at `[ECX+4]` and returns its decision in AL. It first checks
`Progress/Cheats/UnlockAll` and `Progress/Cheats/UnlockCars`; either true makes
the vehicle available. It then switches on absolute ID. Listed special IDs
read one named `Progress/UnlockedCars` field; the default arm returns
available. The only direct retail call reference found is `0x004819CE` in the
Vehicle Select screen path.

`UnlockCups` is not an individual-car bypass in this function. It participates
in class/mode reachability elsewhere.

## Stock IDs 0..25

“Gate result” is the per-vehicle helper, before class reachability and
mode/event eligibility. On a pristine Progress.xml profile, all unlock flags
and relevant cheats default false. “Fresh selectable” also accounts for the
observed Quick Race class reachability (T1 only).

| ID | Class / local | Retail vehicle | Per-vehicle gate | Fresh Quick Race selectable | Evidence |
|---:|---|---|---|---|---|
| 0 | T1 / 0 | Landcruiser | unconditional | yes | switch default |
| 1 | T1 / 1 | Pajero | unconditional | yes | switch default |
| 2 | T1 / 2 | Tata | unconditional | yes | switch default |
| 3 | T1 / 3 | Terrano | `T1CupCar1` | no | ID case + default false flag |
| 4 | T1 / 4 | Chevyblazer | `T1CupCar2` | no | ID case + default false flag |
| 5 | T1 / 5 | Xtrail | `T1CupCar3` | no | ID case + default false flag |
| 6 | T1 / 6 | Frontera | `T1MasterRallyeCar` | no | ID case + default false flag |
| 7 | T2 / 0 | Navara | unconditional | no, class gate | switch default |
| 8 | T2 / 1 | Forester | unconditional | no, class gate | switch default |
| 9 | T2 / 2 | Jump | unconditional | no, class gate | switch default |
| 10 | T2 / 3 | Rmonster | `T2CupCar1` | no | ID case + default false flag |
| 11 | T2 / 4 | Patrol | `T2CupCar2` | no | ID case + default false flag |
| 12 | T2 / 5 | Newrav | `T2CupCar3` | no | ID case + default false flag |
| 13 | T2 / 6 | Kiasportage | `T2MasterRallyeCar` | no | ID case + default false flag |
| 14 | T3 / 0 | Wildcat | unconditional | no, class gate | switch default |
| 15 | T3 / 1 | Simmbugghini | unconditional | no, class gate | switch default |
| 16 | T3 / 2 | Astero | unconditional | no, class gate | switch default |
| 17 | T3 / 3 | Kangoo | unconditional | no, class gate | switch default |
| 18 | T3 / 4 | Megane | `T3CupCar1` | no | ID case + default false flag |
| 19 | T3 / 5 | Mattserati | `T3CupCar2` | no | ID case + default false flag |
| 20 | T3 / 6 | Bruno | `T3CupCar3` | no | ID case + default false flag |
| 21 | T3 / 7 | SeatBuggy | `T3MasterRallyeCar` | no | ID case + default false flag |
| 22 | T3 / 8 | Kamaz | `ChallengeCar` | no | ID case + default false flag |
| 23 | T3 / 9 | Icecream | `Invitation` | no | ID case + default false flag |
| 24 | T3 / 10 | Ufo | `Bonus1` | no | ID case + default false flag |
| 25 | no stock record | — | `Bonus2` special case | no stock actor to select | predicate exists; pristine record is uninitialized |

`T2` and `T3` vehicle gate results marked unconditional do not imply those
classes are reachable in a fresh Quick Race. ID25’s predicate is real code,
but its stock vehicle identity/class are not established because that registry
record is not initialized in pristine retail.

## Frontend representation

`VehicleSelect.xml` keeps locked vehicle controls in its class layout and uses
the frontend disabler/unlocker behavior to represent locked entries; it does
not prove that all runtime callers enforce the same gate. T1 local3-6 and the
corresponding later-class controls show locked-state UI. The T3 local11 control
is absent from the stock XML. ID26’s class slot and UI are separate R5V-F
extensions; G.1 changes only its availability predicate input.
