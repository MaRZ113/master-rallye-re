# R5V-I — multi-slot vehicle registry

## Current result

**R5V-I.0 slot proof: STATIC PASS / READY FOR HUMAN RUNTIME.** The exact
retail executable can be deterministically extended to a 28-record registry
with sparse `T2 local7 -> physical ID27`, while preserving physical ID25
Trooper and ID26 Mercedes. The candidate and matching Vehicle Select overlay
are staged together in the ignored runtime package and verified before launch.

**R5V-I.1 real T2 vehicle: `REAL_T2_PAYLOAD_REQUIRED`.** The I.0 ID27 profile
reuses physical ID7/Navara's render, wheel, physics and audio families as an
explicit slot diagnostic. It is not an independent T2 vehicle and cannot close
the required second-vehicle qualification. The audited corpora contain no
ready independent T2 cooked payload. See [the payload audit](id27-vehicle.md)
and [machine-readable evidence](payload-audit.json).

R5V-I is therefore still **OPEN / NOT FULL PASS**. Static synthesis and the
candidate do not establish in-game T2_Car8 construction, ID27 materials,
physical behavior, collision, damage, AI, or results. Do not report R5V-I as
runtime-confirmed until the human test and a real independent T2 vehicle both
pass.

## Sparse identity map

| Class | Class-local indices | Physical Vehicle IDs | Status |
|---|---|---|---|
| T1 | 0–6 | 0–6 | retail mapping preserved |
| T1 | 7 | 26 | Mercedes, previously runtime-confirmed |
| T2 | 0–6 | 7–13 | retail mapping preserved |
| T2 | 7 | 27 | Navara donor slot proof only; runtime pending |
| T3 | 0–11 | 14–25 | retail mapping preserved; ID25 remains Trooper |

The native mapping uses separate class-local fields. ID27 does not mean ID14:
physical 14 is the first T3 vehicle. All 26 existing retail physical IDs keep
their prior class/local mapping. See [the mapping proof](class-mapping.md).

## Registry and adjacent table

The candidate has 28 `VehicleRecord` slots with a 0x34-byte record stride and
a 4-byte leading header. `VehicleRecord[27]` starts at allocation offset
0x580. The existing 39-row `RaceTest` table begins immediately afterward at
0x5B4, uses 0x2C-byte rows, and the combined allocation is 0xC68 bytes. The
candidate relocates the adjacent RaceTest start by 0x34 from the H.2 parent;
39 initializer displacements and 11 indexed consumers are shifted accordingly.
Constructor, destructor and unwind counts cover 28 records. No participant
capacity, HUD, Results, course, or generic N expansion is part of I.0. See
[registry layout](registry-layout.md) and
[secondary-array relocation](secondary-array-relocation.md).

## Candidate boundary

The candidate composes the exact H.2 physical-ID26 result from pristine
retail. It appends a complete ID27 record, extends the T2 capacity to eight,
adds the T2 sparse mapping and routes ID27 through the existing native
exclusion/append body at Quick Race, new Rallye Cup roster creation and new
Master Rallye competition creation. Existing Cup/Master rosters remain
unchanged; Challenge remains authored; normal Invitation remains on its
T3-only route. Native DriverID selection is preserved.

The I.0 record mirrors the T2 ID10 unlock gate and uses audio profile 7 only
because its current render donor is Navara. The cyan race colour, donor image,
stats, `SLOT PROOF / DONOR` wording and Results label exist to distinguish the
new physical slot from ID7. They are diagnostic scaffolding, not authentic
vehicle identity. See [unlock](unlock.md), [audio](audio.md), [AI](ai.md) and
[human runtime plan](runtime-plan.md).

The old/general randomizer is absent, `Race/NumCars` behavior is untouched,
and this candidate does not force ID27 into a participant slot. The runtime
package excludes PlayerState/save files and raw captures.

## Next gate

Run the I.0 slot proof only after the staged package verifier passes. Stop at
any registry, selection, actor, model, wheel, physics, collision, AI or race
anomaly. A donor-based slot proof can validate slot architecture; it cannot
substitute for R5V-I.1's required independent T2 vehicle. The first needed
input is a distinct cooked T2 family (`car.dx`, `complete.dx`, `wheel.dx`,
its DXT dependencies and independently qualified physics/collision data), or
an explicit decision to start a separate conversion/cooker/physics phase for
the demo Rav4 source.
