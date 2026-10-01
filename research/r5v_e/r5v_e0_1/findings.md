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
   carsheet frame indices. The retail scene has T3_Car1 through T3_Car11, but
   no widget for local index 11 / absolute ID25. E0.2 prepared a generic
   scene-only T3_Car12 candidate using the existing Astero frame5 as a
   diagnostic donor; runtime visibility is pending. Frame25 exists but is a
   red-and-white SUV, not proven Trooper art. See
   [R5V-E0.2](../../r5v_e0_2/findings.md).
4. **Race progress marker** — Hud0/Hud1 use the fixed hud-template frame 3 for
   ProgressCar0 through ProgressCar7. The updater selects Race/CarN progress
   and colour, then uses the same generic white-car marker. It does not choose
   art from the vehicle ID or name.
5. **Race 1P icon** — the R5V-E0.1a follow-up traces the `TimeDiffs` /
   `gaHudTimeDiffsAi` path from participant CarID to record `+0x1C` and an
   embedded image selector. The exact scene child resource binding remains
   unnamed statically, but the owner reports that the `0 -> 29` diagnostic
   changed the top-left 1P icon to the Forklift image while Trooper gameplay
   remained normal.
6. **Race Results icon** — the results producer reads the race participant's
   absolute vehicle ID, then reads VehicleRecord[ID] field +0x1C and publishes
   that integer as Frontend/RaceResults/CarN. The scene applies it to the
   smallcarsheet image selector. E0 initially supplied value 0; the owner later
   reported frame29 after the E0.1a selector diagnostic.

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
| Vehicle Select icon | Diagnostic Astero donor staged; no authentic Trooper icon identified | Static scene mapping proven; R5V-E0.2 runtime P0 pending |
| Race 1P icon | Forklift frame 29 after the E0.1a selector diagnostic | Static CarID-to-record path plus owner-reported runtime result; exact embedded resource binding remains unnamed |
| Progress icon | Generic hud-template frame 3; owner describes it as Astero | PROVEN generic source; Astero-specific identity is not supported |
| Race Results icon | Forklift frame 29 after the E0.1a selector diagnostic | Static numeric field-to-frame path plus owner-reported runtime result |

## R5V-F gate

R5V-E0.1a's SmallCarSheet selector result was later reported FULL PASS by the
owner; the race participant and results icons are separate from the Vehicle
Select carsheet mapping. R5V-E0.1d.2 also closed the progress-marker colour
producer. R5V-F remains **BLOCKED pending the R5V-E0.2 human P0**: verify that
the staged `T3_Car12` scene object is visible at ID25 and that navigation and
existing icons remain stable. The current limitation is scene-object display,
not the SmallCarSheet selector or race-marker colour.

At the original R5V-E0.1 closeout, no executable or runtime candidate was
produced. The separate E0.1a diagnostic candidate is ignored and uncommitted.
