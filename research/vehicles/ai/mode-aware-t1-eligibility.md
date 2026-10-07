# R5V-H.2 — mode-aware ID26 T1 eligibility

## Result boundary

H.2 is a bounded source-pool extension for physical Mercedes ID26 in each
stock mode whose ordinary T1 roster is generated dynamically. It is not a
forced slot, a class randomizer, a participant-count change, or a roster
rewrite. The target vector at each covered T1 generation boundary is the
explicit sparse set:

```text
[0, 1, 2, 3, 4, 5, 6, 26]
```

Physical ID7 remains T2. The native chooser's exclusion logic, candidate
selection, shuffle, DriverID selection, publication, and registry-derived
CarClass remain in the original functions. The player unlock predicate is not
added to AI eligibility. ID26 remains physical CarID26, native DriverID
selection is unchanged, its display-only Results name remains
`JEAN-PIERRE STRUGO`, and the G.2 audio profile remains 0.

## Current-retail mode owners

Static analysis used Ghidra 12.1.4 on pristine retail SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`; hook,
loop, and native body bytes were checked directly against that image.

| Mode | Creation path | Class source / native selection | Persistence boundary | ID26 H.2 seam |
|---|---|---|---|---|
| Quick Race | `FUN_0047B780 -> FUN_00458090` | Player's registry-derived class; explicit absolute-ID vector | New Quick Race generation; Restart reuses current roster (H.1 runtime) | Preserved H.1 T1 hook at `0x00458167` |
| Rallye Cup | `FUN_0045BE10 -> FUN_0045ABC0`; RaceType 6 dispatcher reaches `FUN_0045BE10` at `0x00481722` | `FUN_004B04F0` reads `RaceData/VehicleClass`; single-player call is start=1/count=3, split call start=2/count=2. Pool exclusions use current participant CarIDs. | New Cup roster setup only; later stage path `FUN_0045B170` does not call the pool generator | `FUN_0045ABC0` T1 exit at `0x0045AD14` |
| Invitation | Shared setup `FUN_0045BE10 -> FUN_0045ABC0`; RaceType 8 dispatcher reaches it at `0x004817D1` | Same class input, pool, participant exclusions, and native chooser as Cup | Shared generated roster; this H.2 capture is a T3-only runtime control | Same shared T1 exit at `0x0045AD14`; normal Invitation does not reach the T1 arm |
| Master Rallye | New-competition creator `FUN_00452590 -> FUN_00451DD0`; RaceType 5 dispatch reaches the creator | `MasterRallye/VehicleClass` is read by `FUN_00452590`; single-player uses start=1/count=3, split uses start=2/count=2. Pool excludes existing participant CarIDs. | `FUN_00452640(0)` publishes the new roster into `MasterRallye/CarN`. `FUN_00452FE0` loads saved CarID/Class/DriverID back into race state; stage path `FUN_00452370` reuses stored roster. | `FUN_00451DD0` T1 exit at `0x00451ED9` |

The Cup/Invitation chooser `FUN_0045ABC0` has its own T1 loop 0 through 6;
Master Rallye's `FUN_00451DD0` has a separate 0 through 6 loop. Neither mode
calls Quick Race's `FUN_00458090` for these initial rosters. The ID26 append
therefore sits at each mode's own T1 loop exit, before the native exclusion
and vector append body. This preserves each function's participant exclusions
and leaves its class, shuffle, uniqueness, DriverID, and storage policy intact.

### Roster lifetime

The two hooks are reachable only while their native source loops finish
constructing a new dynamic roster. They do not target Cup stage progression,
Invitation progression, Master Rallye save/load, Master Rallye resume, or
Master Rallye next-stage setup. No native storage layout or save key is
changed. Installing H.2 must not mutate a roster already created by stock;
an old all-stock saved competition may correctly remain all-stock.

This candidate is now runtime-confirmed for Cup stage reuse and Master Rallye
native save/fresh-process resume. The exact capture hashes and roster values
are recorded in [runtime-results.md](runtime-results.md). The older separate
general-RE branch observations remain historical context; H.2 runtime evidence
is independently recorded for the current candidate.

### Other modes

* Challenge uses authored/event-specific setup and is not auto-injected.
* The audited stock frontend/setup dispatch contains no separate Practice
  opponent roster owner. Practice is therefore not applicable to this
  separate-mode pool extension; this bounded finding does not classify every
  informal practice variant.
* The same Cup/Invitation helper is shared, but H.2 extends only its T1 arm.
  The tested normal Invitation path is T3-only and uses ordinary/base T3 IDs
  14..20, so T1 ID26 in Invitation is `NOT_APPLICABLE`, not a failed draw.
  Future non-bonus T3 addons require explicit qualification for this pool;
  bonus/special T3 addons are not included automatically.

## Exact candidate intervention

The candidate builder is
[build_vehicle_mode_ai_candidate.py](../../../tools/build_vehicle_mode_ai_candidate.py).
It reconstructs the frozen H.1 candidate from exact pristine retail, verifies
the exact H.1 executable and normalized manifest, then adds only these four
mode-pool operations:

| Operation | VA / file offset | Retail bytes | Candidate bytes / purpose |
|---|---|---|---|
| Cup + Invitation T1 exit hook | `0x0045AD14` / `0x5AD14` | `E9 4D 01 00 00` | jump to `0x0068E7A0` |
| Cup + Invitation append stub | `0x0068E7A0` / `0x28E7A0` | 25 zero bytes | compare sentinel 27; pass ID26 once through native exclusion/append body; restore ESI=7; exit at `0x0045AE66` |
| Master Rallye new-roster T1 exit hook | `0x00451ED9` / `0x51ED9` | `E9 4D 01 00 00` | jump to `0x0068E7C0` |
| Master Rallye append stub | `0x0068E7C0` / `0x28E7C0` | 25 zero bytes | compare sentinel 27; pass ID26 once through native exclusion/append body; restore ESI=7; exit at `0x0045202B` |

The exact hook replacements and stub bytes are pinned in the generated patch
manifest. The hook replacements are `E9 87 3A 23 00` for Cup/Invitation and
`E9 E2 C8 23 00` for Master Rallye. The 25-byte stubs are respectively:

```text
Cup/Invitation:
83 FE 1B 74 0A BE 1A 00 00 00 E9 40 C5 DC FF
BE 07 00 00 00 E9 AD C6 DC FF

