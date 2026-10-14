# WOOLDAND / PC Forester: independent shape join

The user's proposed alias is strongly supported by original geometry.
PS2 `WOOLDAND/CAR.PSM` corresponds to the PC `Forester/car.dx` family much more
closely than PS2 `FORESTER/CAR.PSM`. At the unchanged .001 model-local corner
tolerance, 1,814/1,845 PC triangles match the union of WOOLDAND source meshes;
only 669/1,845 match the exact-named PS2 FORESTER. This is byte-grounded family
correspondence, not proof of uniform per-draw PS2 material ownership.

All canonical PS2 corpus hashes were freshly verified using the established
`water_runtime.verify_inputs` contract. Original PackFS and visual PSM decoders
and the read-only protected-retail Course SDK DX reader were reused. The source
arrays were not written or committed. `join-evidence.json` retains original
payload provenance, node/material offsets, material spelling, triangle counts,
bounds and exact float32 source digests.

| Source | SHA-256 |
|---|---|
| PS2 WOOLDAND/CAR.PSM | `93a2bd9e9ee884ac32a6d7af4b320212156e853fd85b02bc01bdcc783d0d533d` |
| PS2 FORESTER/CAR.PSM negative control | `c648998af4bcc343c864e762fee075386525bf10d1bc58379721d6639d778bc2` |
| PC Forester/car.dx | `670ef07dc312aefa5628fe24c08aa696ee147043cfecdf2aadaf01e012c8b5fc` |

The WOOLDAND union bounds are X -1.094765..1.097754, Y -0.132352..1.437022,
Z -2.182559..2.141996. Coordinates remain original model-local source coordinates;
no fitting transform or enlarged acceptance tolerance was applied.

## Material boundaries are still important

| PC record | Source triangles | Root non-rubber carshiny match | All WOOLDAND mesh match | Qualification |
|---:|---:|---:|---:|---|
| 2 grill | 4 | 4 | 4 | Complete root.1 mode3 join; PC secondary is Null |
| 7 helmet | 148 | 148 | 148 | Complete root.13 mode3 join; not a painted vehicle body |
| 8 lights | 54 | 43 | 54 | Remaining 11 faces belong to untyped `FLight64` |
| 9 rear | 71 | 43 | 71 | Remaining 28 faces belong to untyped `FRear128` |
| 10 painted side | 400 | 394 | 394 | Six closest-corner residuals 0.00298828..0.00298840 |
| 11 rubber side | 316 | 0 | 311 | Root.7 carshiny preserves rubber, so environment rewrite excluded |
| 12 shade | 34 | 33 | 33 | One unmatched triangle closest-corner residual 0.00499552 |
| 14 sticker | 16 | 13 | 13 | Three unmatched triangles closest-corner residual 0.00298840 |

`FLight64`, `FRear128`, `Chair` and original typo `$shader(crashiny)` retain their
literal spellings and UNKNOWN/default classification. The typo is not normalized
to carshiny. Named-child/brake alternative source meshes retain live-selection
UNKNOWN. A whole PC rear/lights draw is therefore not a pure PS2 carshiny group,
even though its union geometry is exactly shared.

The two complete carshiny candidates are geometry-specific to Forester across
all 78 protected-retail vehicle DX files (no decoder failures), including
expected repeated complete/menu source geometry within that family. The exact
registry digests are in `registry_candidates`. Corpus specificity does not prove
current player ownership, resource generations, environment-stage admission or
runtime source texture availability. Grill Null-secondary and helmet semantics
must be handled independently rather than used to claim full body coverage.

## Bounded decision

Correct the family alias in future source audits. Do not label all painted
Forester triangles exact PS2 mode3 merely because the alias is now proved.
There are concrete three-to-five-millimetre residuals and coalesced PC material
regions. A faithful material transfer requires an explicit decision on those
PC/PS2 ownership differences, or separate verified subregion handling. This
read-only investigation does not expand or alter the accepted 174-entry registry.

Evidence: CONFIRMED_BY_BYTES. Runtime confirmation: NOT_PERFORMED.

Reproduction (requires canonical private corpus and read-only Course SDK):

```powershell
python ps2-research/pc-port/docs/reflection-coverage-fix/wooldand/audit.py
python -m unittest discover -s ps2-research/pc-port/docs/reflection-coverage-fix/wooldand -p test_join.py -v
```

The focused tests only check compact evidence invariants. Fresh corpus extraction
and triangle comparison happen in `audit.py`, not by regenerating fixtures from
the tests themselves. No live runtime identity is asserted by either command.
