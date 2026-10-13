# PS2-RIGID-PORT1.1 — original native lifecycle control

Status: **CONTROL_PARTIALLY_CONFIRMED; PRIVATE_SPAWN_BLOCKED**.
Repository/branch: master-rallye-re-general / master.
HEAD: `0bddf7c7bc5e95831f98714ff6231da05ab073ea`.
Frozen renderer tree: `e33386bcf682db6983380c499e4928726c758fe0`.
No renderer/overlay/native pilot modification, deployment or push.

## Runtime evidence actually obtained

The user performed cold Turkey3 load, brief driving, restart and return to the
menu. Course/activity is **USER_RUNTIME_OBSERVATION**, not a new native course
certificate. The passive sampler opened the exact retail process with query/
read rights only: SHA `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`,
PE32/i386/base400000. Both60second runs produced597 valid snapshots with no
failed/changed reads, no truncation and no engine calls/data writes.

* PID36572: vector0 →1 →0 →1 →0; two different observed instance/body pairs.
* PID12760 under user-operated x32dbg: vector0 →1 →4 →0 →1 →0 →1 →0;
  six different observed instance/body pairs. This source inventory is not a
  count of simultaneously visible props, a new-body generation registry or
  a claim that a particular class is a tumbleweed.

The expected installed backend vtable692318 and its cache-clear slot56FCE0
were read live. Typed state at body+A0..B8 changed while the user drove; its
legacy sampler field is `native_nonvehicle_position`. This name does **not**
independently classify the sampled object's gameplay role. All observed bodies
have vtable691A04/category5; the role remains UNKNOWN without an owner join.
Zero membership after exit means not present in the observed vector, not proof
of each destructor/refcount/free or absence from every other owner.

The saved x32dbg log has126 `RIGID_PROBE` records, all thread **0x1DA4 /7588**.
Six clone-constructor ECX pointers and the corresponding body-bind ECX/arg0
pairs match **all six** passive pointer pairs exactly. The last two pairs
consume the same prototype argument **0x134EEDD8** with different destinations/
bodies. Six original convex-reader enter/RET observations corroborate the
native reader path, but do not identify that resource as the private PS2 hull.
The constructor's stack prototype argument must not be confused with its
allocated-instance ECX.

There are15 observed `physics_update_enter` → `instance_cache_clear_enter`
sequences on the same thread. The initial clear has no captured predecessor;
each breakpoint has an independent counter, so equal hit numbers are not
paired call frames. Original first16bytes of both selected loaded functions
matched the canonical executable after their capped breakpoints disabled.
This supports the already proved cache-clear dependency; it is not proof of
every executed instruction, a safe foreign callback or permission to mutate.

## Proof limits that still block implementation

`body_register_enter` at43E2A0 had **no observed hits**. It is the selected
original nonvehicle registration path, not proved by observing another body's
shared collision interfaces. Absence here is bounded to this logpoint run.
Retirement/destruction/attachment logpoints reached their16-hit caps on early
objects. Their generic Egg observations cannot be assigned to the later target
body; actual target body/prototype release and restart rollback remain unproved.
Native x32dbg instrumentation changes code breakpoint state and timing, not
original files. The passive poll does not show a thread; thread evidence comes
from the explicitly instrumented original functions in this process only.

No private PS2 stream/prototype was registered, no Egg/AI slot was replaced,
no manager vector was edited, no injected physical object or vehicle impulse
was tested. Wire round-trip remains the previous phase's separate format PASS.

| Gate | Result |
|---|---|
| Exact native image / installed backend | PASS, runtime |
| Original shared reader/clone/body binding | PASS within sampled paths |
| Observed physics-update thread / cache clearing | PASS within this session; no admission permission |
| Load/restart/exit vector observations | PASS; not destructor ownership proof |
| Original prop registration43E2A0 | NOT_PERFORMED / no hit in bounded control |
| Private stream/resource/rollback | BLOCKED |
| Target body/shape destruction | PARTIAL; exact target destructor chain missing |
| Private vehicle contact / body-driven rendering | NOT_PERFORMED |
| HUD SpeedDial class evidence | PASS static; live packet/resource join PARTIAL |
| Physics/HUD replacement enabled | NO |

## Smallest implementation decision

**Do not activate spawn yet.** The proposed one-object design is in
`implementation-decision.md`. The next missing contract is an owned bounded
native stream and retained prototype/cache registration, paired with original
prop admission/target teardown. A render-thread mutation or a copied hay hull
does not close it. No larger static physics survey is needed.

Parallel HUD-PORT1 added the actual `gaHudAiSpeedDial` class/vtable evidence
and original owner-to-consumer path in `../hud-port1/semantic-mapping.md`.
The exact vtable fingerprint690F38 permits a bounded read-only current roster
join; a current SpeedDial packet's bank0/texture/geometry/lifetime still has
not been measured. No HUD override or new per-frame Broker/read was introduced.

## Reproduction and validation

See `runtime-recipe.md` for the single recipe actually followed and its
bounded coverage. Raw logs remain ignored in `ps2-research/data/rigid-port1`.
Compact summaries retain hashes/counts/pointers/bounds, not full trajectories.
The offline `rigid_lifecycle_review.py` produced the summaries deterministically;
9 synthetic reviewer tests plus the existing10 probe tests pass. They do not
validate a physical port. Compileall/diff-check and frozen-source verification
pass. Existing accepted DLLs are unchanged; no CMake/native rebuild was needed
for external sampling and offline review, and no new build directory exists.

Baseline DLL: `011dd9a94155d216d0c0dde28e0af97f5b72226aae5be97016f2d767ebdf7138`.
PS2-enabled DLL: `6edc2426e2602545121f16959cdbb2055fb205a907b36173cb85a447b7051deb`.
These are preserved previous accepted build hashes, not a new runtime build.
No original game/SDK files changed. The previous uncommitted port work is
preserved; no broad commit, cleanup or push was performed.
