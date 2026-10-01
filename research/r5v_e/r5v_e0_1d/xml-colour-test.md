# XML `ObjectColour` diagnostic

## Runtime scene selection

The retail `Data.sma` was read directly, not rebuilt from the unpacked tree. It contains 48 XML files under `DataScene/RaceTest/`; 47 contain a `HudLoader`. Every such loader has `Hud No=0` and `HudXml Location / Name=Hud/Hud0`. One-player Quick Race therefore uses `DataScene/Hud/Hud0.xml` for this test. `Hud1.xml` was not changed.

Within the `ProgressCar0` egg's `gaHudAiRaceProgress` values:

| Value | Original | Diagnostic |
|---|---|---|
| `Display Car ID` | `0` | `0` |
| `ObjectColour` | `1.00 1.00 1.00 0.50` | `1.00 0.00 0.00 0.50` |

The archive member has 124,360 bytes before and after the replacement. A reverse substitution of the new token recreates the original member byte-for-byte.

## Candidate contents

- Source retail archive: `D:\Game\Master Rallye\Data.sma`, SHA-256 `9bdf132cfde6e443e32f937b99289b07e9527457ae48fa9c7e0a373b52a28f30`.
- Candidate archive: `research-output/r5v_e0_1d/xml-red/Data.sma`, SHA-256 `10f69fde8c9110abb69bb0c004904697af4e2ca024d4e38a24f97bbd04861072`.
- Its 8,143 members retain the original order and names; the 8,142 other logical member payloads hash-identically. Duplicate member names: zero. The archive CRC check passes.
- The unpacked overlay copy is at `research-output/r5v_e0_1d/xml-red/overlay/DataScene/Hud/Hud0.xml`, SHA-256 `fbf9e1f628e21928e3bd164dae6f4e368e34136ea504e106ce287dfb4001b6b1`.
- The EXE is a byte-identical copy of the prior E0 baseline, SHA-256 `e19e80e64fcf2835d9883b115868e0cb8a0b63e05f48c8527580b2e0b531c0df`. It has no colour hook.
- Machine manifest: `research-output/r5v_e0_1d/xml-red/data-manifest.json`.

The archive was recompressed as a whole, so the archive's physical bytes and size differ. The logical payload comparison confirms that only the named HUD XML payload changed. The source archive itself was not written.

## Test and interpretation

Run a one-player Quick Race in a separate copy of the existing R5V-E0 test installation. Use the candidate as `MRallye.exe`, the candidate archive as `Data.sma`, and keep the same Trooper overlay and settings used for the confirmed E0 test. Do not add the loose XML overlay in the same run. See the ignored [XML test instructions](../../../research-output/r5v_e0_1d/xml-red/TEST_INSTRUCTIONS.txt).

- **XML-A:** marker turns red. `ProgressCar0/ObjectColour` is live in this mode. The property-exists path still needs the second diagnostic.
- **XML-B:** marker remains aquamarine/cyan-like. A later runtime tint replacement is likely; the bypass test checks whether the slot-0 `Race/Car0/Colour` consumer explains it.
- **INVALID:** wrong scene/mode, missing marker, or load failure; do not infer precedence.

No human runtime result is recorded yet.
