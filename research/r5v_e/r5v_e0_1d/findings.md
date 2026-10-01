# R5V-E0.1d progress marker colour producer

## Verdict

**Historical E0.1d status: producer unknown at that phase. Follow-ups: runtime precedence passed by user report; VehicleRecord-tail-to-Race/CarN/Colour path confirmed statically in R5V-E0.1d.2; isolated ID25 red-tail A/B is FULL PASS by user report.** The old slot-0 bypass crashed during race loading and is invalid because its helper violated the stack ABI. That crash is not colour-precedence evidence.

The prior R5V-E0.1c commit remains an accurate record of its then-current blocked state. This phase adds evidence and candidates without replacing that history. E0.1c closeout commit: `685cf1f`.

## Established static evidence

- Retail identity was rechecked: `MRallye.exe` SHA-256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`; `Data.sma` SHA-256 `9bdf132cfde6e443e32f937b99289b07e9527457ae48fa9c7e0a373b52a28f30`.
- `FUN_004A74A0` reads HUD display slot `this+0x18`, forms `Race/Car%d/Colour`, calls the property-exists getter at `0x004A7661`, and copies four 32-bit components if the property exists. The ghost path replaces the colour with white RGB and alpha `0.5`. Raw assembly and the prior Ghidra P-code export agree.
- The object colour loaded from HUD XML is available as the consumer's initial tint. The `Race/CarN/Colour` property conditionally replaces those components in the consumer. R5V-E0.1d.1 user reports establish tested precedence: the property wins normally, and XML becomes visible when the ABI-safe bypass suppresses it.
- The retail archive contains 48 `DataScene/RaceTest/*.xml` files. Forty-seven have a `HudLoader`; each uses `Hud No=0` and `HudXml Location / Name=Hud/Hud0`. The one-player diagnostic therefore edits `Hud0.xml` only. `Hud1.xml` is not part of that one-player path.
- `FUN_0048E2D0` calls `FUN_0048EB40` in its race setup path. `FUN_0048EB40` conditionally constructs a `gaVehicleSplineRecordAI` helper through `FUN_004C0B20` when spline recording is enabled. That constructor registers/reads sibling paths including `Race/Car%d/CarType`, `Race/Car%d/Time`, and `Race/Car%d/Finished`; it is not evidence of the general participant property writer.
- `FUN_004B6A00` handles a `Race/Car%d/DriverID` path and vehicle/driver setup. No Colour write was found in the inspected function. `FUN_0047B780` restores `Frontend/QuickRace/Car0` and `Car1` values into race CarID/CarType state; it does not write the colour property. `FUN_004ADF50` is a generic Quick Race setter helper with no direct callers in the analyzed retail project.
- The complete literal `Race/Car%d/Colour` has a direct code reference in the inspected retail image at the HUD consumer. Schema registration in `FUN_004ABCE0` is not a value producer. A generic schema/struct writer may still materialize the value without that literal; this phase did not identify one.

## Diagnostics and later human results

1. **XML-only:** the retail `Data.sma` copy changes only `ProgressCar0 / gaHudAiRaceProgress / ObjectColour` from `1.00 1.00 1.00 0.50` to `1.00 0.00 0.00 0.50`. The user reports that the bottom marker remained aquamarine/cyan-like. The XML fallback is therefore not the final visible colour in that tested path.
2. **Old slot-0 bypass:** candidate SHA-256 `2d78b8b990ca1e7fa10171352cc95af3ff8e9d2bcdfac54310b4c28c642aaf7f`. The user reports a race-load crash. R5V-E0.1d.1 raw ABI review found that its bypass branch used plain `RET`, leaving the pushed argument on the stack, and its nonzero branch nested a `CALL` into a callee that executes `RET 4`. This candidate is invalid and its crash must not be interpreted as a colour result.
3. **Corrected slot-0 bypass:** the `RET 4` / tail-`JMP` candidate ran by user report. Normal XML produced the grey/white fallback; red XML produced red; opponent colours stayed normal. Its SHA and diff are in [R5V-E0.1d.1](../../r5v_e0_1d_1/findings.md).

The XML archive and old executable remain under ignored `research-output/r5v_e0_1d/`; the corrected executable is under ignored `research-output/r5v_e0_1d_1/`. The retail EXE hash still matches; the current top-level `Data.sma` no longer matches its prior phase hash. R5V-E0.1d.1 records that archive-path difference; this phase did not write the archive. No user-facing or runtime-confirmed producer-level red control exists; E0.1d.2 prepares only an isolated diagnostic.

## Remaining evidence gate

The XML-only, ABI-safe bypass, and ID25 red-tail runtime reports are complete. R5V-E0.1d.2 traces the source vector from VehicleRecord tail into the shared `Race/CarN/Colour` property. The user reports that the ID25 red-tail candidate changed only its marker to red while Astero, opponents, and Trooper gameplay stayed unchanged. The result was not independently reproduced in this workspace.

- `Race/Car0/Colour` runtime precedence is **CONFIRMED BY USER REPORT**.
- Colour producer is **statically traced from VehicleRecord tail through Race/CarN/Colour**.
- The isolated ID25 marker change is **FULL PASS by user report**; the static and reported runtime semantics are closed.
- R5V-E0.1d.2 is **CLOSED**; R5V-F remains gated on the separate Vehicle Select icon issue.

## Success criteria status

| Criterion | Status |
|---|---|
| XML `ObjectColour` final visible effect | User reports red XML left marker aquamarine/cyan-like |
| `Race/Car0/Colour` runtime override behavior proven | User reports normal override and XML fallback with ABI-safe bypass |
| Producer identified | Static producer reads VehicleRecord tail and writes `/Colour` |
| Semantic owner identified | VehicleRecord tail is the static race-property source; user reports matching isolated runtime A/B |
| Player1 colour source explained | Static path resolves participant CarID; user reports ID25 red-tail marker changes to red |
| Clean semantic control changes Player1 marker | ID25 red-tail candidate changed only its RGB values; user reports expected red marker |
| Unrelated HUD and vehicle behavior unchanged | User reports original Astero marker, opponent colours, and Trooper model/physics/collision unchanged |

See [producer.md](producer.md), [override-precedence.md](override-precedence.md), and [validation.md](validation.md).
