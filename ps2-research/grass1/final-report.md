| Field | Result |
|---|---|
| Phase |PS2-GRASS1 |
| Repository |D:\Game\Master Rallye\master-rallye-re-general |
| Branch |master |
| Starting HEAD |080ce812f24bb21b0a9f63d2592556f5f1c978b4 |
| Ending HEAD |The commit containing this report; exact SHA recorded in ignored data/grass1/git-closeout.json and final reply. Resolve with git log -1 --format=%H -- ps2-research/grass1/final-report.md |
| Preflight state |Clean; master ahead3 origin/master |
| Canonical ELF |SLES_509.06,3739852 bytes,b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2 |
| PackFS provenance |Existing tngtool; canonical PAK/000 freshly rehashed, named extraction and fresh/cache equality |
| PC Course SDK reference |Read-only course worktree4244fa0c4d878523c9947f54816bf377cdfb2589; clean before/after |
| Detail strings |All four directive anchors and particles/bush1/grass1 verified in original ELF |
| Directive parser |2d5100, first case-sensitive $detail substring through first closing parenthesis; interning after extraction |
| Internal detail categories |Runtime interner IDs, proxy+98; shrubs pool0, grass pool1; stones/none/unknown excluded |
| Material-to-geometry binding |Tag103 cell u16 triangle/u16 material → shared model vertices and source indices; all36 structural checks |
| Placement source |Actual landscape spatial/collision triangles; shared visual positions; exact visual strip/LOD mapping UNKNOWN |
| Generation timing |Camera-region activation/replenishment, retained point pools; not fresh placement every frame |
| Density/count |World XZ scanlines, float32 pitch1.33; half-open spans; dynamic capacity; <=30 CPU records/group |
| RNG/seed |srand30ff, original low32 LCG, fixed unit-ball jitter table and coordinate hash; live FCSR/guard lifetime UNKNOWN |
| Surface eligibility |Grass/shrubs category and upward normalized crossY>.975; degenerate length²<=2^-23 rejects |
| GRASS1 binding |Pool1 nameID →2fd7d0 GXI handle →311c50 texture state →point packet |
| BUSH1 binding |Pool0, same manager/bind path, category lift/size.4 |
| Stones |Recognized and source-bound; not emitted by this two-pool generator |
| None |Explicit/default ID, source-bound negative control; excluded |
| Singular shrub |Turkey_S1 material11 distinct ID,343 triangles; no matching pool |
| Grass-off |No textual override in traced parser/generator; present only in long visual metadata; other/cooker semantics UNKNOWN |
| Primitive topology |CPU64-byte record; matching embedded pc449 emits two-corner GS SPRITE, six GIF quadwords per point |
| Orientation/scale |Embedded screen-aligned projected rectangle, Q-scaled half-size cap56; no normal/yaw basis |
| Wind/animation |No time/wind deformation in CPU path or matching embedded pc449; residency unproved, no global foliage claim |
| Culling/LOD |Width60 snapped region, rectangle retirement, radial alpha LUT/cutoff; embedded center clip; no stochastic density LOD found |
| Draw producer |3597e0→31da60 REF/UNPACK/MSCAL449; state31e478/MSCAL37c; frame queue359610/317120/31e010; embedded XGKICK pc3d7 |
| GS state |Actual mode11: lower PRIM bits56, blend source-alpha formula, ATE0/ZTE1/GEQUAL, Z writes masked, clamp both axes; higher/inherited state requires capture |
| France1 |All four categories bound; grass/shrubs generate; flat none/stones controls excluded |
| ItalyS1 |Same mechanism; original-source/synthetic-activation diagnostic15 points |
| TurkeyS1 |Singular shrub rejected despite153 slope-passing source triangles |
| Negative control |France material8/source16967, harddirt and slope-pass, zero eligible points |
| Additional cross-country case |Spain1, ordinary grass/shrubs; diagnostic31 grass points |
| Offline diagnostic |detail_runtime.py: source metadata, supplied polygon generation, CPU record and conditional embedded single-sprite contract |
| Executable evidence |42 CPU function contracts and6 bounded VU program blocks; original words/JALs/MPGs, Ghidra12.1.4 bridge queries |
| Independent runtime evidence |NOT_PERFORMED; no supported active PCSX2/debugger capture |
| Tests |unittest150 PASS,0 SKIP; pytest150 PASS and164 subtests; focused20 PASS |
| Compileall |PASS |
| Diff-check |PASS |
| Original inputs unchanged |PASS, four SHA/size identities rechecked |
| Course SDK unchanged |PASS, same HEAD and clean status |
| Commit |research: reverse PS2 terrain detail decoration; SHA is the report's containing commit, recorded in local closeout/final reply |
| Push |Not performed |
| Overall status |**PS2-GRASS1 STATUS: PARTIAL**; exact MPG upload/residency and last-flush execution link remain open |

## What is proved

The earlier names-and-images hypothesis is replaced by an actual CPU execution
contract. A separate spatial-material table is read by2d5100; its detail token
is interned into proxy+98. Each cell reference binds a real source triangle to
that material ID.357628 loads its actual three model positions, checks category
and normalized upward normal, clips the activation polygon, and feeds356b70.
The generator walks a world-grid scanline lattice, chooses deterministic jitter
by coordinate hash, evaluates original-triangle height and appends a Vec3 into
the grass or shrub pool.3597e0 culls/fades those points and builds64-byte records.
3581e8 selects the corresponding resource handle/state and31da60 submits those
records through VIF. Completed packet references enter the real frame chain.

