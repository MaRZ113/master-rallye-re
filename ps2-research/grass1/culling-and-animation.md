# Visibility, lifetime and animation boundary

Creation region and drawing cutoff are different. `357e70` maintains the
snapped width-60 square. `357c38` retains only points with
`xmin<=x<xmax` and `zmin<=z<zmax`, recycles IDs and swap-compacts the pool.
Camera movement activates newly covered rectangles; it does not regenerate
every retained point every frame.

`3597e0` independently performs radial CPU record rejection/fade about the
owner's snapped X/Z center at `+0x1010/+0x1018`, not an assumed unsnapped camera
position. It computes `r = 35 - (p+p)`, approximately **32.34** coordinate units,
then a single reciprocal `1/r`. Original ordered operations are:

```text
dx=(point.x-center.x)*(1/r); dz=(point.z-center.z)*(1/r)
q=original_inline_conversion((dx*dx+dz*dz)*1024)
emit only q<1023
alpha=LUT[q]
LUT[i]=clamp((1-min(1,sqrt(float(i)/1024)))*128,0,128)
```

This is detail-specific culling and radial alpha fade. It does not thin the
source lattice or alter pitch by distance. The integer cutoff, float32 order
and lookup quantization define the boundary; a rounded distance of 32.34 is
not an exact replacement. RGB is fixed 128 in the CPU input.

No detail-specific CPU frustum test, back-face draw rule, stochastic density
LOD or UV animation is found in this producer. Terrain/world traversal and
the general renderer may supply additional culling. They are not relabeled as
a new grass algorithm.

Wind is **not established**. The traced CPU generator uses source coordinates,
the fixed jitter table and a height plane. The per-frame CPU record producer
uses center, projection-related values and fade; it reads no global time,
sinusoid, wind parameter or animated sprite UV. Its negative scope is exactly
these functions. The matching embedded VU1 pc449 also contains no time or wind
input: it projects centers, expands screen rectangles and emits STQ. Its clip
test uses (.8*transformedX,.8*transformedY,transformedZ-1) against +/-abs(W),
setting a second-vertex W mask0xc000 on rejection. This extends negative evidence
to that program, conditional on unproved residency. A global no-animation claim
about all PS2 foliage would still exceed the scope.

Packet builder compares owner +1028 with a frame key, but no subsequent writer
to +1028 was found in this traced owner. The three render-context handles rotate
after completion. Effective build frequency within a frame and packet latency
are runtime questions. They do not change the proved camera-region generation
frequency, which is governed separately by `357e70`.
