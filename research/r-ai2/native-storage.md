# Native storage, update and destruction

## Participant representation and Broker

`4ADA50` allocates the Race access wrapper0xCC, constructor `4ABBD0`. Its +38
is the cached NumCars key; +60/+64/+68/+6C/+74/+7C are scalar suffix keys for
PlayerType/CarType/CarID/WheelType/CarClass/DriverID. They are **not participant
array offsets**. `4AC590` constructs `Race/Car` + decimal N; native setters take
N independently. `493600` formats the Vehicles/CarN namespace. Actor, physics,
AI, progress and result storage have distinct owners.

## Physics and AI

Physics manager0x80 (`43DD40`) has begin/end/capacity at +18/+1C/+20. Creation
is `43EF80` -> `43F020` -> `43E4C0`; new handle0x2C, vector insertion `43BB70`.
Collision registration `43A800` grows +0C/+10/+14 storage; `43AC80` scans its
length and each car's four wheels. `43F890` performs two physical substeps;
its helpers `43F650/43F960/43FA00/43FD50/43FB60/43FC00/43FDA0/43FE00` use
vehicle vector length. `43F450` removes dead handles; `43E020` destroys/frees
all remaining handles and vector storage. These container relationships do not
establish collision behavior in a five-car game run.

AI manager0xC8 (`42A540`) has vector +88/+8C/+90. `42A890` creates an0xD4
controller for each PlayerType2, attaches N via `42CDB0`, and inserts using
`42AD40`. `42AC10` alternates half-vector updates; successive ticks cover the
actual vector. `42BA00/42BD90` and collision helpers use container length.
Correct destructor is **42A6B0**, reached from deleting destructor42A660.
42A680 is a separate vector helper, not the manager destructor. `42A6B0`
walks every controller, calls42CDA0, frees it, then frees the vector.

## Progress, finish, reset and Results

| Owner | Count / physical allocation | Tick / destruction |
|---|---|---|
| 489AF0 | +14 N; +2C/+30 arrays N*4 (Race/Network Finished keys) | 489EC0 / 489A80 |
| 48A880 | +0C N; +10/+14/+18/+1C/+20 arrays N*4 | 48AB20 / 48A810 |
| 48B520 | +2C N; +10 byte[N], +14/+18/+1C/+20/+24/+38 dword[N] | 48AE30 transient rank pairs N*8 / 48ADC0 |
| 48CFE0 | +0C N; +10 byte[N], dynamic per-split CarN keys | 48D260 / 48CC20 |
| 4CC5F0 | +14 N; fifteen separately allocated N*4 arrays +18..+50 | 4CCAF0 / 4CC420 |
| 4CDF00 | +2C N; seven N*4 arrays +20/+24/+30/+34/+38/+3C/+40 | 4CD9B0 / 4CD920 |
| 47D6D0 | each result0x1C; +2C/+30/+34 pointer vector grows via47DBE0 | 47D100 sorting; 47C840 lists; 47C7C0 releases vector block |

Result record: +0 participant index, +4 DriverID, +8 absolute CarID, +C time,
+10 points, +14 sorted position; +18 is not required for the capacity decision.
Finish-area and ranking loops use stored N. Ordinary RaceType2 sets
FinishingType0 at449E90; the FinishingType1 Car0..3 RaceState writes in489EC0
are excluded by the proof configuration.

**Stock reclamation caveat:** 48ADC0 releases five of the seven blocks allocated
by48B520; +20/+24 cached-key arrays are not released by that destructor. Thus
the stock four-car path retains32 bytes there, the five-car path40. The Results
destructor frees its pointer vector without visibly freeing every0x1C pointee;
complete reclamation of those records was not established. This is existing
ownership behavior, not a four-element cleanup bound. R-AI2 does not repair it
or claim every stock heap allocation is reclaimed. Native emulation proves the
fifth physics handle and fourth AI are destroyed and no redzone is written.
Long-run memory stability is not established by a short human proof.

## Scene and Replay

Scene eggs are linked-list nodes. 4F60F0 drains the deletion/new/priority lists;
4F61A0 processes deferred destruction; 4F5780 destroys each egg's four AI slots
and render resources. Four is an **intra-egg** AI-slot count, not a car count.
Wheel/body nodes are released through those lists and the physics/AI managers.

4CADF0 allocates N*0x10+4, stores N in its array cookie, initializes N replay
containers. Each container holds dynamic0x30 frame records. Recorder4CB9B0/
4CBB50 and playback4CB150/4CB410 iterate cached N; 4CB950/4CB0E0 release their
key/flag vectors. Frame-container replacement uses the allocation cookie.
Frame-count limit0x7FFF0 is not a participant bound. Camera viewport ordinal
(+214) remains0 for one human; focus index(+210) and NumCars(+218) are separate.
