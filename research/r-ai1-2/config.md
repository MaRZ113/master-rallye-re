# Configuration V1

Place MRallyeRandomizer.ini next to the candidate EXE/DLL.
Use the [example](MRallyeRandomizer.example.ini) or
[all-Stock control](MRallyeRandomizer.stock.ini); tools do not overwrite an
existing user config automatically.

One [OpponentRandomizer] section, ConfigVersion=1 and optional QuickRace,
Challenge, RallyeCup, Invitation, MasterRallye keys. Values are case-insensitive
Stock/Mixed/Diverse. Default/missing key/invalid value is Stock for that mode.
Missing file, unknown/missing version, malformed lines, duplicate keys,
unknown keys/sections, embedded NUL, non-ASCII or file>4096 bytes fail the
whole file to Stock. V1 samples are ASCII without BOM.

The first active AI loads one bounded config snapshot for the new roster.
Remaining AI slots use that snapshot. A change applies to the next new roster,
not Restart, stage advance or saved-career load.

MRallyeRandomizer.log contains bounded per-generation-slot diagnostics:
mode, policy, AI count, slot, selected class (or Stock '-'), config SHA256.
Its format is distinct from native Dump. IDs and actual actor identity must
be checked from Observatory/human evidence. Logging failure does not affect
selection; logging stops before the file would exceed128KiB. Remove/archive it
manually when needed. No per-frame logging, seeds, weights or capacity knobs.

The checker consumes a preserved generation config and this separate log.
A complete ordered group of AI slots must match mode/policy/count/config hash
and captured classes. Restart/stage/load can reuse that original group; a log
match is provenance, not proof of a fresh generation or actor behavior.

## Runtime closeout

Human edits in a running process took effect at a subsequent roster-generation boundary: CONFIRMED_BY_RUNTIME. Existing roster remains unchanged. Log provenance and observed config hashes are recorded in the closeout.
See [runtime evidence](runtime-closeout.md).
