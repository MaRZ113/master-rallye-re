# Vehicle feature mask and observed truth table

Runtime material+34 is copied directly from raw `unknown_0x24`. Selector
`00580360` and binding builder `00577620` establish these consequences:

| Bit | Vehicle consequence | Confidence |
|---|---|---|
| 01 | Base texture handle gate; contributes to mask&3 base selector | CONFIRMED_BY_EXE |
| 02 | Contributes to mask&3 base selector, including textureless diffuse draws | CONFIRMED_BY_EXE |
| 04 | Env selector/binding with global Reflections>0 | CONFIRMED_BY_EXE |

Observed masks: 1:21, 2:2, 3:363, 5:151, 6:3, 7:938. There are no other
vehicle-used bits in this corpus. Slot2 is NULL in all draws, not asserted
unused engine-wide. A mask outside07, populated slot2, missing base selector,
or optional runtime variant object receives an explicit UNKNOWN reason;
unsupported draws are not silently classified as ordinary base materials.

Mask formula `(slot0?1:0) | (byte2?2:0) | (slot1?4:0)` matches 1478/1478
draws. This is corpus evidence and not a replacement for the separate EXE
consumers. Source slots/mask remain intact when projecting Reflections OFF.

The table assumes Reflections ON; alpha mode is inferred from the two proven
alpha bytes. Every slot2 is NULL. Env bound includes the three NULL-base rows;
the effective preview suppresses them under the separate cascade inference.

| Flags | Mask | Family | Alpha | Env bound | Draws | Example (slot0 / slot1) |
|---|---:|---|---|---|---:|---|
| 00000001 | 1 | base | opaque | no | 10 | ChevyBlazer/car 34: breaklightson / Null |
| 00000001 | 5 | base_env | opaque | yes | 137 | Astero/car 29: breaklightson / perspex |
| 00000100 | 2 | base | opaque | no | 2 | IceCream/car 3: Null / Null |
| 00000101 | 3 | base | opaque | no | 357 | Astero/car 0: underdash / Null |
| 00000101 | 6 | base_env | opaque | yes | 3 | KiaSportage/car 11: Null / perspex |
| 00000101 | 7 | base_env | opaque | yes | 732 | Astero/car 5: asterohelmet / whitepaint |
| 01000001 | 1 | base_alpha | blend | no | 11 | ChevyBlazer/car 35: breaklightsonglow / Null |
| 01000001 | 5 | base_env_alpha | blend | yes | 14 | Astero/car 30: breaklightsonglow / perspex |
| 01000101 | 3 | base_alpha | blend | no | 6 | Mattserati/car 20: mnet1 / Null |
| 01000101 | 7 | base_env_alpha | blend | yes | 206 | Astero/car 21: asterolight1 / perspex |

Names above omit the common `-tga` suffix for compactness. Exact names and
per-resource hashes are in [corpus-validation.json](corpus-validation.json).
ON family totals: base369, base_alpha17, base_env872, base_env_alpha220.
Alpha-test variants are statically established and tested synthetically;
their observed stock count is zero.
