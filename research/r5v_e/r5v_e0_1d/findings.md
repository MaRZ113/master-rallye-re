# R5V-E0.1d progress marker colour producer

## Verdict

**BLOCKED: the colour producer and semantic owner remain unknown.** This phase verified the retail HUD consumer and inspected bounded race setup and Quick Race paths. The subsequent R5V-E0.1d.1 user report records the red XML-only test as leaving the marker aquamarine/cyan-like. The old slot-0 bypass then crashed during race loading and is now invalidated because its helper violated the stack ABI. That crash is not colour-precedence evidence.

The prior R5V-E0.1c commit remains an accurate record of its then-current blocked state. This phase adds evidence and candidates without replacing that history. E0.1c closeout commit: `685cf1f`.

## Established static evidence

- Retail identity was rechecked: `MRallye.exe` SHA-256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`; `Data.sma` SHA-256 `9bdf132cfde6e443e32f937b99289b07e9527457ae48fa9c7e0a373b52a28f30`.
- `FUN_004A74A0` reads HUD display slot `this+0x18`, forms `Race/Car%d/Colour`, calls the property-exists getter at `0x004A7661`, and copies four 32-bit components if the property exists. The ghost path replaces the colour with white RGB and alpha `0.5`. Raw assembly and the prior Ghidra P-code export agree.
- The object colour loaded from HUD XML is available as the consumer's initial tint. The `Race/CarN/Colour` property conditionally replaces those components in the consumer. This is a static control-flow fact; visible runtime precedence still needs the two diagnostics.
- The retail archive contains 48 `DataScene/RaceTest/*.xml` files. Forty-seven have a `HudLoader`; each uses `Hud No=0` and `HudXml Location / Name=Hud/Hud0`. The one-player diagnostic therefore edits `Hud0.xml` only. `Hud1.xml` is not part of that one-player path.
- `FUN_0048E2D0` calls `FUN_0048EB40` in its race setup path. `FUN_0048EB40` conditionally constructs a `gaVehicleSplineRecordAI` helper through `FUN_004C0B20` when spline recording is enabled. That constructor registers/reads sibling paths including `Race/Car%d/CarType`, `Race/Car%d/Time`, and `Race/Car%d/Finished`; it is not evidence of the general participant property writer.
- `FUN_004B6A00` handles a `Race/Car%d/DriverID` path and vehicle/driver setup. No Colour write was found in the inspected function. `FUN_0047B780` restores `Frontend/QuickRace/Car0` and `Car1` values into race CarID/CarType state; it does not write the colour property. `FUN_004ADF50` is a generic Quick Race setter helper with no direct callers in the analyzed retail project.
- The complete literal `Race/Car%d/Colour` has a direct code reference in the inspected retail image at the HUD consumer. Schema registration in `FUN_004ABCE0` is not a value producer. A generic schema/struct writer may still materialize the value without that literal; this phase did not identify one.

## Diagnostics and later human results

1. **XML-only:** the retail `Data.sma` copy changes only `ProgressCar0 / gaHudAiRaceProgress / ObjectColour` from `1.00 1.00 1.00 0.50` to `1.00 0.00 0.00 0.50`. The user reports that the bottom marker remained aquamarine/cyan-like. The XML fallback is therefore not the final visible colour in that tested path.
2. **Old slot-0 bypass:** candidate SHA-256 `2d78b8b990ca1e7fa10171352cc95af3ff8e9d2bcdfac54310b4c28c642aaf7f`. The user reports a race-load crash. R5V-E0.1d.1 raw ABI review found that its bypass branch used plain `RET`, leaving the pushed argument on the stack, and its nonzero branch nested a `CALL` into a callee that executes `RET 4`. This candidate is invalid and its crash must not be interpreted as a colour result.
3. **Corrected slot-0 bypass:** a new static candidate uses `RET 4` for the bypass and a tail `JMP` to the original getter for nonzero slots. It has not yet been run. Its SHA, diff, and instructions are in [R5V-E0.1d.1](../../r5v_e0_1d_1/findings.md).

The XML archive and old executable remain under ignored `research-output/r5v_e0_1d/`; the corrected executable is under ignored `research-output/r5v_e0_1d_1/`. The retail EXE hash still matches; the current top-level `Data.sma` no longer matches its prior phase hash. R5V-E0.1d.1 records that archive-path difference; this phase did not write the archive. No producer-level red control has been produced.

## Remaining evidence gate

The XML-only test is complete. The corrected slot-0 bypass still needs the human runtime test in `research/r5v_e0_1d_1/runtime-test-plan.md`. If it turns the marker red, use `research/r5v_e0_1d_1/manual-x32dbg.md` with the clean E0 baseline to record Car0..Car3 values and catch a writer. Until the corrected test and producer trace establish the source and ownership:

- `Race/Car0/Colour` runtime precedence is **NOT CONFIRMED**.
- Colour producer classification is **UNKNOWN**.
- Colour is not part of `VehicleSlotProfile`.
- R5V-E0.1d is **WAIT FOR HUMAN DIAGNOSTIC** and R5V-F is **BLOCKED**.

## Success criteria status

| Criterion | Status |
|---|---|
| XML `ObjectColour` final visible effect | User reports red XML left marker aquamarine/cyan-like |
| `Race/Car0/Colour` runtime override behavior proven | Corrected bypass runtime pending; old candidate invalid |
| Producer identified | Unknown |
| Semantic owner identified | Unknown |
| Player1 colour source explained | Unknown; only an aquamarine visual report exists |
| Clean semantic control changes Player1 marker | Not implemented; source not known |
| Unrelated HUD and vehicle behavior unchanged | Candidate scope is narrow; runtime pending |

See [producer.md](producer.md), [override-precedence.md](override-precedence.md), and [validation.md](validation.md).
