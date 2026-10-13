# PS2-RIGID-PORT1 — native resource/lifecycle checkpoint

Phase: PS2-RIGID-PORT1 + HUD-PORT0
Repository: D:\Game\Master Rallye\master-rallye-re-general
Branch: master
Starting/ending HEAD: 0bddf7c7bc5e95831f98714ff6231da05ab073ea
Frozen renderer tree: e33386bcf682db6983380c499e4928726c758fe0
Preflight: existing pc-port tracked edits/untracked implementation/revalidation1 preserved
New native physics feature: NOT_ENABLED
New HUD feature: NOT_IMPLEMENTED (research/design only)
Push/deployment: NONE
Overall: PARTIAL; PRIVATE_NATIVE_RESOURCE_AND_LIFECYCLE_GATE_OPEN

## Outcome

The independent GRASS2 audit was read and its two raw session logs were
rechecked locally. Both second-category native draw/state transactions and the
user's visible new branching vegetation are confirmed at their separate
evidence levels. Compact facts/hash provenance are in
`grass2-runtime-review.json`; exact PS2 pixels and physical tumbleweed remain
unproved. Existing grass, shrubs, puddles, reflection, foliage and HUD performance
behavior was left intact; both DLLs are byte-identical to the accepted build.
No further legacy build cleanup was performed or inferred from this task.

The highest-value new native result is the missing **cache invalidation
predecessor**. Original PC update43F2C0 calls maintenance43F310/43F350 before
physics substeps. It clears nonvehicle body+1D4 and calls the installed backend's
vtable+30 ->56FCE0, which clears convex instance+18 before stale-pair cleanup.
Thus the earlier possibility of an indefinitely retained cache cannot be used
as a demonstrated defect. Retiring a new object is still not safe without
valid owner/resource lifetime, update-thread and teardown evidence. The earlier
static report is preserved; this correction is explicit in
`native-pc-lifecycle-20261013.md/.json` (39 original probes/12 function hashes).

## Original tumbleweed and conversion

Selected source is Turkey3 XML list11/egg13/ai0, one of six authored records,
not six measured simultaneous live objects. Original model is
`TUMBLWEED.PSM` SHA eb959250d0bdb6fa051fb69f4a852c4789be200613eb8e90678d36a48ab54bf4.
It contains 96 visual source vertices/48 emitted faces, `bigshrub treeblend`,
and its own `SHRUBTRIG2-TGA.GXI`. Its two convex representations retain8/12 and
26/48 source vertices/faces; source mass5, local MOI(2,2,2), original authored
matrix and trigger metadata are preserved. Dynamic placement can adjust height;
authored position is not a permanently fixed runtime pose.

The exact4612-byte tag101 block passes the existing strict PC Course SDK reader
and serializer **byte for byte**, SHA
27cb1089bf997a0b20d6a4f98fee9827a9089972ff6e891fce5cf34e41e01d48.
Native reader57CE60 consumes the4608-byte payload **after** tag dispatch; do not
feed it the tag twice. The private raw block remains ignored; only compact wire
spans/counts/bounds/hashes and tooling are packaged. No hay hull substitution,
new DX, source XML or SDK change was made. Byte-compatible wire is not native
allocation/registration evidence.

## Exact remaining implementation gate

57CE60 expects ECX=parser, stack+4=native stream, and original stream-vtable
float/integer methods+3C/+44. The native filesystem stream constructor64CE80
does not establish a bounded memory-stream adapter. Attachment56EEF0 obtains
the convex prototype through Egg+50 -> en3d+C model ID ->54B320 model cache ->
wrapper+4 -> model+C, clones via621220, and binds body/category via621310/621330.
54B320 can load/evict/update caches; it is not a read-only observer API.

Required before spawning: an owned stream/private model-cache/prototype bridge,
allocation-failure rollback, native Egg admission on the verified game physics
thread, retained shape/body lifetime, and controlled restart/exit observations.
No guessed wrapper, occupied AI slot, vector mutation, D3D EndScene spawn or
renderer-side collision approximation bypasses this gate. Source mass/inertia
alone cannot prove native solver parity.

## Bounded diagnostic supplied

