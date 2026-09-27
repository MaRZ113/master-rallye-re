# R-COOKER1.2 — Trooper closeout and Forester generalization gate

**Status: READY_FOR_RUNTIME.** R-COOKER1.1 is closed for Trooper as
`PASS — CONFIRMED_BY_RUNTIME`. The generic prototype was applied to Forester
car/complete/wheel and all candidates parse cleanly. Forester runtime remains
`PENDING`. The source GXM copies supplied for both cooker generations are
byte-identical for car, complete, and wheel.

## R-COOKER1.1 closeout: Trooper

The operator reported that all three minimal rev131-derived Trooper resources
were accepted by retail:

| Resource | Reported result |
|---|---|
| `complete.dx` | Frontend complete model works |
| `car.dx` | Race car model works |
| `wheel.dx` | Wheel model works |

Textures/material appearance and geometry were reported correct, with no
visible model deviations, and the vehicle remained operational. Collision
and damage were not separately reported.

For the tested Trooper resources, the official 9.10.0 local triangle/index
reorder was not required for retail compatibility. The demonstrated
transformation is revision 131 to 135 plus the deterministic draw-prefix
reserialization, preserving rev131 local index order. This closes the
Trooper runtime gate only; it is not a universal compatibility claim or a
production upgrader. See [R-COOKER1.1 findings](../r-cooker1_1/findings.md)
and its [runtime closeout](../r-cooker1_1/runtime-test-plan.md).

## Forester outputs and source provenance

The 9.3.1 corpus contains these exact source inputs:

| Role | Corpus filename | Size | SHA256 |
|---|---|---:|---|
| car | `car.gxm` | 219,728 | `3d27573a2358f379de1c1914fb6a17ac525a5a709bd62ab824736d05ac4c2535` |
| complete | `comlplete.gxm` | 257,541 | `3fa2cff8c100b66236b1f076c164a402ac199fe3502838e0bc18be8a381b790f` |
| wheel | `wheel.gxm` | 27,272 | `2f1542430065108649a4629f613493de85332e15a7755dda96ce66d79ea3e48d` |
| shared source sidecar | `Black-tga.gxi` | 1,032 | `f1e8c064908150ef3a0b354bfa2ae6de8493d2b43b895fb803987dc23cdac8a8` |

The `comlplete.gxm` typo is retained in the read-only corpus. For the cooker
role comparison it must be staged in scratch as `complete.gxm`, with its
bytes and hash unchanged. The operator reports that correcting this filename
was runtime-confirmed to restore the Forester frontend preview; that prior
missing preview was a filename issue, not evidence of a DX format failure.

The 9.10.0 corpus has no `DataGx\Vehicles\Forester` directory. The
operator supplied source snapshots under both ignored input folders. For
each role, the 9.3.1 and 9.10.0 GXM copies have identical size and SHA256,
matching the authoritative 9.3.1 source corpus. Source identity is therefore
`CONFIRMED_BY_BYTES` for all three roles. The 9.3.1 `car.dx` and `wheel.dx`
also match the original corpus outputs byte-for-byte; both `complete.dx`
outputs are present in `inputs/`.

The read-only 9.3.1 package contains the typo `comlplete.gxm`; its bytes are
the frontend source staged under `complete.gxm` in scratch. The operator
reports that correcting this filename restores the frontend model. This is
runtime-confirmed filename behavior, not DX-format evidence.

## Forester draw-prefix and structural results — `CONFIRMED_BY_BYTES`

The existing `cooker_diff` comparison aligns all role-labelled draw records.
Each record was checked against the exact Trooper formula:

| Role | Records | Formula matches | Mismatches |
|---|---:|---:|---:|
| car | 15 | 15 | 0 |
| complete | 15 | 15 | 0 |
| wheel | 5 | 5 | 0 |
| **Total** | **35** | **35** | **0** |

The transformed fields are the inserted `(u32 1, u32 0, float32 1.0)`,
flags `A B C` → `A 00 B C`, and preserved `X` and texture-slot count. All
three header revisions are 131 → 135. Position, normal, color, and UV arrays
are byte-identical per role. Draw alignment, shared draw core, texture-name
suffixes, recognized global-index sections, and collision/tail bytes also
match. The local index order differs in each official rev135 output; the
per-draw oriented triangle multisets remain equal.

The paired DXT control, `black-tga.dxt`, is byte-identical: 1,044 bytes,
SHA256 `c8af53e3c1ea06c42178b3e1988dff0b3c64f150b722cba6bdd0450dc1357f82`.

## Forester candidate

The existing generic R-COOKER1.1 converter was used unchanged. Candidates
were produced solely from each supplied rev131 DX, with no official rev135
bytes used as input. All three are revision 135; the canonical parser reports
no errors or warnings, collision parsing is clean, and reconstructed global
indices match. Candidate hashes, sizes, role counts, and full difference
localization against official rev135 are recorded in
[`prototype-results.json`](prototype-results.json) and
[`forester-diff.md`](forester-diff.md).

For each role, candidate and official rev135 have equal file size. Every
candidate-to-official changed byte falls inside the local uint16 index array;
positions, normals, colors, UVs, draw region, global table, collision, and
tail are byte-identical. Per-draw oriented triangle multisets are equal while
all role draw index sequences differ in order. The official files report the
parser's existing stored-global-index mismatch (5,449 car, 6,644 complete,
675 wheel covered positions) because their local index order differs from the
unchanged global table. The candidates preserve the rev131 order and parse
with consistent local/global indices.

## Current evidence state

- Trooper prefix formula: `CONFIRMED_BY_BYTES` for 47/47 Trooper records.
- Trooper no-reorder retail result: `CONFIRMED_BY_RUNTIME` for the tested
  `car`, `complete`, and `wheel` resources.
- Forester same-source identity: `CONFIRMED_BY_BYTES` for car, complete, and
  wheel GXM inputs across both generation folders.
- Forester output-role formula: `CONFIRMED_BY_BYTES`, 35/35 records.
- Forester candidates: generated by unchanged prototype; rev135 parse clean.
- Forester retail result: `PENDING`.
- Cross-vehicle evidence: `TWO_VEHICLE_STATIC_SUPPORT_PENDING_RUNTIME`,
  scoped to the tested Trooper and Forester assets; no universal claim.
