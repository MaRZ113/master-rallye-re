# Retail Trooper physics

The primary binding is **physics family Trooper, model donor Trooper**. The
physics values come from retail `DataGame/vehicles.xml` and
`DataGame/Modifications.xml` inside the clean retail `Data.sma`; no Astero
physics data is copied.

| Check | Result |
|---|---|
| Family | `Trooper` |
| Semantic compatibility | `COMPATIBLE` |
| Total family fields | 147 |
| Fixed required fields | 120 / 120 present |
| Player1 modification fields | 13 |
| Groups | Chassis 16; DamageParams 25; Dimensions 8; Engine 45; Steering 5; Suspension 48 |
| Engine gears / torque entries | 7 / 6 |
| Config SHA-256 | `vehicles.xml`: `a6762bb20999c7224c71b9f5d1d7edca55bcea147ff9f973300a8cf8d350aee0`; `Modifications.xml`: `16df5a3a6b0c50c40f4ee74186e47b40294e6cb4ac11e0a3d7d20dafb8a5a65d` |

Selected retail values:

| Property | Value |
|---|---:|
| Wheelbase | 2.40000 |
| Front / rear track width | 1.65000 / 1.65000 |
| Front / rear wheel radius | 0.38000 / 0.38000 |
| Body height | 1.50000 |
| Total mass | 1350.00000 |
| Front / rear ride height | 0.05000 / 0.05000 |
| Front / rear spring rate | 34000 / 32000 |
| Front / rear damper rate | 2200 / 2100 |
| Front / rear max bounce | 0.30000 / 0.30000 |
| Front / rear max droop | 0.10000 / 0.10000 |

R-PHYS3/R-VEH1 established runtime-tested filewise loose-over-archive model
composition and separated model donor from physics family. The earlier
R-COOKER1.1 Trooper test confirmed the three converted model files and prior
Trooper operation in retail. Neither result is a runtime test of ID25 bound to
Trooper; this candidate still needs the P1 test in
[runtime-test-plan.md](runtime-test-plan.md).
