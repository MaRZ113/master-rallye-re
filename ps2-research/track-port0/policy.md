# TRACK-PORT policy (T0)

## 1. Delivery channels
| Channel | Mechanism | Used for | Rules |
|---|---|---|---|
| A | D3D8 proxy render overlay (`pc-port/renderer`, generalising `course_objects`) | Extra geometry, PS2 materials, visual splines/birds | Stock default; live course/camera certificate; exact state restore |
| B | Modified copies of course data (RaceTest XML, DX, DXT) built deterministically from originals | Added Eggs, trigger changes, textures | Originals and the user's `Data.sma` never modified; output in a separate folder |
| C | Native calls into `MRallye.exe` from the proxy DLL | Physics props, reading Car0 state | No EXE patch; each entry point needs a recorded evidence gate (owner, thread, teardown), as in RIGID-PORT1.x |

Each registry element has exactly one channel. `UNDECIDED` is allowed only while `status` is `NOT_STARTED`/`RESEARCHED`.
The schema forbids a `C_NATIVE_HOOK` element from reaching `IMPLEMENTED_PENDING_USER_RUNTIME` without the gate being recorded
(checked by `validate_registry.py`; the gate itself is documented in the element's `sources`).

## 2. Proposed `PS2Port.ini` keys
Existing naming: `GrassMode`, `ShrubsMode`, `CourseObjectsMode` (0 = Stock). Proposed, not yet implemented:

| Key | Values | Meaning |
|---|---|---|
| `CourseDeltaMode` | 0 / 1 | Master switch; 0 = no new file reads, no new draws |
| `CourseDeltaAssetDirectory` | path | PS2OBJ02 assets (channel A) |
| `CourseDataDirectory` | path | Channel B output folder |
| `CourseAmbientMode` | 0 / 1 | Spline objects and birds (T6) |
| `CourseRigidMode` | 0 / 1 | Physics props (T7), additionally gated |

Existing `CourseObjects` stays for the Turkey3 puddle layer until PS2OBJ02 replaces it.

## 3. Evidence gates
- G-COLL (T2): PS2 `.BSP` versus PC tag100 over the delta region. Passing means collision needs no change. Failing needs a separate user decision about a rebuild.
- G-ROUTE (T3): added RaceTest Egg proven to load on a copy of the install.
- G-PROP (T7): owner, update thread, reset and teardown for an added prop. Predecessor: RIGID-PORT1.3 NO-GO.
- Every gate result goes in the phase `validation.md` with the evidence label from the shared vocabulary in the schema.

## 4. Performance budget (to be ratified by the user)
Proposed per course against Stock, fixed three-camera comparison with `PS2PerfTiming`:
- +1.0 ms mean CPU frame time at most;
- additional draw calls capped at 64 per frame (adjust after T4 measurement);
- no memory growth after 3 race/menu cycles.

## 5. Pinned inputs
- PS2: `cdelta1/input-provenance.json` (`ps2_inputs`: SLES_509.06, SYSTEM.CNF, TNG.PAK, TNG.000 with sizes and SHA-256).
- PC: `cdelta1/input-provenance.json` (`pc_source_sha256`, 126 PS2 payload hashes); Course SDK `4244fa0` (read-only).
- Phases re-verify these hashes before use and record the check, never copy the originals.
- Original game files are read-only inputs and are not distributed in the repository.

## 6. Open items carried from the plan
Rebuild path (GXM writer and Demo 9.10 cooker; `research/r-demo-pipeline` not merged), channel B deployment form (loose files vs `Data.sma`),
live PCSX2 capture.
