# Quick Race participant count and course-start safety

R-MOD1 v13 exposes a static, opt-in one-human range of four through seven AI
(five through eight total participants). It preserves the v11 five-total
runtime result as a regression reference. Higher counts are not gameplay
qualified and must be tested progressively.

## Evidence boundary

- R-AI2 confirmed a five-participant full lifecycle on its separate candidate.
- R-AI2.1 tested six through eight with fixed research rosters. Do not treat
  those rosters as R-MOD behavior.
- R-GRID8 structurally audited 36 RaceTest resources. Their actor templates
  include Car0..Car7 and native placement is generated from StartArea. It did
  not prove terrain/obstacle clearance for every course.
- The native `FUN_00458090` chooser supports a caller-provided count and
  replenishes its shuffled physical-ID pool after unique eligible IDs are
  consumed. See the exact-build evidence note. Repeated-identity gameplay is
  pending.

## Progressive runtime gate

| Requested AI | Total | Test profile | Current evidence |
|---:|---:|---|---|
| 1–3 | 2–4 | ordinary profile | Existing normal-count runtime evidence |
| 4 | 5 | `experimental-five-total-t1.ini` | v11 human runtime pass; v13 regression pending |
| 5 | 6 | `experimental-six-total-t1.ini` | Pending human runtime |
| 6 | 7 | `experimental-seven-total-t1.ini` | Pending human runtime |
| 7 | 8 | `experimental-eight-total-t1.ini` | Pending human runtime |

Each profile raises `MaxOpponents` by one. The Start precheck refuses an
extended request above the selected ceiling, refuses non-Quick-Race modes and
enforces the Car0..Car7 limit. The raw frontend SplitScreen boolean is logged
but does not veto Start; actual one-human topology is determined from
initialized Race/NumPlayers and participant PlayerType. No post-setup native
veto/observer is installed. It does not impose a permanent Track10, human
CarID/class, Ghost, or arbitrary unique-ID gate.

## Course qualification

Start with Track10/Italy_S4, one T1 human and Ghost OFF to retain comparability
with the earlier five-total test; these are test conditions, not universal
guards. Examine visible placement before accelerating, then the countdown,
opening seconds, contact, reset/restart, AI behavior, finish, Results and
frontend return. At each AI-count step, stop on crash, wrong NumCars or
NumPlayers, missing/duplicate participant slot, invalid CarID/Class/DriverID,
inactive AI, overlap, terrain contact or unstable handling. Do not proceed to
the next profile until the current one passes.

After the first extension is stable, repeat a representative run on a course
with a different start orientation/layout. No course beyond the human-tested
set is represented as clearance-qualified. The 36-course structural audit is
not a substitute for those runs.
