# R5V-A slot feasibility

**Class: E — UNKNOWN. New slot: POSSIBLY.** Static research has found a fixed-capacity registry and one default-constructed trailing record, but it has not proved that record 25 is spare or that all consumers tolerate it. No executable was patched.

The asset-authoring path is ready; the registration path is the blocker. `vehicles.xml` alone cannot add a playable car because final EXE code explicitly initializes 25 named records and the frontend dereferences those fixed 0x34-byte records. Forklift is localized and packaged as an asset, but lacks an initialized record and physics block. Its non-finite tag101 hull is a separate runtime risk.

## Candidate future design

The least invasive *hypothesis* is to initialize the already allocated record 25 and append a class-2 frontend list entry, **if** the existing 26-entry capacity is truly 25 cars plus one spare. This is not yet an authorized patch plan: record 25 might be a sentinel, and 0x45A150 has a case for ID 25 whose semantics are untested. The alternative would be expanding/relocating the singleton, but that requires an xref audit of all direct offsets and parallel arrays. A hook is least desirable without a complete caller map.

## Required R5V-B preconditions

1. In Ghidra or equivalent, type the final singleton and inspect all code/data xrefs to 0x6F5ED4, 0x45A3C0 and constructor 0x458E00. Identify every index consumer and 25/26 bound.
2. Determine the meaning of record 25 and jump-table case 25 at 0x45A150; show whether it is a sentinel.
3. Trace the builder of `Frontend/VehicleSelect/VehicleList`, including class-2 count, unlock filter and next/previous wrap. Prove a new entry can be appended without removing an existing one.
4. Trace the car name → physics broker key → resource path chain and validate failure behavior for a missing namespace.
5. Audit AI/opponent selection and persisted `CarID`/quick-race indices for out-of-range access. Use a fresh throwaway player state for any later runtime test.
6. Only after the above, create an isolated copy of game data and EXE for a one-slot proof. First payload: a duplicated normal stock vehicle and matching physics. Preserve all 25 original IDs. Test frontend appearance, race loading, driving and restart. Then assess Forklift separately.

**Exact patch points approved now: none.** The addresses in `exe-vehicle-registry.md` are static research anchors. The final R5V-A criteria for an EXE change are not met, specifically the absent audit of dependent arrays and frontend list generation.