# R5T-F.1 — tag100 reciprocal region swap

**Status: PASS.** The reciprocal runtime swap completed after the static
preparation below. For the tested France1 `COLLIDE_finishline03` state, runtime
physical collision followed the selected donor region beginning at tag 100.
R5T-F.2 later parsed that region as a tag100 tree followed by separate 1339
and 1400 records. The tested source-plane family is found in the tag100 tree,
but F.1 did not independently hold the later 1400 region fixed. The runtime
result is therefore bounded to the whole tag100-starting suffix and this
tested source state; it does not establish a general tag100/BSP identity.

## Final reciprocal-swap runtime result

Both hybrids loaded with the visible finish geometry at its original location,
and `RACE COMPLETE` still triggered at the unchanged FinishArea.

| Hybrid | Prefix donor | tag100-starting suffix donor | Old right-support collision | New translated collision | FinishArea |
|---|---|---|---|---|---|
| A | baseline | modified | absent | present | unchanged; race completed at original area |
| B | modified | baseline | present | absent | unchanged; race completed at original area |

The reciprocal suffix result is **CONFIRMED_BY_SOURCE_RUNTIME_EDIT**,
**CONFIRMED_BY_COOKER_DIFFERENTIAL**, **CONFIRMED_BY_RECIPROCAL_REGION_SWAP**,
and **CONFIRMED_BY_RUNTIME_TEST**. For this tested source mesh, the selected
tag100-starting suffix carries the compiled physical state that moved by
runtime X +20. F.2 identifies matching translated face-plane records inside
the tag100 tree. The reciprocal runtime test itself did not isolate that tree
from the following tag1400 region. It does not show that all tag100 data is
physical, that the full tag100 grammar is known, or that every source
`COLLIDE_*` object uses the same compilation rules.

## R5T-F.2 loader-boundary clarification

The original F.1 operation swapped each byte from the parser-derived tag100
offset through end-of-file. The F.2 Retail loader-guided parser finds that the
recursive tag100 tree ends before a 44-byte tag1339 record and a distinct
tag1400 region. In the controlled baseline/modified pair, the 1339 record is
byte-identical; the later tag1400 region has the same size and 64 changed byte
positions. The F.1 result must therefore be read as a reciprocal swap of the
tag100-starting suffix. F.2's source-plane correlation locates the tested
collider's geometric plane records in the tag100 tree, while the independent
runtime contribution of the changed tag1400 bytes remains unisolated.

## Accepted R5T-F.0 result

The controlled edit translated the 14 exclusive source positions of
`Model/$autovsphere_300/$bsp/$nodraw/COLLIDE_finishline03` by source X +20.0.
The human tester reports that baseline collision existed at the visible right
finish support. In the modified course, the visible support stayed in place
and became pass-through, while physical collision was encountered at the
predicted +20 runtime-X position in empty/non-rendered space. `RACE COMPLETE`
remained at the unchanged RaceTest FinishArea. This is
**CONFIRMED_BY_RUNTIME_EDIT** for the tested physical effect and its movement.

This establishes a runtime physical effect for the source edit, not its
compiled carrier. R5T-F.0 independently established a stable source-to-tag100-
starting-suffix change across three cold cooks per cohort. The reciprocal swap
below tests whether the tested physical state follows that suffix or the
render/pre-tag100 prefix. Do not generalize to all tag100 content or call
tag100 a BSP.

## Donors and parser-derived regions

The exact files are baseline-03 and modified-03, both from the retained Demo
9.10.0 run-03 runtime and its captured snapshot. Snapshot and retained-runtime
DX hashes match. Both parse as revision 135 with validated render geometry;
the tag100-starting suffix is preserved exactly as raw bytes.

| Donor | DX SHA-256 | DX bytes | Prefix `[0, tag100.offset)` | Prefix SHA-256 | tag100 bytes | tag100 SHA-256 |
|---|---|---:|---:|---|---:|---|
| baseline-03 | `b7820fe13c5ef7eb53593bcee4e54943cf97780244b47f6fe7cb549d5c5ee7f2` | 14,795,948 | 4,677,700 | `4c9aef8897b9f368d34fcb88c6b3f628f5c308475ae38de697afbef657472316` | 10,118,248 | `9a3ea51096fc24ab82689ac929951cf8ba3291f3dc9d688fb95365383ef5a7d7` |
| modified-03 | `01289e705750fa257037b65f55f7b469db795b4c649f74b45777da0a8d08bac2` | 14,803,389 | 4,688,545 | `133ba62271dded14b2075546028290be3eca595f6b3ede492730be53bbd10b36` | 10,114,844 | `e31f79ae9ac83db3141a631363e7f982e0fbd9d4ba281bbb5f4a4f21bdf19d07` |

The offsets differ by 10,845 bytes and tag100 sizes differ by 3,404 bytes. The
tool obtains both boundaries independently from `parse_course_dx`; it uses no
fixed file offset and does not patch header fields.

## Reciprocal hybrids

