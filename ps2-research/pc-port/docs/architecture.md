# Build overlay and extension boundary

The baseline under `modernization/renderer/` is preserved byte-for-byte at the
locked Git revision. A PS2-enabled build is made from a separate `git archive`
staging tree in `ps2-research/pc-port/.staging/`; no integration patch
is applied to the source checkout.

The staged integration adds one opt-in build flag and the `PS2PortExtension`
interface to the existing D3D8 proxy. The ordinary baseline has no reference to
the extension and keeps the historical F10 mirror predicate. In the staged
PS2 build, buffer mirroring activates at device initialization for a supported
build with explicit `FoliageMode=1`, `2`, or `3`, before course buffers are
created and filled. Mode 0 is Stock. F10 logging remains independently gated.

At indexed draw time, the existing core constructs an immutable snapshot from
the actual D3D8 arguments, live France1 race-owner certificate, exact mirrored
geometry ranges, and current buffer generations/revisions. The extension
returns no request or a mode-specific masked state request. The core validates
native/effective state agreement only for masked states, applies temporary
states, executes the original draw once, and restores successfully changed
states. Partial state failures roll back only attempted masked states.
There is one D3D8 proxy in each build output; no proxy chaining or EXE patch is
used.

The overlay's staged-only generator patch keeps generated declarations and
early buffer wrapping consistent after regeneration. Both source variants are
tested twice for deterministic generated output, with exact expected hashes.
The source renderer's generator is not modified.

Reset echo detection remains ahead of the PS2 generation invalidation. A
successful actual device Reset advances the PS2 reset generation; a failed
Reset does not. Existing ReflectionScope, Trace, state tracking, Free Camera,
HUD, road teleport and window-mode handling remain in the shared core path.

Implementation details and evidence limits are in
[`../implementation.md`](../implementation.md) and
[`../validation.md`](../validation.md).
