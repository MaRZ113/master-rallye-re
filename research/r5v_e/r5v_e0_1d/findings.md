# R5V-E0.1d progress marker colour producer

## Verdict

**BLOCKED: the colour producer and semantic owner remain unknown.** This phase verified the retail HUD consumer, inspected bounded race setup and Quick Race paths, and prepared separate XML-only and slot-0 bypass diagnostics. Neither diagnostic has been run in the game, so XML precedence, runtime override behavior, colour values, and the effect of the bypass remain unconfirmed.

The prior R5V-E0.1c commit remains an accurate record of its then-current blocked state. This phase adds evidence and candidates without replacing that history. E0.1c closeout commit: `685cf1f`.

## Established static evidence

- Retail identity was rechecked: `MRallye.exe` SHA-256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`; `Data.sma` SHA-256 `9bdf132cfde6e443e32f937b99289b07e9527457ae48fa9c7e0a373b52a28f30`.
- `FUN_004A74A0` reads HUD display slot `this+0x18`, forms `Race/Car%d/Colour`, calls the property-exists getter at `0x004A7661`, and copies four 32-bit components if the property exists. The ghost path replaces the colour with white RGB and alpha `0.5`. Raw assembly and the prior Ghidra P-code export agree.
- The object colour loaded from HUD XML is available as the consumer's initial tint. The `Race/CarN/Colour` property conditionally replaces those components in the consumer. This is a static control-flow fact; visible runtime precedence still needs the two diagnostics.
- The retail archive contains 48 `DataScene/RaceTest/*.xml` files. Forty-seven have a `HudLoader`; each uses `Hud No=0` and `HudXml Location / Name=Hud/Hud0`. The one-player diagnostic therefore edits `Hud0.xml` only. `Hud1.xml` is not part of that one-player path.
- `FUN_0048E2D0` calls `FUN_0048EB40` in its race setup path. `FUN_0048EB40` conditionally constructs a `gaVehicleSplineRecordAI` helper through `FUN_004C0B20` when spline recording is enabled. That constructor registers/reads sibling paths including `Race/Car%d/CarType`, `Race/Car%d/Time`, and `Race/Car%d/Finished`; it is not evidence of the general participant property writer.
- `FUN_004B6A00` handles a `Race/Car%d/DriverID` path and vehicle/driver setup. No Colour write was found in the inspected function. `FUN_0047B780` restores `Frontend/QuickRace/Car0` and `Car1` values into race CarID/CarType state; it does not write the colour property. `FUN_004ADF50` is a generic Quick Race setter helper with no direct callers in the analyzed retail project.
- The complete literal `Race/Car%d/Colour` has a direct code reference in the inspected retail image at the HUD consumer. Schema registration in `FUN_004ABCE0` is not a value producer. A generic schema/struct writer may still materialize the value without that literal; this phase did not identify one.

## Diagnostics prepared

1. **XML-only:** a retail `Data.sma` copy changes only `ProgressCar0 / gaHudAiRaceProgress / ObjectColour` from `1.00 1.00 1.00 0.50` to `1.00 0.00 0.00 0.50`. The EXE is an unchanged copy of the existing Trooper + SmallCarSheet29 baseline.
2. **Slot-0 bypass:** a second executable redirects the existence query at `0x004A7661` through a helper. It returns false for HUD display slot 0 so the XML colour remains active, and calls the original getter for every nonzero slot. Pair it with the same red XML archive only after recording the XML-only result.

Both are static candidates only. The candidate archive and executables are under ignored `research-output/r5v_e0_1d/`; original retail EXE and archive hashes remain unchanged. No final semantic red-control candidate was produced.

## Remaining evidence gate

The human must run the XML-only diagnostic, then the slot-0 bypass diagnostic, and report the marker result for each. Afterward use the manual x32dbg plan in [dynamic-trace-plan.md](dynamic-trace-plan.md) to record Car0..Car3 values and catch a writer. Until those steps establish the source and ownership:

- `Race/Car0/Colour` runtime precedence is **NOT CONFIRMED**.
- Colour producer classification is **UNKNOWN**.
- Colour is not part of `VehicleSlotProfile`.
- R5V-E0.1d is **WAIT FOR HUMAN DIAGNOSTIC** and R5V-F is **BLOCKED**.

## Success criteria status

| Criterion | Status |
|---|---|
| XML `ObjectColour` precedence experimentally understood | Candidate ready; runtime pending |
| `Race/Car0/Colour` runtime override behavior proven | Runtime pending |
| Producer identified | Unknown |
| Semantic owner identified | Unknown |
| Player1 colour source explained | Unknown; only an aquamarine visual report exists |
| Clean semantic control changes Player1 marker | Not implemented; source not known |
| Unrelated HUD and vehicle behavior unchanged | Candidate scope is narrow; runtime pending |

See [producer.md](producer.md), [override-precedence.md](override-precedence.md), and [validation.md](validation.md).
