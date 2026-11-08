# Forced AI roster and starting grid

Vehicle identity and grid position are separate controls. A participant has a
stable `CarN` slot; that slot receives a physical `CarID`, a registry-derived
`CarClass`, an independently selected `DriverID`, and later a transform from
the course start-grid builder. Reordering one axis must not silently rewrite
the others.

## D1 — Forced physical vehicle roster

**Status:** feasible with localized patches. **Confidence:** medium-high for
the new-roster boundary; low for duplicate-ID gameplay. The native builders
publish each selected vehicle through the per-slot setters at `0x004ACAF0`
(`CarID`), `0x004ACC10` (`CarClass`), and `0x004ACCD0` (`DriverID`). The class
comes from the selected physical VehicleRecord. The participant slot passed to
the setters is independent of the physical ID. The Quick Race chooser itself
is `0x00458090`; Cup/Invitation use `0x0045ABC0`; Master Rallye uses
`0x00451DD0`; Challenge publishes authored identities in `0x0044FEC0`.

A bounded first implementation should resolve a manifest/config slot to a
validated absolute physical ID at a new roster boundary, then publish that ID
and its actual registry class for the same `CarN`. Keep native DriverID
selection and participant/controller construction. Do not set only CarID while
leaving a stale class. Do not write to an active Race or an existing
`RaceData/CompetitorN` / `MasterRallye/CarN` roster after the event has been
created. Cup and Invitation create a roster once; Master Rallye creates one
only for a new competition. Challenge needs a separate event-specific rule and
must feed the identical forced identity to its prepared preview and race
consumer.

Repeated physical IDs are a later gate. The retail AI chooser refills an empty
physical-ID pool, but neither the R-MOD seven-AI crash nor duplicate CarID
materialization has been qualified. A forced roster must still create separate
participant objects, controllers, DriverIDs, progress and result records.

**Unknowns:** whether every mode accepts arbitrary cross-class IDs while
preserving competition rules; whether duplicate IDs are safe through all
runtime and Results paths; how active two-human paths assign human slots.

**Risks:** wrong-class competition semantics, preview/race divergence,
campaign-save mutation, duplicate-sensitive caches, and collision with the
existing F3 selection hooks. **Required owner:** one unified patch planner;
mode-owned generation boundaries only.

**Minimal PoC:** force one stock physical ID for one AI slot in a new Quick
Race, check CarID/Class/DriverID and two independent participant identities,
then complete Results and return. Test a repeated ID only after crash cause is
understood. **Effort:** medium for Quick Race, high for all modes.

## D2 — Forced starting positions

**Status:** native-slot permutation is feasible with a localized patch;
arbitrary world-space transforms require substantial changes. **Confidence:**
medium. The retail grid owner is `FUN_0048E2D0` at VA `0x0048E2D0` (RVA
`0x48E2D0`), which calls `FUN_0048EB40` at VA `0x0048EB40` (RVA `0x48EB40`).
The latter reads course `StartArea` geometry, derives row/column positions from
participant count, and writes a per-`Race/CarN/Transform` result. The native
formula uses course-relative inputs and fixed spacing; it is not a public,
course-independent coordinate API.

The least invasive design is a permutation from participant slot `CarN` to
the already generated native grid ordinal. Preserve each course's transform,
orientation, native AI path initialization and reset behavior. Arbitrary
coordinates would need terrain alignment, orientation, collision clearance,
and AI path setup; no general coordinate model is established here.

The corpus audit covers 39 scene registrations and 36 distinct course
RaceTest resources. All 36 contain structural `Car0..Car7` templates and
StartArea data. The audited normal-path formula reads the first two marker
positions `P0` and `P1`, derives horizontal forward `d`, side vector, segment
length `L`, and `K = trunc(abs(L * 0.1666666716))` (minimum 2). For ordinal
`i=0..7`, it uses `row=i//K`, `column=i%K`, and normally assigns slot
`Car(7-i)` at `P1 - d*(L/2) - d*(6*column) - side*(8*row)`. Longitudinal and
row spacings are six and eight world units. All 36 course runtime-clearance
statuses are `NOT_TESTED`.
The earlier eight-participant Italy_S4/Track10 observation was unsafe/near
geometry. Therefore no course is certified clear for a forced eight-car
layout by this static audit.

**Unknowns:** whether grid ordinal is also consumed as a stable AI/Results
ordering key; behavior on restart/replay and split-screen; safe spacing by
course and vehicle bounds; authored Challenge grid assumptions.

**Risks:** overlap, terrain penetration, wrong-way orientation, first-frame
AI movement and authored event choreography. **Required owner:** install a
single slot permutation before transforms and AI paths are initialized;
disabled mode must preserve the retail sequence exactly.

**Minimal PoC:** one explicitly runtime-qualified course, four participants,
swap two grid ordinals while keeping CarID/DriverID fixed, and verify start,
first seconds, reset, full race, Results and return. Expand per course only
after clearance tests. **Effort:** medium for ordinal permutation, high for
course-wide qualification; arbitrary coordinates are very high.

## Course qualification boundary

R-AI2.1 confirmed actor/capacity and complete lifecycle on its tested
fixed-roster candidate. R-GRID8 establishes structural availability, not
physical clearance. Forced-grid work must consume a per-course qualification
allowlist; it must not infer safety from the eight CarN templates or from the
participant capacity.
