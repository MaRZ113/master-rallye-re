# R5V-F — retail ID26 / sparse T1 slot

## Result

The retail object has a safely extensible heap layout. This phase builds an
ignored P0 candidate with 27 physical VehicleRecords, keeps IDs 0–24 unchanged,
retains the confirmed Trooper ID25 profile, and maps `T1 local7 ↔ ID26` without
moving T2 or T3. The new record uses Landcruiser ID0 values and the original
full initializer, including its owned-name construction path.

**Core expansion: owner-reported runtime PASS. Cleanup: pending. Independent
record proof: pending.** The original candidate completed an offline stage,
but runtime testing found two defects: T2 exposed an unintended eighth slot,
and Quick Race displayed `GALOCAL UNKNOWN` for ID26. These defects do not
invalidate the physical slot or observed race path, but the proof candidate is
not clean and the duplicated ID0 payload does not demonstrate independent
record reads.

## Owner-reported core runtime result

The owner confirmed that the eighth T1 entry is physical ID26, its preview
loads, Quick Race starts, the vehicle drives normally, a full offline stage
completes, Race Complete is reached, and returning to the frontend works.
Record this as:

```text
R5V-F CORE REGISTRY EXPANSION = PASS
ID26 OFFLINE RACE PATH = RUNTIME-CONFIRMED
T1 local7 -> ID26 = RUNTIME-CONFIRMED
```

This report is user-provided and is not tied to a supplied candidate hash or
capture. It does not close the two cleanup defects below.

## Closed expansion gates

| Gate | Finding |
|---|---|
| Registry storage | `operator new(0xC00)` is a heap allocation. Expanded size is `0xC34`; record26 occupies `[+0x54C,+0x580)`. |
| Construction | `0x458CD0` default-constructs 26 VehicleRecords at stride `0x34`; count becomes 27. The 39-row RaceTest array moves from `+0x54C` to `+0x580`. |
| Destruction | `0x458E00` destroys the RaceTest rows and VehicleRecords in reverse construction order; vehicle count becomes 27. Both exception-unwind descriptors are updated consistently. |
| Owned string | Record26 is initialized by `0x45A0B0` with a temporary `Landcruiser` string. The initializer deep-copies it; no VehicleRecord memcpy or string-pointer alias is used. |
| Secondary array | All 39 initializer LEAs and 11 direct retail field-displacement readers are adjusted by `+0x34`. The separate anonymous object near `0x40A6B9` is not a RaceTest-array reader and is left unchanged. |
| Sparse class map | `0x481E20` maps only T1/local7 to 26. `0x481E50` maps 26 only to T1/local7. Other IDs follow their original code. |
| Frontend capacity | T1 changes 7→8; T2 stays 7; the E0.2-tested T3 capacity stays 12. The 12-position updater and existing `Button7XPos` support the new widget. |
| Preview/display | The selected absolute ID remains 26 for record/stat/preview lookup. Only the two localization selectors alias ID26 to ID0. |
| Unlock | ID26 receives a test-only override at the Vehicle Select gate. The original ID25 test profile remains selectable. |
| Race path | Static retail flow carries the absolute ID through `Race/Car0/CarID`, then indexes record26 and resolves its owned `Landcruiser` name for car/wheel resources and named physics. P1 still requires human validation. |

## Donor record

ID26 is a value-level duplicate of retail ID0:

| Field | ID26 value |
|---|---|
| ID / class / T1 local | `26 / 0 / 7` |
| Internal name / runtime family | `Landcruiser` |
| Frontend stats | Speed 4, Acceleration 2, Handling 4, Endurance 6 |
| SmallCarSheet selector | 9 |
| Race colour RGBA bits | `3DAA05CC 3ED675DB 3E8172F5 3F800000` |
| Vehicle Select artwork | retail carsheet frame 3, cloned from `T1_Car1` |
| Display identity | ID0 localization selector, `TOMMEK DIRTBEAST` |

Record25 remains the runtime-tested Trooper profile: class2/local11, the
Trooper internal/resource family, SmallCarSheet selector29, Astero-derived
presentation fields, and the existing T3_Car12 scene binding. Trooper DX
overrides remain external to Git and must be present in the isolated test
installation for the P0 ID25 preservation check.

## Demo capacity oracle

The independently inspected demo constructors confirm the same development
pattern: the main record array is heap allocated, followed by a separately
constructed inline array whose start moves when the main count changes. From
demo-8.4.1 to demo-9.3.1, capacity rose 26→27 and the secondary array grew
22→39 rows. Retail has its own `0x34` record stride and 39-row secondary array;
the demo byte layouts are architectural evidence, not patch templates. Details
are in [demo-capacity-diff.md](demo-capacity-diff.md).

## Original candidate and cleanup gates

The ignored candidate is under `research-output/r5v_f/runtime-test/`. It contains
the hash-locked executable copy, a Data.sma with both existing T3_Car12 and new
T1_Car8 bindings, patch manifest, categorized binary diff, validation JSON and
P0 instructions. The archive was built from the previously staged E0.2 archive
(`BB3C…18020`); exactly one member, VehicleSelect.xml, differs from that base.

The original runtime package has now been exercised by the owner, who reported
the full-stage result above. That test also exposed the false T2 local7/Bowler
entry and the Quick Race localization failure. R5V-F.1 creates a new cleanup
candidate and requires a fresh frontend-only P0 followed by the independent
record P1 canary. Save persistence and network support remain unproven; use a
disposable profile and stay offline. The event/AI vehicle pool remains stock
IDs 0–24.

## E0.2 closeout

R5V-E0.2 is already recorded as FULL PASS by the owner in commit `5ac8fae`:
ID25 remains visible/selectable, the 12th T3 icon appears correctly, Trooper
preview is retained, and the frontend stays stable. That earlier human result
was not tied to an archive hash. Both demo builds independently contain the
authentic Trooper icon in carsheet frame14; this R5V-F package uses donor frame3
for ID26 and the existing diagnostic frame5 for T3_Car12. See the E0.2
findings and Trooper icon inventory.

## Evidence boundaries

Registry counts, raw operands, and control flow are static retail Ghidra
evidence cross-checked against instruction bytes and a Capstone decode of the
candidate code cave. The candidate's SHA hashes and archive member diff are
automated local checks. Core slot/race observations are owner-reported runtime
evidence; the cleanup P0 and independent-record P1 remain pending.
