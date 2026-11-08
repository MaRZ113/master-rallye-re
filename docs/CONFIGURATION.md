# Configuration

Edit `MRallyeRandomizer.ini` beside `MRallye.exe`. The included file is a
commented ConfigVersion 2 example. The parser accepts ASCII only, up to 4096
bytes, and rejects unknown keys, duplicate keys/sections, malformed values,
and inline comments. An invalid file is ignored as a whole.

## Randomizer policies

Each key selects the policy for that game mode. `0` retains native stock
selection. `1` restricts eligible opponents to T1, `2` to T2, and `3` to the
mode-eligible T3 pool. `4` (Full) selects from the union of verified eligible
classes. `5` (Mixed) selects a class first and leaves car selection to the
native chooser. `6` (Diverse) cycles through a shuffled class order. Full,
Mixed, and Diverse are distinct policies.

`QuickRace`, `RallyeCup`, `MasterRallye`, `Invitation`, and `Challenge` apply
only to their named mode. A policy change affects a newly generated roster;
it does not rewrite an active race, an existing Cup, or a saved Master Rallye
competition. Challenge Preview and its resulting race use the same prepared
opponent.

## Other settings

- `Duplicates=0` avoids repeating physical vehicle IDs. `Duplicates=1`
  prefers unique IDs and allows repeats when the eligible pool is exhausted;
  repeated opponents remain separate participants.
- `MaxOpponents` is the maximum selectable Quick Race AI count, not a forced
  count. The included default is 5. Five AI means six total vehicles with the
  player. Changing the menu maximum requires a game restart.
- `Addons.Include=0` uses stock vehicles only. `1` asks a verified in-process
  addon provider for registered vehicles. This standalone release does not
  include complete Vehicle SDK integration; leave this at 0.
- `Logging.Enabled=1` enables troubleshooting logs beside the game files.
  Logging changes require a restart.

Seven AI has known instability with some T1/T2 player-car setups. The cause has
not been established. Higher limits are available, but are less qualified.

ConfigVersion 1 remains supported by the runtime for existing users. Version
1 has a different numeric policy ordering; do not change an older file's
version without updating its values. Version 2 does not accept hidden
experimental enable switches.
