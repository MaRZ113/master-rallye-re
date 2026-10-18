# TRACK-PORT policy

Revision 2. Replaces the first draft after six plan corrections (see section 7).

## 1. Delivery channels, per aspect
A composite object (for example a tumbleweed, a checkpoint, a boat) is split into four aspects. Each aspect has its own channel,
so one element can be drawn by the overlay, spawned from copied data and simulated by a native hook.

| Aspect | Meaning |
|---|---|
| visual | what is drawn: meshes, textures, materials |
| spawn | how the object comes to exist: Egg in RaceTest XML, overlay-managed instance, none |
| physics | collision shape, rigid body, surface behaviour |
| logic | triggers, AI, timing, controllers |

| Channel | Mechanism | Rules |
|---|---|---|
| A_RENDER_OVERLAY | D3D8 proxy overlay (`pc-port/renderer`, generalising `course_objects`) | Stock default; live course/camera certificate; exact state restore |
| B_DATA_COPY | Modified copies of course data (RaceTest XML, DX, DXT) built deterministically from originals | Originals and the user's `Data.sma` never modified; output in a separate folder |
| C_NATIVE_HOOK | Native calls into `MRallye.exe` from the proxy DLL | No EXE patch; needs recorded `gates` (owner, thread, teardown) before the element can leave RESEARCHED |
| NONE | The aspect exists but nothing will be ported | |
| N_A | The aspect does not exist for this element | |
| UNDECIDED | Allowed only while the status is NOT_STARTED or RESEARCHED | |

`validate_registry.py` enforces: all four aspects present; native hooks need `gates` once implemented; trigger elements carry
`behavior_intent`; the first course carries PCSX2 verification on every non-SAME element.

## 2. Comparing geometry: coverage, not triangles
An unmatched triangle is not necessarily absent on PC (re-triangulation, another pose, another texture, hidden under terrain).
T1 therefore reports, per element and area-weighted:
- exact triangle matches (SAME);
- coplanar and near-parallel PC surface coverage (`geometry_delta`: `coverage`, `near_coverage`);
- plan-view relation to the PC surface below (coincident, overlay, slightly or far below or above, none under);
- rigid congruence to PC draws of the same texture or of draws that exactly matched the same texture (a placement difference, not a missing mesh).

Only an element with no exact match, no surface coverage and no congruent counterpart is `MISSING_ON_PC`. Everything else is
`PLACEMENT_DIFFERS`, `DIFFERENT_MATERIAL` or `UNCLASSIFIED` with the numbers attached.

## 3. Evidence gates
- **G-COLL (collision).** AABB overlap and plane sets do not prove equal physics, so they are only used to pre-select regions.
  The gate needs (a) geometric queries run on both collision datasets through the same query set: vertical ray height grid over the
  delta regions, horizontal rays and convex sweeps along the RaceLine, closest-point and penetration depth for the car hull and for
  prop hulls, and the surface-type id returned by each query; and (b) a runtime check: the same probe points driven or
  teleported in the PC game, and on PS2 through PCSX2 (section 4), comparing height, contact and surface. A mismatch beyond
  the stated tolerance fails the gate. Dependent on T2 reversing the PS2 `.BSP`.
- **G-ROUTE (T3).** Added RaceTest Egg proven to load on a copy of the install.
- **G-PROP (T7).** Owner, update thread, reset and teardown for an added prop (RIGID-PORT1.3 was NO-GO).
- Every gate result goes in the phase `validation.md` with the evidence label from the schema.

## 4. PCSX2 verification is mandatory for the first course (Turkey3)
Static reading is not enough to claim PS2 behaviour. Before Turkey3 elements can be marked verified, the live PS2 side is captured
with PCSX2 Nightly (version 2.9.117.0 was used in REVALIDATION2; installed at `C:GamesPCSX2_Nightly`) on the canonical disc and ELF,
following [../revalidation2/pcsx2-capture-plan.md](../revalidation2/pcsx2-capture-plan.md).
Required captures: fixed-camera frames for puddles, shrubs, hut, house, caravans and boats; GS state for puddle and treeblend draws;
collision probes from section 3; split timing and checkpoint contact; observed bird and emitter behaviour; prop contact.
Each registry element of the first course carries `pcsx2_verification` REQUIRED_PENDING until captured, then PERFORMED.
If a capture raises a question the static data cannot answer, further dumps (GS registers, EE memory, VU micro-RAM) are taken on
request and recorded in `validation.md`. Later courses use the same capture set when the captured feature is new to them.

## 5. Trigger and logic criteria: intended versus unchanged
Every trigger element states `behavior_intent`:
- **UNCHANGED_FROM_PC.** Parity test: Stock and modified runs of the same drive must agree on split times, progress percentage,
  event order and LimitState within the repeat-run noise measured on Stock. Any difference fails.
- **INTENTIONALLY_CHANGED.** The specification of the new behaviour (for example a different ExtraTime or a moved trigger) is
  written down with its PS2 source before testing. The test checks that the specified change happens and that every other
  quantity listed under UNCHANGED_FROM_PC still holds.
- **UNDECIDED** blocks implementation.
The PC-only `Copy of SplitTime1` Egg on Turkey3 is UNCHANGED_FROM_PC unless the user decides otherwise.

## 6. Proposed `PS2Port.ini` keys, performance budget, pinned inputs
Keys (not yet implemented): `CourseDeltaMode` (0/1 master switch), `CourseDeltaAssetDirectory`, `CourseDataDirectory`,
`CourseAmbientMode`, `CourseRigidMode`. Existing `CourseObjects` stays until PS2OBJ02 replaces it.

Budget per course against Stock (three fixed cameras, `PS2PerfTiming`), to be ratified by the user: at most +1.0 ms mean CPU frame time,
at most 64 additional draw calls per frame (revisit after T4), no memory growth over 3 race/menu cycles.

Pinned inputs: `cdelta1/input-provenance.json` (PS2 files and `pc_source_sha256`), Course SDK `4244fa0` (read-only).
Phases re-verify hashes and record the check. Original game files are read-only and not distributed.

## 7. Plan corrections recorded in this revision
1. Compare geometric coverage, not only triangles (section 2; T1b metrics).
2. G-COLL uses geometric queries and a runtime check, not AABB and planes (section 3).
3. Channels are per aspect (section 1; schema `channels`).
4. T1 is split: Turkey3 first (done as T1a/T1b), then the prototype, then the full 36-course census (T1-full) after the prototype gates.
5. PCSX2 checks are mandatory for the first course with follow-up dumps on demand (section 4).
6. Trigger criteria separate intentionally changed and unchanged behaviour (section 5).
