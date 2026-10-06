# R5V-G.1 — locked-state integration correction

## Status

**READY FOR HUMAN RUNTIME.** The correction candidate is deterministic and
fail-closed against the exact pristine retail EXE. The stock-locked ID3 oracle,
ID26 locked visuals/commit gate, and naturally unlocked ID26 regression still
need human validation on this exact EXE-plus-XML pair.

## Runtime evidence carried forward

The new captures confirm the stock-like predicate itself is working:

* With `Progress/UnlockedCars/T1CupCar1=False` and both car cheats false,
  Vehicle Select reports `CarModel=-1`, `ManufacturerName=CAR LOCKED`, and
  `ModelName=CAR LOCKED` for the highlighted ID26.
* With `T1CupCar1=True` and cheats false, it reports physical `CarModel=26`,
  `MERCEDES`, and `ML-320`.
* The locked-state capture also contains `selectedCar=26` and `Race/Car0/CarID=26`.
  Those Broker values do not by themselves prove that the user committed the
  car; `selectedCar` is published by the highlight/cursor path. The owner also
  reported that the old ID26 widget could be committed, which is the defect to
  correct.
* Vehicle Setup currently reports `GALOCAL UNKNOWN` for ID26, with the native
  diagnostic `gaLocal: Can't find id [53]`. Decimal 53 is group `0x35`.

Capture IDs and JSON/raw hashes are in `runtime-captures.json`. The F.2f setup
capture is kept distinct from the three G.1 locked/unlocked snapshots.

## Static result

The native vehicle gate `FUN_0045A150` reads the absolute record ID and applies
the stock progress and cheat rules. The current wrapper supplies ID3 only as a
temporary gate input for physical ID26. The ID3 rule is
`Progress/UnlockedCars/T1CupCar1`; ID25 retains its `Bonus2` predicate.

The first slot-control divergence is in the scene data. Locked-capable stock
T1 local3 / ID3 is `T1_Car4`. It has a `gaFrontendDisablerAI` that selects normal
frame 27 or the common locked frame 15, plus a
`gaFrontendButtonUnlockerAI` that controls the `Enabled` field of its XY button
AI. The previous ID26 `T1_Car8` extension used an always-unlocked template and
omitted both controls. The corrected overlay raw-clones `T1_Car4`, preserving
the native unlock gate, then changes only the new slot's name, normal frame,
and horizontal button binding.

The generic positive-action path checks `UI/Enabled`; the locked button path
returns the stock disabled result rather than continuing the positive action.
The current failure and candidate correction are static/code evidence. The
human ID3/ID26 interaction comparison remains the acceptance oracle.

The locked requirement text is an ID switch in `FUN_004819B0`, not a missing
localization entry. Group 6 selector 8 is the generic `CAR LOCKED` line. Stock
ID3 uses selector 9 for its requirement line; ID26 previously fell through to
selector 8. The new hook maps only ID26 to selector 9 and replays the retail
table/default path for all other IDs.

Finally, Vehicle Setup's writer `FUN_0044F8E0` makes a separate group-0x35
lookup at `0x0044FA29`. The new wrapper returns the existing combined
`MERCEDES ML-320` string only for physical ID26 and replays the original
`gaLocal` call for every other vehicle.

## Candidate boundary

The exact candidate does not change the unlock policy, ID26 record, class map,
or runtime identity. It keeps the F.2f manufacturer/model and Quick Race
overrides, adds the locked-reason and Vehicle Setup wrappers, and must be
staged with the XML overlay. There is no global localization fallback and no
asset change.

See `locked-selection.md`, `locked-presentation.md`,
`../localization/frontend-consumers.md`, and `runtime-handoff.md`.
