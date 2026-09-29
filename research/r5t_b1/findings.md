# R5T-B.1 findings: GXM geometry and controlled cooker proof

## Verdict

**MORE WORK NEEDED.** A bounded GXM float3 bank spatially correlates with
cooked course DX in three same-build source/compiled pairs, and a candidate
source-to-Blender identity transform follows from existing coordinate
conversions. France1's startpoint candidate is visualized in the existing
Blender add-on as eight points only. A one-float source edit and two isolated
runtime cohorts are prepared, but the mandatory three baseline plus three
modified cooks have not been captured. No compiled or runtime effect is
claimed.

## Geometry evidence

The source table remains cross-validated by exact paired TXT node names,
classes, parentage, unknown-node child counts, and mesh spans for Demo 8.4.1
France1 and Italy1. The new bounded float3 reader uses header word 7 and the
measured table boundary; it does not assign those points to each node.

| Pair | DX revision | Source nodes | Finite float3 points | Exact DX position matches | Within 1 unit | Best source-to-DX transform |
|---|---:|---:|---:|---:|---:|---|
| France1 | 127 | 2,322 | 49,278 | 6,366 | 36,081 | `(x, z, -y)` |
| Italy1 | 127 | 1,117 | 34,048 | 6,517 | 28,568 | `(x, z, -y)` |
| Developer Boinds | 125 | 17 | 4,933 | 38 | 4,749 | `(x, z, -y)` |

All 48 signed axis permutations were tested. These are point-set matches, not
per-node matches. The existing DX-to-Blender transform `(x, -z, y)` composes
to source-to-Blender identity. Both source-to-DX and composed source-to-Blender
are `HIGH_CONFIDENCE_INFERENCE`; source node transforms and per-node geometry
membership remain `UNKNOWN`.

For France1, the `startpoint` `moMesh` record is ordinal 1, parent 0,
`Index 0`, `Size 12`. The first eight points are the eight corners of a
10-unit axis-aligned box. Its DX-space center is
`(-982.05554, 53.53905, 468.66672)` and is 1.559 units from Demo 9.10
RaceTest Marker 0. This is spatial correlation only. Face connectivity,
source index semantics, and the exact node-to-pool link are unresolved.

## Small developer oracles

Current inputs contain source GXM for GordonTrack flatTrack/track,
RussiaTurkey1, Boinds track01, and collisiontests crack/crack2. Only Boinds
has a complete GXM/TXT/cooked-DX pair. It is useful for global coordinates and
small source/cooked structure; it does not isolate `$bsp`. The other samples
lack paired TXT and/or DX, so companions were not guessed or generated.

## Controlled experiment status

An ignored scratch copy of 8.4.1 France1 changes one float only: source point
0 X, at byte offset `10,838,403`, from `-987.0555419921875` to
`-986.0555419921875` (+1.0). The original GXM/TXT/GXI corpus is unchanged.
Independent Demo 9.10 runtime clones are staged for baseline and modified
cohorts; each has identical runtime EXE bytes and the France1 DX plus 66 DXT
cache outputs cleared. Their source manifests differ only in the recorded
GXM change.

R5T-B previously captured two forced cooks of identical source. Both render
prefixes passed validation but varied in vertex/triangle/draw counts, while
the 10,118,248-byte tag100 region hash and all 172 non-DX files matched.
This is why R5T-B.1 requires at least three independent cooks in each cohort.
The new variance-aware comparer rejects non-identical within-cohort inputs and
labels differences relative to baseline variation. Actual six-run evidence is
still pending in the current workspace.

## Subsystem status

- `$bsp`: source hierarchies/spans and retail tag100 boundaries are inventoried;
  no controlled BSP edit or source-to-tag100 mapping was made.
- Startpoint: one candidate point edit is staged; compiled destination and
  runtime effect are unknown pending the six cooks.
- Foliage: source directive and compiled flag differences remain correlation;
  no controlled source material edit was cooked.
- Raceline and limits/boinds: exact names/spans are inventoried, but point
  ordering and compiled mapping are unknown.
- SFL: no spatial registration evidence was added; dimensions/header meanings
  and historical FL/SF relation remain as documented in R5T-A.
- XML: existing marker/split-time parser and read-only Blender overlay remain
  unchanged. Marker proximity to the candidate startpoint is not a binding.

No course DX/BSP/SFL/route/surface writer, custom layout, registry change, or
EXE patch was added. Vehicle SDK v1 is unchanged.

## Evidence artifacts

- [`gxm-geometry.md`](gxm-geometry.md) / [`gxm-geometry.json`](gxm-geometry.json)
- [`multi-cook-method.md`](multi-cook-method.md)
- [`blender-validation.md`](blender-validation.md)
- [`startpoint.md`](startpoint.md)
- [`bsp-source-compiled.md`](bsp-source-compiled.md)
- [`foliage-alphatest.md`](foliage-alphatest.md)
- [`raceline.md`](raceline.md)
- [`limits-boinds.md`](limits-boinds.md)
- [`sfl-registration.md`](sfl-registration.md)
- [`runtime-test-plan.md`](runtime-test-plan.md)
