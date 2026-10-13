# Original shrub contract and PC reconstruction boundary

## Selection and resource ownership

```text
Turkey3 tag103 material3/4, plural $detail(shrubs)
  -> 0x002d5100 parser, proxy detail IDs at +0x98
  -> 0x00357628 triangle/material binding and upward-normal test
  -> 0x0035793c owner+0x1030 comparison
  -> 0x00357954 pool selector +0x1024 = 0
  -> 0x00356b70 shared scanline generator
  -> 0x00357378 append point into selected category
  -> 0x003581e8 category resource cache/batch traversal
  -> particles/bush1 -> 0x002fd7d0 name/root/.gxi resolution
  -> 0x00311c50 texture binding -> 0x003597e0 point records
  -> 0x0031da60 REF/UNPACK/MSCAL449
  -> UNKNOWN LINK: selected live VU residency and visible GS output
```

Parser extraction is first case-sensitive `$detail` substring through the first
`)`; the subsequent interner lowercases ASCII. It does not pluralize `shrub`,
infer a detail from `$surfacetype(grass)`, or use an arbitrary texture name as the
category. Missing/unknown detail categories do not reach either generating pool.

BUSH1 GXI hash:
`2e4178614fbcbb3dbc3eaf5931001d2a566e76d59ef6adf7e66cd372556d40e9`.
It is 4104 bytes: the supported 8-byte simple-GXI header and 4096 stored RGBA
pixel bytes. Dimensions 32×32; alpha range 0–255, 213 distinct values, 674
nonzero-alpha texels. Preserve original row order and alpha bytes. The RGBA
channel interpretation reuses the established GXI evidence; it is not inferred
solely from the filename. Existence, static binding, PC upload and PS2 runtime
sampled-image confirmation are separate evidence levels.

## Placement equations

For a generating source triangle A,B,C, calculate its upward normal from the
actual positions. Reject `N·N <= 2^-23`; otherwise require normalized `Ny > .975`.
The material category then selects the pool. Surface type is a separate field
and does not determine category eligibility in this consumer.

The recovered generator scans the caller's C,B,A/clipped polygon in world XZ
with float32 pitch 1.33, half-open row/column intervals and epsilon .001.
For a lattice point X,Z, preserve original float32 operation order:

```text
h = (X*21.123102 + Z*(-34.923172)) + (X*(-Z))*184.12938
i = CVT.W.S(h) & 1023
x = X + jitter[i].x*0.5
z = Z + jitter[i].y*0.5
y = (plane.constant + x*plane.X + z*plane.Z) + lift
lift(grass) = float32(0.33)
lift(shrubs) = float32(0.4)
```

Both use the original fixed jitter table seeded 0x30ff; placement does not draw
a new random number per point. No category-specific pitch, randomized scale,
wind, yaw or texture selection is present in the traced path. Density is the
count of actual scanline iterations, not area multiplied by a random chance.

The source-backed PC artifact uses only strictly matched retail PC surfaces at
0.001 game-source units, nearest-even conversion as an explicit diagnostic
choice, and full original triangle activation. This is
`FLOAT32_RECONSTRUCTION` / `SYNTHETIC_FULL_TRIANGLE_ACTIVATION`, not the original
camera-history clipping/replenishment sequence. Duplicate original samples are
retained, and no extra terrain lift is added.

## Primitive and appearance

Constructor words at 0x00353304..0x0035330c form 0x3ecccccd (shrubs lift);
0x003545a8..0x003545b0 form 0x3ea8f5c3 (grass lift).
The shared CPU record producer reads category+0x3c at 0x003598a8 and multiplies
by 3 at 0x003598c4. Shared renderer constants produce:

```text
sizeX = (64 / renderer[+0x11c]) * (3*lift)
sizeY = ((global[0x0042d2c4]*64) / renderer[+0x11c]) * (3*lift)
```

GRASS1's matching embedded VU program expands the record to two screen-aligned
GS SPRITE corners, Q-scaled projected size capped at 56, full-image STQ,
distance-faded alpha and a shared center clip. It does not construct a terrain
normal basis or crossed world quads. Exact live projection constants, FCSR,
microprogram residency and pixel parity are not proved by this pass.

The existing PC rectangle preview and source-alpha blend remain approximations.
Its first type's absolute half-size may be multiplied by the proved category
ratio for the second; this does not establish exact original PS2 screen size or
GS alpha/128 equivalence. The shader/GS state itself is shared by both categories
in the traced original path.
