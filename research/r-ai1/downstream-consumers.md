# Downstream mixed-class audit

This is a bounded ordinary offline Quick Race audit, not all game modes or full
subsystem reconstruction. The cited path/key/data selection is
**CONFIRMED_BY_EXE**. The table preserves the original runtime-check checklist;
fixed ID14/Driver7 model/physics/contact/driving/results observations have since
passed [the bounded runtime proof](runtime-result.md). Other combinations remain
unconfirmed; the table does not imply every listed behavior was exercised.

| Consumer | Observed selection and evidence | Remaining runtime check |
|---|---|---|
| Identity preparation | `0x44A320` loops current NumCars; `0x44A450` human/AI types; `0x44A510` per-ID registry family -> CarType/WheelType/colour | Exactly four actor identities |
| Body model | `0x4B6A00` Frontend/Active branch, N<NumCars, CarType getter; `0x4B7027` Vehicles/<own family>/car | Visibly Wildcat, no alias |
| Wheels | Same owner; `0x4B71E1` Vehicles/<WheelType>/wheel | Correct loaded wheels |
| Physics | `0x44ED50 -> 0x493E30/0x4938C0/0x493600` copies own named family to Vehicles/CarN | Target wheelbase2.77, front track1.66, diff ratio3.72; movement |
| Collision | Own loaded stock body and bound information used by AI init `0x42CDB0`; both body DX retain stock tag101 collision data | Actual normal contacts, recovery and no unstable collisions |
| AI | Per-N driver/controller/own physical ceiling; player class scalar retained (`0x42D0D0/0x42E020/0x42DDE0`) | Target drives, progresses, finishes |
| Camera | `0x4B8810` selects humans by PlayerType; camera+0x210 target participant, +0x214 human ordinal | Player camera stays normal; full camera logic not reconstructed |
| HUD/name | `0x4AAE70` per-participant CarID -> registry row image/localization | Target marker/name/image where exercised |
| Results | `0x47D6D0` per-N CarID/DriverID/time/Finished -> stride0x1C record; `0x47C6C0` initializer | Normal result/end/return path |
| Race class title | `0x4BBE8C` reads Car0 class for race description | Title remains T1; it is not every car's class |
| Sound | `0x408F20` own CarID switch includes stock ID0 case | Target normal sound where audible |
| Damage | `0x4A41F0` own CarN handle/global damage thresholds; named DamageParams copied with each vehicle's physics family | Normal damage behavior as exercised; whole damage system not reconstructed |
| Reset/recovery | `0x4CC5F0` registers own CarN/Controller/Progress/LastMarker/LimitState/ResetNo/Finished/Resetting; `0x4CCAF0` operates these handles | Normal recovery if exercised |
| Network-style mirrors | `0x4333D0` registers per-N Network/CarN/Finished and FinishTime; no class filter at this boundary | Paths alone do not establish live network/vehicle actors |

## Lifecycle gates

`0x449D40 -> 0x449E90` chooses ordinary offline preparation. Campaign modes
5/6/8 use `0x44A710` and network uses `0x44A8E0`, outside this proof.
`0x44ED50` has an alternate non-running frontend/campaign source; use the
normal active/running frontend flow. A previously supplied frontend capture
showed Active/Running=True, mode2, three opponents: **SOURCE_EVIDENCE**, not
R-AI1 runtime success. The oracle requires Frontend/Active=True in mixed-race.

At `0x4B6B17`, the active frontend branch takes its own Race CarType and jumps
to `0x4B6F9F`. The inactive branch uses authored scene car names and can set
DriverID/NumCars. Successful Broker assignment must not be treated as proof
that a different branch instantiated the intended car.

`0x48EB40/0x4C0B20` inspected here concerns placement/optional spline recording;
it is not relied on as the normal body/physics materializer. No course editing
or spline reconstruction was performed.

## Protected corpus cross-check

Both normal stock families have their car/complete/wheel resources and named
retail physics. Fresh body parser checks passed with collision sections present:

- LandCruiser/car.dx SHA256 `c3a61a935244e9e1dcfcd72ecf993ea301e371794ba33d931dd8cfd205627103`;
- WildCat/car.dx SHA256 `ccbcb74985d5b21a594b471eb42d242b5eb5809d8646e57ece08b4a1cd6614cd`.

Named physics distinguishing Landcruiser from Wildcat: wheelbase2.45 vs2.77,
front track1.50 vs1.66, diff ratio3.95 vs3.72. These are
**CONFIRMED_BY_CORPUS**, not proof of which actor loaded them. Model/physics/
collision identity and stability for other combinations remain the human runtime gate.
