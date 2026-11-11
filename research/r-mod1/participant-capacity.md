# Quick Race participant count and native chooser capacity

## Evidence levels

- R-MOD1 v11: one human plus four AI / five active participants —
  `CONFIRMED_BY_RUNTIME` by owner report. This is the stable regression
  reference. Results/Replay/full lifecycle are not newly evidenced here.
- R-AI2: five-participant full lifecycle — `CONFIRMED_BY_RUNTIME` for its
  separate candidate.
- R-AI2.1: six through eight participants — `CONFIRMED_BY_RUNTIME` for
  separate research candidates using fixed research rosters. Those results
  prove engine participant capacity, not this configurable R-MOD candidate.
- R-MOD1-E v13: 4..7 AI static gate, native count handoff and native physical
  chooser refill — `STATICALLY_VERIFIED`; all counts above four remain
  `PENDING_HUMAN_RUNTIME`.

## Native setup and count handoff

Retail `FUN_0047B780` reads the selected count at `0x0047B88A`, publishes
count plus one through the native `Race/NumCars` setter, reads the selected
count again at `0x0047B8DD`, and invokes the physical chooser. The one-human
path passes `first=1`, the actual selected count, the human's class and
physical CarID. R-MOD1 v13 leaves both getters and the chooser call untouched;
there is no R-AI2 hardcoded count shim and no fixed roster.

See [`native-chooser-count-evidence.md`](native-chooser-count-evidence.md) for
exact function hashes, caller sites, pool behavior and per-slot writes.

## v13 candidate envelope

| Selected AI | Expected total | Candidate gate | Evidence |
|---:|---:|---|---|
| 1–3 | 2–4 | Native behavior unchanged | Prior R-MOD normal-count human passes |
| 4 | 5 | Opt-in; MaxOpponents ≥ 4 | v11 runtime-confirmed; v13 regression pending |
| 5 | 6 | Opt-in; MaxOpponents ≥ 5 | Static ready; human runtime pending |
| 6 | 7 | Opt-in; MaxOpponents ≥ 6 | Static ready; human runtime pending |
| 7 | 8 | Opt-in; MaxOpponents = 7; Car0..Car7 bound | Static ready; human runtime pending |

For all counts above three, require Quick Race mode, Opponents enabled,
`Experimental.ExtendedAI=1`, a selected count no greater than `MaxOpponents`,
with the raw frontend SplitScreen flag treated as diagnostic only. The actual
one-human roster is checked from Race/NumPlayers and participant PlayerType
after setup; no post-setup veto is installed. The total-participant ceiling is
eight. This is an experimental candidate gate, not a claim that
every grid is safe.

The package uses progressive profiles whose MaxOpponents ceilings rise from
4 to 7. The owner should test each next count only after its prior count passes.
The default configuration remains features off and three AI maximum.

## Randomizer separation and physical repeats

The UI count and vehicle class policy remain independent. With Randomizer
disabled, native Stock-class physical selection stays active for an extended
race. With Randomizer enabled, Full/T1/T2/T3/Mixed/Diverse class policy runs
once per AI slot and leaves CarID and DriverID to native code.

For `Duplicates=WhenNeeded`, native `FUN_00458090` drains a shuffled physical
ID pool, refills it from the eligible class pool after exhaustion, and creates
separate per-slot CarID/Class/DriverID state. This is static evidence only; a
seven-AI repeated-ID race remains a separate mandatory runtime qualification.
The initial test profiles use `WhenNeeded`.

## Grid scope

The R-GRID8 corpus audit found `Car0..Car7` actor templates in all 36 distinct
RaceTest resources, and the native grid generator derives placement from
StartArea. That establishes structural readiness, not terrain or obstacle
clearance. Track10/Italy_S4 is the prior controlled test environment; it is
not a universal safe-start claim. Test it first because the five-total R-MOD
path is already qualified there, then stop at any overlap, instability or bad
spawn. Qualify a second distinct layout after the first extended race passes.

No all-course eight-participant clearance matrix is claimed. Human runtime
must inspect starts/countdown, first seconds, reset/restart, finish, Results
and frontend return at each count.
