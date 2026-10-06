# Progression boundary for the ID26 qualification

This phase preserves the already-selected, bounded policy:

```text
physical ID26 -> evaluate availability as stock ID3
              -> Progress/UnlockedCars/T1CupCar1
```

The native `UnlockCars` and `UnlockAll` bypasses remain active. No award,
progress writer, save format, or campaign threshold is changed. The broad
progression architecture is not being redesigned here.

The previous stock-unlock matrix is copied into this canonical research folder
at `stock-unlock-matrix.json`; the historical `research/r5v_g1/` source remains
untouched. Its 0–25 vehicle records are stock retail records. ID26 is an addon
qualification record and remains a separate profile in `id26-policy.json`.

The three G.1 captures show a false-to-true transition for
`T1CupCar1` while both global car cheats remain false. The locked snapshot also
shows `CarModel=-1`; the unlocked snapshot reports `CarModel=26`. This confirms
the observed predicate/presentation transition, but not accept behavior or save
serialization.

## Out of scope

No unlock ordering, award threshold, persistence encoding, menu ordering,
audio, AI pool, T2, ID27+, or generic addon unlock-policy work is included.
