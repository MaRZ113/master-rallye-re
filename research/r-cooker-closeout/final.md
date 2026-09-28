# R-COOKER final closeout

**Status: CLOSED — practical demo vehicle DX compatibility problem solved for
the supported vehicle revision-131 grammar.** This is not a claim that every
historical field in GXM, GXI, DXT, or the original cooker has been
reverse-engineered.

## Phase progression

| Phase | Final status | What it established |
|---|---|---|
| R-COOKER1 | CLOSED | Controlled same-source Trooper comparison between Demo 9.3.1 revision 131 and Demo 9.10.0 revision 135; established the main differences in draw serialization and local index order while tracking provenance and structural comparisons. |
| R-COOKER1.1 | CLOSED — `CONFIRMED_BY_RUNTIME` | A rev131-only Trooper candidate changed the revision and reserialized draw prefixes while preserving local triangle order; all three vehicle resources loaded in retail. The official triangle reorder was unnecessary for those tested resources. |
| R-COOKER1.2 | CLOSED — `CONFIRMED_BY_RUNTIME` | Reused the generic converter unchanged for same-source Forester car/complete/wheel resources; all three no-reorder candidates loaded in retail. This extended runtime evidence to a second vehicle family. |
| R-COOKER2 | CLOSED | Productionized the supported rev131-to-rev135 converter, with strict preservation checks, structured reporting, and single-file/directory CLI modes. |
| R-COOKER2.1 | CLOSED — `PRODUCTION_READY` | Separated strict generated-output validation from existing official rev135 validation, added deterministic corpus scanning, and regenerated current corpus coverage. |

Historical reports preserve what was known at each stage. This summary records
the final conclusions without rewriting earlier evidence chronology.

## Frozen rev131-to-rev135 transform

For supported vehicle DX revision 131, the tool:

1. changes the header revision from 131 to 135;
2. replaces each 11-byte prefix `A B C | u32 X | u32 texture_slot_count` with
   `u32 1 | u32 0 | float32 1.0 | A 00 B C | u32 X | u32 texture_slot_count`;
3. preserves geometry, positions, normals, UVs, colors, texture references,
   draw cores, local uint16 index order, collision, bounds, hierarchy and
   other non-render data, and trailing/global data.

The official Demo 9.10.0 local triangle reorder is intentionally not
reproduced. It was unnecessary for the tested Trooper and Forester candidate
resources. This is a retail compatibility transform, not a byte-for-byte
recreation of the official cooker.

### Current corpus result

The scanner command is:

```powershell
python tools/scan_dx_131_135_corpus.py inputs --json research/r-cooker2/corpus-coverage.json --markdown research/r-cooker2/corpus-coverage.md
```

The regenerated report records:

- 8 vehicle families; 36 DX file instances; 35 unique DX payloads.
- Revision 131: 21 instances, 20 unique payloads; all 20 converted and passed
  strict generated-output validation.
- Revision 135: 15 instances, 15 unique payloads; all 15 passed the
  existing-input policy, including the observed local/global index ordering
  divergence.
- 10 source-GXM-hash-verified role pairs; 2 same-family/role pairs have
  different source hashes and remain unverified; 12 outputs have no paired
  counterpart.
- 135/135 direct draw-prefix records matched; zero formula mismatches.
- All 10 verified candidate/official comparisons differed only in local
  triangle ordering; no additional differences were found.
- Six generated DX hashes match runtime-tested Trooper/Forester candidates;
  the other 14 unique rev131 payloads are structurally supported only.

Duplicate file instances are counted separately from unique SHA256 payloads;
duplicates are not treated as independent format evidence.

## Final asset-format status

| Area | Status for current restoration goals | Evidence and boundary |
|---|---|---|
| Vehicle DX rev131 → rev135 | **SOLVED FOR SUPPORTED VEHICLE DX** | `CONFIRMED_BY_BYTES`, `CONFIRMED_BY_CORPUS`, and `CONFIRMED_BY_RUNTIME` for the supported grammar and exact runtime-tested candidates. |
| DXT | **SUFFICIENTLY CHARACTERIZED FOR RESTORATION; NO CONVERSION REQUIRED BY CURRENT EVIDENCE** | Tested paired texture controls did not require a separate revision-compatibility transform. DX Upgrader does not rewrite DXT; retain/copy package textures unchanged. This does not claim every historical DXT variant has been analyzed. |
| GXI | **SUFFICIENTLY CHARACTERIZED; NON-BLOCKING** | Useful header/pixel and conversion relationships are established for the inspected corpus. Complete GXI format reconstruction is not required when already-cooked supported DX files are available. |
| GXM | **PARTIALLY CHARACTERIZED; FULL RE NOT REQUIRED FOR CURRENT RESTORATION GOALS** | Source-side geometry, materials, texture references, hierarchy, `$chull(...)`, and `$cylinder(...)` information are documented to varying confidence. The original 9.10.0 cooker remains a source-side bridge when starting from GXM/GXI. |
| Original cooker executables | **NOT REQUIRED** to convert supported rev131 vehicle DX; **STILL USEFUL** for source-only GXM/GXI and historical research. | No further broad cooker executable analysis is planned for the current restoration roadmap. |

## Frozen R-COOKER decisions

1. Convert supported vehicle DX revision 131 directly to revision 135.
2. Do not reproduce the official 9.10.0 triangle optimizer.
3. Preserve the original revision-131 local triangle order.
4. Apply strict validation to output generated by this upgrader.
5. Accept an existing official rev135 local/global order divergence only when
   the triangle topology and all other structural checks remain valid.
6. Do not convert DXT.
7. Do not require full GXM/GXI/original-cooker reconstruction for the current
   vehicle-restoration goal.
8. Change these decisions only when new evidence justifies the change.

## Release and roadmap

The standalone **Master Rallye DX Upgrader v0.1.0** is packaged separately
from Vehicle Composer. Its release archive contains only allowlisted tool
code, documentation, and the MIT license; it contains no game assets.

Release candidate details:

- Archive: `MasterRallye-DX-Upgrader-v0.1.0.zip`
- SHA256: `3b1fa71f587fc3053b62eccbdf71c8225867883a90109f7dd1a9fdf547c43fcb`
- Size: 49,065 bytes; 19 files
- Validation: allowlist/content validator and clean-extraction CLI/README smoke
  tests passed.

The practical cooker/asset-pipeline compatibility work is closed. The original
cooker remains useful when the available source is GXM/GXI, but broad
historical-format reconstruction is non-blocking and out of scope. The next
major research direction is R5V vehicle roster capacity expansion; no R5V
implementation is part of this closeout.

## Final closure

The practical Master Rallye demo vehicle cooker-compatibility problem is
considered closed for the supported vehicle DX revision-131 grammar. Such DX
files can be converted directly to retail-compatible revision-135
serialization without running the original 9.10.0 cooker. The original
cooker remains useful for source-side GXM/GXI work and historical research.
Further broad GXM/GXI/cooker reverse engineering is not required by the
current vehicle-restoration roadmap. This closure does not imply that every
historical asset-format detail is known.
