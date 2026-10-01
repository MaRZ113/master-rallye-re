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

## Human test result and interpretation

The user reports the result from the one-player diagnostic:

```text
marker remained aquamarine/cyan-like
```

This is XML-B. The red XML value alone is not the final visible value in the tested race path. It supports looking for a later runtime replacement, but it does not identify that replacement. The previous bypass executable crashed due to an ABI bug and is invalid evidence. Use only the corrected candidate described in `research/r5v_e0_1d_1/runtime-test-plan.md` for the next test.

The original isolated test instructions remain in the ignored [XML test instructions](../../../research-output/r5v_e0_1d/xml-red/TEST_INSTRUCTIONS.txt).
