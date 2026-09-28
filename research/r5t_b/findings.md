# R5T-B findings: course cooker and source semantics

## Verdict

**MORE WORK NEEDED.** The 9.10.0 runtime cooker bridge is reproduced twice on
the same France1 source in an isolated clone, the render parser validates both
outputs, an exact paired GXM/TXT node-table reader now covers 8.4.1 France1 and
Italy1, and the existing Blender add-on can overlay RaceTest XML markers.
However, no controlled source edit was made. GXM transforms/geometry arrays,
SFL spatial mapping, and source-helper compiled destinations remain unresolved.

## Confirmed findings

- **`CONFIRMED_BY_RUNTIME`:** launching the Demo 9.10.0 runtime and selecting
  France1 triggers a cook when the DX/DXT caches are absent. The user supplied
  screenshots show `Loaded Successfully`; owner evidence says recooked 8.4.1
  France1/Italy1 run with AI and retain old start/grid behavior.
- **`CONFIRMED_BY_BINARY`:** both forced France1 outputs are revision 135 and
  pass complete course render-index validation. They differ in DX hash, vertex,
  triangle, and draw counts. Their raw 10,118,248-byte tag100 payload is
  identical.
- **`CONFIRMED_BY_CORPUS`:** 172 non-DX France1 files (66 DXT, 104 GXI, GXM,
  TXT) are byte-identical across the two observations and match source hashes.
- **`CONFIRMED_BY_SOURCE_COMPILED_PAIR`:** all 2,322 France1 and 1,117 Italy1
  old GXM node records match paired TXT names/classes/spans; encoded unknown
  child counts match TXT braces. Transform and coordinate fields are not
  parsed.
- **`CONFIRMED_BY_CORPUS` + `CONFIRMED_BY_BINARY`:** old France source
  lacks `$alphatest`/`$shader(tree)` strings; late source contains them. Old
  source recooked foliage candidates use `01000101` flags; native late tree
  candidates predominantly use `01010101`. This does not establish that an
  alpha-test change fixes the observed occlusion.
- **`CONFIRMED_BY_BINARY`:** the current RaceTest XML reader extracts 583
  France1 and 277 Italy1 marker positions and three split-time records per
  course. Every marker lies within the corresponding Demo 9.10 DX vertex AABB.
  A shared coordinate frame is a `HIGH_CONFIDENCE_INFERENCE`.

## Differential tool and Blender work

`mrtool diff-course BASE MODIFIED` compares DX render sections/material flags/
root and batch shapes/tag100 hashes, TXT materials/nodes/spans, paired GXM node
tables, HNT entries, XML nodes/attributes, SFL changed-cell bounds, and hash-only
DXT/GXI files. Inputs are never changed. Synthetic tests cover the structural
parsers and semantic diff.

The existing Blender add-on now has **Import RaceTest XML Markers**. It adds
neutral marker empties into a separate course collection, uses the established
coordinate conversion, and preserves original XML values. It does not decode
startpoint, raceline, limits, boinds, BSP, or SFL geometry.

## Separate unknowns

- **Render-sort BSP:** cooker log shows sort-plane generation and plane-choice
  warnings. It is kept distinct from tag100.
- **DX tag100:** same raw payload hash across two recooks; internal boundary and
  meaning remain unresolved. `$bsp` causality was not isolated.
- **Foliage:** draw splitting is strongly correlated with old blended source
  candidates, but no source-side material probe or runtime fix candidate was
  prepared.
- **Startpoint/route/bounds:** exact source nodes/spans exist; source geometry
  coordinates and transforms do not. No source edit or runtime candidate is
  ready.
- **SFL/FL/SF:** R5T-A structure remains; R5T-B inputs lack raw fields/TGAs for
  spatial registration, and unknown header values do not justify stretch-to-
  bounds overlays.
- **Developer tracks:** the small isolated GXM/TXT oracles listed in the plan
  are not present in the current local inputs.

No course writer, layout edit, registry patch, or executable patch was added.
Vehicle SDK v1 history is unchanged. See `runtime-test-plan.md` for gated next
experiments and `research/r5t_b/` machine reports for exact counts/hashes.
