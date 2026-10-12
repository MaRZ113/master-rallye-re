# Global HUD Hide source archive

`source-archive.zip` contains the current review snapshots for the Global HUD Hide implementation, its production configuration path, native policy tests, and handoff documentation. It excludes build outputs, proprietary game files, and runtime captures.

`replay-support-source.zip` is the follow-on source snapshot for the narrow active-replay HUD admission change and its regression tests. The diagnosis and acceptance boundary are recorded in `replay-support.md`; `validation.md` records the current build/test identities. It excludes the supplied runtime JSONL/frame capture and all build outputs.

The repository had pre-existing uncommitted renderer work when this phase began. Several shared source files in the archive therefore include the complete current working version of adjacent renderer features as well as this phase's HUD changes; the archive is a reproducible source snapshot, not a patch isolated against `HEAD`.

The archive contains:

- Renderer CMake configuration and example INI.
- HUD policy header/source and the affected configuration, race-context, input, trace, and D3D8 wrapper sources.
- The deterministic interface generator and generated wrapper header.
- HUD, production INI, and race-context tests.
- `implementation.md`, `runtime-handoff.md`, and `validation.md`.

The replay follow-on archive contains the race context and HUD policy source, their tests, and the current implementation, replay support, runtime handoff, and validation documents. Shared files are snapshots of the current working version, not patches against `HEAD`.
