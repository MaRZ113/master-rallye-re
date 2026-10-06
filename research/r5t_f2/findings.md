# R5T-F.2 — tag100 physical grammar archaeology

**Status: PASS, bounded.** A Retail rev135 loader-guided, read-only parser
decodes the variable-length tag100 tree. The 24-triangle France1
`COLLIDE_finishline03` source mesh has 12 unique face planes; all 12 match
float4/code records in both baseline and modified trees. Under the controlled
source X +20 translation, stable-code plane pairs follow the expected
`d' = d - 20*n.x` relation. This is a strong geometric binding, but not a
one-source-triangle-to-one-record mapping.

## Loader and parser

The supported Retail executable is SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. Its DX
section loop at `0x00551430` dispatches tag 100 at `0x0055167A` to
`0x0057E2D0`; the recursive record reader is `0x0057E550`. The root allocation
is 0x74 bytes. Three typed pools use 8-byte, 8-byte, and 0x24-byte allocation
strides; their fields and count relationships are recorded without assigning
gameplay names. The wire header is 24 bytes: tag 100 plus five little-endian
uint32 words. Nodes contain two leading uint32 fields and conditional
child/sibling links; their optional float4/code record and optional
float3/float/code list item are each 20 bytes. In-memory strides are not wire
record widths.

The parser uses neutral field and allocation-role names, validates counts,
flags, truncation, list bounds, and unexplained trailing data when strict mode
is requested. It has no write, edit, or rebuild API. Five additional top-level
siblings are retained in the France1 root sibling chain; they are not malformed
orphan records.

## Tested source geometry binding

The source pair changes only 14 exclusive target positions, each by source
X +20; the triangle bank and object table remain byte-identical. The established
coordinate mapping carries this to runtime X +20. Baseline and modified DX
hashes are respectively:

- Baseline: `b7820fe13c5ef7eb53593bcee4e54943cf97780244b47f6fe7cb549d5c5ee7f2`
- Modified: `01289e705750fa257037b65f55f7b469db795b4c649f74b45777da0a8d08bac2`

The source triangles collapse to 12 unique plane equations. With normal
component tolerance `1e-5` and plane-distance tolerance `1e-3`, all groups
match records in both parsed trees, covering all 24 triangles. There are 41
baseline and 45 modified candidate records because records repeat in the
rebuilt hierarchy. Thirty-nine stable-code record pairs preserve their normal
and translate `d` according to the plane equation; maximum absolute residual
is `4.143710998505412e-05`. Source triangle count is not compiled record count;
the uint32 code meaning remains **UNKNOWN**.

Source AABB translates exactly +20 in runtime X. No target-specific compiled
AABB field has yet been found. The decoded fields therefore support plane
geometry correlation, not a complete primitive or leaf ownership map. The
tree's two leading uint32 fields, partition rule, child ordering semantics,
terminal meaning, and runtime query traversal remain **UNKNOWN**.

## F.1 runtime boundary

F.1 reciprocally swapped every byte from the tag100 marker through EOF. The
loader-guided parse finds a tag100 tree of 8,293,376 baseline bytes and
8,289,972 modified bytes. It is followed by a 44-byte tag1339 record that is
identical in the pair, then a 1,824,828-byte post-tag1339 remainder, now separated as tag1400 U (1,809,324 bytes) plus tag1500 R (15,504 bytes). The 64 changed byte positions are in U; R is byte-identical. The physical collision followed the selected
suffix donor in both runtime hybrids, with visible finish geometry and
FinishArea completion unchanged. Thus the runtime result is **CONFIRMED** for
the complete tag100-starting suffix and the tested source state. The F.1 test
did not isolate the parsed tree from tag1400 at runtime.

Absolute file offsets: baseline tag1339 `0x00C5EC44`, tag1400 `0x00C5EC70`;
modified tag1339 `0x00C60955`, tag1400 `0x00C60981`. Section hashes and the
same offsets are stored in the machine-readable reports.

The source-plane records reside inside the parsed tag100 tree. Their binding
to the tested moving physical state is **HIGH_CONFIDENCE_INFERENCE**, supported
by the unique plane groups, repeated-cook differential, exact translation
relation, loader path, and reciprocal suffix result. At the F.2 checkpoint, tree-only runtime proof had not yet been obtained. F.2.1 below supersedes that boundary: the tested state follows the tag100 tree donor. The broader runtime contribution of tag1400 remains **UNKNOWN**.

## Retail structural validation

The retail course corpus parsed the tag100 tree in 36/36 DX files. Node counts
range from 174,559 to 386,835 (mean 294,151.28); plane-bearing node counts range
from 87,279 to 193,417 (mean 147,075.14); maximum depth ranges from 27 to 46.
All corpus trees have zero optional list items. This is structural parser
coverage only; no physical runtime claim is made for the other 35 courses.

The exact counts, pool roles, depth, and post-tree hashes are in
[`tag100-layout.json`](tag100-layout.json). The tested geometry and candidate
offsets are in [`collide-finishline03-binding.json`](collide-finishline03-binding.json).
The implementation is [`course_tag100.py`](../../src/master_rallye/course_tag100.py);
the corpus probe is [`r5t_f2_tag100_probe.py`](../../tools/r5t_f2_tag100_probe.py).

## Validation

- `python tools\r5t_f2_tag100_probe.py` — retail structural parse **36/36**;
  12 source plane groups matched in each controlled cohort.
- `python -m unittest discover -s tests/synthetic -v` — **205 passed, 0
  failed**.
- `python -m compileall src tools tests blender/master_rallye_io` — passed.
- `python tools\r5t_f1_tag100_swap.py verify` — both hybrid hashes, prefix
  and suffix donor bytes, rev135 render parsing, runtime EXE, and RaceTest XML
  verified.
- Both F.1/F.2 machine-readable reports and the F.1 swap manifest parse as
  valid JSON. `git diff --check` passed.
- Blender smoke was not run because this phase changed no Blender code.

## Remaining unknowns

- Complete spatial-tree and primitive semantics.
- Unique node/leaf ownership for the tested source mesh.
- Runtime isolation of the parsed tree from tag1400 was unresolved at F.2 and is resolved for the tested translation by F.2.1.
- Meaning of the record code and leading node fields.
- Exact `$bsp -> tag100` relationship and behavior of other source collision classes.
- Any write or rebuild grammar. No writer was implemented.

## R5T-F.2.1 closeout

**R5T-F.2.1: PASS — TREE_CARRIER_CONFIRMED.** Hybrid T (modified tree / baseline tag1400) had OLD collision absent and NEW collision present. Hybrid U (baseline tree / modified tag1400) had OLD collision present and NEW collision absent. The visible support stayed at the original render location, and FinishArea completion remained at its original region in both builds. Thus the tested physical location follows the tree donor. Modified tag1400 was neither sufficient nor required for this tested translation; no broader tag1400 meaning is claimed. See [`../r5t_f21/runtime-results.md`](../r5t_f21/runtime-results.md).
