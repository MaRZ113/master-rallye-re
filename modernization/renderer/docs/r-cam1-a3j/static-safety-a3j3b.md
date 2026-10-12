# R-CAM1-A3j.3b — Runtime-backed static safety assessment

**Status:** `STATIC_SAFETY_MAP_EXTENDED / TELEPORT_NOT_READY`
**Scope:** interpret the successful A3j.3a stock-recovery capture, trace the six sampled chassis DWORDs and flag-clear paths in the exact retail image, and update the safety decision. This adds research only. No game state was written, no teleport was attempted, and prior A3j documents were left unchanged.

## Exact build and capture

The local primary executable `D:\Game\Master Rallye\MRallye.exe` hashes to `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` (3,121,214 bytes; PE32/I386; timestamp `0x3C02695D`; ImageBase `0x00400000`). The runtime session names the same pristine image and hash. The proxy hash recorded by the session is `67b82fe57e22a74c0d687b858f359f1e9a9d4b0788b382907011848eda7fa050`.

The external capture is `session-20261011-070934-30052.jsonl` (4,190,340 bytes; SHA-256 `ecfc80436cd36bf40ad3d98783f53aa4aaf82e23d13e69986c5d0376d5b8b2f9`). Parsing found 1,327 valid JSONL records and no malformed lines. The read-only exact-build probe installed with `exact_callsites_installed_read_only`; it emitted 29 physics events and 24 substep-boundary records, with no dropped events, invalid snapshots/managers, identity changes, or overlapping controller calls. Release reported `patch_restored=true` and `module_pinned=true`.

This one capture proves the supported one-human run's `PlayerType=1` candidate and stable pointer chain for this session. It does not prove general player ownership for other modes or builds.

## Six-DWORD map

The prior A3j.3 analysis called body `+0x11C..+0x130` opaque and left all velocity semantics unproven. Exact-build static dataflow now narrows that statement. The old documents remain read-only; this is the continuation's annotation.

| Body offset | Static role | Evidence |
|---|---|---|
| `+0x11C`, `+0x120`, `+0x124` | X/Y/Z of the body's translational velocity vector. The per-car controller projects it onto the body's forward basis and stores a longitudinal-speed scalar; other consumers compute magnitude/direction, and the physics update uses its prior-step copy. | `CONFIRMED_BY_EXE`: `0x00444AE0` / RVA `0x00044AE0`, `0x004446A0` / RVA `0x000446A0`, `0x00443B60` / RVA `0x00043B60`, `0x0043F650` / RVA `0x0003F650`. Runtime evolution below independently agrees. |
| `+0x128`, `+0x12C`, `+0x130` | Components of a second body-oriented vector. `0x004FF4E0` transforms source vector `body+0x110..+0x118` through the current body orientation into this triplet; the substep start copies it to `+0x180..+0x188`. A rotational/angular-velocity interpretation is plausible, but the exact physical label is not uniquely established by the inspected consumers. | Transform and history relationship: `CONFIRMED_BY_EXE`. “Angular velocity”: `HYPOTHESIS`, not a write contract. |

The reset route explains why the observer's six values become zero. `SetPhysicsBodyPose_0043A020` (VA `0x0043A020`, RVA `0x0003A020`) writes current and previous position, rebuilds orientation, clears the two source vectors at `+0x104..+0x10C` and `+0x110..+0x118`, then calls `0x004FF4E0` at VA `0x0043A22A` / RVA `0x0003A22A`. The latter derives the first triplet by dividing the first source vector by the scalar at body `+0x20`, and derives the second triplet by transforming the second source vector with the body orientation. `+0x20` is left unnamed here; this evidence does not require assigning it a semantic label.

The zero values used by the pose setter (`DAT_006F9580`, `DAT_006F9584`, `DAT_006F9588`) resolve into the virtual zero-fill tail of the exact PE `.data` section: RVA `0x2F9580..0x2F958B` is inside its virtual range but beyond its raw-data extent. The loader supplies zeros there. Thus the native pose transaction clears both source vectors and recomputes both observed output triplets as zero. This is an exact explanation for the capture, not a guessed offset write by the proxy.

The secondary triplet must remain conservatively named. `0x00435630` reads both body vectors in a two-body record path, and `0x0043F650` saves both each substep, but neither use by itself proves that the second vector is angular velocity. Also, several unrelated wheel/controller types reuse offsets such as `+0x120` and `+0x130`; those references are not evidence about the chassis.

## Runtime correlation

At the first `controller_transform_consumer` event, the native call saw `P+0x33=1`. The body position changed from approximately `(-1632.3969, 51.2841, 154.0741)` to `(-1629.4900, 51.4942, 153.2100)`, matching the translation in `P+0x34..+0x70`; previous position `body+0x144..+0x14C` matched the new current position. The six sampled DWORDs changed from `[0.061169, -0.002864, -0.053029, 0.002342, -0.002156, -0.001505]` to six zeros across that native-consumer call.

The first two subsequent physics substeps begin with the first vector at zero. Their tail samples then show its Y component evolving to about `-0.163510` and `-0.327040`, while the second triplet remains zero. This is consistent with a translational velocity reset followed by ordinary physics evolution; it does not prove an angular policy under a turning or collision case.

