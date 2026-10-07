# ID27 I.0 slot-proof profile

I.0 assigns physical ID27 to T2 local7 while temporarily using stock physical
ID7 / Navara as the render, wheel, physics and audio donor. This isolates the
registry/class-slot question from the availability of a second complete T2
asset family.

| Property | Diagnostic value | Meaning |
|---|---|---|
| Physical ID / class / local | 27 / T2 / 7 | new slot identity |
| Donor physical ID | 7 / Navara | stock resource family reuse |
| Frontend stats | 7 / 6 / 6 / 5 | diagnostic record values |
| Smallcarsheet / Vehicle Select frame | 13 / 23 | stock Navara presentation donor |
| Race colour | cyan (0,1,1,1) | physical-ID canary |
| Unlock oracle | ID10 / `T2CupCar1` | native T2 lock semantics |
| Audio profile | 7 | Navara donor only |
| Results label | `ID27 SLOT PROOF` | explicitly non-production |

ID7 remains intact as its own stock T2 vehicle. ID26 remains Mercedes with
its established T1 mapping, resources, audio profile0 and Strugo Results
display. Native DriverID selection is not changed. These values are static
candidate properties until human runtime tests confirm them.

Passing I.0 would prove a second allocated/indexed registry slot and its
bounded runtime use with a donor. It would not prove that an independent
second addon vehicle exists, nor complete R5V-I.
