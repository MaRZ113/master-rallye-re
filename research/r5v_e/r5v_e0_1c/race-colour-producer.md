# Race progress colour: consumer, HUD config, and unresolved producer

## Retail executable identity

Static evidence refers to retail `MRallye.exe`, SHA-256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`, as recorded by the preceding validated R5V-E0.1 work. Targeted Ghidra Bridge exports for the consumer, HUD object construction, schema registration, and strings are preserved outside Git under `research-output/r5v_e0_1c/bridge/`.

## Confirmed consumer

`FUN_004A74A0` contains the only direct reference found for the format string `Race/Car%d/Colour` (`0x006E51A8`). Its code:

1. Reads the HUD display-slot integer at `this+0x18`.
2. Formats that value into the property key `Race/Car%d/Colour`.
3. Checks for the property with `FUN_004D7470`.
4. If present, obtains a pointer with `FUN_004D7340` and copies four consecutive 32-bit values into HUD state at `this+0x3C`, `+0x40`, `+0x44`, and `+0x48`.
5. Copies the four values to the marker render object's colour fields at `+0x14`, `+0x18`, `+0x1C`, and `+0x20`.

The ghost branch forces those components to `1.0, 1.0, 1.0, 0.5`. This supports an RGBA-like order and confirms tint application. The string key and consumer structure do not establish the semantic meaning of the display-slot index.

Evidence: raw Ghidra Bridge decompilation/P-code in `bridge/004a74a0.json`, raw string/xref summary in `bridge/strings-colour.txt`, and targeted retail Ghidra analysis. **RAW_GHIDRA_SUPPORTED.**

## Schema registration is not a producer

`FUN_004ABCE0` calls the generic key-registration function for `/Colour`, alongside `/Time`, `/DriverID`, `/CarClass`, `/WheelType`, `/CarID`, and other Race/HUD keys. This creates/registers a schema key; the function does not supply a colour value. Its direct caller is the schema setup function `FUN_004ABBD0`.

The only literal xref for the full key `Race/Car%d/Colour` is the consumer `FUN_004A74A0`. The inspected `RaceTest` configuration contains Race/Car fields but no explicit per-car colour value. These negative searches narrow static leads but do not prove that no dynamic writer exists.

## HUD widget `ObjectColour` source

`FUN_004A72A0` constructs a `gaHudAiRaceProgress` HUD-config object. It reads `Display Car ID` from the widget parameter at `param1+0x18`, and passes the four values at `param1+0x3C` to the generic config binding for `ObjectColour`. It also binds `Display Car Offset`.

This proves that each HUD progress widget has an `ObjectColour` config field available to the generic HUD object. It does not show that `ObjectColour` writes, initializes, or backs the separate runtime property `Race/CarN/Colour`. The caller that creates the race property remains unidentified.

The unpacked HUD XML inventory found these widget values:

| Widget | `Hud0.xml` ObjectColour | `Hud1.xml` ObjectColour |
|---|---|---|
| ProgressCar0 | `(1,1,1,0.5)` | `(1,1,1,0.5)` |
| ProgressCar1 | `(0,1,1,0.5)` | `(0,1,1,0.5)` |
| ProgressCar2 | `(1,0,1,0.5)` | `(1,0,1,0.5)` |
| ProgressCar3 | `(1,1,0,0.5)` | `(1,1,0,0.5)` |
| ProgressCar4 | `(0,0,1,0.5)` | `(0,0,1,0.5)` |
| ProgressCar5 | `(0,1,0,0.5)` | `(0,1,0,0.5)` |
| ProgressCar6 | `(1,0,0,0.5)` | `(0,0,0,0.5)` |
| ProgressCar7 | `(0,0,0,0.5)` | `(1,0,0,0.5)` |

For `Hud0.xml`, `ProgressCarN` has `Display Car ID=N` and offset `0`. For `Hud1.xml`, the same IDs appear; offsets are `+2` for Car0, `-2` for Car1, and `0` for Car2..7.

Source hashes: `Hud0.xml` `91616caa529fb4762e8e263f58bfe0f35ee5aebf127e8ba2fc3014a677ea4dbf`; `Hud1.xml` `9146cb6832cd3fe70b9e1765019a20ce0ea886da3dd035dafaaa9dc195beffbe`. The machine-readable extraction is preserved in ignored `research-output/r5v_e0_1c/hud-colour-config-summary.json`.

The owner-reported in-game marker was aquamarine, but no runtime float or packed value was captured. `ProgressCar0`'s static widget `ObjectColour` is white, so the XML inventory does not explain the reported runtime appearance by itself. The relationship among the widget config, the `Race/Car0/Colour` property, and the eventual render tint remains unknown.

## Semantic-owner audit

| Hypothesis | Evidence | Result |
|---|---|---|
| Fixed Player1 colour | The consumer key uses a display slot; there is no writer or Player1 mapping in the inspected call path | Unknown |
| Participant-index palette | HUD XML supplies per-widget colours and IDs, but no link to the race property writer is proven | Plausible lead only; unknown |
| Player profile/network colour | No profile/network source was traced into the property | Unknown |
| Vehicle ID/class/family colour | The consumer does not read VehicleRecord, CarID, class, or runtime family while fetching the tint; upstream writer was not traced | Not established either way |
| Race setup/team/other | No value producer or source object was traced | Unknown |

The E0.1a SmallCarSheet selector test changed ID25's participant/results icon while leaving the progress marker aquamarine. This excludes that selector field as the marker control, not every possible vehicle-derived source.

## Current classification

`Race/CarN/Colour` is a four-component property consumed by a generic HUD marker renderer. The property's concrete backing address/type/lifetime, initialization point, writer function, caller, source object/table, index semantics, and overwrite order are **UNKNOWN**. Car0 and Car1+ runtime values are **NOT CAPTURED**. Colour is not proven vehicle-dependent, so it must not be added to `VehicleSlotProfile` at this stage.
