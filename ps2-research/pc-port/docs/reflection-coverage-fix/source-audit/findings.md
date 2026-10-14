# Missing reflective source-panel audit

Read-only, canonical original PS2 PackFS and protected retail PC DX. Existing
PSM visual-strip and Course SDK parsers are reused. No runtime identity, renderer
code, original data, or previous frozen findings are changed.

## Scope and result

The twelve requested exact-name families were processed in 3.9 seconds. Forester /
Wooldand is independently investigated by the other source-mapping workstream.
All PC physical draws were inspected, including slot1 Null/glass/rubber and flags
other than 00000101. Matching never requires texture names to agree.

`registry-additions.json` contains **29 additional unique-family PC draw hashes**:
27 have complete unsigned nondegenerate-triangle coverage against unconditional
PS2 carshiny meshes; two more have complete strict coplanar surface coverage.
All 78 original retail vehicle DX files were scanned for digest collisions, with
no decoder failures or cross-family collisions. Runtime race/body owner and
current buffer/texture generations remain mandatory.

| Vehicle | Additional complete source records | Number |
|---|---|---:|
| LandCruiser | 13,14,16,21,22 | 5 |
| Tata | 3,7,9,12,15,28 | 6 |
| ChevyBlazer | 4 | 1 |
| Xtrail | 13,21,22 | 3 |
| Navara | 5,23,24 | 3 |
| Jump | 8,19 | 2 |
| Patrol | 10 | 1 |
| Bruno | 17 | 1 |
| SeatBuggy | 12,23 | 2 |
| Kamaz | 6,10,11 | 3 |
| IceCream | 14,15 | 2 |
| Ufo | none; original two complete source records already registered | 0 |

The two additional LandCruiser surface joins are explicitly STATIC_INFERENCE
with strict plane distance .001, absolute normal agreement .99999 and coverage
.99999. Inspect the structured output for actual record IDs; the compact table
is informational and does not define the live predicate.

## Why the original source audit missed records

* PC slot1 exclusions happened before shape matching, losing actual original PS2
  carshiny surfaces whose PC material has Null or glass as the secondary texture.
* Identical slot0/slot1 texture names were required as a prefilter. This excludes
  verified geometrically identical surfaces with platform texture differences,
  including ChevyBlazer draw4 and SeatBuggy draw12 painted surfaces.
* PC raw triangle counts were compared against PS2 **nondegenerate** triangles.
  Tata draw12 has 112 PC triangle records but only110 nondegenerate triangles;
  all110 match the original PS2 root carshiny mesh. The live digest continues to
  include all112 records, retaining exact original draw identity.
* One complete PS2 root mesh was required for an entire PC draw. LandCruiser16,
  Tata3 and Patrol10 combine faces from several unconditional root meshes, all
  independently proved carshiny mode3.
* Flags00000101 excluded Xtrail and Jump light records with01000101 despite
  their actual original PS2 carshiny source ownership. This does **not** authorize
  changing alpha-test handling; native state/semantics must be considered by the
  renderer integration workstream.

## Distinct source-vertex material joins

`vertex-material-candidates.json` contains Jump1, Jump2, Bruno5 and IceCream4.
Every unique PC nondegenerate position matches an original unconditional PS2
carshiny material-owned source strip position within .001. Existing PC faces
retain different topology or source strip suppression; these are **not** promoted
to complete triangle/surface equivalence. The exact PC compiled draw digest and
unique vehicle ownership are independently established. Their remaining PC
faces are not proved to be equivalent actual PS2 emitted primitives.

This particularly explains why a source-only all-triangle registry could omit
IceCream's main iceside group (487/502 exact triangles,318/318 material-owned
positions), even though all of its source positions belong to PS2 shiny material.
It does not explain whether runtime state gates also reject the existing records.

## Still-partial principal panels

LandCruiser8 and9, Xtrail1, Navara3 and4, Patrol1 and2, Bruno4, SeatBuggy7,
Kamaz13 and ChevyBlazer7 remain partially geometrically different. They are **not**
silently accepted by this audit. `source-coverage.json` retains exact matched
face counts, unique position counts and bounds of unmatched positions.
Examples: LandCruiser8 215/240 triangles,168/170 positions; LandCruiser9
373/477,289/349; Navara3 672/674 nondegenerate faces,543/544 positions;
Kamaz13 312/318,192/193. Actual topology/position differences require a separately
qualified material-level correspondence rather than pretending exact geometry.

Driver helmets are a useful negative control: their PC secondary texture is
whitepaint, but none of their positions match unconditional PS2 carshiny source
meshes. No helmet is admitted by either proposal.

26 conditional child candidates remain outside the complete root proposal.
These include brake-light and windscreen state alternatives. Child wrapper,
live visibility and material lifetime semantics are preserved as unresolved.

## Validation and reproduction

```
python ps2-research/pc-port/docs/reflection-coverage-fix/source-audit/audit.py
python -m unittest discover -s ps2-research/pc-port/docs/reflection-coverage-fix/source-audit -p test_audit.py -v
```

Five focused metadata/known-answer checks PASS, including29-record subtests.
Canonical PS2 hashes are checked through the existing verifier; exact decoded
payload and protected retail DX hashes are preserved in every proposal. No full
mesh arrays, image data or proprietary binaries appear in the reports.

These outputs are source evidence, not proof that an overridden native draw
executed, nor visual parity or complete-body coverage in the actual frame.
