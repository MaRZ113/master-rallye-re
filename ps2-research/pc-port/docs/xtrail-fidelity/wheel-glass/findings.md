# X-Trail wheel, lamp cover and decal source audit

This is a read-only source comparison. No wheel or glass renderer implementation
is authorized by these source facts alone. `source-evidence.json` preserves exact
source offsets, whole-geometry keys, shader ownership and the two supplied live
PC F10 files. All comparisons use model-local game coordinates and **0.001**
corner tolerance; no fitted transform or screenshot-tuned tolerance is used.

## Number decal

PC CAR record13, offset98085, vertexbase1459,20vertices,indexstart3678,
42indices/14faces, has digest
`e580100f2670ba7bd87589727e194026f3f28d9b54b42eda325d51e47aa136b3`.
All14faces correspond to PS2 CAR root.14, node174533,
`$shader(carshiny)`, primary `mastersticker069-tga`, secondary
`silverpaint-tga`, executable mode3 with dynamic mixed target substitution.
PC secondary is `Null`. Source UV0 matches exactly; normals differ by at most
1.1920929e-7 and source diffuse alpha is255. A20-entry position-hash-to-normal
table has no coincident-normal ambiguity and contains no reconstructive positions.

Both new PC F10 captures show a layout-correlated14face/20vertex DIP at
FVF0x142/stride24, stage1 disabled, alpha test0, blend0, Zwrite1. Native upload
format lacks normals. A body environment classifier requiring FVF0x152 and an
already active environment stage necessarily excludes it. Reusing the source
normal values is supported **only after validating exact current native geometry,
UV/diffuse, owner transform and resource lifetime**. F10 has no upload bytes.

## Wheels

All252 PC WHEEL faces match PS2 WHEEL at0.001. No mesh transplant is needed to
obtain the examined PS2 wheel shape:

| PC wheel record | Faces | PS2 owner | Source distinction |
|---|---:|---|---|
|0|72|root.0|Rubber map retained, no mixed environment substitution|
|1|36|root.1|Rubber tread map retained, no mixed environment substitution|
|2|54|root.0|Rubber map retained, no mixed environment substitution|
|3|90|root.2|Chrome `carshiny`, dynamic target; different rim image and UV|

The rim uses PC `xwheel-tga` versus PS2 `jumpwheel64-tga`; normal residual is
1.1920929e-7 and UV0 residual0.17088175. Thus an authentic-looking rim needs the
original image **and UV conversion**, rather than a body reflection state change
alone. `CommonTextures/JUMPWHEEL64-TGA.GXI` is64x64, alpha255, SHA
`03671ce44fc80512b23da204cddf63c3936bc51031f6a9980e9818ab60fd897e`.
Rubber draw0 UV0 matches; tread/other side use integer UV differences of3/1,
whose equivalence depends on actual wrap state and must not be silently assumed.

The original wheel PSM is SHA
`d53360eab52761fdadf1a4d5a2c87196be7674fbbb603c41cd4726a4b303773c`.
The strict previously proved trailer adapter reads its102 cylinder auxiliary
(.4,.2), preserving the visual tree and original bytes. Physics is not touched.
All four whole-source wheel keys are unique in the examined78 PC DX files, but
this does not prove the live rotating wheel owner/matrix. Live wheel admission
is **UNKNOWN** in this pass. No wheel material override should be integrated.

## Headlight cover versus lamp layers

PC CAR10,18faces, digest
`fad797c65838c39d359767a9ef06d0d5579d847fa2b23a9ee8febe8c171b361c`,
matches18/18 PS2 root.19, node175376, **carglass mode20**. Source bounds are
X[-.86584,.85384],Y[.54050,.86810],Z[1.90502,2.16729], placing this in the
front lamp region. Front windshield root.24 is separately at
Y[.98802,1.44754],Z[.26079,1.01601]. The attribution therefore follows geometry,
not the misleading PS2 primary name `windscreen32-tga`.

PC primary/secondary are both `lights-tga`; PS2 primary is
`windscreen32-tga`, authored secondary `glass-tga`, effective secondary static
`CommonTextures/windscreen-reflect`. Normals match1.1920929e-7; UV0 differs by
1.00338298. Original REFL1 mode20 is a blended primary with masked depth writes
and a separate0.75 additive static highlight, sharing the normal generator. It
is not the body mode3 mixed framebuffer material. Simply enabling body reflection
or changing COLOROP on PC lights is not an authentic mode20 implementation.

Distinct lamp surfaces21 (28faces) and22 (14faces) match PS2 root.5/root.11
carshiny with their original lights textures. In both live captures these are
later alpha-blended PC draws:21 FVF0x142/stride24;22 FVF0x152/stride36. They
must remain distinct from the opaque cover/body and must not be admitted under
an opaque-body predicate. Brake-light conditional off/on/glow geometry is also
separate and remains untouched.

## Other mixed material checks

The existing CAR1 partition remains195 carshiny faces then14 carflat faces.
The14flat-face bounds areX[-.91168,.90117],Y[.96581,.99366],Z[-.47527,.58984],
a narrow horizontal interior region. Its exact named component isUNKNOWN.
CAR2 contains28carflat plus6rubber-authored-map faces;CAR3 is8carflat.
The audit includes all32CAR records and all4WHEEL records with original-order
category runs. Conditional screen/brake overlaps are markedAMBIGUOUS where
different original material owners share the same positions.

## Screenshots and proof boundary

The supplied PC0/1 screenshots show a changed body finish while the number
decal, wheels and lamp region retain their former appearance. The PS2 race image
suggests a softer lamp cover and the PS2 frontend image shows different rim
appearance. These are **USER_RUNTIME_OBSERVATION / SCREENSHOT_CORRELATION**,
not proofs of live material bindings. The frontend frame and race frame have
different camera, lighting and context; no pixel-level parity is claimed.

No renderer, overlay, build directory, game asset or source decoder was changed.
Regenerate metadata with `python .../wheel-glass/audit.py` (canonical PS2 PackFS
and protected retail SDK/corpus required). Corpus-independent focused validation:
`python -m unittest discover -s .../wheel-glass -p test_evidence.py -v`.
