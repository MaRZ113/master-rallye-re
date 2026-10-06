# Four serialized bytes and their vehicle consequences

All offsets below refer to the runtime material loaded by `005528B0`.
They do not rename or alter the raw DX parser/writer fields.

| Byte | Runtime | Established role | Stock counts | Confidence |
|---:|---|---|---|---|
| 0 | +22 | alpha family enable | 0:1241, 1:237 | CONFIRMED_BY_EXE |
| 1 | +23 | alpha-test selector when byte0 enabled | 0:1478 | CONFIRMED_BY_EXE; stock absence CONFIRMED_BY_CORPUS |
| 2 | +20 | pass vertex diffuse enable, conditioned on pass flag01 | 0:172, 1:1306 | CONFIRMED_BY_EXE |
| 3 | +21 | pass source UV enable, conditioned on pass UV count>0 | 0:2, 1:1476 | CONFIRMED_BY_EXE |

Byte2's concrete chain is material+20 -> `005781B0` descriptor flag08 ->
`00575E70` FVF bit40 DIFFUSE -> `00575D50` diffuse byte offset at
descriptor+15 -> `00577DD0` copying source color dwords into the interleaved
render vertices when that offset is not FF. Base/env passes both permit diffuse
with pass flag01. Env also permits normals with pass flag02/FVF10.

Focused branch from `005781B0`:

```c
if (material[0x20] != 0 && (pass_flags & 1) != 0)
    descriptor_flags |= 8;
if (material[0x21] != 0 && pass_uv_count > 0) {
    descriptor_uv_count = pass_uv_count;
    /* each UV descriptor component count = 2 */
}
```

The FVF builder writes `fvf |= 0x40` for descriptor flag08. The UV count goes
into FVF bits8..11; two-component coordinate encoding is zero in the per-set
size field. `00577DD0` consults pass UV mapping+10 and descriptor UV offsets
at+17 to copy each selected source UV pair. If an enabled UV set is absent
from source it writes a zero pair. Disabling byte3 excludes source UVs from
that pass's FVF. The current corpus's only byte3=0 records are the textureless
IceCream draws, so there is no ordinary textured stock variation to infer from.
The synthetic no-UV preview uses zero coordinates as a labelled approximation.

These material reads were followed in the vehicle compiled-pass path; their
downstream FVF and vertex-copy effects are resolved. Optional variant objects
and unobserved nonvehicle passes are not declared exhaustively understood.
Neither byte chooses alpha nor adds a texture stage. In particular byte2=0
can coexist with byte0=1: observed brake-glow alpha layers use this combination.

Mask bit02 equals `(byte2 != 0)` in 1478/1478 draws, but its runtime selector
and the byte's FVF consumer are distinct. EXE proof of mask&3 selecting base
must not be presented as EXE proof that mask02 itself copies vertex color.
The correlation is CONFIRMED_BY_CORPUS.

Byte0 agrees with uniquely resolved sidecar slot0 UsesAlpha in 1364/1365
bindings; Kamaz/complete.dx draw19 is the retained exception. HasAlpha,
UsesAlpha, and DXT nonopaque pixels are different facts. The renderer selector
uses raw bytes, not the sidecar or image statistics.

FVF naming references: [FVF constants](https://learn.microsoft.com/en-us/windows/win32/direct3d9/d3dfvf)
and [texture-coordinate size encoding](https://learn.microsoft.com/en-us/windows/win32/direct3d9/d3dfvf-texcoordsizen).
No byte1/2/3 writer was added by this closeout.
