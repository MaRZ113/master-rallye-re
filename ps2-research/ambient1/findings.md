# PS2-AMBIENT1 findings

**PS2-AMBIENT1 STATUS: COMPLETE — bounded static/executable reverse.**
**RUNTIME_VALIDATION: NOT_PERFORMED.**

The principal result is a proved controller-to-model write, not a population
count. `gaEntitySpline` is a 0x130-byte independently constructed owner with
vtable `00473b10`. Its real update entry `001a80e8` calls `001a9498` for path
position, builds forward/up/right, copies the pose, and calls `001aa308`.
That last function dereferences **entity +0x50** and writes every word of
**en3d +0x20..+0x5c**, the model's world matrix. The Egg loader binds the model
name to the same carrier. This is `CONFIRMED_BY_EXE`; binding it to the selected
canonical XML records is `CONFIRMED_BY_BOTH`.

The curve is uniform Catmull–Rom over ordered XYZ controls. Timing is a separate
table of cumulative **chord-derived times**, not a sampled curve arc-length
table. Constant-speed mode therefore does not guarantee constant speed along
the curved trajectory. Nonconstant mode gives equal time to each knot span.

Three consequential details were previously unknown:

- Open constant-speed paths include the last-to-first chord in their **total
  clock duration**, while position already clamps at the final marker.
- Triggering uses X/Z distance between the current published model position
  and the Broker's `Car0/gaVehicleOutputData` position. Inactive owners freeze
  their time and retain their visible matrix; reactivation resumes.
- `Number Of Samples` allocates a bank-angle history buffer. Banking changes
  the up row; the right row remains `(forward.z, forward.y, -forward.x)`.
  Replacing that with a conventional orthonormal frame would change behavior.

All 24 CDELTA1 authored instances in 17 courses are structurally applicable:
18 dinghies, two barges, four airships. This is neither an observed runtime
population nor evidence that every Egg is loaded, unpaused and visible.

The diagnostic reconstructs finite valid inputs using IEEE float32 operations.
An independent decoder executes the original ELF basis words; analytic cases
and lifecycle checks supplement it. Neither these checks nor the SVGs are
gameplay captures. PS2 FPU bit fidelity, real tick cadence, first-init heap
state, renderer interpolation and PC object equivalence remain bounded unknowns.

Start with [execution chain](owner-factory.md), [math](spline-algorithm.md),
[world transform](transform-pipeline.md), [cases](case-studies.md) and
[closeout](final-report.md). Canonical hashes and coordinate-free evidence
are in `case-evidence.json`; function addresses and original byte-window hashes
are in `elf-functions.json`. All decoded routes, raw exports and timelines
remain ignored under `../data/ambient1/`.

Four bounded causal chains (all solid links `CONFIRMED_BY_EXE`, selected
XML links `CONFIRMED_BY_BOTH`):

```text
A Configuration:
Version4 Egg/AI node -> 292a48 owner broker -> virtual+24 / 1a7dc8
 -> typed XML readers -> instance fields -> prep/tick/advance/bank consumers
B Route:
MarkerList Name -> interned owner+0c -> 1fde60/1fdba8 named list
 -> source-order 80-byte records -> XYZ+40 -> owned controls and time knots
C Movement:
21f088 owner dispatch -> observer/active gates -> current +68 time
 -> 1a9498 cubic -> 1a9e08/1a9fd0/1aa2e0 pose
 -> publish -> 1aa3b8 post-publish clock/rest advance
D World transform:
owner pose -> 1aa308 -> *(entity+50)+20..5c named model world matrix
 -> scene entity submission
 -> UNKNOWN: platform interpolation, PSM child propagation, GS pixels
```
