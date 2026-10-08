# PS2-AMBIENT1 final report

| Closeout field | Result |
|---|---|
| Phase | PS2-AMBIENT1 — gaEntitySpline runtime ownership and movement |
| Repository | `D:\Game\Master Rallye\master-rallye-re-general` |
| Branch | master |
| Starting HEAD | `6dbf84997cbdef023fe133ee80471d6206c9e73b` |
| Ending HEAD | The commit containing this report; exact SHA in ignored `data/ambient1/git-closeout.json` and user-facing closeout |
| Preflight state | Tracked tree/index clean; unrelated untracked ps2-research.zip recorded, absent at closeout with UNKNOWN cause |
| Canonical ELF | SLES_509.06, 3,739,852 bytes, SHA256 b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2 |
| TNG corpus | Exact TNG.PAK/TNG.000/SYSTEM.CNF size/SHA checks passed; full fingerprints in case-evidence.json |
| Course SDK reference | Read-only research/r5t-course-archaeology at 4244fa0c4d878523c9947f54816bf377cdfb2589, clean and unchanged |
| gaEntitySpline owner | Interned name 475658 -> global 48e1d0; independent per-Egg controller |
| Factory | 15b190; audited allocation/constructor callsites 15d374/15d37c |
| Constructor | 1a7b08; fresh clone 1cefc0 |
| Config / init / update | 1a7dc8 / 1a7ef8 / 1a80e8 |
| Vtable / object size | 473b10 / 0x130 bytes |
| MarkerList resolution | Exact interned name -> 1fde60/1fdba8; source-order controls |
| Runtime marker record | 80 bytes; XYZ +40/+44/+48; No and Dir do not select spline geometry |
| Spline/interpolation | Uniform Catmull–Rom, time -> fractional control index -> clamped/modulo four controls |
| Sampling table | Number Of Samples is the banking history ring; path uses controls and cumulative knot times |
| Constant-speed behavior | Ordinary chord/speed times, closing chord also added for open routes; curved speed is not uniform |
| Variable-speed behavior | Normal Const=False mode gives equal control-span times; dormant +20 acceleration mode is separate |
| Loop behavior | Evaluator equality wrap; post-publish advance strict overflow resets zero and discards overshoot |
| Trigger behavior | Car0 output vs current model XZ position, strict squared hysteresis; freeze/resume |
| Rest behavior | Open-only signed low32 seconds*30 counter; closed paths ignore it; reset one overflow invocation after bound reached |
| Banking/orientation | Displacement forward, moving-average quaternion up, explicit right=(fz,fy,-fx); first-init flag remains a runtime question |
| Final world-transform consumer | 1aa308 writes all sixteen words to *(entity+50)+20..5c; affine world consumer 2639c8 and scene submission 21ea20 traced |
| ITALY3 barge | 11 points, open constant mode, trigger 400/1000; extra endpoint hold |
| TURKEYW barge | 10 points, open constant mode, trigger disabled; observer still required |
| FRANCE1 boat1 | 6 points, closed constant mode; configured 9000 rest ticks ignored by closed branch |
| FRANCEM airship | 4 points, closed Const=False; same XYZ/publisher pipeline |
| SPAINS2 dual boats | Independent 7/5-point routes, speeds 8/6, banking 1/.6, triggers 300/600; authored translations overwritten |
| Offline evaluator | tools/spline_runtime.py; bounded six-case builder; defined observer/state assumptions |
| Numerical validation | Original-word basis probe, independent analytic constraints, deterministic float32 reconstruction; no PS2 bit-equality claim |
| Independent runtime validation | **NOT_PERFORMED** |
| Tests | Focused 32, full unittest 130, pytest 130 +158 subtests PASS; no skips with canonical fixtures enabled |
| Compileall / diff-check | PASS / PASS |
| Original files unchanged | Four canonical input fingerprints rechecked and unchanged |
| Course SDK unchanged | PASS, same HEAD and clean status |
| Files changed | 17 ambient1 docs/metadata, two new tools, one new test, README index, ambient1 query-output choice: 22 paths |
| Commit | research: reverse PS2 spline ambient movement; resolve SHA with git log -1 --format=%H -- ps2-research/ambient1/final-report.md |
| Fresh-data archive | Ignored data/ambient1/ps2-ambient1-research-bundle.zip, generated after commit with member hashes and actual commit identity |
| Push | Not performed |
| Overall status | **PS2-AMBIENT1 STATUS: COMPLETE — static/executable reverse**; preservation audit Gate 1 PARTIAL for the unrelated absent ZIP |

