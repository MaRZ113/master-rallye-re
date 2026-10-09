# Quick Race participant-count and course-start safety

## Evidence

- R-AI2 confirmed a five-car race with one human and four unique T1 AI through
  models, physics, AI, collision, damage, HUD/progress, finish, Results, Replay
  and return. The exact test profile was Track10 / Italy_S4, player CarID0/T1,
  Ghost OFF and all-T1 AI.
- R-AI2.1 confirmed six, seven and eight active participants through the
  applicable normal-race engine lifecycle. This establishes engine capacity,
  not safe terrain/obstacle clearance for every course.
- R-GRID8 audited 36 distinct RaceTest resources and 39 scene records. Every
  resource has Car0..Car7 actor templates and four StartArea markers; native
  `0x0048EB40` generates a count-based layout.
- The R-GRID8 audit has no course statuses recorded and no `PASS_CLEAR` row.
  Its transforms are predictions only. A human report for the eight-car
  Italy_S4 start raised unsuitable/nearby geometry concerns.

## Fail-closed policy in the semantic core

Native one-to-three AI remain stock and do not use participant extension. The
only extended start profile provisionally admitted for the next R-MOD human
candidate is the exact five-car R-AI2 qualification envelope:

- Quick Race, one human, split-screen disabled;
- Track10 / Italy_S4;
- player physical ID0, class T1;
- four AI, all class T1;
- Ghost OFF.

This is a reuse of the exact five-car runtime envelope, not an eight-car or
all-course clearance claim. Even this path still requires a newly composed
R-MOD candidate and human validation.

Six-to-eight total cars are refused by the core until course/count/roster
clearance has a runtime-qualified allowlist. Counts 5..7 opponents are not
enabled merely because the UI can display them or engine structures can carry
Car5..Car7. The UI extension may be menu-tested separately; Start must be
blocked when the current track/roster tuple is not qualified. That runtime
Start guard has not yet been implemented in a game candidate.

## Qualification needed for higher counts

For every course/count tuple, capture native generated transforms, actor bounds
and collision dimensions, check pairwise spacing and static terrain/tree/barrier
intersections, observe the countdown and first 5–15 seconds, then test restart
and reset. Class/vehicle size must be represented in the tuple. Test results
must be human-visible and separate from Broker state. One passing track does
not qualify all 36. Do not attempt the old Italy_S4 eight-car profile as a
default safe release path.

The first higher-count human sweep should establish a course-specific safe
subset and stop on the first overlap, terrain contact, impulse or unstable
physics. No course is currently allowlisted for six, seven or eight total cars.
