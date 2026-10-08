# Master Rallye Observatory v0.2.2-beta

## Quick Start

1. Extract the ZIP to a writable folder.
2. In your own `DataGame/dev.xml`, set the existing `Menues/Enabled` Boolean to `True`.
3. Start Master Rallye.
4. Run `MRallye-Observatory.cmd` from the extracted folder.
5. Capture the active game state.

## What's new

- Compatible retail-derived executables are checked automatically against the Broker family structure; a new executable SHA256 does not need to be added when the audited layout is unchanged.
- The offline compatibility auditor recognizes the exact NULL-safe StringList and XmlData trampoline variant. A live process is checked separately: Observatory verifies the on-disk executable, mapped PE identity, unchanged Broker/Dump anchors, the full in-memory walker, and both exact trampolines before allowing native Dump.
- The pristine retail executable remains stock on disk when R5V-J.1 installs its hardened walker in memory. Status and capture provenance distinguish the disk variant from the effective process-memory variant; Results-screen Dump is marked safe only after the active process passes the complete live check.
- Unknown executable identities, changed walker bytes, altered trampoline destinations/instructions, unreadable targets, and unrelated Broker anchor mismatches fail closed. Passive Broker reading retains its independent verification gate.

## Compatibility

Windows and Python 3.11 or newer are required. Exact known builds are recognized directly. Other retail-derived builds must pass the included PE32 and Broker-structure audit. Hardened Results Dump support requires the known native walker with both audited pointer guards, unchanged surrounding walker bytes, and valid control-flow targets. Incompatible builds are rejected.

## Known limitations

- Flow Builder is not verified for locally audited compatible builds.
- Stock native Broker Dump may crash on the Race Results screen when a typed StringList has a NULL payload. Do not request a native Dump from Results unless Status confirms the active process's hardened in-memory variant and Results safety.
- Structural compatibility does not establish every optional feature or general compatibility with arbitrary modified executables.
- Captures can contain local paths and game state. Review them before sharing.
- No game executable, assets, saves, raw captures, or personal profile cache is included.

## Troubleshooting

- **Game not found:** start Master Rallye and run the launcher again. If several copies are open, close extras or use `--pid`.
- **Developer menu unavailable:** verify `Menues/Enabled=True` in your own `DataGame/dev.xml`, then restart the game.
- **Compatibility check failed:** Observatory did not connect. Use a retail-derived executable that passes the structural audit; there is no bypass switch.
- **Results Dump safety is not verified:** use passive recovery or leave the Results screen before requesting a native Dump.

## Technical details

The package remains standalone and read-only. Local exact profiles are cached by SHA256 and re-audited on each use. The in-memory J.1 classification is pinned to the exact complete walker SHA256, exact hook targets, exact trampoline bytes, and audited null/continuation control flow. Observatory never writes process memory.

## Checksums

The candidate ZIP is accompanied by a manifest listing each member's size and SHA256, plus the archive SHA256. The manifest is generated with the package and is not a publication record.
