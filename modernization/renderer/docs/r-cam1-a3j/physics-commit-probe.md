# Road Teleport — physics commit probe

**Status: `PHYSICS_COMMIT_PROBE_READY`.** The integrated DLL fixes clear-writer capture starvation. It does not implement teleport, a T binding, a request queue, or vehicle/Broker writes. Native installation, suspension/quiescence, exact-retail gating, callsite contexts, getter `ret 4`, and restoration are unchanged. No native hook was added or moved.

Repository: `D:\Game\Master Rallye\master-rallye-re-general`, branch `master`, starting HEAD `676ed24b2d32543c3b9356ed359e280f2b36a309`. Earlier dirty work is preserved. The pristine EXE SHA256 is `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` (3,121,214 bytes, PE32/I386, ImageBase `0x00400000`). The EXE is unchanged.

## Accepted runtime and the exact remaining gap

The supplied `session-20261011-113911-34600.jsonl` was read directly. It reports successful installation and normal-exit restoration, one flag rise, one flagged controller call, one later clear, zero invalid snapshots, and zero controller overlap. The 32 retained writer events contain **31 gate-rejection zero stores and one mode-0 zero store**. Another 465 writer events were dropped. There is no retained writer sample with flag 1. The actual clear writer cannot be recovered from this log.

The controller/substep samples use thread 24052 in this session. The flagged controller's pre-sample QPC is 11703079433718; the subsequent zero-flag controller pre-sample is 11703079746916 (31.3198 ms later at 10 MHz). This bounds an interval, not the clear timestamp. One consumption is observed, not guaranteed. No controller or bounded substep sample was labelled paused; this does not prove those paths never execute during pause.

The live RaceLine is accepted as runtime-confirmed: 448 markers, stride `0x48`, position `+0x38`, fingerprint `0x622B94DBA2805A53`. Its scene-bound invalidation is working. The supplied F10 preview selected ordinal 1, `(-1643.270, 51.140, 162.670)`, 6.90 horizontal units from Freecam. This remains a geometric road candidate, not an obstacle/physical-clearance certificate.

## Native transaction review

Addresses below are pristine **VA**; **RVA = VA - 0x00400000**. Existing Ghidra 12.1.4 read-only exports were reused. No callable Ghidra bridge was exposed in this session; targeted instructions were checked against hash-verified PE bytes with Capstone. No database was changed.

| VA / RVA | Exact branch and consequence | Evidence |
|---|---|---|
| `0x004CCFF1` / `0x000CCFF1` | Recovery mode 1 sets `[P+0x33]=1`. **This precedes** the matrix-copy call at `0x004CD12C` (`ECX=P+0x34`, source on stack). Publication is not matrix-first. | `CONFIRMED_BY_EXE`; exact context regression |
| `0x00443827` / `0x00043827` → `0x00444AE0` | The controller consumes the level flag, calls the known transform/chassis/wheel reset path. It does not clear the flag. | Existing static research and accepted runtime |
| `0x004CCC70` / `0x000CCC70` | `ResetManager_Update_004CCAF0` gate-rejection branch; zeroes selected entry's timer/state arrays and backing flag. It does not test consumption. | `CONFIRMED_BY_EXE`; actual 1→0 use unobserved |
| `0x004CD1A1` / `0x000CD1A1` | `ResetManager_Recovery_004CCC90`, mode 0, resolved backing entry; clears flag without testing consumption. | `CONFIRMED_BY_EXE`; actual 1→0 use unobserved |
| `0x004CD1DE` / `0x000CD1DE` | Helper `0x004CD1B0` called at `0x004CCBD2` from the **positive timer** branch, after decrement. `XOR ECX,ECX` precedes the CL store. Clear occurs whether the decremented timer is zero or still positive; extra backing control writes depend on that timer. No physics acknowledgement is checked. | `CONFIRMED_BY_EXE`; actual 1→0 use unobserved |

The historical trace name `recovery_timer_expired` is retained for compatibility, but is narrower than the actual helper's behavior. The helper clears on a timer-path visit, not only at expiry. On the expiry iteration the update calls this helper **before** invoking mode-1 recovery. A later timer, mode-0, or gate-rejection visit may clear the newly set flag. Their branch execution during pause remains to be observed.

Approach A: the complete recovery routine has participant/mode inputs (`ret 8`), and fetches the route ordinal through current progress before the nearby-car adjustment. Its callers do not pass an external marker ordinal. Substituting Freecam's ordinal would require a new, independently proved contract; mutating progress or bypassing the neighborhood is not implemented.

