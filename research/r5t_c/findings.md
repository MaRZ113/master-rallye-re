# R5T-C course spatial and tag100 findings

Status: **MORE WORK NEEDED**. This checkpoint adds a bounded tag100 differential
analyzer and prepares a controlled whole-startpoint translation. No source cook
or runtime observation has yet been made for the whole-volume candidate.

## Baseline

- Branch: `research/r5t-course-archaeology`.
- R5T-B.1 closeout baseline: `f110e11` (`research: record R5T-B.1 controlled tag100 proof`).
- Vehicle SDK v1 remains frozen. Course work is read-only except for controlled
  source copies staged under ignored `.research-output` for the original Demo
  9.10 runtime cooker. No course writer or executable patch is present.
- Full synthetic suite at this checkpoint: 137 tests pass. Blender 5.2.2
  headless checks pass for retail Italy1/France1 and the translated source
  helper points.

## R5T-B.1 closeout reproduced

The saved France1 experiment contains three baseline and three one-point
modified cooks. The only source difference is one float32 in `France1.gxm`,
point 0 X from `-987.0555419921875` to `-986.0555419921875` (+1.0). All six DX
files are revision 135 and pass render/index validation. The render prefix
varies naturally across repeated identical inputs, while each cohort's
10,118,248-byte tag100 suffix is byte-identical internally. Baseline SHA-256 is
`9a3ea51096fc24ab82689ac929951cf8ba3291f3dc9d688fb95365383ef5a7d7`; modified
SHA-256 is `c89654dbf502de96df366d05ecdd87051b0051e8308851550c0e0b6d37c23086`.
The controlled source-to-compiled response is
`CONFIRMED_BY_SOURCE_COMPILED_PAIR`. The owner observed no obvious gameplay
change from the one-corner tracer; this does not establish whole-volume spawn
or trigger semantics.

## Tag100 differential

`src/master_rallye/tag100_diff.py` extracts tag100 only at the exact trailing
boundary returned by the validated course render parser. It refuses a missing
tag, a different payload size, or an unvalidated render prefix. It does not
scan for an integer 100 and does not infer the internal payload boundary.

Across the current retail corpus, all 36/36 revision-135 course DX files pass
render parsing and expose a structurally reached tag100 suffix. Payload sizes
range from 5,634,127 to 10,975,471 bytes. Retail France1 is 10,145,749 bytes;
retail Italy1 is 7,517,509 bytes. The complete repeatable retail scan reported
no parser errors. The small paired Demo 8.4.1 `boinds/track01.dx` is revision
125 and is outside the current course parser's supported revision; it is not
counted as a tag100 parse success.

For the saved France1 one-point source edit:

| Measure | Result |
|---|---:|
| Raw tag100 size in each cohort | 10,118,248 bytes |
| Changed bytes | 452 (0.004467%) |
| Contiguous changed ranges | 253 |
| Unchanged bytes | 10,117,796 |
| Finite aligned float32 candidates touched | 273 |
| Non-finite aligned float32 candidates touched | 3 |
| Unit-normal-like float4 windows | 11 |

The ranges fall into three 64 KiB navigation neighborhoods; those groups do
not imply record boundaries:

| Relative interval | Ranges | Changed bytes |
|---|---:|---:|
| `0x5CA315–0x5CA599` | 16 | 31 |
| `0x5F0045–0x5F64E5` | 178 | 328 |
| `0x86B05C–0x87675E` | 59 | 93 |

The 11 float4 windows have first-three-component lengths within 0.01 of 1.0;
their measured lengths are effectively one at float32 precision. Seven begin at
relative alignment 0 mod 16 and four at 8 mod 16. These are
`HIGH_CONFIDENCE_INFERENCE` plane-like coefficient candidates only. The
alignment sweep also shows overlapping interpretations, so it does not prove a
16-byte record grammar. Exact candidates, deltas, adjacent windows, byte ranges,
and unchanged spans are in
[`tag100-diff-france1-one-point.md`](tag100-diff-france1-one-point.md) and its
JSON companion.

### Candidate plane test against the startpoint box

The eight first source points form the previously measured 10-unit axis-aligned
box. Under the corpus-level source-to-DX hypothesis `(x, z, -y)`, every one of
the 11 candidate float4 windows was tested against all eight box corners for
both `n·x + d = 0` and `n·x = d`.

- For `n·x + d = 0`, each candidate's closest corner residual is between
  15.631578 and 46.130277 source units.
- For `n·x = d`, the closest residual for each candidate is between 50.202269
  and 709.053580 units.
- No corner satisfies either equation within 1e-3.

