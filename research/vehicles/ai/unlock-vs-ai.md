# Player unlock policy versus AI pool eligibility

These are distinct identity axes.

The general player availability function `FUN_0045A150` is not called by the
Quick Race pool builder `FUN_00458090`. Its T1 arm directly appends physical
IDs 0–6 without consulting their player unlock flags. Several stock T1 entries
can be locked for a fresh player's Vehicle Select while remaining present in
the AI pool. This is executable evidence that player unlock state is not a
general AI-eligibility predicate.

The T3 arm has special handling for reward/event vehicles: it appends IDs
22/23/24/21 only after direct checks of their individual stock progress
indices. That is a per-entry pool policy, not a call to the general player
availability routine. ID25 is not appended by this arm.

ID26's G.1 player `unlock_policy` mirrors the native ID3 T1 Cup predicate.
That policy controls whether a human can commit/select the car. It does not
make the physical ID26 part of the AI pool. The first H candidate bypasses
only the pool's missing ID26 membership for Car1, after the normal chooser has
selected a stock T1 vehicle. It does not change player unlock state.

The later natural-pool representation should therefore state AI eligibility
independently, conceptually `ai_eligible=true` and `ai_pool=T1`, while keeping
the existing G.1 player unlock rule separate. This is a future architecture
note, not an implemented addon manifest.

**Evidence:** `CONFIRMED_BY_EXE` for pool construction, direct T3 progress
checks, and absence of the general availability call. No natural ID26 AI
runtime result is claimed yet.
