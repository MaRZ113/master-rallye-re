# Opponent identity producers by mode

This is a bounded map from current vehicle-branch evidence. Only the Quick
Race chooser has been revalidated in the current branch; historical general-RE
observations are not promoted to this branch's runtime evidence.

| Mode | Classification | Evidence / boundary |
|---|---|---|
| Quick Race | Dynamic class pool through `FUN_0047B780 -> FUN_00458090`; H.1 appends physical ID26 only to T1 | Base path `CONFIRMED_BY_EXE`; H.1 candidate `READY_FOR_HUMAN_RUNTIME` |
| Practice | UNKNOWN | No separate Practice opponent producer traced in this phase |
| Rallye Cup | UNKNOWN | Current vehicle-branch producer not yet traced; no pool change made |
| Invitation | UNKNOWN | Current vehicle-branch producer not yet traced; no pool change made |
| Master Rallye | UNKNOWN | Current vehicle-branch producer not yet traced; no pool change made |
| Challenge | `AUTHORED / FIXED ROSTER` — `HISTORICAL_PARALLEL_BRANCH` only | Prior general-RE branch treated the tested Challenge opponent as authored/event-specific; not revalidated here |

No natural addon inclusion is applied to authored Challenge/event rosters or
persisted championship rosters. A Quick Race pass does not establish pool
membership in other modes. Any later mode-specific change requires identifying
its native identity producer first.