Approach B: writing a matrix/flag at the existing controller callsite is not certified. The stock flag is level-triggered; clear ownership belongs to ResetManager policy, rather than an acknowledgement from the physics consumer. Flag-before-matrix publication also requires a proved manager/physics scheduling relationship to exclude partial reads. The sampled single thread does not establish global scheduling, pause, overwrite, or teardown guarantees. No render callback calls a pose setter.

The known native path resets current/previous chassis position, source motion and derived velocity, and selected wheel/controller state. These accepted stock facts are preserved. Arbitrary wheel/contact fields are neither inferred nor written. General suspension/contact/broadphase rebuilding and road clearance for an externally selected anchor remain unproved.

Placement uses route geometry and conditional native surface handling: adjacent-point direction (previous point at final entry), a native vertical query segment using `±2.0`, and the successful-hit branch using hit Y plus `1.0`. These constants were read from the exact image. They are **not** a universal `marker.Y+1.004` policy. No selected-marker placement service or independently certified subset/range is delivered; stock recovery at its current-progress destination remains the safe fallback.

## Priority-aware capture

The buffer remains **32 records**, split into **24 store-transition slots** and **8 abnormal/unreadable diagnostic slots**. Production uses the tested `observe_clear_store` model:

- Valid `0→0` stores increment per-writer counters; they consume no event slot.
- Different pre-value/native-value pairs receive reserved transition slots (including `1→0`, `0→1`, and noncanonical changes).
- Repeated nonzero stores and unreadable samples use the separate diagnostic partition. They cannot starve transitions.
- Transition overflow and diagnostic overflow are separate. `all_sampled_store_transitions_retained=false` explicitly reports lost transition evidence. Suppression is not overflow. Retention covers the first 24 sampled transitions for a probe attachment; a short one-Reset session is the intended window.

Retained records include VA, backing and exact flag address, pre-value, native store operand, QPC, thread, recent pause state, race context, controller and local identity generation, flagged consumer count for the latest interval, last flagged-consumer QPC/thread, and whether its callback is in progress. A current native-link reread distinguishes live matching human/AI candidates from historical-only association; ambiguity fails closed. `PlayerType=1` remains a **candidate**, not a new universal human-owner certificate.

These are **before-original-store observations**, with `store_completion_observed=false`. The unchanged bridge then replays the original instructions. A later same-owner/thread zero-flag controller sample corroborates clearing. No post-store hook or inferred success event is introduced. Events are emitted in sequence order on normal probe release; routine calls are represented by summary counters, not continuous logs.

The pure capture regression reproduces 497 zero observations (the old 32/465 case), followed by a retained clear. It also checks rises, both partition limits, unreadable samples, noncanonical values, counter saturation and reinitialization. Built-DLL tests additionally check all three unchanged clear bridges' saved-register/flags prologues, callback targets, cleanup and exact replayed stores, alongside the accepted getter ABI harness.

`tools/analyze_physics_commit.py` correlates a retained current-human clear candidate with the last flagged consumer and a later zero consumer on the same thread/backing. It reports capture loss and legacy starvation explicitly. Even a successful attribution report always emits `one_shot_guaranteed=false` and `teleport_authorized_by_this_report=false`.

## One-session human handoff

1. Back up the accepted DLL, install this probe DLL, fully restart with the **pristine** EXE and offline France1. Keep Freecam enabled for the existing race/pause certificate. In `MRRRenderer.ini`, use `[PhysicsObserver] Enabled=1` and `RoadTargetPreviewEnabled=1`; leave radius 60. No teleport setting or key exists.
2. Drive briefly, then perform **one ordinary stock Reset**. Wait for normal driving to resume. Pause normally for 2–3 seconds, then resume manually and drive briefly. This samples pause without attempting relocation or releasing it automatically.
3. Optionally activate Freecam and take one F10 preview near the road. Exit normally. Supply the single session JSONL; the frame is optional.

Expected setup: `installed=true`, `reason=exact_callsites_installed_read_only`. Expected summary: `patch_restored=true`, `clear_writer_capture.policy=transition_priority_v1`, transition overflow 0, suppressed zeros >0. Desired evidence: retained flag-1/native-0 store with current human links, matching backing/thread and consumer count, followed by the zero-flag controller. A lack of transitions or overflow is a failed attribution capture, not evidence to bypass verification. Pause unknown/absent remains unknown.

The exact next gate is **safe selected-road publication → one native consumption → owned clear, on a certified physics phase, without stock Reset overwrite**. The capture identifies the stock clear branch and local ordering; it does not by itself certify a new request protocol or physical destination. No teleport-ready or runtime-validated claim is made.
