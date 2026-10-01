# VehicleRecord tail vector

## Layout and role

Retail vehicle records have a `0x34`-byte stride. The constructor writes the four tail components from four separate stack arguments:

| Record offset | Current label | Evidence-backed role | Confidence |
|---|---|---|---|
| `+0x24` | float A | First component read into `Race/CarN/Colour` | Raw Ghidra assembly/P-code |
| `+0x28` | float B | Second component read into `Race/CarN/Colour` | Raw Ghidra assembly/P-code |
| `+0x2C` | float C | Third component read into `Race/CarN/Colour` | Raw Ghidra assembly/P-code |
| `+0x30` | float D | Fourth component read into `Race/CarN/Colour` | Raw Ghidra assembly/P-code |

The appropriate semantic alias after the ID25 runtime check is `race_colour_rgba`. `progress_marker_rgba` would be too narrow: race setup has more than one direct tail-vector writer, and the HUD is a consumer of the race property rather than the only statically established role.

## Corpus result

The 25 normal retail initializer calls in `FUN_00458E70` produce:

- 25 finite vectors;
- all RGB values in the normalized `[0,1]` range;
- alpha exactly `1.0` in every row;
- 25 unique RGB triples after conversion to 8-bit display values;
- no out-of-range or non-finite outliers.

Two call sites use less regular stack staging but still resolve unambiguously in raw assembly: ID20 (Bruno) stages the vector at `[ESP+0x08..+0x14]`; ID23 (Icecream) stages its first two words before a stack adjustment and the remaining two after it. The TSV records the words actually passed at each initializer call, not a guessed continuation of the common layout.

The synthetic ID25 Trooper profile inherits ID16 Astero's vector:

```text
0x24 = 0.067924529  (bits 3D8B1C04; approx R=17)
+0x28 = 0.535849035  (bits 3F092D67; approx G=137)
+0x2C = 0.483018875  (bits 3EF74E40; approx B=123)
+0x30 = 1.000000000  (bits 3F800000; approx A=255)
```

This predicts RGB `(17,137,123)`, matching the reported aquamarine ID25 marker. The match is supporting evidence; the isolated red-tail test remains the direct runtime control.

Machine-readable inventory: [corpus-colours.tsv](corpus-colours.tsv). Raw initializer assembly is ignored at `research-output/r5v_e0_1d_2/ghidra/458e70.asm`; no executable or game asset is committed.

## Caution

Do not rename the four profile fields or alter compatibility manifests until the runtime A/B result is recorded. Static flow establishes their source and destination in the race property graph, but runtime isolation is still required to validate this particular synthetic record's visible outcome.
