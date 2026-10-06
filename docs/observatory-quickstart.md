# Master Rallye Observatory v0.1.0-beta

Read-only capture and comparison of the game's live Broker state.

## Quick Start

1. Extract the v0.1.0-beta ZIP to a writable folder.
2. In your own `DataGame/dev.xml`, set `Menues/Enabled=True`, preserving the rest of the file.
3. Start pristine retail Master Rallye.
4. Run `MRallye-Observatory.cmd` and select the installation if prompted.
5. Capture the active state, then use **Diff Last Two** to compare captures.

## What it does

Observatory reads the game's existing Debug text buffer and stores checked JSON/raw capture pairs. It can show and compare captured state offline. It does not edit game state or upload captures.

## Requirements

- Windows
- Python 3.11 or newer, standard library only
- Pristine PC retail `MRallye.exe`
- The game's developer menu enabled as described above

## Compatibility

This immutable v0.1.0-beta release supports only pristine retail with SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. Patched and demo builds are rejected.

## Known limitations

The original native Broker Dump can crash on the Race Results screen when a StringList has a NULL payload. Do not request a native Dump from Results. Captures can contain local paths and game state; review them before sharing.

## Troubleshooting

- **Game not found:** start retail Master Rallye and run the launcher again.
- **Developer menu unavailable:** verify `Menues/Enabled=True` in your own `DataGame/dev.xml`, then restart the game.
- **Executable rejected:** use the pristine retail build supported by this release.
- **Cannot write captures:** extract the package to a folder where your account can create files.

## Technical details

Each capture is a JSON file and raw `.dump.bin` sidecar under `observatory-data/captures/`. Observatory does not use WriteProcessMemory, inject code, attach a debugger, suspend the game, or patch the executable. It uses the original game UI to request the Broker's native Dump.

## License

Project code and documentation are MIT licensed. No game files are included.
