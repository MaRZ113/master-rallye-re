# PS2 vehicle models without Reflection=4

The PS2 models (menu COMPLETE, race CAR, AI fleet, wheels, lamps) draw with `Reflection=0`; the game's own PC reflections are
not touched. Their secondary layer comes from the model files, except for the meshes whose original PS2 secondary is the live
reflection render target (`mixed` in the fleet profiles: body panels, lamps, rims). Those carry placeholder maps in the model
files.

| Key | Effect |
|---|---|
| `SourceReflectionVFlip=1` | reverses only the generated environment V of the secondary layer (`Reflection=0` only); the shared chrome lamp/rim map (SHA-256 `7bc7aab4...`) is mirrored on upload because it is stored the other way round |
| `PS2UniformReflection=0` (default) | the `mixed` meshes use the placeholder maps stored in the model |
| `PS2UniformReflection=1` | the `mixed` meshes all use the PS2 static environment map `ReflectionSourceGXI` at 80/128 (the static term of the mixed target): uniform, but darker |

## Known look: ChevyBlazer
With `PS2UniformReflection=0` the ChevyBlazer body shows patchy reflections: its panels carry different placeholder maps
(chrome balls on some, light blobs on others), with a visible seam on the tailgate. Game test 2026-11-03. Other cars look
acceptable. `PS2UniformReflection=1` removes the patchwork at the price of darker reflections. A per-car fix was not made;
the PC model of the Blazer is fine. The proper alternative would be to give those meshes the PC native reflection of the
stock draw.

## Kia
The Kia ON-core/glow path now accepts an unknown tracked pixel-shader state (it left at its bindings gate without
`Reflection=4`); game test: Kia brake lamps work.
