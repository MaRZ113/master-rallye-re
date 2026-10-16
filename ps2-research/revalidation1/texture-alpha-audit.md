# France1 foliage texture audit

## Source identities

| Platform | Resource | SHA-256 | Dimensions / storage | Stored alpha |
|---|---|---|---|---|
| PS2 | `\\TNG\\DATAPSM\\COURSE\\FRANCE1\\BUSH01-TGA.GXI` | `4c82e76360e2266d0cc4acac2c5d1688e750d454dd1e947e2707e5efa1b1cd29` | 64×64, RGBA32 decoded | 0–255, 89 distinct values; 1,673 nonzero pixels |
| PC | `DataGx/Course/France1/bush01-tga.dxt` | `24beae6fbd549a62939e56b3c83655fb10f487f04d00441ea7667d3729972396` | 128×128, DXT wrapper with BGRA payload; SDK converts to RGBA | 0–255, 15 distinct values; 4,713 nonzero / 4,168 opaque pixels |

The PC alpha-plane hash under the documented conversion is
`4691d725592da36edfeba6e9b49cd54a2df336547453111522435f8b3c509d49`. The
PS2 GXI decoded payload hash recorded in prior provenance is
`4c82e76360e2266d0cc4acac2c5d1688e750d454dd1e947e2707e5efa1b1cd29`.
These assets are not byte-identical and differ in resolution and alpha
distribution.

## What the values do not prove

Stored channel order, source GXI/PC DXT alpha, PS2 TEXA expansion, texture
combine, vertex diffuse alpha, D3D8 texture-stage operations, filtering/mips,
row orientation at runtime, and final GS `As`/D3D blend factor are distinct
questions. Runtime sampling and texture-stage traces are not in the available
raw capture set. Do not infer that the PC image is appropriate for
source-alpha blending from a shared basename or nonzero alpha alone.

The PC pilot intentionally leaves the stock PC texture bound. The two
resource hashes and pixel summaries are compact evidence only; original
images are excluded from the handoff archive.
