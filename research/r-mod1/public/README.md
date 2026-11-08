# Master Rallye Randomizer & AI Extender

An unofficial fan-made mod for the 2001 PC game *Master Rallye*. It offers
separate AI vehicle policies for several game modes and a larger selectable
opponent count in Quick Race.

## Quick Start

1. Use the supported original retail game executable.
2. Extract this ZIP into the folder containing `MRallye.exe`.
3. Keep the existing graphical `d3d8.dll` unchanged. Check for another
   modification that already uses `dinput8.dll` before installing.
4. Run `MRallye.exe` normally and choose an opponent count in Quick Race.

The included configuration defaults to Full AI vehicle selection in all five
supported modes and a maximum of five Quick Race AI opponents. The maximum is
selectable; it does not force every race to use five AI.

## What it does

- Select Stock, T1, T2, T3, Full, Mixed, or Diverse AI vehicle policies for
  Quick Race, Rallye Cup, Master Rallye, Invitation, and Challenge.
- Keep native opponent rosters across later Cup and Master Rallye stages.
- Keep the Challenge Preview opponent synchronized with the race.
- Reload Randomizer policies for the next new opponent roster without
  restarting the game.
- Extend the Quick Race opponent menu to the configured maximum.

## Requirements

This beta supports only the exact 32-bit retail `MRallye.exe` with SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. The mod
checks the game before installing its in-memory changes. The executable on
disk is not modified.

## Compatibility

The mod uses a local `dinput8.dll` DirectInput proxy and is designed to
coexist with the game's graphical `d3d8.dll`. It does not include or replace
that renderer file. Another mod that installs its own `dinput8.dll` may
conflict; do not overwrite one without checking compatibility.

## Known limitations

The default Quick Race maximum is five AI. Seven-AI races have shown
instability in some T1/T2 player-car setups; the exact cause is unknown.
Higher values are available but less stable. The release does not provide
Vehicle SDK interoperability, player-car randomization, forced grids, or
opponent-count changes outside Quick Race.

## Configuration and help

Edit `MRallyeRandomizer.ini` beside the game executable. See
[`docs/CONFIGURATION.md`](docs/CONFIGURATION.md) for each setting and
[`docs/INSTALLATION.md`](docs/INSTALLATION.md) for removal instructions.

## License and notice

The included MIT License covers this project's code and documentation only.
It does not cover the game, its name, or proprietary game files and assets.
This fan-made modification is not affiliated with or endorsed by the game's
publisher or developers.
