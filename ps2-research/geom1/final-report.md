| Field | Result |
|---|---|
| Phase | PS2-GEOM1 |
| Repository | D:/Game/Master Rallye/master-rallye-re-general |
| Branch | master |
| Starting HEAD | b23c67b42f4a0f341b1bfede12dbd239433af8ed |
| Ending HEAD | Containing GEOM1 commit; exact SHA in handoff MANIFEST.json and final closeout |
| Preflight | CLEAN; master ahead 6; no pre-existing modified/untracked work |
| Canonical PS2 sources | Fresh four canonical size/SHA matches before and after; source-provenance.json |
| PC Retail corpus | Authoritative compiled retail DX/TXT/XML; 11 inspected original files rehashed |
| Course SDK reference | Read-only; 4244fa0c4d878523c9947f54816bf377cdfb2589; clean before/after |
| PS2 visual format coverage | Selected landscape tags 0/1/2/5/6, terminal 100, 52-byte vertices, ADC; selected dinghy EOF extension |
| PC compiled geometry coverage | Complete/disjoint validated selected revision-135 course draws; original SDK readers |
| Coordinate convention | GAME_SOURCE; no Blender conversion during matching |
| Alignment proof | Independent internal course identity, ordered RaceLine and authored identity landscape matrices |
| Source transform confidence | Identity for selected landscapes; dynamic object pose remains UNKNOWN |
| Triangle matcher | Six corner permutations, max-coordinate epsilon; separate float32 bit/numeric position checks |
| Surface equivalence matcher | Normal/plane gates, dominant-axis disjoint polygon subtraction, union coverage |
| Tolerance profiles | Strict .0001, baseline .001, relaxed .01; separate plane/normal/coverage/near thresholds |
| Spatial acceleration | Centroid hash plus 3D AABB grid; sorted deterministic candidates; explicit budgets |
| Turkey3 | 36,001 exact / 40,832 PS2 source triples; 745 puddle faces retain zero exact PC matches |
| France1 | 41,620 exact / 41,817 PS2 source triples; 3,586/3,586 shared water |
| ItalyS1 | 39,682 exact / 40,479 PS2 source triples; 1,329/1,329 shared water, differing shader metadata |
| Non-water comparison | Three independent ground anchors; bounded foliage/hut/boat/tyre source groups |
| Material differences | Geometry-independent shader/slot/ambiguous-source classifications |
| PS2-only geometry | Turkey puddle source addition proved; other unmatched groups remain bounded candidates |
| PC-only geometry | 971 / 1,922 / 1,694 unmatched compiled-face candidates; no global exclusivity claim |
| Shared geometry | Extensive exact correspondence across all supported material groups |
| Changed geometry | Separate partial/near/equivalent coverage, with residuals; no automatic common-author identity |
| Ambiguous geometry | Relocation, alternatives, incomplete material mapping and active subsets remain explicit |
| Hierarchy/LOD | Paths, offsets, flags, strips and ancestors retained; live branch selection UNKNOWN |
| Source-versus-runtime visibility | AUTHORED_VISUAL_GEOMETRY; runtime NOT_PERFORMED |
| Scene-object case | Blue/red standalone spline dinghies versus PC baked dinghy-textured draws |
| Dinghy/static duplication risk | Positive baked geometry; replace/hide only after exact instance correspondence |
| Tata/Kia feasibility | 1,442/2,016 and 1,739/2,289 PS2 local CAR source faces match selected retail car.dx |
| Diagnostic visualization | Three local ignored SVGs, inspected Turkey3 PNG; no Blender/add-on required |
| Geometry delta schema | Version 1; stable source IDs; 90 compact selected records with counterpart metadata |
| Portability backlog | Reuse/material/visual-content/runtime requirements distinguished; research only |
| Unittest | 214 PASS, 0 FAIL, 0 SKIP; isolated 200 reported / 17 declared dependency skips |
| Pytest | 214 PASS + 268 subtests; isolated 187 PASS / 27 SKIP + 166 subtests |
| Compileall | PASS |
| Diff-check | PASS |
| Performance | 11.433 / 14.817 / 11.511 s measured batches; exact candidate counts in summary JSON |
| Determinism | Three fresh baseline reports byte-identical; independent Turkey3 CLI agrees |
| Handoff integrity | Isolated tests PASS; ZIP CRC/payload SHA verification; external dependencies documented |
| Original sources unchanged | PASS: canonical PS2 and all inspected PC inputs |
| Course SDK unchanged | PASS |
| PC renderer unchanged | PASS |
| Files changed | Only geom1 docs/metadata, research tools/test, two shared research helpers and README index |
| Commit | research: map PS2 and PC visual geometry deltas; exact SHA recorded outside recursive report |
| Push | NOT_PERFORMED |
| Overall status | PS2-GEOM1 STATUS: COMPLETE — bounded static geometry bridge; no runtime visual parity claim |

