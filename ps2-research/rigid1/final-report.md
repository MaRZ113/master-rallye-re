# PS2-RIGID1 final report

| Summary field | Result |
|---|---|
| Phase | PS2-RIGID1 |
| Repository | D:\Game\Master Rallye\master-rallye-re-general |
| Branch | master |
| Starting HEAD | d34a95de2033d6b6cfc94d3b2f55bd0100198d9b |
| Ending HEAD | scoped phase commit recorded in handoff MANIFEST.json and external receipt |
| Preflight | master ahead1; six unrelated modified/untracked Observatory paths preserved |
| Canonical ELF | 3739852 bytes; SHA256 b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2 |
| PackFS provenance | allfour canonical SHA/size checked; existing PackFS reader reused |
| Authored objects | 83 gaAiRigidBody records; not a live population count |
| Haybales | 58 authored records |
| Tumbleweed | 25 authored records |
| Course coverage | 36 canonical pairs;9 rigid courses;3 detailed controls |
| Model aliases | two hay paths,byte-identical; exact tumblweed spelling retained |
| Model hashes | hay cd6da2625e707387c8b18e02f42fcf655d5135fa8e9986cb8894bf10734447cb; tumble eb959250d0bdb6fa051fb69f4a852c4789be200613eb8e90678d36a48ab54bf4 |
| gaAiRigidBody registration | string472360; vtable473820 |
| Factory | 15b190,prop constructor call15d014 |
| Constructor | 19fcd0; AI allocation3c |
| Property parser | 19fe98; typed readers1e2470/1e2510/1e2a48 |
| Update | 1a0258 |
| Destructor | 1cfe90 owner; separate body destruction2667e0 |
| Runtime layout | AI3c; body1dc; manager74; transform AI14; convex instance20 |
| Physics manager | 1715c8 ->171c78 prop vector; update1733a0 |
| Collision shape | PSM tag101,base+two convex representations; hay A8/12 B16/28,tumble A8/12 B26/48 |
| Shape ownership | model+34 ->2e2f10/244108 ->244230 body and entity carrier |
| Mass semantics | authored m ->body+20; inverse1/m ->+24 |
| MOI semantics | diagonal local inertia ->inverse ->R IbodyInv transpose(R) |
| Trigger Distance semantics | typed owner+18; NOT_READ_IN_1a0258; broader consumer UNKNOWN |
| Shadow parameter semantics | typed owner+10; actual render consumer UNKNOWN |
| Activation | first two view entries,shared radius4 predicate,3D squared distance<=10000 |
| Deactivation | far pause plus60-invocation factor1/60 decay |
| Sleep/wake | successful contact wakes paused prop; near resumes far-paused; low-speed contact clamp can sleep |
| Reset | manager/body destruction proved; complete per-entity/restart sequence UNKNOWN |
| Physics timing | two float32 halfsteps .01666666753590107 per manager invocation; wall-clock frequency UNKNOWN |
| Linear motion | momentum state,v=P/m,selected mode1 RK4 |
| Angular motion | world omega/quaternion Hamilton derivative,normalization and original quaternion matrix |
| Force inputs | base force/torque and extra contact accumulators |
| Gravity | 27d060,F=(0,-float32(9.81)*m,0) |
| Wind | no input found in selected callback/owner; other extra-force writers not exhausted |
| Damping/friction | owner far decay and rest logic proved; solver friction/restitution mix UNKNOWN |
| Vehicle contact | 16e498 dispatch/wake ->selected response branch ->state writes |
| Terrain contact | convex/BSP2470f8,initial placement16f2f0 and manager contact chain |
| Impulse response | 25da08 applies selected J=lambda*n to both bodies; lambda magnitude UNKNOWN |
| Body-world transform | 267f60 rows=right/up/forward; translation=position-R COM |
| Visual transform consumer | Broker1e3f50 ->same key ->265d18/1e36d8 ->entity en3d+20..5c |
| ItalyS1 | 14 Egg records/13 matrix hashes;mass500,MOI565/447/565 |
| Turkey1 | 7 records;mass5,MOI2/2/2; authored convex/treeblend model |
| Cross-course control | Italy2,11 records;MOI562/447/562;shadowFalse |
| PC haybale content | standalone34 vertices/28 triangles; two convex reps agree within.0001; baked candidate draws13/16 |
| PC tumbleweed content | NOT_FOUND_IN_SCANNED_PC_CORPUS,7595 names/270 XML-TXT files |
| Static duplication risk | exact PS2 Egg-to-PC baked triangle subset UNKNOWN; no whole-draw replacement |
| Offline diagnostic | rigid_runtime.py inventory/shapes/pc/contract/evaluate |
| Runtime validation | NOT_PERFORMED |
| Unittest | 345 PASS,0 fail,0 skip; focused37 PASS |
| Pytest | 345 PASS +290 subtests,0 fail,0 skip |
| Compileall | PASS |
| Diff-check | final closeout recorded in validation.md |
| Determinism | byte-identical explicit synthetic CLI and compact source regeneration; isolated301 pytest PASS/44 external skips |
| Originals unchanged | four full PS2 and five inspected PC hashes; no source writers |
| Course SDK unchanged | clean at4244fa0c4d878523c9947f54816bf377cdfb2589 |
| PC renderer unchanged | renderer/proxy diff empty |
| Commit | actual scoped hash in MANIFEST.json/ZIP receipt and final user response; no recursive self-hash |
| Push | NOT_PERFORMED |
| Overall status | PS2-RIGID1 STATUS: COMPLETE â€” bounded static/executable reverse |

