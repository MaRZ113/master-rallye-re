# R5V-E0.1c race participant colour producer

## Verdict

**BLOCKED: the producer of `Race/Car0/Colour` and its semantic owner remain unknown.** The retail HUD consumer is confirmed from Ghidra assembly/P-code, and the related HUD widget configuration was inventoried, but neither identifies the writer that supplies the race property. The dynamic debugger pass did not reach a confirmed colour-property read or write, so it captured no runtime values. No tint diagnostic or executable candidate was built.

This phase is therefore not a full or partial colour-path closure. The prompt's PARTIAL PASS condition requires producer semantics to be proven; that condition is not met.

## Established evidence

- R5V-E0.1b stats are **FULL PASS** (commit `ab3da88`). The owner observed Vehicle Select bars follow `(3,4,6,10)` while the ID25 vehicle retained Trooper configuration. This confirms the four fields as presentation controls, not as a change to Trooper simulation physics.
- Retail `FUN_004A74A0` constructs `Race/Car%d/Colour` from its HUD display-slot field at `this+0x18`, checks the property, reads four adjacent 32-bit components, and copies them into HUD tint state at `this+0x3C..+0x48`. It then copies those values to the marker render object at `+0x14..+0x20`. **RAW_GHIDRA_SUPPORTED.**
- The ghost branch overwrites the components with `(1,1,1,0.5)`. This supports an RGBA-like component order; no numeric non-ghost runtime value was captured.
- `FUN_004ABCE0` registers the `/Colour` key in the Race/HUD property schema. It does not write a value.
- `FUN_004A72A0` builds a `gaHudAiRaceProgress` config object and loads `Display Car ID` and `ObjectColour` from the HUD widget config. This establishes a per-widget HUD colour input, but no evidence links it to the race property writer.
- `Hud0.xml` and `Hud1.xml` define separate `ObjectColour` values for `ProgressCar0..7`. Their exact values and source hashes are in [race-colour-producer.md](race-colour-producer.md). `ProgressCar0` is configured white with alpha 0.5, while the owner has described the visible player marker as aquamarine. These observations do not identify how runtime `Race/Car0/Colour` is produced.
- Earlier owner testing changed ID25's SmallCarSheet selector while the bottom marker stayed aquamarine. This proves that the icon selector does not control that marker; it does not rule out every other vehicle-dependent mapping.

## Unresolved edge

```text
race setup / participant state / HUD configuration / other source
    -> property write or initialization
    -> Race/Car0/Colour
```

The specific writer, its caller, source object/table, index/key, storage lifetime, and overwrite timing are not established. `Car0` is the consumer's display slot key; its relationship to Player1, participant order, vehicle ID, or player profile remains unknown. The RGB(A) values for Car0 and Car1+ remain unknown.

## Diagnostic and phase status

No source-specific control point has been proven, so a red tint patch would be speculative. No candidate, patch manifest, binary diff, or runtime test package was produced. The ignored `research-output/r5v_e0_1c/debug-run/` directory contains only prior scratch copies used for debugger setup; it is not a colour candidate.

R5V-F remains **BLOCKED** on this unresolved upstream edge. Keep `progress_marker_colour` out of `VehicleSlotProfile`; if later evidence establishes participant or player ownership, place the control in a separately named race/HUD participant profile. The separate `T3_Car12` Vehicle Select icon remains unresolved and should be tracked as UI mapping work, not conflated with marker tint.

See [dynamic-trace.md](dynamic-trace.md), [race-colour-producer.md](race-colour-producer.md), [runtime-diagnostic.md](runtime-diagnostic.md), [validation.md](validation.md), and [r5v-f-readiness.md](r5v-f-readiness.md).