This is authored surface/category data plus runtime generated decoration:
**a hybrid data contract, with procedurally generated positions**. It is not a
preauthored tuft list, random barycentric scatter or conversion-time baked
grass mesh. Source geometry is the spatial/collision table using shared visual
vertices. Exact source-triangle to visual strip/LOD correspondence is still
UNKNOWN, so eligible triangle counts are never visible tuft counts.

The four evidence-annotated causal diagrams are in [findings.md](findings.md).
The positive and negative controls are actual source bindings in one France1
model: material4 harddirt+grass and material8 harddirt+none.900 negative-control
triangles pass slope but are excluded by category. This isolates material
behavior from surface-label or slope assumptions.36/36 models yield671,413
unique material-bound source triangles under the bounded structural contract.

## Placement and repeatability

Pitch is original float32 `3faa3d71` (about1.33). Camera center snaps at twice
pitch; caller width is60. Newly exposed rectangles activate query/clip/generation;
old points are retained or swap-retired outside the active rectangle. Slope
test is strict Ny>.975 after cross-product normalization. Source winding matters.
Scanlines use half-open edge/column bounds and epsilon.001. Interior density
is approximately1/pitch²; the exact count comes from these discrete loops,
not an area*random-probability formula. Grass and shrubs share the lattice,
with different vertical lift/size (.33/.4), not separate proved density factors.

The fixed original random table starts at seed0x30ff after1024 uniform draws,
then rejects three-component candidates outside the unit ball. Placement uses
its first two components at scale.5. Coordinate hash preserves ordered
float32 operations with constants21.123102,-34.923172,184.12938, then original
CVT.W.S&1023. No attractive synthetic seed replaces the original. Live FCSR,
guard/reset lifetime, clip history and duplicate-point/order behavior remain
important to exact full-course replay. The numerical diagnostic explicitly
labels rounding and full-triangle activation as synthetic inputs.

An original inline integer-conversion quirk was retained: normalized negative
powers of two below1 convert to0, despite ordinary inputs behaving like floor.
The plane evaluator retains original FPU order and fails closed for unsupported
exceptional divisions. Arithmetic is FLOAT32_RECONSTRUCTION, not a promise of
bit-identical PS2 FPU/VU execution. See [placement](placement-and-density.md),
[randomness](randomness.md) and [offline validation](offline-validation.md).

## Resources, primitive and renderer

Shrubs pool0 selects particles/bush1; grass pool1 selects particles/grass1.
Name IDs survive owner records,100-slot handle cache, named GXI resolution and
311c50 texture-state binding. Canonical32×32 GRASS1/BUSH1 payloads are separately
verified using the existing GXI parser. Existence, static load/bind contract and
live rendered texture confirmation remain different evidence levels.

Late bounded analysis located canonical `.vudata` and five MPG chunks. The
MSCAL449 address maps to ELF4443e8; pc37c maps to443d78. Their layouts match
the CPU record/state input. The embedded program performs two transforms,
Q division, projected size cap56, two sprite corners, full STQ rectangle,
integer RGBA/FTOI4 and center clipping. It writes six GIF quadwords per point
and NLOOP=2*count. State pc37c copies the AD state and caches the sprite tag.
The shared194-quadword output half sets EOP and uses XGKICK atpc3d7/ELF444050.

These instruction contracts are concrete; the link from CPU startup to upload
of this exact stream is **STATIC_INFERENCE**. No useful CPU pointer xref was
established. The final flush caller and live resident VU/GIF state are likewise
unproved. Thus a supported conditional VU contract is available for future
work, but the full runtime submission chain is not closed by assertion.
See [primitive](primitive-geometry.md), [drawing](draw-pipeline.md) and
[VU provenance](vu-contract.json).

Mode11's real jump-table target312dc8 and shared tail315a00 set sprite/texturing/
blend lower PRIM bits56. Original register-ID stores distinguish TEST1 from
CLAMP1. Alpha test is disabled, blend uses source alpha, depth test GEQUAL is
enabled and depth writes are masked. Higher PRIM bits, actual texture memory,
filtering overrides and destination-alpha state remain inherited/unobserved.
Texture alpha alone is not treated as proof of either testing or blending.

## Category contrasts and exact remaining links

Stones has an interned ID and real France triangles but no pool in this
generator. None/default and unknown singular shrub are excluded by the same
category selection, with different parser identities preserved. `$grass(off)`
has no override in this path and is absent from its short spatial materials;
no claim about all cooker/visual-material semantics is made.

The essential unresolved arrow is **CPU upload/residency and last flush →
decoded VU/GIF contract actually executed**. Additional precision boundaries
are visual strip/LOD equivalence, full rectangle clipping/history replay,
live FCSR/transforms, RNG initialization guard, owner frame-key writer and
ring latency. No independent runtime capture was possible. No screenshot or
synthetic sprite becomes runtime PASS. The20-gate matrix and configured test
results are in [validation.md](validation.md).

## Future PC implications and next phase

Selected retail PC course sidecars still contain ground surfaces/textures but
no checked PS2 detail directives. A future implementation needs an explicit
terrain-source/material-category interface plus runtime generation and a draw
consumer. Asset reuse or an unannotated D3D8 wrapper alone is insufficiently
supported. SDK, runtime hook and renderer choices remain planning classifications;
no port or SDK modification was made.

Exactly one recommended next phase is **PS2-GRASS2 — VU1 residency and targeted
detail capture**. It should prove the exact upload/last-flush link and correlate
one unchanged-ELF source/record/texture/GIF batch with a controlled frame.
[next.md](next.md) gives the experiment and nine portability answers. Turkey3's
puddle discrepancy remains a future lead; this phase begins no water,
reflection, treeblend, ambient or physics work.