# Most important discoveries

This is a real rigid-prop subsystem for both authored families. The recovered contract runs from typed source properties and actual model convex geometry through a registered physical state to the same entity's visual world matrix. It reaches position/orientation updates and contact state commitment, rather than only class names or a list of candidate functions.

Two corrections matter for future fidelity. First, the authored `Trigger Distance` values5/15 do not control the selected update; it uses a fixed view-qualified100-unit distance. Second, proximity alone does not wake an initially paused, settled body. A successful contact wakes it; near visibility resumes a previously moving body paused because it became far away. Replacing this with ordinary player-radius wake behavior would change the original semantics.

# Authored data and ownership

Fresh extraction reproduces83 ordered source records (58hay/25tumble) over nine courses. ItalyS1's coincident transform remains two source records. Property reader19fe98 feeds direct mass and diagonal local inertia through19ff18. Both hay aliases are identical, while tumbleweed has different authored convex topology. Trigger/shadow storage is proved; their broader consumers remain unknown. Source parameters and live population are deliberately separate.

The AI allocation3c owns a pointer to a separate1dc body registered in the74-byte manager. The model owns a static convex prototype at+34; the installed concrete collision backend clones it per entity and binds the actual body pointer into its component representations. A separate transform AI consumes the shared entity-derived Broker key. Manager destruction owns body cleanup; mid-course removal/restart/name-pool behavior remains bounded.

# Five evidence-backed causal chains

```text
A authored
canonical RaceTest gaAiRigidBody record [BYTES]
 ->factory15b190/call15d014 ->ctor19fcd0 [EXE]
 ->typed19fe98 ->owner fields ->19ff18 body parameters [BOTH]

B physical shape
selected prop PSM tag101 [BYTES]
 ->38fac0/3946e0/3b4c20 ->model+34 [EXE]
 ->2e2f10/244108/244230 ->registered body shape [BOTH]
 ->2e3270 pair dispatch [EXE]

C movement/contact
1733a0 manager ->173b68 two substeps ->173cc8/269968 [EXE]
 ->force27d060 + derivative266e20 ->2670b0 state/R/bases [EXE]
contact16e498 ->selected solver branch ->25da08 ->23e968 state [EXE]
UNKNOWN LINK: full constraints/materials ->chosen impulse magnitude

D displayed pose
body x,q,R/COM ->267f60 ->1e3f50 Physics/{name}/Transform [EXE]
 ->same key265b58 ->265d18/1e36d8 ->same en3d matrix [EXE]
 ->shared entity model draw21ea20/3301c8/3302b8/330780 [reused EXE]
UNKNOWN LINK: independently captured live prop/frame

E PC counterpart
PS2 convex A/B ->independent SDK PC standalone collision [BYTES]
 ->identity-coordinate .0001 vertex agreement +same indices [STATIC_INFERENCE]
PC baked hay draw/TXT leads [BYTES]
UNKNOWN LINK: individual PS2 Egg ->removable PC baked instance
```