| Hybrid | Prefix donor | tag100-starting suffix donor | Total bytes | Full SHA-256 | Parsed tag100 offset | Parser result |
|---|---|---|---:|---|---:|---|
| A | baseline-03 | modified-03 | 14,792,544 | `d6c05253ffdf7587dd8b8fa3b58897b2b030565aca9be256b01554111246aff4` | 4,677,700 | rev135; render validated; tag100 hash matches modified; no parser errors/unparsed bytes |
| B | modified-03 | baseline-03 | 14,806,793 | `3f3b347d4550b979e0c82f6f82bf267f1b00ca8bdd4758d8ebf027f4292731bc` | 4,688,545 | rev135; render validated; tag100 hash matches baseline; no parser errors/unparsed bytes |

Byte provenance was checked for both: each hybrid prefix is byte-identical to
its selected donor and each byte from the tag100 marker through EOF is
byte-identical to its selected suffix donor. Total sizes equal the selected
region sizes. Render parsing produces
the exact diagnostics of the selected prefix donor: Hybrid A has the baseline
prefix's 84,774 vertices / 75,138 triangles / 4,629 draws; Hybrid B has the
modified prefix's 84,946 vertices / 75,311 triangles / 4,647 draws. In both,
the old expanded AABB contains 184 decoded render vertices and the translated
AABB contains none. This is render-prefix validation only.

Both staged runtime clones are copied from the same baseline-03 runtime and
were hash-compared with it excluding only `France1.dx`: all 2,862 other files
are identical. This intentionally keeps the baseline GXM, TXT, DXT files,
RaceTest XML, executable, and other resources constant in both tests; Hybrid B
still uses the modified compiled render prefix.

The machine-readable identities and checks are in
[`swap-manifest.json`](swap-manifest.json). The research-only builder is
[`tools/r5t_f1_tag100_swap.py`](../../tools/r5t_f1_tag100_swap.py). Full runtime
copies and hybrid game assets remain ignored under `research-output/`.

## Runtime interpretation gate (pre-runtime prediction; superseded below)

No physical-carrier conclusion is made before the human tests.

| Observation | Bounded conclusion |
|---|---|
| A has NEW collision and B has OLD collision; FinishArea stays normal | Tested physical state follows the selected tag100-starting suffix donor; confirm only for this tested state and these compatible rev135 prefixes. |
| A has OLD collision and B has NEW collision | Tested physical state follows the prefix donor; the stable tag100 change is not the direct independent carrier. |
| Either hybrid fails to load or physical response is neither donor state | Region coupling or another compatibility issue remains; no independent-sufficiency claim. |
| A and B show the same state | First verify loaded paths, hashes, stale caches, and selected course before interpreting. |

Visual support remains expected at the old render position because the hybrid
prefixes retain their donor render geometry. RaceTest XML and the FinishArea
are unchanged in both runtime copies. The exact tests and launch paths are in
[`runtime-handoff.md`](runtime-handoff.md).

## Evidence labels

- **CONFIRMED_BY_RUNTIME_EDIT:** the tested source edit moves physical
  collision while visible support rendering and FinishArea completion remain
  at their prior locations.
- **CONFIRMED_BY_COOKER_DIFFERENTIAL:** the source edit changes stable tag100
  bytes across 3+3 cold cooks.
- **CONFIRMED_BY_BINARY:** donor identities, parser boundaries, hybrid sizes,
  hashes, and byte provenance.
- **CONFIRMED_BY_SOURCE_RUNTIME_EDIT / CONFIRMED_BY_RUNTIME_TEST:** for the
  tested `COLLIDE_finishline03` edit, the reciprocal hybrids show the physical
  state follows the selected suffix beginning at tag100. The later tag1400
  region was not held fixed, so this does not isolate the tag100 tree alone.
- **UNKNOWN:** the full tag100 grammar, semantics of other tag100 structures,
  and whether other source collision classes compile identically.

## Current gate

`python tools\r5t_f1_tag100_swap.py inspect`, `build`, and `verify` completed.
The independent static verification and the human runtime result both passed.
R5T-F.1 is closed as **PASS**. The pre-runtime outcome table above is retained
as history and is superseded by the final observations at the start of this
document.

## Validation

- `python -m unittest discover -s tests/synthetic -v` — 197 passed, 0 failed.
- `python -m compileall -q src tools tests blender/master_rallye_io` — passed.
- `python tools/r5t_f1_tag100_swap.py verify` — both staged hybrids passed
  byte-provenance, parser, executable, and XML checks.
- F0 cooker differential, F1 swap manifest, and the ignored local manifest
  parse as JSON and the two F1 manifests are equal.
- Blender smoke was not run: this phase changed no Blender/add-on files.
- `git diff --check` — passed before commit.


## F.2.1 boundary refinement

The earlier F.2 phrase ‘tag1400 region’ used the entire 1,824,828-byte remainder after tag1339. F.2.1 separates that controlled-pair remainder into tag1400 U (1,809,324 bytes; 64 changed byte positions in 47 ranges) and tag1500 R (15,504 bytes; byte-identical between donors). The original F.1 reciprocal runtime result still applies to the complete tag100-starting suffix. The staged T-only/U-only hybrids are the first runtime isolation test; their result is pending.