`tools/rigid_lifecycle_probe.py` supplies explicit-PID read/query-only samples
and an exact-EXE x32dbg logpoint generator. Holder6F957C -> backend+8 is gated by
vtable692318; vector14/18/1C and the corrected instance slots are preserved.
Only typed nonvehicle body691A04 allows XYZ/four-word orientation decoding. Root/vector/
instance double reads, pointer/count/finite limits and bounded reads fail
closed. Read-only snapshots are not atomic, do not establish a course owner,
and cannot prove contact or deletion. The separate capped debugger recipe
establishes original function/thread observations when run by the user; it
instruments live code/timing and was not executed here. See `runtime-control.md`.

One original vehicle is a valid **shared convex-interface** control when no
original nonvehicle prop is available in Turkey3. It is not proof of private
prop ownership or contact. No game was launched or sampled by Codex in this
phase. An actual native physical-object/car test remains required after safe
admission is implemented. Visual integration is intentionally blocked until
the same native body's live pose/lifetime can own the private source mesh.

## Separate statuses

| Contract | Status | Evidence/boundary |
|---|---|---|
| RIGID_NATIVE_INTERFACE | PARTIAL | Original class/backend/reader/body/update interfaces proved; admission ABI/thread remains open |
| RIGID_COLLISION_RESOURCE | PARTIAL | Original convex wire and strict round-trip PASS; private native registration/retention BLOCKED |
| RIGID_ENTITY_LIFETIME | PARTIAL | Original cache clear/cleanup proved; injected ownership/rollback/restart capture missing |
| RIGID_VEHICLE_CONTACT | NOT_PERFORMED | No injected body or vehicle impact executed |
| RIGID_VISUAL_INTEGRATION | BLOCKED | No admitted body/owner supplying a verified live world pose |
| RIGID_RUNTIME_READINESS | BLOCKED | Read-only control ready; physical pilot remains disabled |
| HUD_PS2_CONTRACT | PARTIAL | Original HUD banks/assets/owners and selected math proved; final display composition/live mapping incomplete |
| HUD_PC_INTEGRATION_FEASIBILITY | PARTIAL | Proposed plate-only pilot; exact SpeedDial packet/resource ownership still missing |

HUD's separate source comparison, feature matrix and no-implementation proposal
are in `../hud-port0/final-report.md`. It preserves PC live value feeds and the
recent once-per-frame HUD race cache. The PS2 minimap is a procedural feature,
not an interchangeable radar image; pause changes remain out of scope.

## Verification and handoff

Both serial incremental Win32 Release builds PASS in canonical reusable roots.
Baseline24/24 CTest, PS2-enabled30/30 CTest; focused port Python107/107 PASS
including10 new observer tests and9 wire/source tests, no failures/skips in
the original checkout. Generator determinism/exact patches, D3D8 exports,
compileall and diff-check PASS. HUD math29/29; final Pillow-equipped canonical
PSB rerun25/25 PASS. The earlier venv's missing-Pillow dependency attempt stays
documented separately. No packages were installed.

Baseline DLL SHA:
011dd9a94155d216d0c0dde28e0af97f5b72226aae5be97016f2d767ebdf7138

PS2-enabled DLL SHA:
6edc2426e2602545121f16959cdbb2055fb205a907b36173cb85a447b7051deb

These equal the independently reviewed GRASS2 release. Stock modes remain0;
there is no new rigid/HUD mode to enable. Renderer Git/source hashes and clean
Course SDK HEAD4244fa0c4d878523c9947f54816bf377cdfb2589 were verified. Original
PS2 corpus identities were freshly rechecked by the source/HUD audits; no
original PC/PS2 files, renderer code, game data or SDK files were written.

The new compact handoff is `dist/PS2-RIGID-PORT1-HUD-PORT0-handoff.zip`, with
sources/tests/exact overlay patches/docs/compact evidence/two unchanged DLLs/
manifest/build report. It excludes original hulls/textures/ELF/DX/XML/raw logs
and full renderer copies. See its HANDOFF for isolated vs external-data tests.
Existing uncommitted port work is preserved; no broad commit or push was made.

## One next step

Perform the single bounded **original native convex lifecycle control** in
`runtime-control.md`. Use the observations to close original thread/ownership/
teardown links, then design the owned stream/cache bridge for one source object.
Checkpoint barrels, broader population and HUD implementation are deferred.
