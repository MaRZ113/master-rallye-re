# R-COOKER1.2 — Trooper closeout and Forester generalization gate

**Combined phase status: MORE_WORK_NEEDED.** The R-COOKER1.1 Trooper
runtime gate is closed as `PASS — CONFIRMED_BY_RUNTIME`. Forester
cross-vehicle testing is blocked at the required fresh same-source output
gate; its draw-prefix formula has not been tested and no Forester candidate
has been generated.

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

## Forester gate: waiting for fresh paired outputs

The 9.3.1 corpus contains these exact source inputs:

| Role | Corpus filename | Size | SHA256 |
|---|---|---:|---|
| car | `car.gxm` | 219,728 | `3d27573a2358f379de1c1914fb6a17ac525a5a709bd62ab824736d05ac4c2535` |
| complete | `comlplete.gxm` | 257,541 | `3fa2cff8c100b66236b1f076c164a402ac199fe3502838e0bc18be8a381b790f` |
| wheel | `wheel.gxm` | 27,272 | `2f1542430065108649a4629f613493de85332e15a7755dda96ce66d79ea3e48d` |
| shared texture source observed | `Black-tga.gxi` | 1,032 | `f1e8c064908150ef3a0b354bfa2ae6de8493d2b43b895fb803987dc23cdac8a8` |

The `comlplete.gxm` typo is retained in the read-only corpus. For the cooker
role comparison it must be staged in scratch as `complete.gxm`, with its
bytes and hash unchanged. The operator reports that correcting this filename
was runtime-confirmed to restore the Forester frontend preview; that prior
missing preview was a filename issue, not evidence of a DX format failure.

The 9.10.0 corpus has no `DataGx\\Vehicles\\Forester` directory. The
repository's ignored `inputs/` currently contains only paired Trooper
outputs, not Forester outputs. The 9.3.1 corpus has pre-existing `car.dx`
and `wheel.dx` files, but no `complete.dx`; these were not freshly generated
for this phase and their exact source-to-output provenance is not established
here. They are not used as a same-source comparison pair.

Consequently there are no fresh Forester rev131/rev135 pairs to inspect.
The 47-record Trooper formula cannot be generalized by assumption. The hard
gate remains closed until fresh outputs are produced from identical GXM
bytes in isolated copies of both demo generations. The exact handoff is in
[`forester-diff.md`](forester-diff.md).

## Current evidence state

- Trooper prefix formula: `CONFIRMED_BY_BYTES` for 47/47 Trooper records.
- Trooper no-reorder retail result: `CONFIRMED_BY_RUNTIME` for the tested
  `car`, `complete`, and `wheel` resources.
- Forester source identity: source bytes and hashes recorded above from the
  read-only 9.3.1 corpus.
- Forester same-source cooker pairs: unavailable.
- Forester draw-prefix formula, candidate parse, and runtime: `NOT_TESTED` /
  `PENDING`.
- Cross-vehicle generalization: `TROOPER_ONLY` until the Forester static and
  runtime gates are completed.
