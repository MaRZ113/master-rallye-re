# Pose and final world transform

**The final model-world write is proved.** It is not merely a private path
cache: `1a82fc -> 1aa308` passes owner in a0 and actual entity in a1;
the publisher reloads `*(entity+50)` for each row and writes all sixteen words
of its en3d matrix. The original instruction decoder test validates effective
addresses, including three integer SW zero pads and thirteen SWC1 stores.

| Output | Owner source | Destination |
|---|---|---|
| Row0 right XYZ, W=0 | +d4/+d8/+dc | en3d +20/+24/+28/+2c |
| Row1 up XYZ, W=0 | +c8/+cc/+d0 | en3d +30/+34/+38/+3c |
| Row2 forward XYZ, W=0 | +bc/+c0/+c4 | en3d +40/+44/+48/+4c |
| Row3 world XYZ, W=1 | +b0/+b4/+b8 | en3d +50/+54/+58/+5c |

`21e290` allocates the 0x80 carrier at entity +50. `292a48` binds the Egg model
through `262f88` (carrier model ID +c) and initially copies the authored
matrix into these same fields. `263038` initializes the identity layout.
Spline init/update **overwrite** that matrix; no authored offset/rotation/
scale composition occurs. ITALY3, TURKEYW, FRANCE1 and FRANCEM have identity
authored matrices. Both SPAINS2 boats have identity basis rows but nonzero
authored translations: those translations are replaced, not added to the
Marker route. The compact case metadata records identity/nonidentity without
committing the proprietary coordinates.

`1ca568` proves row-vector affine convention:
`world = local.x*Row0 + local.y*Row1 + local.z*Row2 + Row3`.
The scene's named-model bounding-corner consumer `2639c8` passes this actual
en3d+20 matrix to that helper, independently corroborating its world role.
This bounded read is not a physics reverse. Entity scene submission `21ea20`
passes the same entity pointer to interface virtual +4c. The platform draw
implementation, PSM child transforms, GS upload and inter-tick interpolation
are outside this proved boundary. No independent raster/visibility result
is claimed, and those missing links are explicitly retained below.

Forward `1a9e08` uses displacement between new Q(t) and previous position.
If every component is <=0.0001 in magnitude, preserve previous forward.
Otherwise normalize when norm²>2^-23, and use the result if its resulting
norm²>=0.0001; otherwise preserve previous forward. This is a secant, not
the analytic curve derivative or Marker Dir. No altitude/ground/water lookup
or family test appears; Y flows through unchanged apart from arithmetic.

Banking `1a9fd0` is enabled only when +128==1. With old/new unit forward F/G,
position displacement D and configured speed S:

```text
ratio = length(D)*30/S (zero if S<=0)
b = (1-dot(G,F))*0.5 * ratio * Banking * pi * 5000
if dot(G,(-F.z,F.y,F.x)) > 0: b=-b
mean = (mean-old_ring_sample/N) + b/N
ring_sample = b
q.xyz = sin(mean/2)*G; q.w = cos(mean/2)
up = quaternion_matrix(q).Row1
```

Pi is the exact float32 `40490fdb` returned by `15acb0`. Original sine/cosine
wrappers are `3f3140/3f2f50`; their small-angle kernels `3f6b20/3f6078`
independently establish sine/cosine roles through odd/even polynomials and
small-input returns x/1. Host libm substitution is approximate platform
arithmetic. Banking-disabled up is (0,1,0). Right `1aa2e0` always returns
**(G.z,G.y,-G.x)** and ignores the up argument. Only up is banked; there is
no cross-product reconstruction or normalization of the complete matrix.
For vertical G, or a banked up row, this matrix need not be orthogonal.
The diagnostic preserves that behavior rather than inventing a conventional
airship frame. Unit scale/basis orthogonality is not a valid universal test.

```text
CONFIRMED_BY_EXE:
Q(t) -> displacement forward -> history-derived up + explicit right
     -> cached owner pose -> 1aa308 -> actual named model en3d world matrix
     -> scene entity submission
UNKNOWN / not expanded:
platform render interpolation -> PSM child propagation -> GS pixels
```
