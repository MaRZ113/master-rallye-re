# Forester native-source qualification

**Status:** Native source cook and runtime model use are confirmed for this
Forester source under the temporary Mercedes runtime namespace. Static
cache-only validation passes for a Forester-named package. A Forester-family
cache-only runtime test remains pending.

## Source identity

The exact source bytes match across the 9.3.1 source folder, the source copies
associated with the R-COOKER2 comparison, and the 9.10.0 input folder:

| Role | Original source filename | Size | SHA256 |
|---|---|---:|---|
| `car` | `car.gxm` | 219,728 | `3d27573a2358f379de1c1914fb6a17ac525a5a709bd62ab824736d05ac4c2535` |
| `complete` | `comlplete.gxm` (staged as `complete.gxm`) | 257,541 | `3fa2cff8c100b66236b1f076c164a402ac199fe3502838e0bc18be8a381b790f` |
| `wheel` | `wheel.gxm` | 27,272 | `2f1542430065108649a4629f613493de85332e15a7755dda96ce66d79ea3e48d` |

The spelling `comlplete.gxm` is the corpus filename typo. Its staged
`complete.gxm` copy has the same SHA256; the authoritative input was not
renamed or modified. Every role prefix is supported by the current inventory
reader. The three source identity comparisons are `CONFIRMED_BY_BYTES`.

Machine-readable details and actual comparison paths are recorded in
[forester-cross-strategy.json](forester-cross-strategy.json).

## Native outputs

The current collected package under the ignored R-COOKER3 output tree passes
the canonical package validator: 3 revision-135 DX, 23 parseable required DXT,
no DX parser warnings/errors, and no GXM/GXI in the portable package.

| Role | Size | SHA256 | Parsed counts and collision |
|---|---:|---|---|
| `complete.dx` | 138,687 | `852d2188d8ee3913ea366a684ca818b1e51bed61e4c4b685308dee3939153aa7` | 2,649 vertices; 2,328 triangles; 15 draws; tag102 |
| `car.dx` | 128,522 | `27217ef5129dbb84f4237308400a0285babba12988f9d27eb6ffa8248f187492` | 2,459 vertices; 1,864 triangles; 15 draws; tag101, Rep A 8/12 and Rep B 30/56 |
| `wheel.dx` | 13,002 | `ce2b6557cbd8975ec14d1c20a4d3df902512a3433c713dc3822f09bfd35ca01c` | 220 vertices; 252 triangles; 5 draws; tag102 |

All 23 native-package DXT hashes match the corresponding source DXT bytes.
They were copied/reused, not recooked. A separate family-scoped cache-only
package was assembled at the ignored path
`.research-output/r-cooker3_1/forester-cache-only/DataGx/Vehicles/Forester/`.
It contains only those three DX files and the 23 required DXT files. The
package validator reports `PASS` for 26 total files.

## Runtime observations and scope

The project operator reports:

- Forester model appeared in Vehicle Select;
- race loaded and the model worked;
- collision and damage worked, including external/internal damage;
- normal driving was observed.

These observations are `CONFIRMED_BY_RUNTIME` with provenance
`USER_SUPPLIED_RUNTIME_OBSERVATIONS`. The native-cook harness mounted the
Forester model under runtime family `Mercedes`. This confirms that the cooked
Forester model/collision resources are usable in the tested runtime path. It
does **not** confirm that the runtime used authentic Forester physics
configuration.

The cache-only Forester-named package has static validation only. Runtime
absence of Forester GXM/GXI and historical-path dependency has not yet been
observed; see [the short test plan](forester-cache-only-runtime-test.md).

## Cross-strategy comparison

All three GXM role files were byte-identical between the 9.3.1 and 9.10.0
source copies. Their official 9.10.0 outputs and their R-COOKER2 candidates
were compared with the native retail output.

- All roles have revision 135, matching vertex/triangle/draw counts, exact
  render positions/normals/colors/UVs, exact local and global indices between
  native cook and minimal R-COOKER2 candidate, and matching draw texture
  references.
- Native `complete.dx` and `wheel.dx` are byte-identical to their R-COOKER2
  candidates, including tag102 collision bytes.
- Native `car.dx` differs from R-COOKER2 in tag101 collision bytes only. Its
  base scalar is bit-identical at `2.6695199012756348`. Rep A/B triangle
  topology, edges, adjacency, and face loops are equal. Maximum observed
  component deltas are about `1.2e-6` for Rep A and `5.5e-6` for Rep B;
  face-scalar drift is at most `5.5e-6`.
- In that car tag101 comparison, 4 Rep A and 10 Rep B secondary descriptor
  lists differ; 6 Rep B differences are pure permutations. These fields remain
  semantically unresolved and are not normalized away.
- R-COOKER2 versus official 9.10.0 differs only in the local uint16 index
  array for each role: car 7,134 bytes; complete 8,221 bytes; wheel 675 bytes.
  The existing R-COOKER1.2 per-draw triangle-set checks establish equivalent
  oriented topology, while the official local ordering differs. The official
  trailing/global index table remains equal to the rev131-derived table.
- Native Forester matches the minimal R-COOKER2 render/index path. Native car
  collision is recomputed and therefore differs from the official/R2 car
  tag101 bytes as described above; it is not an unexplained render or topology
  change.

Evidence is limited to this source family and these three resources. It does
not establish arbitrary GXM support or full tag101 secondary descriptor
semantics.

## Qualification decision

**SECOND INDEPENDENT FAMILY QUALIFIED FOR THE RETAIL-NATIVE GXM STRATEGY** for
the exact Forester source and cook harness tested. Keep a separate status of
**Forester-named cache-only runtime portability: PENDING** until the package
loads with GXM/GXI and the historical authoring path absent from the Forester
namespace.
