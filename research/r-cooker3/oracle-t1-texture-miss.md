# T1 — ordinary DXT cache miss

## Result

**CONFIRMED_BY_RUNTIME — negative result, scoped to the tested ordinary
Mercedes texture-consumer path.**

The isolated T1 run had one missing
`DataGx/Vehicles/Mercedes/underdash-tga.dxt` while the matching GXI remained
available through the verified authoring bridge. The runtime reported
`Cannot load cached texture` for that DXT. The capture contains no
`Reading GXI` and no `Saved cached texture` event. No automatic DXT
regeneration was observed.

This does not establish that the GXI writer is unreachable in every runtime
path. It establishes only that the ordinary cache miss exercised here does
not regenerate a DXT from GXI.

## Inputs and evidence

| Item | SHA256 |
|---|---|
| GXI `Underdash-tga.gxi` | `c8e3578ac885531aad2dc8c56ba2b5edcdf35237b325a09452626b6ae436ded5` |
| Historical DXT `underdash-tga.dxt` | `d2eda2c6196d9d50448f90828450d81c4f6dc1d8041b7c0ae04ddbbcb81f8a9f` |
| Offline encoder output | Same hash and bytes as historical DXT |
| T1 DebugView log | SHA256 `fd9979230a0d767df66c9bd5a616d139b9eb02ef8132d9384aa0a2daa192b0d0`, 138,593 bytes |

The runtime capture is kept as a local ignored research input at
`research-output/r-cooker3/remove_underdash.log`; it is not committed.

## Architecture consequence

V1 uses two independent strategies:

- Model and collision structures: retail-native GXM cook in the isolated
  supported runtime.
- Textures: validate/reuse matching DXT; if absent, use the existing offline
  GXI-to-DXT encoder and validate its output.

The tested Mercedes offline encoding is byte-identical to its historical DXT.
That result does not require or imply an automatic retail cache-miss path.
