# R-CAM1-A3j.4a — native Reset apply-flag lifecycle

Current continuation: [physics-commit-probe.md](physics-commit-probe.md). The accepted A3j.4a.1 run proves one stock consumption, but writer attribution was lost to 32/465 capture starvation. Production now suppresses routine zero stores and reserves transition slots. The old buffer description below is historical. The compatibility writer label `recovery_timer_expired` actually denotes the timer-path helper, which may clear while the decremented timer is still positive. Strict hook verification/restoration remain intact.

**Status:** clear writers are statically mapped and now have bounded, exact-build read-only observers. Branch attribution and pause behavior remain pending the integrated runtime capture. The one-shot teleport protocol remains `ONE_SHOT_PROTOCOL_UNPROVEN`.

## Static path

The prior A3j.3a/A3j.3b evidence remains unchanged. The exact-retail recovery writer sets `Controller/CarN` backing byte `P+0x33` in mode 1 at VA `0x004CCFF1` / RVA `0x000CCFF1`. The controller consumer is called at VA `0x00443827` / RVA `0x00043827` and reaches `PerCarControllerUpdate_00444AE0` (VA `0x00444AE0`). That consumer reads and applies the transform at `P+0x34`; it does not clear `P+0x33`.

The three exact-retail clear stores are:

| Store VA / RVA | Function and branch | Complete patch context | Static role |
|---|---|---|---|
| `0x004CCC70` / `0x000CCC70` | `ResetManager_Update_004CCAF0`, gate-rejection branch reached from `0x004CCC35` | `8B 40 08 C6 40 33 00` at `0x004CCC6D` | Clears the selected entry's backing byte when the manager gates reject that participant. |
| `0x004CD1A1` / `0x000CD1A1` | `ResetManager_Recovery_004CCC90`, mode 0 | `8B 48 08 C6 41 33 00` at `0x004CD19E` | Explicit no-recovery path clears the selected entry's backing byte. |
| `0x004CD1DE` / `0x000CD1DE` | Function at `0x004CD1B0`, positive timer branch | `8B 40 08 88 48 33` at `0x004CD1DB` | Clears the backing byte while the recovery timer is advanced; the helper also updates other reset-manager state. |

The `0x004CD1DE` store writes the low byte of the original `CL`; the observer records that value rather than assuming it. The other two store immediate zero. All three contexts, instruction boundaries and addresses were read from the pristine image's `.text`; they are pinned by native and Python tests. The existing physics consumer/substep contexts remain exact and strict, including the full 25-byte sequence at `0x0043F8DC`.

## Runtime observation

The integrated default-off observer wraps the three established physics callsites, the optional native RaceLine getter, and these three inline clear sequences. Each clear bridge preserves flags and general registers, records the entry/backing identity, flag sample and actual byte to be written before replaying the original store, current thread, QPC, and a recent read-only pause sample, then executes the original instructions unchanged. The sample is diagnostic and does not synchronize competing game threads. Records are bounded to 32; dropped records are counted. `owner_known` is only true when the backing matches a controller identity already observed by the consumer hook.

The summary reports `controller_calls_while_paused`, `substep_phase_records_while_paused`, `clear_writes_while_paused`, and dropped clear events. `substep_phase_records_while_paused` counts instrumented before/after boundary callbacks in the bounded post-rise window, not unique physical integration steps. Pause state comes from the existing typed pause read sampled at the camera scheduler; it is accepted for at most 500 ms. Older/missing samples are `unknown`, not evidence that the game was running. No pause value is changed.

A runtime clear event with `apply_flag_before=1` and a matching `player_type` identifies which observed writer branch actually ended the live flag for that participant. `apply_flag_before=0` records a real clear that did not end a set interval. QPC and thread IDs can correlate that write with controller consumer and substep events, but one capture still proves only the observed session's ordering.

## One-shot decision

**`ONE_SHOT_PROTOCOL_UNPROVEN`.** The observed stock reset is a level-triggered manager transaction: the reset manager may publish a matrix, controller updates may consume it over multiple calls, and a later manager branch clears it. Seeing one stock set/clear interval does not prove where a future request could be published without a manager overwrite, how cancellation behaves across race-generation changes, or whether a pending request can safely wait through pause. No write-enabled request queue or direct flag/matrix write is present.

The next runtime capture should determine which clear writer sees `P+0x33=1`, whether controller callbacks continue while paused, and whether the bounded substep phase is reached while the pause sample is fresh. Even a clean result narrows the stock lifecycle; it does not authorize a teleport commit or arbitrary destination.