## Most important discoveries

The central gap is closed at the executable boundary: the actual spline
owner publishes into the same en3d carrier to which the Egg loader binds
the named model. This is not only a route cache or a likely moving-object
name. `1a82fc -> 1aa308` writes all four world-matrix rows, verified against
original effective store addresses. Initial/tick publication replaces the
authored transform, including meaningful SPAINS2 boat translations.

The curve is uniform Catmull–Rom, but its clock is not a true arc-length
parameterization. Const=True schedules ordinary chords by length/speed;
Const=False normally gives equal time per span. Open constant-mode paths
add last-to-first time even though position clamps at the last control,
creating a potentially substantial stationary period before rest handling.

Number Of Samples smooths **bank angle**, not path geometry. Forward comes
from successive positions; banking changes only up, and right retains the
explicit `(fz,fy,-fx)` expression. A conventional orthonormal replacement
would therefore differ from the recovered behavior. Triggering freezes time
and retains the world matrix, and an absent Car0 payload freezes even an
owner configured with triggering disabled.

## Recovered execution chain

```text
RaceTest Version4 Egg + model name + AI gaEntitySpline
 -> 292a48 hatch / 1fc4c0 prototype lookup / 1cefc0 fresh clone
 -> config virtual+24 / 1a7dc8 typed properties -> instance fields
 -> attach virtual+34 / 1a7ef8
 -> 1a8330 exact named MarkerList -> ordered XYZ controls + knot times
 -> 21f088 virtual+2c / 1a80e8 observer and activation gates
 -> current time +68 -> 1a9498 curve position
 -> 1a9e08 forward / 1a9fd0 up / 1aa2e0 right -> cached pose
 -> 1aa308 -> actual named model en3d+20..5c WORLD MATRIX
 -> 1aa3b8 post-publication time/rest advance

World-role corroboration: 2639c8 passes this matrix to affine helper 1ca568.
Scene submission: 21ea20 passes actual entity to interface virtual+4c.
UNKNOWN: concrete renderer interpolation -> PSM children -> GS pixels.
```

Configuration, route, movement and world-publication chains are also shown
separately in [findings.md](findings.md). Registration, virtual slots and
fresh instance lifetime are in [owner-factory.md](owner-factory.md);
field accesses and original byte-window fingerprints are in
[object-layout.md](object-layout.md) and [elf-functions.json](elf-functions.json).

## Mathematical contract

For the containing knot span, `x=i+(t-Ti)/(Tnext-Ti)`, `k=floor(x)`, `u=x-k`.
Controls are `P[k-1..k+2]`, clamped for open paths and modulo N for closed.

```text
w0=-0.5u^3+u^2-0.5u
w1= 1.5u^3-2.5u^2+1
w2=-1.5u^3+2u^2+0.5u
w3= 0.5u^3-0.5u^2
Q=((P0*w0+P1*w1)+P2*w2)+P3*w3
```

Original operation ordering, cache behavior and XYZ sum windows are documented
in [spline-algorithm.md](spline-algorithm.md). The 24 original-word basis
probes and independent rational/collinear checks constrain the reconstruction.
Timing equations, the open closing hold and the separate internal acceleration
branch are in [sampling-and-speed.md](sampling-and-speed.md).

