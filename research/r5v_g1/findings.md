# R5V-G.1 — Vehicle unlock architecture

## Status

**STATIC COMPLETE / READY FOR HUMAN RUNTIME.** The research candidate maps the
Mercedes ID26 Vehicle Select availability check to the retail T1 CupCar1 gate.
The fresh-versus-progressed comparison has not yet been run. No class-ordering,
audio, AI-pool, registry-capacity, or generic SDK work is included.

## F.2f closeout carried forward

The owner reports the F.2f frontend check passed: Vehicle Select, Quick Race,
Race Options, and a second Race Options entry show the correct Mercedes
identity; `GALOCAL UNKNOWN` does not return; switching to a stock vehicle and
back remains correct; ID25/Trooper remains separately represented. The
F.2e active-race capture carried forward identifies physical `CarID=26`, class 0,
`CarType=Mercedes`, `WheelType=Mercedes`, and the deliberate red ID26 colour
canary. This is a frontend-identity and core-gameplay pass, not a full
stage/results/return claim. The candidate hash is recorded in
[`../r5v_f_2f/findings.md`](../r5v_f_2f/findings.md).

## Result

The stock game has separate gates:

1. Quick Race class reachability is built by `FUN_00480B60`. On the Quick Race
path, T1 is always added; T2/T3 are added from `Progress/OpenedModes/T2Cup`,
`Progress/OpenedModes/T3Cup`, and the cup/global cheat flags.
2. Per-vehicle availability is evaluated by `FUN_0045A150` from a pointer to a
native vehicle record. It reads the physical ID at `[ECX+4]`, applies the
`UnlockAll`/`UnlockCars` bypasses, then follows an ID switch to
`Progress/UnlockedCars/*` for gated entries.
3. Mode/event eligibility is a separate question. Campaign records and
Challenge definitions carry their own class/vehicle context; a class or
vehicle being globally selectable does not prove it is legal for every event.

The direct retail call to `FUN_0045A150` is at `0x004819CE` in the generic
Vehicle Select path. No additional direct call reference was found in the
audited pristine executable. That bounds the proven consumer; absence of a
direct xref does not rule out indirect calls or mode-specific validation.

## ID26 research policy

The F.2f profile uses a Vehicle Select-only unconditional test unlock. The new
G.1 profile keeps the full Mercedes physical/presentation profile but changes
the gate input for ID26 to stock vehicle ID3. ID3 is the T1 CupCar1 oracle, so
the expected policy is:

| State | Stock ID3 | Mercedes ID26 in G.1 profile |
|---|---:|---:|
| Fresh profile; `T1CupCar1=False`; no car cheats | locked | locked |
| `T1CupCar1=True`; no car cheats | selectable | selectable |
| `UnlockCars=True` or `UnlockAll=True` | selectable | selectable |

The hook changes only the temporary identity passed to the availability
function. The registry, selected `CarModel`, runtime participant, model family,
wheel family, physics, and race `CarID` remain ID26/Mercedes. Other vehicle IDs
continue through the native function with their original record. This is
**STATIC / CANDIDATE PREPARED**, not runtime-confirmed progression behavior.

The G.1 candidate also removes the earlier ID25 forced-test-unlock patch, so
the newly initialized Trooper ID25 follows the native `Bonus2` predicate.
This change is isolated to the G.1 research profile; it does not rewrite the
F.2f historical result.

## Files

- [`unlock-layers.md`](unlock-layers.md): model and boundaries.
- [`vehicle-availability.md`](vehicle-availability.md): native ID switch and
  stock vehicle matrix.
- [`class-reachability.md`](class-reachability.md): Quick Race class gate.
- [`progress-state.md`](progress-state.md): Broker and persistence metadata.
- [`unlock-producers.md`](unlock-producers.md): traced native writers.
- [`mode-consumers.md`](mode-consumers.md): mode-by-mode evidence limits.
- [`id26-integration.md`](id26-integration.md): candidate and patch semantics.
- [`runtime-handoff.md`](runtime-handoff.md): controlled human test.
- [`validation.md`](validation.md): reproducible checks and hashes.
- `stock-unlock-matrix.json`, `unlock-consumer-map.json`, and
  `id26-unlock-profile.json`: machine-readable summaries.

## Evidence limits

`Progress.xml` defaults and `SavePlayerState=True` identify Broker fields and
serializer eligibility, not the binary save encoding. No save file is edited.
Several late reward writers are mapped only to their flag and broad event
context; exact campaign thresholds are marked unknown where the current
disassembly trace is incomplete. Human runtime is still required to verify the
ID3/ID26 locked-to-selectable comparison.
