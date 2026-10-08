# PS2-DRESSING1 findings

PS2-DRESSING1 STATUS: COMPLETE at the bounded static ownership level.
RUNTIME_VALIDATION: NOT_PERFORMED. This does not establish object populations,
selected live LOD, or visual parity.

The four GEOM1 candidates are material-owning landscape source groups, each
under a tag5 parent, one tag6 selector and the tag1 root. They contain no
serialized per-object matrix. Their source parents contain different materials;
neither a parent nor one disconnected component is a proved scenery instance.

| Candidate | Source faces | Strips | Shared-index components | Welded-vertex components | Whole-edge components |
|---|---:|---:|---:|---:|---:|
| Turkey3 TURshrub2 | 256 | 14 | 64 | 16 | 16 |
| Turkey3 rustic Hut | 139 | 13 | 53 | 11 | 12 |
| Turkey3 boat1 | 113 | 12 | 51 | 7 | 7 |
| ItalyS1 pinus2 | 64 | 5 | 28 | 3 | 4 |

All four have zero exact world-position triangle matches at 0.001 against all
paired PC compiled draws. The conclusion becomes more useful after shape search:
three 20-face hut components have congruent unit-scale rotated/translated
counterparts in PC Turkey3 draw627. More strongly, the whole113-face boat group
fits a subset of PC draw825 under one common proper rigid transform. Every
source corner and face is verified, with errors below0.001 (whole boat maximum
0.000394). These are fitted geometry relationships, not authored instance
transforms. Hut/boat families
therefore cannot be declared absent from PC.

The ELF creates bounding wrappers around tag6 children, builds child-index and
generation-stamp vectors, selects children using model-owned region data and
the view, then applies a sphere range/direction/side-plane test before ordinary
child traversal. This establishes culling ownership; no separate LOD alternative
is proved for these four source paths. See [hierarchy-runtime](hierarchy-runtime.md).

France1 independently distinguishes two PS2 gaEntitySpline scene references
from PC baked dinghy geometry. A unit rigid exact-face search finds no local
model correspondence; per-instance placement and safe hiding remain NOT_READY.
The optional single supplementary family is ItalyS1 haybales:14 authored
references,13 unique matrix hashes, with duplicate records preserved.

The [four complete candidate cards](novel-candidates.json),
[count/ownership inventory](dressing-inventory.json) and
[ELF probes](elf-functions.json) retain source hashes, bounds, ancestor offsets,
materials, controls, grouping methods, PC scope and explicit unknowns.
No new count of trees, houses, boats or simultaneously visible objects is claimed.
