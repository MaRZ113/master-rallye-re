# Master Rallye vehicle classes — working map (2026-11-13)

Owner decision 2026-11-13: **T4 = trucks only**; the retail Kamaz (ID22, now T3) moves to
T4. Further distribution of cars is the owner's; the table below is the working proposal.

| Class | Content | Candidates (source) |
|---|---|---|
| T1 UNMODIFIED | stock 4x4/SUV | retail T1; Evo 2 stock SUVs; Michelin RAV4; TXR3 Isuzu VehiCROSS; Evo 2 GC Jeep Wrangler Rubicon |
| T2 MODIFIED | prepared 4x4/SUV | retail T2; Evo 2 Rally Editions; Paris-Dakar BushRanger |
| T3 CUSTOM | fun / special | retail T3 (without Kamaz); Evo 2 GC Stillen monster truck; CMR Baja Bug, Hovercraft |
| **T4 TRUCKS** | trucks | **Kamaz (retail ID22)**, Dakar 2 Hino, Paris-Dakar Tatra / Nippon / KTM trucks, DiRT Kamaz / MAN |
| T5 RAID | rally-raid prototypes | Dakar 2 Pajero and Nissan (currently in the T4 pilot), Paris-Dakar Pajero RED/Silver, L200, Hilux, Patrol, MEGA Desert; Total Drivin' Citroën ZX Rallye Raid; Evo 2 race trucks (Calmini, Warn, Tundra, Frontier) |
| T6 WRC | modern rally | Michelin WRC, GT3 rally cars, RCX, CMR |
| T7 GROUP B / CLASSIC | historic | Michelin Group B, RCX Quattro/Stratos, Rally Trophy |
| T8 KIT / F2 | front-drive kit cars | Michelin F2, RCX small cars |

Engine notes: the current T4 layer is frontend-only (records keep race class T3);
T5+ need race-side class support (opponent switch `0x458090`, group `0x4F`,
championship keys) — see `research/vehicle-class-t4:docs/sdk/NEW_CLASS_RESEARCH.md`.
Moving Kamaz is a roster/registry change (class field +8 of its record and the
Vehicle Select maps), to be done in the Vehicle Manager roster, not in this branch.
