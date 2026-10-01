# Corrected bypass runtime test (completed by user report)

## Result supplied by the user

The ABI-safe candidate loaded the race. The bottom marker used the grey/white fallback with normal HUD XML and became red with red `ProgressCar0/ObjectColour` XML. With bypass active, all Player1-selected cars shared that XML fallback while opponents kept their normal colours. This closes the tested fallback/override precedence, but does not capture the backing property pointer or writer.

## Inputs

Use a separate test copy of the existing confirmed R5V-E0 runtime installation. Keep the Trooper overlay, SmallCarSheet29 configuration, and other settings unchanged.

- Replace only the isolated copy's executable with `research-output/r5v_e0_1d_1/override-bypass/MRallye_slot25_trooper_smallsheet29_xmlred_colour-bypass-abi-safe.exe`.
- Use `research-output/r5v_e0_1d/xml-red/Data.sma` as the archive.
- Confirm archive SHA-256 `10f69fde8c9110abb69bb0c004904697af4e2ca024d4e38a24f97bbd04861072`.
- Do not also overlay the loose `Hud0.xml`; the archive already contains the sole red XML edit.
- Do not put either candidate file in the original retail installation.

## Run

Start a one-player Practice/Quick Race using the same simple path as the XML-only test. Confirm the Trooper/Forklift slot and bottom progress marker are visible. Record whether the game loads, whether the vehicle remains functional, and the exact bottom-marker appearance.

| Result | Record | Next action |
|---|---|---|
| Game loads and the bottom marker becomes red | Corrected bypass has restored the red XML fallback while the property exists query is suppressed for display slot 0. This confirms the tested `Race/Car0/Colour` override precedence at runtime. | Proceed to the manual producer trace in [manual-x32dbg.md](manual-x32dbg.md). |
| Game loads and the marker stays aquamarine/cyan-like | The bypass point does not explain the final tint or the tested display object/property identity differs. | Stop semantic claims and trace later tint writes or property identity. |
| Game crashes or the marker/race path is invalid | Do not infer colour semantics. | Stop, save the exact crash context, and audit the corrected helper/register/stack path. |

## Record form

```text
Candidate EXE SHA-256: ce17e26a87f0d1f6aed4b96e77d2d57a4b3b7f9772c5f19f677af3c35d0a71fb
Data.sma SHA-256:      10f69fde8c9110abb69bb0c004904697af4e2ca024d4e38a24f97bbd04861072
Mode / race:
Game reached race:     yes / no
Trooper still shown:   yes / no
Bottom marker:         red / aquamarine-cyan-like / other / not visible
Other HUD changes:
Crash details:
```

The prepared corrected candidate is not itself runtime evidence. Wait for this human result before closing colour precedence.
