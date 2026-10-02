# Startup and reload order

## Successful retail startup

`00403A40` issues, in this order:

1. logical Game, reset/replacement=1, immediate pump=1;
2. logical options, reset=0, immediate pump=1;
3. logical PlayerState, reset=0, immediate pump=1.

`005FC950` registers the read job and, for its last nonzero argument, calls the
resource manager's pump virtual. `0054A340 → 0054A360` repeatedly takes a queued
read until empty. Successful read `005FCAD0` moves the job off that queue before
calling its callback. `00522BD0` queues dependencies with immediate=0; they are
then consumed by the still-running pump loop. This combination establishes
**successful Game dependency/default loading → options → PlayerState**, rather
than relying only on the textual enqueue order or “async” class name.

## Override meaning

Typed load makes a temporary manager; non-reset load merges by the same interned
path ID and copies value/flags/scope/SaveFile/revision. Later successful loads
therefore replace matching earlier paths and reassign provenance. PlayerState
can supersede both config defaults and options for overlapping keys. There is
no separate scope namespace in this match.

Game.xml's DefaultOptions/Progress/vehicle dependency Values explain where the
base entries come from. Runtime paths now assigned PlayerState need not still
report their original Progress SaveFile.

## Failure and loose-file precedence

Resource reads first attempt the loose candidate and can fall back to the archive
through `0064D530(..., read, allow_archive=1)`, an existing resource-manager result
corroborated by the current read pump. Missing read `005FCA50` moves the job and
calls virtual +04; read/parse errors log and notify failure. `00522B10(false)`
selects Default and does not enqueue that file's dependencies. No typed entries
from the missing file are merged, leaving earlier defaults available.

The pump returns on read failure; still-pending work may be serviced later.
Consequently all malformed/missing dependency interleavings are not covered by
the successful-order proof. U3 must record logs and actual post-reload provenance.
No original DataGame file or authoritative archive was changed to test this.
