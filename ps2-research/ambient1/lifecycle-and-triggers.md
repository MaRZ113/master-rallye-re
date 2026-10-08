# Lifecycle, trigger and rest contract

Initial route setup evaluates Q(1) and Q(0), initializes position to Q(0),
derives forward from Q(1)-Q(0), builds rows and publishes via `1aa308`.
Time becomes zero. Active is cleared if trigger enabled, otherwise retains
constructor True. Initial bank flag uncertainty is recorded separately in
[layout](object-layout.md).

Active tick order in `1a80e8` is exact:

1. Resolve Broker `Car0`, member ID `gaVehicleOutputData` at global `40e698`,
   through `1e4280 -> 1e3820`. Wrapper payload pointer is +8; position is
   payload +a8/+ac/+b0. Missing pointer returns **without any time update**, even
   when trigger is disabled. `Car0` is the literal observer, not PlayerID-based
   local-player selection; its relation to a human in multiplayer is UNKNOWN.
2. Read current en3d translation +50/+54/+58. Zero the Y contributions and
   compute `(observer.x-model.x)^2 + 0 + (observer.z-model.z)^2`.
3. If triggering, `1aa438` applies hysteresis. Inactive activates only if
   d2 < On². Active deactivates only if Off² < d2. Equality retains state.
   Thresholds are squared, not sorted or clamped.
4. If still inactive, return. The published matrix, time, rest counter and
   bank ring all remain unchanged. No visibility bit, unload or entity-removal
   call occurs in this branch. Later activation **resumes**, not restarts.
5. Increment bank ring index modulo samples; evaluate current time, derive
   new forward/up/right, copy scratch pose into the published pose.
6. Publish en3d matrix, then call `1aa3b8` to advance time/rest.

Advance adds nominal 1/30 first. The endpoint test is **duration < new time**:

- Closed: reset time to zero, discard overshoot. Rest flag/counter is not read
  in this branch. Evaluator itself wraps time == duration to Q(0).
- Open: clamp time to total duration. With Rest=False, keep active and keep
  evaluating/publishing the endpoint on later active ticks.
- Open with Rest=True: if counter < rest_ticks, increment counter. Otherwise
  reset time and counter to zero. The reset happens on the overflow invocation
  **after** the counter has reached its bound; Rest=0 resets immediately on
  first overflow. This rest period starts after any open constant-speed extra
  closing-chord hold. Pause/deactivation also pauses the rest counter.

FRANCE1 boat1's Rest=True and 300 seconds become 9000 ticks in the instance,
but its Closed=True branch never uses them. TURKEYW reaches/stays at its final
marker without waiting for a proximity trigger; it still needs the observer
Broker to exist. ITALY3 starts inactive and uses 400/1000 thresholds measured
from its current model, including its frozen endpoint position.

State is per cloned owner: +60 active, +68 time, +54 rest, +a4 cursor,
+12c ring and owned buffers. SPAINS2 boat1/boat5 share only the observer and
marker manager infrastructure; their 8/6 speeds, paths, 1/.6 banking and
activation decisions remain independent. Entity freeze/removal gates in
`21f088` are outside this private active flag and also suppress dispatch.