This does **not** reject plane semantics elsewhere in tag100. It rejects only a
direct equation match between these candidate windows and the eight
startpoint-box corners under the tested transform/conventions. Per-node point
membership is not decoded. The one-corner tracer is not a rigid translation,
so no plane translation law is claimed from that experiment. The exact
per-candidate residual table and source hashes are in
[`startpoint-plane-test.md`](startpoint-plane-test.md) and
[`startpoint-plane-test.json`](startpoint-plane-test.json).

## Whole-volume startpoint candidate

The new source patch translates the same X coordinate of all eight first-pool
points by +3.0 source units. The exact source bytes, per-point edits, hashes,
old/new AABBs and centers are in the ignored
`.research-output/r5t_b1/experiments/france1-startpoint-whole-x3/source-patch.json`.

| Measure | Before | After |
|---|---|---|
| X bounds | `[-987.055542, -977.055542]` | `[-984.055542, -974.055542]` |
| Y bounds | `[-473.666718, -463.666718]` | unchanged |
| Z bounds | `[48.539051, 58.539051]` | unchanged |
| Center in source coordinates | `(-982.055542, -468.666718, 53.539051)` | `(-979.055542, -468.666718, 53.539051)` |
| Maximum pairwise-distance change | — | `0.0` |

Exactly eight float32 fields are targeted; 12 actual byte positions differ due
to their encoded values. `France1.gxm` is the only changed source file and the
paired TXT is byte-identical. The source node binding remains
`HIGH_CONFIDENCE_INFERENCE`, not proven index membership.

The mapped old center is 1.558779 units from Demo 9.10 XML Marker 0; after the
candidate +3 X translation it is 3.420021 units away. Both runtime clones retain
the same RaceTest XML SHA-256
`6048ed26c78118f3f82d9ddbcaf4f75c6655b24d805189d3cf3bd772202dc0df`. This is a
controlled spatial split, not evidence that the candidate controls spawning.

Two isolated Demo 9.10 runtime copies are prepared with two runs each. The
staging validator passes (`PASS_STAGED`), confirms that `France1.gxm` is the
only cross-cohort source difference, verifies matching runtime executable and
XML hashes, and confirms DX/DXT caches are absent before cooking. The compiled
comparison remains pending until the user selects France1 twice in each
isolated runtime and snapshots all four outputs. See the ignored
`validation.json`, each cohort's `TEST_INSTRUCTIONS.txt`, and
`RUNTIME_TEST_INSTRUCTIONS.txt` in the experiment directory.

## Source `$bsp` oracle

No safe isolated `$bsp` edit is prepared. The only complete small developer
GXM/TXT/DX source pair, Demo 8.4.1 `boinds/track01`, contains `Surface $landdb`
and `$boinds` but no `$bsp`; its cooked DX is revision 125 and cannot be parsed
by the current revision-135 course reader. `gordonTrack`, `RussiaTurkey1`, and
`collisiontests/crack*` have source GXM files but no matching TXT/DX pair in the
local developer corpus. France1 has a large `$bsp` subtree, but its source
point-pool membership by node is still unknown. Therefore `$bsp` to tag100 is
still `UNKNOWN`, not rejected.

## Render-sort BSP versus tag100

The cooker log's `moSortPlane`, draw-plane and render-sort messages remain
evidence for render processing only. The controlled repeats show naturally
variable render prefixes while tag100 is stable for identical source and
deterministically different for the isolated one-point source edit. This
supports treating the validated render prefix and trailing tag100 region as
separate data regions. It does not establish that tag100 is physical collision,
a trigger structure, or a tree, nor explain why its bytes changed.

## Blender

Blender 5.2.2 passed the existing retail Italy1/France1 course smoke: both
render meshes, draw/source identity attributes, course collection placement,
and all 172/172 DXT material images loaded. The translated old-source
startpoint overlay also passed with eight point-only empties under Course
Helpers; no edges/faces or behavior were inferred. No tag100 diagnostic geometry
was added because the float4 candidates do not pass a source-plane equation
test.

## Remaining blockers

1. Complete two baseline and two modified cold-cache cooks and compare render,
   tag100, TXT, SFL and other captured outputs.
2. Observe the first baseline and modified race states in the staged runtime;
   record spawn, grid, heading, countdown and start behavior. No runtime result
   is claimed here.
3. Find a complete small source/cooked `$bsp` pair or decode enough France1
   node-to-point membership to make one bounded source patch defensible.
4. Test candidate tag100 planes against mapped compiled source geometry and, if
   whole-volume cooks support it, test the rigid-translation law.

No general course writer, tag100 decoder, or executable patch was added.
