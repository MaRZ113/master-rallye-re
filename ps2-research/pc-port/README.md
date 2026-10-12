# PC PS2 Graphics Port

This is the isolated home for future PS2-derived PC rendering work. Existing
PS2 research directories remain evidence sources; `modernization/renderer/`
is the frozen, stable D3D8 baseline.

## Current state

`docs/architecture.md` records the inspected baseline boundary and the smallest
safe integration design. The baseline has no supported draw-extension API, so
the France1 `bush01` override is not wired or activated. The architecture brief
requires approval before adding the proposed hook to the frozen renderer.

`docs/pilot1.2-design.md` describes how the PS2-specific extension should own
its foliage policy while the baseline retains device interception, buffer
provenance, state tracking, native draw submission and restoration.

No renderer source, PC asset, Course SDK file, game executable or runtime
installation is modified by this architecture record.
