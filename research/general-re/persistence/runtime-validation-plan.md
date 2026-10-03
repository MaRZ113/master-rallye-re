# Human validation plan — not performed

All experiments use a **disposable full retail install**, pristine EXE hash
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
Authoritative installations and corpus are read only. Keep a stopped-install
baseline copy outside the test's active folder. Retain captures/logs under the
general-re worktree's ignored research-output. The Observatory does not send
save/edit/commit commands; ordinary game actions below are performed by the human.

## First: frontend observational smoke test

Follow [docs/broker-observatory.md](../../../docs/broker-observatory.md). Launch
the one-command menu; check supported process, Broker-open state, Debug-buffer
size and previous captures. Capture a labelled frontend snapshot twice; verify
new complete Dump offset each time, valid paired files, latest and diff-last.
Close/reopen Broker, repeat after the buffer reallocates. Do not select mutation
menus. This validates the new automatic command/capture frontend, not persistence.

## U1 — scope/lifetime, observation only

**Question:** which named entries persist, disappear or change scope across
frontend→ordinary race→return to frontend? **Anchors:** entry +14, known whole
reset `00522910`, unresolved normal scene clear `004D7A60`.

Human captures `u1-front`, enters a normal race, captures `u1-race`, returns by
the normal menu and captures `u1-return`. Record game actions, debug messages and
whether the editor was preserved. Run diffs for race/vehicle/persistence presets.
If SCENE rows disappear, trace their owners; this does not prove 004D7A60 was
called. GLOBAL CarN removal would demonstrate explicit lifetime independent of
the GLOBAL label. USER rows would supply real producer anchors; none is expected
from the current three samples. Restore by stopping and discarding the disposable
install. No broker values are edited.

## U2 — one normal Options value

**Question:** does a normal option with Options bit4 persist through native
write/reload? **Anchors:** mode2 `005FE460`, `005229B0`, native writer `0054A4B0`.
**Expected path:** backend-root `DataGame/options.xml`, backup `options.xml#`.

First capture `u2-before` and find the **actual displayed path** for a harmless
audio-volume option through normal menus and the read-only Broker view. Confirm
its Options flag in persistence-report; do not guess a path from its UI label.
Record existing options/backup file hashes and copy both while the game is stopped
before starting the test. Change exactly one audio-volume setting through the
normal game UI; use its normal Apply/back action, record all clicks. Capture
`u2-after`, stop normally, record file existence/hashes, relaunch and capture
`u2-reloaded`. The option returning proves value persistence; SaveFile/revision
changes on reload are expected metadata effects. A changed file without restored
value means wrong path/filter/override or a serialization issue; an unchanged
file means that UI action did not save or the assumed bit/path was wrong. Retain
logs and do not retry with developer Save commands. Restore stopped test files
from the external baseline, or discard the whole disposable copy.

## U3 — historical initial plan (superseded for the name round trip)

The normal-name round trip is now [FULL PASS](final-closeout.md), including the
[mapped QuickRace SelectCar test](u3-save-trigger-test.md). The original plan
below is historical; no additional progress experiment is requested.

**Question:** does one normal progress change selected by PlayerState bit2
survive reload? **Anchors:** mode3; known gameplay save callers `004841B0`,
`004501D0/00450310`; `DataGame/PlayerState.xml` and `PlayerState.xml#`.

Use a fresh disposable baseline profile, choose a **normal finish/result action**
with one identifiable WinStatus/unlock change. Read and record the exact live
path and PlayerState flag before the action; do not force an unlock in Broker.
Capture before/after result acceptance, record the normal UI sequence, stop,
hash the native file and backup, relaunch and capture. If the value persists
with SaveFile PlayerState, that corroborates mode3 merge. If defaults return,
use the file/log evidence to distinguish no writer, wrong eligibility, read error
and later override. Multiple normal progress changes must be recorded rather than
pretending a race writes only one key. Restore the entire stopped disposable
profile/install baseline. No EXE patch or automated race is required.

## U4 — developer Game/Options output, gated

**Not ready for invocation through the current helper.** Write IDs 0x33..0x37
are deliberately absent. The shipped main menu does not provide a proven native
launcher route for these commands. A future explicit writer activation phase
must review its own trigger and obtain separate authorization.

For that future phase, test one **new DataGame basename** such as
`rbroker1-probe.xml`, never a whole registered Game save initially. Record
whether SaveGameAs retags live SaveFile groups before IO (`004D5400`), select a
known group, backup all affected loose originals and the registry capture, and
record output/`#` behavior. An archive-only target can fail at CopyFileA; a new
file can also have no backup. Only after this bounded result should all-group
Game saving be considered. Expected interpretations are in [save-pipeline.md](save-pipeline.md).
Stop on unexpected changed paths; restore the whole disposable baseline.

## Evidence checklist

For each executed human test: exact EXE hash, baseline identity, action sequence,
timestamps, before/after/reload capture pairs, file existence/size/SHA256, backup
identity, error/debug log, PASS/PARTIAL/FAIL with observed facts. Mark planned
tests `NOT_RUN`; do not infer native behavior from synthetic tests.