Master Rallye:
83 FE 1B 74 0A BE 1A 00 00 00 E9 E5 36 DC FF
BE 07 00 00 00 E9 52 38 DC FF
```

At both exits the original loop has advanced through IDs 0..6. The stub
temporarily supplies ESI=26 and branches back into the stock body, which
applies the existing exclusions and advances to the sentinel 27. The stub's
second visit restores ESI=7 before taking the original class-arm common exit.
The two 25-byte caves do not overlap each other or the H.1 caves. `.text`
VirtualSize ends at `0x0068E7D9`, before `.rdata` RVA `0x28F000` and within
the original `.text` raw data. No allocation, array, save/load, stage,
participant count, Results, HUD, or network loop is changed.

All patch operations pin the original bytes; operation application checks
non-overlap and exact originals, and the builder inverse-checks that reverting
its declared ranges reproduces the exact retail input. The candidate verifier
rebuilds from retail and compares both executable and manifest bytes. No
unknown-build mode exists.

The reproducible research artifacts are:

| Artifact | Value |
|---|---|
| Exact retail input | `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` |
| Frozen H.1 parent | `e59895776dd53acb3ac4a25e1973c8de341da815b90407ec372b696be06d363a` |
| Candidate profile | `mode-aware-natural-t1-id26` |
| Candidate SHA256 | `de5e81c0b126619574834f25ac941cd491139235fd2f89086d8e125f063dcac9` |
| Size | 3,121,214 bytes |
| Candidate patch manifest SHA256 | `9cb7adbd71a6207218cfba10e94b48d13363f698e6398b03994725f1bf6882eb` |
| Staged runtime package | 145 files; generated PlayerState excluded |
| Candidate package | `.research-output/vehicles/ai/mode-aware-id26/runtime-package/` (ignored output) |

## Evidence status

* H.1 Quick Race ID26 membership and the display-only Strugo Results name:
  `CONFIRMED_BY_RUNTIME` for the supplied natural T1 Quick Race captures.
* H.2 Rallye Cup ID26 T1 inclusion and Cup-stage roster reuse:
  `CONFIRMED_BY_RUNTIME`.
* H.2 Master Rallye ID26 T1 inclusion, native roster storage, and fresh-process
  native save/load restoration: `CONFIRMED_BY_RUNTIME`.
* Invitation's normal tested route is T3-only; T1 ID26 is
  `NOT_APPLICABLE`. The H.2 patch's shared T1 arm does not alter its T3 pool.
* Candidate and staged package remain deterministically verified; full raw
  capture-sidecar hashes are recorded in `runtime-results.md`.
* Class probability and guaranteed presence in any one race: not claimed.
