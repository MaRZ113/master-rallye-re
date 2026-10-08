# Normal-based environment coordinates

The original selector1 is a **2D transformed-normal mapping**, not a proved
reflection-vector or sphere-map equation. This is CONFIRMED_BY_EXE from the
canonical embedded VU instruction pairs and CPU inputs. The offline evaluator
is FLOAT32_RECONSTRUCTION; live VU execution remains unconfirmed.

## Inputs and ownership

Normal n=(nx,ny,nz) is the model-local source vertex at+0. `3900f0` retains it
in the48-byte runtime vertex; `31f4e0` places it in cached64-byte qword0.
Base UVs are qword2.xy. Positions are qword3 and do not feed helper408.

`330780 ->3628c0(cache,record,manager+40,force)` prepares the two object matrices.
cache+30 always receives the input; cache+70 may retain its orientation when
initialized, force=0, definition+70 bit34 is set, context+60!=2 and both row0/row1
dot comparisons are>=0.9. Otherwise its orientation is refreshed. Translation
updates differ across these branches but cannot enter the normal's affine direction
equation. Do not call these matrices simply “previous/current frame” without
that retention rule.

`3432b8` copies cache+70 and+30 to42e230/270; `31c228 ->317770` emits their eight
qwords followed by MSCAL2cf. Camera owner=manager+34 supplies position+70/+c0,
negated forward+60/+b0 and up+50/+a0. `3387c8 ->36fc18` constructs two view
matrices at manager+1e0/+220. The helper normalizes its camera basis with an
epsilon2^-23 guard and a handedness switch43e88, forms cross products, then
`36fb28` combines negative position translation with transposed orientation
(`370080`). `343458` copies these to42e2b0/2f0;317470 emits MSCAL30e.
The alternate338ab8 context instead passes the same fixed view matrix twice.

These are object-to-world and world-to-view stored row matrices as consumed by
the row-vector product. The original cross-product/handedness branch is preserved
as an input-owner fact; no screenshot-derived sign or axis swap is introduced.
Projection matrices are separate input qwords. They participate in position
projection, not the selected environment-normal formula.

## Original equation and operation order

Let w=VU data319.w, O0/O1=the two object matrices, V0/V1=the two view matrices.
Each stored matrix is four row vectors.

```text
O = (1-w)*O0 + w*O1                 helper41c..42f
V = (1-w)*V0 + w*V1                 helper41c..42f
M = O * V                          helper430..448, x/y/z/w accumulation

ki = (+0.5*M[i,0], -0.5*M[i,1])     i=0,1,2; matrix setup2f5..30d
UVenv = (0.5,0.5) + nx*k0 + ny*k1 + nz*k2   helper408..41b
UVpacked = (base_u,base_v,env_u,env_v)
```

At2d4 BAL327 targets41c (interpolation), not a matrix multiplication. At2f3
BAL316 targets430, multiplying the interpolated object matrix by view rows616..619.
Rows608..611 are loaded into vf17..20, rotated twice by MR32, xy cleared, then
zw scaled by(.5,-.5). In408, MULAx/MADDAy/MADDAz accumulate only normal xyz;
MADDAw.xy retains the original base UV; the bias is added in zw.
There is no vertex-minus-camera vector, dot(n,v), normalization, inverse transpose
or reflected-vector computation in this helper. Nonuniform scale is not corrected
by a modern normal-matrix substitution.

The embedded program initialization writes w=0 at PC7. A separate embedded
3a7..3c8 block can update it using a state key, subtraction,0.6 increment and
[0,1] clamp. Its actual CPU invocation was **not established**: no live w is
invented. The evaluator requires explicit w and matrices; captured values can
later be supplied with a provenance label. Runtime interpolation ownership/cadence
is the remaining bounded input-state question, not an invented blend-rate model.

## Controlled consequences

With identity matrices, +X normal gives(1,.5),+Y gives(.5,0),+Z gives(.5,.5).
Vehicle rotation and camera rotation affect the corresponding matrix rows.
Affine translations leave the direction result unchanged; world movement can
still change the framebuffer-derived **image**, a separate dependency.
Normals of length2 can yield UV outside[0,1]: no normalization/clamp is added.
Final GS addressing is separately inherited/state-dependent.

Synthetic tests use explicit quarter-turn matrices, interpolation endpoints,
translations and scaled normals with independent expected values. Host float32
rounding preserves operation order but not all VU ACC precision, denormal,
overflow or fused-operation behavior. No bit-exact parity claim is made.