All sampled controller and substep records in this session use thread ID `18628`. That confirms the observed local order for this one run. It is not a global scheduling guarantee. QPC frequency is 10,000,000; the set-edge and clear-edge consumer *before* samples are 319,647 ticks (31.9647 ms) apart. The probe observes the clear before a later controller call; it does not hook the writer, so that interval is not an exact write timestamp or proof of which ResetManager branch cleared the byte.

## Apply-flag writer and clear paths

The backing byte is consumed at `0x00444AE0`; that consumer does not clear it. Exact-build static references show:

- Recovery mode 1 sets `P+0x33` at VA `0x004CCFF1` / RVA `0x000CCFF1` inside `ResetManager_Recovery_004CCC90` (`0x004CCC90` / `0x000CCC90`).
- The active timer path in `ResetManager_Update_004CCAF0` calls `0x004CD1B0` at `0x004CCBD2`; that helper clears the byte at `0x004CD1DE` / RVA `0x000CD1DE`.
- The update function also has a gate-rejection clear at `0x004CCC70` / RVA `0x000CCC70`.
- Recovery mode 0 clears the byte at `0x004CD1A1` / RVA `0x000CD1A1`; the update function has a mode-0 call path as well as its mode-1 call path.

The runtime proves a clear was visible at the controller consumer and that controller bytes `+0x13/+0x18` changed from 1 to 0 during that call. It does not identify which static clear branch executed. The most useful future diagnostic, if branch attribution becomes necessary, is a bounded read-only record at these verified writer sites; repeating an otherwise identical stock Reset is unnecessary for the current safety conclusion.

## Wheels, collision state, scheduler, and destination

The handle links four wheel records at stride `0x188`. The known reset helper `0x00443740` clears each wheel's `+0x120` dword, calls `0x004437B0(0)` to clear selected chassis/wheel/controller bytes, and calls `0x0043C310` for controller state. It does not directly write wheel pose or a complete suspension state. The runtime observer sampled only wheel `+0x04` and `+0x120`; all were zero, which does not establish wheel rotation/pose, spring compression, tire contact, contact manifolds, solver warm-start state, or broadphase coherence.

Static local order remains: physics wrapper `0x0043F2E0` calls manager update `0x0043F310`, then the two-iteration substep wrapper `0x0043F890`; each iteration starts at `0x0043F650`. Per-car update `0x00443820` reaches the controller consumer before its wheel routines. The capture confirms this order for the sampled thread. ResetManager-to-physics job ordering beyond this route, pause behavior, and a safe queued one-shot write boundary remain unproven.

Stock recovery chooses a RaceLine sample and considers other participant positions through `0x004CD200`; it is not an arbitrary camera-position ground query. In the inspected recovery path the collision-service boolean check returns false, so that call does not establish physical ground height or normal there. No verified chassis-footprint/obstacle/foliage-clearance query or safe Undo transaction has been found in this route.

## Safety decision

| Invariant | Result for stock recovery | Result for arbitrary relocation |
|---|---|---|
| Controller-to-chassis pose application and previous position | `CONFIRMED_BY_RUNTIME` for this exact build/session | Does not provide a safe commit API |
| Translational velocity initial reset | `CONFIRMED_BY_EXE` and `CONFIRMED_BY_RUNTIME` for the observed normal recovery | Destination-independent write policy still not authorized or tested |
| Secondary vector | Source/transform/recompute chain mapped; exact physical type remains a hypothesis | Insufficient to prescribe a complete angular-motion policy |
| Wheel/suspension/contact/broadphase coherence | Selected reset fields and a conditional collision adjustment are known | `UNPROVEN` |
| Safe phase, pause, supported player ownership outside this capture | Local sampled order only | `UNPROVEN` |
| Ground/clearance, race-state coherence, Undo | Not required to prove this stock RaceLine recovery succeeded once | `UNPROVEN` |

**Decision:** the observer capture plus static map proves a useful stock-recovery transaction and its linear-velocity reset. It does not prove an arbitrary relocation transaction. No teleport candidate should be built yet. Do not inject a Freecam XYZ destination or write guessed fields. No second identical stock-Reset capture is needed. Remaining work is static proof of secondary-vector meaning, complete wheel/contact/broadphase invalidation, and a validated ground/clearance and rollback path; only unresolved scheduler branch attribution would justify a new bounded writer-site diagnostic.

## Evidence sources

- Exact retail EXE: `D:\Game\Master Rallye\MRallye.exe`; hash above. PE section layout was read from this file.
- Runtime capture: `D:\Game\Master Rallye Pristine\MRRRenderer\logs\session-20261011-070934-30052.jsonl`; hash above. Raw log remains outside the repository.
- Ghidra: 12.1.4 bridge queries against the existing A3j3 project and the exact retail program. Queries were read-only; no Ghidra database was changed.
- Prior A3j.3 documents were not edited. Their “all six velocity fields unproven” wording should now be read as narrowed: the first triplet is translational velocity, the second remains an unnamed transformed vector, and arbitrary-relocation policy remains unproven.
