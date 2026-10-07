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
| Rallye Cup | Dynamic at new cup/event setup: `FUN_0045BE10 -> FUN_0045ABC0` | ID26 is possible in the new T1 roster; later stages reuse it | ID26 inclusion and stage reuse `CONFIRMED_BY_RUNTIME` |
| Invitation | Shared setup path, but the tested normal route is T3-only and uses ordinary/base T3 IDs 14..20 | H.2 extends a shared T1 arm that this route does not reach | T1 ID26 `NOT_APPLICABLE`; ordinary T3-addon eligibility requires explicit future qualification |
| Master Rallye | Dynamic at new competition creation: `FUN_00452590 -> FUN_00451DD0` | ID26 is possible in a new T1 roster; native competition state stores it | ID26 inclusion and fresh-process native save/load restore `CONFIRMED_BY_RUNTIME` |
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
runtime evidence for this candidate is now recorded in
[runtime-results.md](runtime-results.md). The nine JSON/raw pairs identify the
same H.2 executable and all raw sidecar hashes were verified against actual
bytes.

Invitation is not an H.2 T1 inclusion failure: its observed RaceType 8 route
is T3-only, with ordinary/base pool IDs 14..20. A future non-bonus T3 addon
must qualify for that Invitation pool explicitly; bonus/special T3 addons are
not inserted based on class alone.
