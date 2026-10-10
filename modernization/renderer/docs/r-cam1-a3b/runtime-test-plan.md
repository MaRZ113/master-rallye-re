# R-CAM1-A3b: one ownership verification before first flight

**No functional Freecam DLL or INI exists. Do not attempt a first-flight test.**

The remaining question is narrow: distinguish a successfully initialized current
race owner from the prior owner retained through a pending/failed same-course
request. Native renderer consumption is already mapped through EndFrame; do not
repeat the traversal/particle investigation.

## Smallest targeted observation

Using a side-effect-free debugger observation or a subsequently tested read-only
observer, record the following as one bounded France1 offline Quick Race restart
sequence:

1. Existing scene request at `0x00522330` / RVA `0x00122330` writes requested ID
   at `0x005223D0` / RVA `0x001223D0`.
2. The scene job executes and commits at `0x00522680` / RVA `0x00122680`, or
   takes error callback `0x0052D5E0` / RVA `0x0012D5E0` or `0x0052D600` /
   RVA `0x0012D600`. Record the distinction, not just job-list emptiness.
3. At the first subsequent pre-traversal `0x006532DD`, resolve existing
   `RaceLimits` text ID and record unique registration/live-list membership,
   actor retirement bit, AI pointer/type/count and participant RaceState.
   Correlate the owner with successful scene initialization, including whether
   a pointer address was reused. Record exact retail profile, thread, camera
   count and explicit offline/one-human/replay exclusions.

No on-disk EXE patch, camera mutation, native Broker getter or guessed pool ID is
needed. Do not create an I/O failure by deleting/protecting game assets. The
failure branch is already statically established; normal restart observation
should identify a success/owner epoch mechanism that fails closed on that branch.
If new observer hooks are needed, their own ABI/rollback tests precede use.

**PASS for the missing proof:** a bounded read-only predicate or observer epoch
can positively associate the current unique live owner with successful scene
initialization, revoke it immediately on request/retirement, and leave it revoked
on failed completion. Pointer, vtable, Source90, RaceState2 and zero countdown
alone are insufficient. An observed successful restart alone does not certify
all failure exclusions; its mechanism must be reconciled with the proven native
error paths.

**FAIL:** pending/failed requests retain permission, missing fields are treated
as false/safe, or epoch identity depends only on a reused pointer/name/scene ID.

Two newest available session files inspected in this stage,
`session-20261010-044035-32596.jsonl` and `session-20261010-044020-46684.jsonl`,
contain no separate camera/race-gate observation events. They do not supply the
missing scene/owner correlation. No new runtime acceptance is claimed.

After this proof, implementation proceeds with the documented single scope,
real x86 fixtures, coherent planes/VIEW, controls, focus handling and Stock
restoration. Only that functional result qualifies for France1 first flight.
