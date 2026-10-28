# GT Garage Lab — execution and evidence plan

Worktree: `master-rallye-re-vehicles`, branch `research/vehicles`.
Baseline: `9416ddbc976da283964ab0ea621884b1789e0fe4`.

1. Audit existing stages, freeze accepted Lancer/Subaru/Pajero and protected-file
   hashes. Review local GT2-to-GT4 research without copying its vendor snapshot.
2. Implement read-only GT3 inventory, exact catalog/model associations and
   original palette/material colorway records; bounded resumable checkpoints.
3. Qualify separate GT3 adapter using shared VIF/GS primitives. Preserve unknown
   GT3 lighting, masks and instance state. Verify native claims against original
   CORE and independent R5900 decoding; never import GT4 defaults as GT3 facts.
4. Compile semantic Classic recipes from explicit approvals; retain the existing
   Lancer recipe as an immutable output oracle. Unknown surfaces stay intact.
5. Pilot a different GT3 vehicle and actual source colorways, integrate project
   selection/history and isolated build. Render concrete comparisons before
   requesting the existing exact Classic report approval for game build input.
6. Repeat Windows/module regressions, source/archive audits, document evidence
   levels and owner tests, then commit validated phases locally. No publication.

Private evidence: `.research-output/vehicles/gt-garage/`.
Native scratch: `vehicles_scratch/gt_garage/` (ignored).

## Current audit findings

- The early `vmesh_gt3_to_dx.py` reproduces V-MESH1, deliberately discarding GT
  texture/UV semantics. It cannot serve as the universal fidelity importer.
- Later Subaru helpers contain reusable UV/atlas/topology/wheel components, but
  classification, repairs, donor placement and source selectors remain specific.
- GT4 already separates command, geometry, GS texture and material interpretation;
  share primitives, not its ModelSet2 hierarchy or unproven native defaults.
- Existing Classic low-level topology, wheel shelf, material copy and texture
  binding operations are reusable. Version-1 orchestration requires Lancer-pinned
  hashes, selectors and paint regions. Do not apply that default recipe elsewhere.
- GT2-to-GT4's vendored MR modules are an older pinned snapshot, not replacements
  for current files. Its race PAT/menu palette incompatibility is relevant to
  source colorways; its edited Evo III assets are not inputs for this milestone.

## Read-only source findings (not runtime acceptance)

- Local GT3 volume: SCUS_971.02 / NTSC boot metadata. VOL SHA256
  `27c84369911bf2352bbe5f6ba21830357c23cd82fe529b25c38c22986d37fa88`.
- 5,333 RoFS members; 574 day/night model members; 572 structural parses,
  562 distinct decoded hashes among those parses. Two tiny `ho0100` members
  decode to empty data and are MISSING INPUT. These are not 562 successfully converted vehicles.
- Catalogs: US244, EU244, JP242. Exact GTAR CAR table30 u64@48 → table5 key@0
  → model key@24 → IDDB → exact member resolves US244, JP242, EU231.
  Thirteen EU model references are absent in this US volume; no alias guessing.
- Owner approved Clio V6 `re0011` as the GT3 pilot: four original colors. Viper
  remains an explicit unsupported CLUT diagnostic case, not a substituted pilot.
- Selected Viper body model0/LOD0, lights-off diagnostic branch: 2,881 triangles.
  This includes source multipasses; it is not a final MR render count.
- Native CORE `fdcea2aa...` shape submitter at `0x24e4a0` writes STMASK
  `0xc0c0c0c0` ahead of descriptor DMA. Ghidra R5900 and 16 Rabbitizer instruction
  cross-checks agree. UV XY lanes remain DATA; unknown editions fail closed.
- PSMCT16 source CLUT handling and GT3-only VU lighting still need qualification.
  Strict import rejects unsupported palettes; diagnostic mode records affected
  draws instead of silently making them opaque or inventing texture samples.

Source Fidelity candidate is built and statically validated at gt-garage/t/sf.
Corrected Clio Classic report c38d712c is explicitly approved and built. No gameplay qualification claimed.
The automatic importer was synchronized without rollback; owner-approved UV
gating is now enforced in derivation and decoding. Actual GUI creation/color
history and shared project builds passed; see GT_GARAGE_RESULTS.md.

Final owner-feedback corrections: Y=.188m presentation hubs; original source-
qualified bonnet environment coverage; explicit windscreen orientation and
banner-free side/rear optical sampling. See GT_GARAGE_RESULTS.md.