Time advances by float32 `3d088889` (1/30) per active invocation after
publication. The owner consumes no elapsed-time argument. Actual dispatch
cadence/display FPS remains unmeasured. [transform-pipeline.md](transform-pipeline.md)
gives forward fallbacks, banking equations, exact row destinations and
row-vector affine convention. Host float32/sqrt/sin/cos are explicit
approximations to platform arithmetic; actual R5900/libm bit identity is
UNKNOWN. No proprietary route coordinates or decompilation are committed.

## Lifecycle and contrasting cases

Initialization publishes Q(0) with a Q(1)-Q(0) forward. Triggered owners start
inactive; nontriggered owners start active but still require the Car0 Broker
payload for ticks. Strict XZ hysteresis preserves state at threshold equality;
deactivation freezes pose, time, rest and bank history. Activation resumes.
Closed advance resets at strict overflow and ignores rest. Open advance
clamps to duration; optional rest counts active overflow invocations before
reset. Complete branch ordering is in [lifecycle-and-triggers.md](lifecycle-and-triggers.md).

ITALY3/TURKEYW isolate trigger-on/off in open barges. FRANCE1 shows that an
authored rest flag does not imply resting on a closed path. FRANCEM isolates
normal Const=False on an airship; its route has constant Y, so it does not
demonstrate changing flight altitude. SPAINS2 demonstrates separate route,
clock, activation and bank-history state for two boats. All six selected
routes have constant authored Y; synthetic XYZ-varying cases and original
component instructions constrain vertical evaluation without inventing
family-specific flight/water behavior.

[case-studies.md](case-studies.md) compares settings and durations.
[case-evidence.json](case-evidence.json) ties six cases and all 24 structurally
applicable CDELTA1 owners to payload/route SHA, fingerprints and deterministic
artifact hashes. The 360-invocation synthetic timelines and separate 601-time
spatial sweeps stay ignored and are never called gameplay recordings.

## Remaining uncertainties and portability

First init calls banking before assigning flag +128; the constructor does
not initialize it. Allocator zero-fill/heap-reuse behavior is unproved, so
the diagnostic requires an explicit pre-init zero assumption. No actual
garbage value, first-frame failure or allocator bug is asserted. Arbitrary
captured previous pose/cache/bank state would need fuller state restoration.
Unsafe malformed routes and the dormant unserialized acceleration mode are
documented but outside the supported diagnostic input domain.

The final matrix write and its world-role consumer are proved. Actual scene
loading, dispatch cadence/pause behavior, render interpolation, PSM child
propagation and visible motion of the selected objects need a synchronized
capture. Existing individual screenshots cannot answer those questions.
See [validation.md](validation.md) for all 19 gates, regressions, provenance,
SDK preservation and the unrelated ZIP audit.

The common owner contains no boat/barge/airship-specific path branch. Its
finite-state movement contract is suitable for later semantic reproduction,
subject to measured cadence and platform tolerances. A future Course SDK
read descriptor would preserve exact Egg/model/route identity, authored
matrix, ordered typed properties and controller semantics. A separate PC
runtime hook would need stable object ownership and a proven matrix/lifecycle
integration. These are requirements, not an implemented hook or SDK extension.

PC French scenery already contains grouped/static dinghy mesh-name records.
Matching actual placement, grouped geometry and collision must precede a
hide/replace/reuse decision; raw counts do not establish equivalent visible
objects. Per-case planning hypotheses and read-only SDK limits are in
[portability-notes.md](portability-notes.md). No PC implementation was started.

## Exactly one next research recommendation

**PS2-AMBIENT-RUNTIME1: controlled spline-owner/world-matrix capture.**
Measure first-init flag, real controller cadence, trigger crossings, open
endpoint hold and a banking turn, linked to the visible named object. The
bounded acceptance plan is in [next.md](next.md). This is a recommendation;
no further subsystem or PC port is authorized or started by this closeout.