# Main discoveries

The course bridge now compares whole supported visual PSM inventories against
complete compiled PC course draws, beyond the prior water filters. Most selected
PS2 source faces have a geometric counterpart. Grouping, duplicate source faces,
material metadata and conditional geometry prevent these totals from becoming
live polygon budgets or object counts.

| Course | PS2 source triples | PC compiled triangles | PS2 exact | Full equivalent coverage | Near modified candidates | Partial overlap | PS2 unmatched candidates | PC unmatched candidates |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Turkey3 | 40,832 | 42,237 | 36,001 | 1 | 336 | 12 | 4,478 | 971 |
| France1 | 41,817 | 64,577 | 41,620 | 18 | 51 | 11 | 117 | 1,922 |
| ItalyS1 | 40,479 | 46,367 | 39,682 | 13 | 35 | 59 | 690 | 1,694 |

Turkey also has four diagnostic degenerate PS2 triples and one PC triangle; they
are inventoried, not quietly dropped. Counts are directional. PC source repeats
can match the same PS2 face; an exact relation is not a one-to-one draw/instance
bijection. All material groups and every supported source face participate.

# Matching methodology

The bridge reuses PackFS, WATER1's visual reader, REFL1's selected vehicle reader
and the read-only Course SDK. Spatial/collision PSM triangles never substitute
for visual strips. Triangle comparison tries all six permutations; winding and
strip control remain separate rendering attributes. Positions have bitwise,
numeric and epsilon agreement metrics instead of calling every float difference
new geometry.

Unmatched triangles query a bounded 3D spatial index. Plane distance and normal
alignment precede projected union coverage. Subtracting cutters from disjoint
remaining fragments prevents duplicate/overlapping target triangles from
inflating coverage. Synthetic opposite diagonals, fan subdivision and T-junctions
prove topology independence. Parallel surfaces at different heights remain
distinct; partial coverage never becomes whole-surface equivalence.

SAME_SURFACE_DIFFERENT_TRIANGULATION is a directional coverage classification.
It can also catch merging and small coordinate-boundary differences; it does not
prove an intentional historical retessellation. GEOMETRY_MODIFIED denotes near
parallel overlap, not an automatically established common authored surface.
Unmatched labels mean no match under the declared local contract in the examined
compiled landscape. Relocated, alternative or separate-scene counterparts remain
possible. All thresholds and residuals survive in evidence.

# Course comparisons

Turkey3 reproduces all WATER1 anchors: 17 puddle material-owning meshes, 51 strips,
745 nonsuppressed nondegenerate source faces, 537 distinct positions and 11
shared-edge components. Zero exact triangle and zero position matches remain
against all PC compiled draws at .001. Independently matching 22,679 other source
positions and 420 ordered route points support the common frame. Near underlying
ground is not the same 3D puddle surface. The evidence remains additional authored
PS2 puddle source geometry in the examined landscape, without a live LOD claim.

France1 reproduces 3,586/3,586 selected water faces, then extends to ordinary ground
and foliage groups. Ground node 3613136 maps 441 faces to PC draw 519. A bounded
pinetree group becomes fully exact at relaxed .01; the baseline records partial
and equivalent coverage rather than calling it extra vegetation. Tyre node
3564909 is particularly instructive: 47 baseline unmatched faces disappear when
all 384 become exact at .01. It is not evidence of additional PS2 tyres.

ItalyS1 reproduces 1,329/1,329 water faces with PS2 puddle versus PC water source
metadata. Its ordinary hard-dirt node 3758051 maps 336 faces to draw 530. Italy's
route has two differing points among 292 compared; 290 agree exactly and the
largest outlier is 26.822 source units. That local route difference is preserved,
not used to fit a course transform. Both landscape matrices are identity, and
the independent non-water original-byte geometry probe corroborates alignment.

