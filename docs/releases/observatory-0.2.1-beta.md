# Master Rallye Observatory v0.2.1-beta

## Quick Start

1. Extract the ZIP to a writable folder.
2. Enable `Menues/Enabled=True` in your own `DataGame/dev.xml`.
3. Start Master Rallye.
4. Run `MRallye-Observatory.cmd`.
5. Capture the active game state.

## What's new

- Standalone package; no repository checkout or repository-side Python path is required.
- Structural compatibility verification accepts unknown exact hashes only when the required retail Broker layout and read-core fingerprints match.
- Exact compatibility profiles are cached locally against the executable SHA256 and re-audited on each use.
- Capture provenance records build compatibility and capability information.
- Build-family support removes the need to add a source profile for each compatible cosmetic executable change.

## Compatibility

Windows and Python 3.11 or newer are required. Exact known builds are recognized directly. Other retail-derived builds must pass the included PE32 and Broker-structure audit. Builds that do not match are rejected. This candidate has not been published; compatibility remains limited to the audited retail family and exact profiles.

## Known limitations

- Stock native Broker Dump may crash on the Race Results screen when a typed StringList has a NULL payload. Do not request a native Dump from Results unless Status confirms post-Results Dump safety.
- Structural compatibility does not imply every optional feature is available. Broker reading, native Dump, Broker Editor opening, Flow Builder, and Results-Dump safety are tracked separately.
- Captures can contain local paths and game state. Review them before sharing.
- No game executable, game assets, saves, raw captures, or personal profile cache is included.

## Files / checksums

The candidate ZIP is accompanied by a manifest listing each member's size and SHA256, plus the archive SHA256. The manifest is generated with the package and is not a publication record.
