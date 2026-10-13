# PS2-REFLECTION-PORT1: one Tata paint material

The implemented experiment is **TataBonnetPS2StaticContribution**, not the full
PS2 environment-target producer. It replaces the selected PC material's secondary
image with original PS2 ENVSOURCE RGB multiplied by 80/128 and uses source-color
addition. The framebuffer term, PS2 body-color preparation, two-pass GS
rasterization and complete VU coordinate path are not ported.

## Original PS2 contract

REFL1's canonical TATA/CAR.PSM root.3, node 170755, material 170849, selects
$shader(carshiny). Primary: CommonTextures\tatabon-tga; authored secondary:
CommonTextures\whitepaint-tga. Handler 0x3ade58 writes mode 3 and replaces the
secondary with CommonTextures\rendertarget64x64.

The target producer is 0x330780 -> 0x31a518, called at 0x33257c and 0x3325c8.
Nominal target RGB = 80/128 * ENVSOURCE + 48/128 * FlipY(current framebuffer).
It is a mixed static/framebuffer source, not a cube map or an extra reflection
camera. The first eligible model call updates shared storage after a presentation
reset; exact live frame ordering remains unconfirmed.

Body primary: texture MODULATE with prepared color, ABE=0, depth writes allowed.
Body secondary: RGB DECAL, ABE=1, ALPHA 0x0000008000000029, Cout = Cd + Cs.
Texture alpha is not the secondary coefficient. Coordinates come from local
normals through object/view orientation, scale and bias. The selected helper
is not REFLECTIONVECTOR sphere mapping. Evidence is CONFIRMED_BY_EXE/BOTH,
not a new controlled PS2 runtime capture.

## Source and live material identity

The fresh source check is in material-source-contract.json:

- PS2 payload 9397b4b9b60567a3ac3f5e0ac752a6794b3fea9ace8c2bb524db53bb565e6c84:
  57 nonsuppressed source triangles.
- PC protected-retail Tata/car.dx,
  45b7bfba6938e259c0ac6d79a42a878a8c66b1e53547a53a6d23343092fb34cb:
  record 19, offset 95648, vertex base 1524, 48 vertices, 165 indices, 55 triangles.
  Ordered slots: tatabon-tga, whitepaint-tga, Null.
- 55/55 PC faces correspond to 55/57 PS2 faces at 0.001 model-local units.
  The two remaining PS2 faces are not added.
- PC geometry SHA:
  f80ae53d8c8691ebb8387680b0555343e10100459949c56e3338c484b680e669.
  It is unique among the 39 source draws in this car.dx.

Record 19 is a compiled source identity, not a D3D8 ordinal. Runtime admission
requires the whole bitwise position signature, current CPU-mirrored VB/IB
generations and upload revisions, an exact supported executable, a live race
certificate, the existing unambiguous vehicle-body oracle, FVF 0x152 / stride 36,
and the original opaque normal-environment stage contract. Texture identities
and generations must be current; native state must agree with the effective
tracker. Unknown geometry, wheels, glass, UI, missing mirrors, altered buffers
and a conflicting ViewDependent2D policy fail closed.

Sixteen bounded cache entries retain geometry digests keyed by device/reset,
VB/IB generation/revision and source range. Ownership and state are checked each
time; an upload revision change triggers a new digest. Only the 48-vertex and
165-index candidate range is copied from the CPU mirror. No GPU buffer lock or
complete per-frame buffer digest is used.

## PC cross-check

Existing R-GFX4/R-MAT1 evidence establishes stage 0 texture x diffuse and
stage 1 MODULATEALPHA_ADDCOLOR, camera-space normals and COUNT2.
This phase's REA session independently identifies the canonical PC executable
SHA and reads constructor bytes at 0x5860a0. Writes include four float32 0.5
values. The native texture matrix remains unchanged by the pilot.

The current provider does not define a function at 0x586150; no new decompiler
boundary is invented there. Source slot 1 names whitepaint, but its actual
runtime image writer/update cadence is not established here. The experiment
explicitly supplies the PS2 static term and does not label an unknown PC image
as the PS2 framebuffer mixture.

## Native implementation

Mode 0 makes no reflection request, opens no GXI and creates no reflection
texture. No CPU mirror is requested unless another existing opt-in needs it.

Mode 1 validates the local GXI SHA, magic, size and 64x64 dimensions. RGBA rows
are retained, RGB becomes BGRA using floor(channel * 80 / 128), alpha becomes
255. A single one-level managed A8R8G8B8 texture is uploaded. There is no network
acquisition, embedded proprietary pixel data, render-target allocation,
framebuffer copy or extra draw pass. This is APPROXIMATE_D3D8_IMAGE_CONVERSION:
PS2 PSMCT16 conversion, GS rounding, filtering and saturation are not emulated.

The staged native integration saves stage 1 COLOROP and its exact texture
binding. It sets COLOROP=ADD (7) and the private image, submits the original
DrawIndexedPrimitive once, and restores texture then COLOROP. Alpha test/blend,
blend factors, ZWRITE/ZFUNC, culling, paint, normals, UV matrix, filtering,
address state, fog and render target remain native PC. Logical game state stays
native; effective state records successful temporary writes and restores.

Partial application rolls back before submission. Failed restoration retains
the original GetTexture reference and pending changes for repair before another
draw or unreviewed state-block path. If repair still fails, that later draw is
not submitted in leaked state. A normally submitted draw retains its original
HRESULT even if post-draw restoration fails; the feature is then disabled.

ReflectionScope remains outermost. The PS2 pilot refuses ViewDependent2D
admission rather than changing that mode. Window-mode reset echoes occur before
extension invalidation. Before a real Reset, private resources and saved
references are released. Failed Reset suspends the reflection until a real
successful reset; Stock draws remain native. Only an unrepaired override blocks
draws for state safety. Normal success recreates the image. Final device release drops reflection
resources before native Device::Release. PILOT1.4's pixel lifecycle is separate.
Upload mirroring and buffer-proxy ownership continue while a requested, verified
reflection is temporarily suspended, so resumed admission cannot use data that
escaped through a raw buffer getter during the suspension.

## Frozen renderer build identity

The old script rejected every repository HEAD differing from 3f837f4.
Lock schema 2 verifies the complete renderer Git tree
7f9f5a7d9464b7b86ff09a9bf6c34b7ce341682d at both the pinned commit and current
HEAD. Tracked renderer edits and untracked source files are rejected; ignored
build outputs are not inputs.

Staging still comes from immutable commit
3f837f4ddcb27ee1034a4b0753634c92009360ec. Unrelated research commits with the
same renderer tree are permitted. File, exact patch and generated-interface
hash checks remain; there is no fuzzy patch or automatic source repair.
Only integration patch 0001 changes. Generator patch 0002 and its locked output
hashes stay intact. A separate report path preserves PILOT1.4's previous report
and ignored build artifacts.

## Evidence boundary

Source correspondence and the original PS2 material contract are established.
The new live predicate and native transaction are implemented and tested.
Actual port admission, visible bonnet changes, driver behavior and PS2
appearance equivalence require the user's controlled PC test. No complete
mixed-target or visual-parity claim is made.