# Novel non-water evidence

The strongest selected candidates stay unmatched in strict, baseline and relaxed
profiles: Turkey3 rustic Hut node 3429766 (139 faces), boat1 node 3583641 (113),
TURshrub2 node 3620664 (256), and ItalyS1 pinus2 node 3706566 (64). Their source
owners, offsets, slots, bounds and areas are retained in the compact delta map.
These are source mesh groups, not counts of huts, boats, shrubs or trees. PC may
contain related families elsewhere, and active alternative/LOD ownership still
needs investigation. No unsupported top-ten scenery inventory is inferred.

Materials are a separate relation axis. Shared geometry can carry different
water/puddle shader metadata or different texture-slot bindings, including ground
noise. Later non-null maps retain their original slots. PC TXT material candidates
can be ambiguous; a named moMesh and its source Index/Size are not assumed to
index compiled DX faces. Identical names do not prove identical final pixels.

# Objects and static duplication

The exact blue/red standalone dinghy PSMs share their position-bank bytes. Each
has 60 source vertices, two tag2 material meshes and 24 nonsuppressed faces. Their
observed ffffffff EOF sentinel is a narrowly tested extension, not permission to
guess arbitrary model tags. Model-local coordinates remain separate from world
coordinates.

France1 authored red/blue entities use gaEntitySpline and boatlist1/boatlist2.
AMBIENT1's proved route-to-world-matrix publication explains why authored zero
Row3 is not an instance-placement oracle. No runtime pose capture was attempted.
PC dinghy-textured draws 897/904 positively contain baked course geometry: 261
faces and 31 coordinate-edge components. TXT's 11 hull and 11 mast names are
mesh leads, not a validated boat population or direct draw mapping.

A representative PC component spans 13.5454 units between points, greater than
the entire PS2 model's 9.1370 maximum separation. It cannot be identical unscaled
rigid geometry. Compatible object family, unknown scale/partition and unknown
placement correspondence are recorded separately. Adding a moving counterpart
later risks duplicate scenery, but hiding whole PC draws now would be unjustified.

# Vehicle feasibility

Exact retail Tata/car.dx and KiaSportage/car.dx were available. Reusing REFL1 and
PC parse_dx gives useful identity-frame common subsets: 1,442 of 2,016 Tata PS2
source faces and 1,739 of 2,289 Kia match at .001. Bounds and source hashes are
recorded. Wheels, menu models and complete.dx were excluded. Conditional CAR.PSM
parts remain source alternatives; a full part/LOD/damage mapping is outside GEOM1.

# Portability and inspectable evidence

Shared water often needs material/renderer work, not new mesh data. Turkey3
puddle source additions may later require visual-course delivery as well as the
WATER1 material contract. Robust non-water candidates need ownership research
before content transfer. Baked dinghies need instance correspondence before any
replacement/controller plan. Visual and collision deltas remain independent.
Nothing was written into playable PC data, the Course SDK or the renderer.

The three source-coordinate SVGs and Turkey3 PNG make local deltas inspectable.
They stay ignored because they reproduce original geometry. Their top-down
projection collapses height and has arbitrary diagnostic layer order; it cannot
establish runtime visibility, LOD, poses or pixel equivalence. The committed
versioned map has 90 selected compact records and actual counterpart metadata;
full relations stay local. HANDOFF.md supplies dependencies and regeneration
commands without proprietary source meshes.

# Known limitations and next recommendation

Unsupported PSM tags fail closed. Source flags, ancestors and strip scale are
preserved without guessed selection semantics. Source normals/UVs are not used
to fabricate runtime lighting or culling. No global relocation/instance search,
universal 36-course decoder, complete TXT-to-DX face map or runtime draw capture
is claimed. Double-precision diagnostic math is not PS2 FPU/VU emulation.

All 23 acceptance gates are bounded in validation.md. Original input identities,
SDK/renderer preservation, full/isolated tests and deterministic hashes are
recorded separately from runtime. Exactly one next recommendation is
**PS2-DRESSING1**: establish grouping, alternatives and scene ownership of the
stable non-water candidates. It has not begun. GEOM1 ends at research closeout.