The compact machine-readable contract,75 function records and original instruction/vtable probes support the arrows. Function names are proposed roles, exact addresses are canonical; truncated bounds and the backend installation's enclosing function start are explicitly UNKNOWN.

# Physics and actual visual transform

The13-value state is position,q(wxyz),P,L. Velocity=P/m and omega=worldInverseInertia*L. The derivative contains .5*((0,omega) Hamilton-product q), base+extra force and torque. Init installs gravity9.81; no selected wind/RNG operation was found. Mode1 RK4 preserves the original repeated-add weighted expression. Two halfsteps per invocation are proved, while real scheduler cadence is not.

Contact dispatch can clear a prop's pause/rest state. Given the selected lambda,25da08 applies J=lambda*n and r cross J with opposite signs to the two bodies. Accumulators and23e968 commit velocity/momentum/position;267940 reconstructs angular momentum. Friction/restitution mixing, lambda selection and full narrowphase are not invented. These boundaries are not required to close the meaningful bounded update/pose chain.

Pose producer267f60 forms model rows from body basis and translation=position-R*localCOM. Its Broker matrix is consumed by265d18 into all16 words of the actual entity en3d world matrix. The generic renderer reads that model/world state. This establishes the physical-to-visual owner path without a fresh universal GS/VU reverse or emulator frame claim.

# Primary cases and PC restoration implications

ItalyS1 mass500/MOI565,447,565 haybales and Turkey1 mass5/MOI2,2,2 tumbleweed use the same proven controller with different shape/material/parameters. Italy2's11 records and different MOI/false shadow provide a bounded third control. Authored static transforms are only the initial input, not the later race pose.

PC has a standalone hay model and collision geometry whose two convex vertex sets match within0.0001 and index arrays are identical. It also has baked hay-texture draw candidates in Italy_S1/Italy2. Counts of candidate draws and named sidecar meshes are not object counts; no per-instance removal/replacement is ready. No named tumbleweed counterpart was found in the bounded scan. A future restoration needs instance mapping, PC scene/body/contact interfaces, safe lifetime and visual matrix ownership; the draw proxy alone does not provide them.

# Remaining proof boundaries

Original contact impulse magnitude; meanings/mixing of body surface coefficients; detailed convex A/B narrowphase selection; the initial matrix-to-quaternion helper205628 nonpositive-trace branch; effective clamp configuration and wall-clock scheduling; shadow/trigger consumers beyond selected init/update; later COM writers; individual teardown/restart; exact PC baked-instance correspondence; live original physical/visual parity. Positive static gravity/controller/pose evidence is retained without universal claims about all environment forces. The evaluator takes an explicit quaternion and does not synthesize the unresolved initial conversion branch.

**RUNTIME_VALIDATION: NOT_PERFORMED.** The capture plan identifies exact points to inspect for a selected ItalyS1/Turkey1 prop. Synthetic math, byte equality and passing tests are not a captured car strike.

# Next recommendation

**PC-VISUAL-PILOT1**, separately authorized, bounded to one previously proved material effect on shared France1/ItalyS1 water geometry. The survey now supports a small visual pilot; RIGID1's instance/contact gaps make full dynamics a less suitable first implementation. This phase does not start the pilot or any further reverse.
