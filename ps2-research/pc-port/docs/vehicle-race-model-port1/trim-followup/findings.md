# X-Trail exact remaining trim masks

`masks.py` independently loads hash-pinned original PC `car.dx` through the read-only Course SDK and the hash-pinned private PS2 CAR conversion. No geometry, texture or renderer files are written. `masks.json` contains only triangle ordinals, original float32 geometry hashes and ownership metadata.

Matching uses all six vertex permutations with maximum per-coordinate error at most 0.001 in unchanged model-local coordinates. Every accepted PC triangle has exactly one candidate among PS2 roots2,15,18, and every PS2 face is claimed exactly once across the examined PC records. No position fit, UV inference or material broadening is used.

| PS2 root | PC source record and original PS2 face ordinals | Count |
|---|---|---:|
|2|PC1:28..41|14 (already replaced)|
|2|PC2:0..27|28|
|2|PC3:42..49|8|
|15|PC2:0..5|6|
|15|PC17:6..7|2|
|18|PC17:0..1|2|

Ranges above are sets in PS2 root-local face order. JSON arrays retain the exact pairing in PC source-face traversal order; use them for source submeshes. Roots2,15,18 total60 faces;46 are additional to the already replaced PC1 subset.

PC17 faces0..37 must remain native. PC17 faces38..39 match root15 faces6..7, and faces40..41 match root18 faces0..1. Its `runtime_hash_categories` map keys every original unsigned float32 triangle hash and exact multiplicity. A runtime consumer must validate the complete42-face multiset, current owner, source signature and resource generation before separating the four source-owned faces. Missing, extra or modified faces fail closed; historical ordinals alone are not identity. This metadata does not itself authorize runtime suppression or prove damage-state compatibility.

Root2 is flat black; root15 retains its authored rubber secondary; root18 uses the independently verified original default texture. Do not apply reflective body material indiscriminately to the three categories. Retain the original source vertex attributes and accepted primary-V runtime interpretation.

Reproduction: `python ps2-research/pc-port/docs/vehicle-race-model-port1/trim-followup/masks.py`. Tests: `python -m unittest discover -s ps2-research/pc-port/docs/vehicle-race-model-port1/trim-followup -v`. Original proprietary files are local inputs and are not included in handoffs. No live runtime result is claimed here.
