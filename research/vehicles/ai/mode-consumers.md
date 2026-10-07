# Opponent identity producers by mode

This map distinguishes the native owner that creates a roster from the later
stage, resume, and materialization paths that reuse it. Executable evidence is
from exact pristine retail SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`; runtime
labels below apply only to the captures named in
[runtime-results.md](runtime-results.md).

| Mode | Roster classification / owner | ID26 status | Evidence boundary |
|---|---|---|---|
| Quick Race | Dynamic class pool: `FUN_0047B780 -> FUN_00458090` | Natural T1 membership in H.1 | H.1 `CONFIRMED_BY_RUNTIME`; H.2 preserves it |
| Rallye Cup | Dynamic at new cup/event setup: `FUN_0045BE10 -> FUN_0045ABC0` | H.2 extends the native T1 candidate source | `CONFIRMED_BY_EXE`; H.2 `READY_FOR_HUMAN_RUNTIME` |
| Invitation | Dynamic at event setup through the same `FUN_0045BE10 -> FUN_0045ABC0` path, selected by RaceType 8 dispatch | H.2 extends the shared T1 source | `CONFIRMED_BY_EXE`; persistence is a historical parallel-branch runtime oracle |
| Master Rallye | Dynamic at new competition creation: `FUN_00452590 -> FUN_00451DD0` | H.2 extends only the new T1 roster source | `CONFIRMED_BY_EXE`; H.2 `READY_FOR_HUMAN_RUNTIME` |
| Challenge | Authored/event-specific setup; not the generic dynamic pool path | Not auto-injected | Historical runtime/static event evidence; H.2 does not touch it |
| Practice | No distinct stock Practice opponent mode/AI roster owner found in the audited frontend and setup dispatch | Not applicable to a separate Practice pool | Bounded `CONFIRMED_BY_EXE` search; does not claim every informal practice variant is absent |

## Scope and lifecycle

H.1 changed only the Quick Race T1 pool in `FUN_00458090`. It did not change
Cup, Invitation, or Master Rallye. Their absence from an H.1 race is therefore
not evidence of a bad random draw.

H.2 appends physical ID26 to the T1 source in the two native mode-specific
pool owners. The append re-enters each function's existing exclusion body, so
its existing participant-ID exclusions and subsequent native selection and
DriverID policy continue to apply. The patch does not consult the player's
T1 Cup unlock flag, change CarClass, alter roster storage, or rerun selection
during stage/resume.

The patch is reached when the stock code creates a new Cup/Invitation roster
or a new Master Rallye competition. Later Cup/Invitation stage setup and
Master Rallye stage/load setup do not call the changed pool exit. An existing
competition is therefore allowed to keep its all-stock roster; this is the
required native persistence behavior, not a missed upgrade.

The code patch and deterministic candidate metadata are documented in
[mode-aware-t1-eligibility.md](mode-aware-t1-eligibility.md). Current-branch
runtime validation is pending in the exact procedure in
[mode-aware-runtime-plan.md](mode-aware-runtime-plan.md). Historical Rallye
Cup, Invitation, and Master Rallye persistence observations from the separate
general-RE branch remain `HISTORICAL_PARALLEL_BRANCH / RUNTIME ORACLE`, not
H.2 runtime evidence.
