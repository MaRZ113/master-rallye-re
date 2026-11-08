# Master Rallye Randomizer & AI Extender

Configurable AI vehicle selection for Master Rallye, with an expanded Quick
Race opponent menu.

## Quick Start

1. Download `MasterRallye-Randomizer-v0.1.0-beta.1-win32.zip` from the release.
2. Extract its contents into the folder containing your original
   `MRallye.exe`.
3. Leave the game's `d3d8.dll` unchanged. Resolve any existing `dinput8.dll`
   mod conflict before copying the mod proxy.
4. Run `MRallye.exe` and play. Edit `MRallyeRandomizer.ini` to select policies.

## What it does

The mod chooses AI vehicle policies separately for Quick Race, Rallye Cup,
Master Rallye, Invitation, and Challenge. It also allows a larger selectable
AI count in Quick Race. The default configuration uses Full randomization and
allows up to five AI opponents. It does not force every race to use the
maximum.

## Requirements

Use the exact 32-bit retail executable identified by SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. The mod
checks the executable and refuses unsupported builds.

## Compatibility

The mod uses `dinput8.dll` and is designed to coexist with the game's existing
graphical `d3d8.dll`. It does not replace or include the renderer proxy.
Another modification using `dinput8.dll` may conflict. See
[`COMPATIBILITY.md`](COMPATIBILITY.md).

## Known limitations

Seven-AI Quick Races have shown instability with some T1/T2 player-car setups;
the exact cause is unknown. The included configuration defaults to five AI.
Vehicle SDK interoperability, player-car randomization, forced grids, and
opponent-count changes outside Quick Race are not included.

## Troubleshooting

Enable `Logging.Enabled = 1`, restart, and inspect `MRallyeRandomizer.log`.
Configuration errors are rejected as a whole. See
[`TROUBLESHOOTING.md`](TROUBLESHOOTING.md).

## Technical details

The runtime applies in-memory changes only after exact executable and native
preimage checks. The retail executable on disk is not modified.

## Checksums

The ZIP includes `SHA256SUMS.txt` for its payload files. The release-preparation
manifest records each archive member and the outer ZIP SHA256; publish the
outer checksum with the download.

This is an unofficial fan-made modification and is not affiliated with or
endorsed by the game's publisher or developers. The included MIT license
covers this project's code and documentation only, not the game or its assets.
