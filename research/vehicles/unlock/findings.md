# R5V-G.1 — locked-state integration correction

## Current result

The active-root lock test is now a human runtime pass: locked ID26 displays the
locked thumbnail and native requirement, `UI/Enabled=False`, and normal accept
does not commit it. After the native T1 Cup condition is completed, ID26 is
selectable and its unlocked Mercedes presentation returns. Race Details has a
separate static fix ready for a two-mode human check; that final check is still
pending. Current phase status is therefore **READY FOR HUMAN RUNTIME**, not
closed.

## Current status

The initial overlay deployment test was invalid because its Root did not
contain the generated VehicleSelect scene. That packaging defect is fixed; the
corrected-root runtime result is documented in `runtime-correction-2.md` and
`runtime-captures.json`.

## Runtime correction #2 evidence

The raw sidecars for `20261006-143000_merc_not-locked`,
`20261006-143558_id3-locked`, `20261006-143842_merc-masterrallye-mode`, and
`20261006-144257_merc-rallyecup-mode` hash-match their JSON metadata.

Fresh locked state:

* ID3: `CarModel=-1`, `CAR LOCKED`, `UNLOCK BY WINNING 2 T1 CUPS`,
  `selectedCar=3`, `UI/Enabled=False`.
* ID26: same locked text, `CarModel=-1`, `selectedCar=26`,
  `UI/Enabled=True`.

The owner observed ID26 accepted into a race, where `CarID=26` and
`CarClass=0`. This separates the actual interaction result from `selectedCar`.
The latter is only the highlighted/current frontend identity: stock locked ID3
also publishes its ID before acceptance.

Race Details separately fails in both captured modes: `Race/Car0/CarID=26`,
but `Frontend/RaceDetails/CurrentVehicleString="GALOCAL UNKNOWN"`. The capture
records correct mode and event text. This pass does not trace or patch that
producer until the scene deployment gate is met.

## Native and scene model

The G.1 executable hook mirrors ID3 only as the temporary input to the stock
availability predicate and locked-reason selector. Physical registry ID26,
T1 local7 mapping, model, wheel, physics, and runtime ID remain unchanged.
ID25 keeps its stock `Bonus2` gate.

Stock locked ID3 is `T1_Car4`; it contains both the disabler AI that chooses
normal/locked image frames and the unlocker AI that disables its XY button. The
corrected overlay clones this widget into `T1_Car8`. Its structure and exact
hash are statically verified, but the last human process did not load that
loose file from the active Root. The previous visible unlocked art and enabled
button cannot be attributed to a native AI defect until the exact staged scene
is runtime-proven.

## Candidate boundary

The candidate remains the exact deterministic G.1 EXE plus the existing
Vehicle Select overlay. The new packaging helper creates an isolated runtime
Root with pinned `Data.sma`, audio/video, options, and qualified Mercedes DX/DXT
assets; it omits old profile state and refuses mismatched hashes. It does not
modify the captured historical resource tree, retail source, Mercedes assets,
or any native selection/commit handlers.

See `locked-selection.md`, `locked-presentation.md`,
`runtime-correction-2.md`, `runtime-handoff.md`, and
`../localization/frontend-consumers.md`.
