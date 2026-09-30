# R5V-E0.1 — frontend identity channels

Date: 2026-09-30

Build: retail, with narrow comparisons against demo-8.4.1 and demo-9.3.1.

## R5V-E0 closeout

R5V-E0 P0 and P1 are FULL PASS by the owner's 2026-09-30 runtime report.
Vehicle ID25 is selectable in T3, loads the Trooper preview/race/wheel
resources, uses Trooper physics and collision, completes a stage, reaches
results and returns to the menu. The owner reports that IDs 0–24 remain
available. The dedicated E0 closeout is commit 21f8f65
(research: record R5V-E0 Trooper runtime confirmation). The exact tested EXE
hash, screenshots and runtime log were not supplied, so this remains attributed
human evidence rather than an independently reproduced run.

This E0.1 phase is read-only. It does not change the executable, assets,
frontend scene files, registry, T1/T2 capacity, or track data. No optional
icon redirect or other runtime candidate was created.

## Finding

The visible identity is assembled from separate data sources:

1. **Display name** — the unlocked Vehicle Select update resolves manufacturer
   and model localization groups by absolute vehicle ID. At ID25 the owner
   sees STEEL MONKEYS FORKLIFT. The record's Trooper resource name is a separate
   string.
2. **Stats** — the Vehicle Select updater indexes the four integer fields in
   VehicleRecord[ID]. Trooper ID25 shows Astero-derived stats because the E0
   profile deliberately initialized those four fields with Astero's values;
   there is no separate ID25-to-Astero stats alias in this reader.
3. **Vehicle Select icon** — T3 icons are assigned by static XML widgets and
   image-bank indices. The retail scene has T3_Car1 through T3_Car11, but no
   widget for local index 11 / absolute ID25. The carsheet frame 25 file exists;
   the binding is absent.
4. **Race progress marker** — Hud0/Hud1 use the fixed hud-template frame 3 for
   ProgressCar0 through ProgressCar7. The updater selects Race/CarN progress
   and colour, then uses the same generic white-car marker. It does not choose
   art from the vehicle ID or name.
5. **Race 1P icon** — the R5V-E0.1a follow-up identifies `TimeDiffs` /
   `gaHudTimeDiffsAi` as a strong candidate and finds a raw-code helper that
   reads participant CarID -> record `+0x1C` -> image selector. The static
   dispatch edge and scene child resource binding are still open; a dedicated
   `0 -> 29` candidate is waiting for human runtime validation. See
   `research/r5v_e/r5v_e0_1a/`.
6. **Race Results icon** — the results producer reads the race participant's
   absolute vehicle ID, then reads VehicleRecord[ID] field +0x1C and publishes
   that integer as Frontend/RaceResults/CarN. The scene applies it to the
   smallcarsheet image selector. E0 supplied the Astero-equivalent value 0,
   which selects frame 0.

The registry accessor returns the registry object base, while records begin at
object offset +4 and have stride 0x34. This distinction resolves the Race
Results address: registry base + ID*0x34 + 0x20 is VehicleRecord[ID] +0x1C,
not the owned internal-name pointer at VehicleRecord +0x20.

The six channels are analyzed separately in the linked reports:

- [Display name](display-name.md)
- [Frontend stats](frontend-stats.md)
- [Vehicle Select icon](vehicle-select-icon.md)
- [Race HUD icons](race-hud-icons.md)
- [Race Results icon](race-results-icon.md)
- [Trooper UI asset search](trooper-frontend-assets.md)
- [Cross-channel matrix](identity-matrix.md)
- [Validation and evidence limits](validation.md)

## Confidence summary

| Channel | ID25 result | Evidence |
|---|---|---|
| Display name | STEEL MONKEYS FORKLIFT | STRONGLY_SUPPORTED: raw selector calls are ID-indexed; owner confirms rendered text; EXE contains the Forklift strings |
| Stats | Astero-derived values | PROVEN data source and values: direct record reads plus E0 initializer profile |
| Vehicle Select icon | Missing | PROVEN: no T3_Car12 widget/binding; frame 25 asset itself exists |
| Race 1P icon | TimeDiffs image candidate; selector 0 -> 29 pending | STRONGLY_SUPPORTED static data path; dispatch/object match awaits runtime test |
| Progress icon | Generic hud-template frame 3; owner describes it as Astero | PROVEN generic source; Astero-specific identity is not supported |
| Race Results icon | Frame 0; owner describes it as Astero | PROVEN numeric field-to-frame path; visual Astero identification is STRONGLY_SUPPORTED |

## R5V-F gate

R5V-E0.1 closed as a read-only research phase. The later R5V-E0.1a candidate
is waiting for human runtime results. R5V-F remains **BLOCKED** as a generic
frontend identity-profile phase until the in-race 1P icon is matched to a
runtime object and source. Also, the static
Vehicle Select scene has no ID25 widget binding, so a future generalized slot
profile must account for this scene-level mapping rather than treating all
icons as one per-vehicle field. The exact unresolved edge is documented in
[race-hud-icons.md](race-hud-icons.md).

At the original R5V-E0.1 closeout, no executable or runtime candidate was
produced. The separate E0.1a diagnostic candidate is ignored and uncommitted.
