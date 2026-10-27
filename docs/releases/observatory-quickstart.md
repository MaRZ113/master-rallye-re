# Master Rallye Observatory

Read-only runtime inspection for Master Rallye's internal Broker state.

## Quick Start

1. Extract the release ZIP to a writable folder.
2. In your own `DataGame/dev.xml`, set the existing `Menues/Enabled` Boolean to `True`. Preserve the rest of the file; Observatory does not provide or edit game files.
3. Start Master Rallye.
4. Run `MRallye-Observatory.cmd` from the extracted folder.
5. Capture a snapshot when the game state you want to inspect is active.

### Modified executables

Known on-disk builds are identified exactly. Any other retail-family build is located from its code: Observatory finds the Debug sink, Broker Editor Dump route, Dump walker and the Broker Editor opener by byte signatures and the references between them, so moved code, grown sections, localized builds and renamed executables connect. Each action is enabled only when the code it uses was found, and it is re-checked in the running process before use.

Run `MRallye-Observatory.cmd resolve "<game-folder>\MRallye.exe"` to see what was located, which addresses moved and why anything is missing.

If the Dump walker is not a recognized stock or hardened variant, Observatory asks before sending native Dump (`--allow-unknown-walker` skips the question for scripted use). For R5V-J.1, Status distinguishes the pristine stock EXE on disk from its approved NULL-safe walker installed in memory.

## What it does

Observatory reads the game's existing Debug text buffer and stores each checked capture as a JSON file with its raw Dump sidecar. It can show and compare captures offline. It does not edit game state or upload captures.

## Requirements

- Windows
- Python 3.11 or newer, using the standard library
- A supported Master Rallye PC executable
- The game's developer menu enabled as described above

## Compatibility

Exact known builds are verified by SHA256. Modified retail-family executables are supported when their Broker/Debug code can be located; each optional action is gated by the code it needs. Demo builds are not supported.

## Known limitations

- Observatory does not include a game executable, assets, saves, or captures.
- The stock native Dump formatter can crash on the Race Results screen when a StringList has a NULL payload. Status warns when the active process's Results-screen Dump safety is unverified or unsafe; do not request a native Dump from Results in that case.
- Captures may contain game state, local paths, and values printed by the game. Review them before sharing.
- Offline parsing and comparison do not require a running game; live process discovery is Windows-only.

## Troubleshooting

- **Game not found:** start Master Rallye and run the launcher again. If several copies are open, close extras or use `--pid`.
- **Developer menu unavailable:** verify `Menues/Enabled=True` in your own `DataGame/dev.xml`, then restart the game.
- **Compatibility check failed:** Observatory did not connect. Run `resolve` on the executable; it lists every item it could not locate and why.
- **Unknown Dump walker:** answer `y` only on a disposable install during an active race, or use passive `recover`.
- **Capture timed out:** wait for the game to finish processing, then use the passive recovery option only if a complete Dump may already exist. Observatory will not resend the command automatically.
- **Cannot write output:** extract Observatory to a folder where your account can create files.

## Technical details

The launcher runs the included `mr_observe.py`. By default it discovers a running `MRallye*.exe` (or the configured executable name); advanced users can select an executable explicitly with `MRallye-Observatory.cmd --exe "<game-folder>\MRallye.exe"`. Runtime data and the exact-hash compatibility cache remain inside the extracted Observatory folder.

The process access is limited to querying and reading. Observatory does not call WriteProcessMemory, inject code, attach a debugger, suspend the game, or patch executable bytes. The reviewed native UI commands open the Broker Editor and request the game's original Debug→Dump command.

## Checksums

Release archive checksums are listed in `RELEASE-NOTES.md` and the release manifest.
