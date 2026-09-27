# R-COOKER1.2 — Forester source and DX differential

## Same-source provenance — `CONFIRMED_BY_BYTES`

The `inputs/9.3.1_dxForester/` and `inputs/9.10.0_dxForester/` GXM copies
were hashed and compared directly. Each generation's copy is byte-identical
to the other and matches the 9.3.1 corpus source hash:

| Role | 9.3.1 source file | Size | SHA256 in both input folders |
|---|---|---:|---|
| car | `car.gxm` | 219,728 | `3d27573a2358f379de1c1914fb6a17ac525a5a709bd62ab824736d05ac4c2535` |
| complete | staged as `complete.gxm` from corpus `comlplete.gxm` | 257,541 | `3fa2cff8c100b66236b1f076c164a402ac199fe3502838e0bc18be8a381b790f` |
| wheel | `wheel.gxm` | 27,272 | `2f1542430065108649a4629f613493de85332e15a7755dda96ce66d79ea3e48d` |

The source corpus also contains 24 GXI files; their hashes remain inventoried
in [`prototype-results.json`](prototype-results.json). `Black-tga.gxi` is
present in both input folders with SHA256
`f1e8c064908150ef3a0b354bfa2ae6de8493d2b43b895fb803987dc23cdac8a8`.
The supplied `black-tga.dxt` outputs are byte-identical, 1,044 bytes, SHA256
`c8af53e3c1ea06c42178b3e1988dff0b3c64f150b722cba6bdd0450dc1357f82`.

The old corpus typo `comlplete.gxm` is not changed. The copied bytes were
staged as `complete.gxm` for both cooker inputs. The operator reports that
correcting the filename restores the frontend preview; the former missing
preview was not a DX-format incompatibility.

## Supplied rev131 and rev135 outputs

| Role | Rev131 size / SHA256 | Rev135 size / SHA256 | Draw records |
|---|---|---|---:|
| car | 128,327 / `eb2909b1d623f9e053a11114fe1d6d17283495bf7cab902755f87d2ee299e7de` | 128,522 / `fbe8d15af205a3cbe95773d5241372352729f7fbcef21e61386123209a80a423` | 15 |
| complete | 138,492 / `d42ce558a6455a3c8e75b661b962ab472cf9a6ebeceeda9658a70ac1d163e219` | 138,687 / `72a3b98f616d55e66e43bf0bbc2702bdb5ff464406ae7e14338cc3c4a5a4ee15` | 15 |
| wheel | 12,937 / `1e2fefdf5fdaa4eba94490a3287de2fbc14863b6812c5902ba8f4d3a089d3dd7` | 13,002 / `191009bd708ed20fd0d46c00572e8d8ba833ff5cff5c5f8f92b6772bd1d9a328` | 5 |

The rev131 and rev135 headers report revisions 131 and 135 respectively.
The file growth is exactly 13 bytes per draw record: +195 bytes for car and
complete, +65 bytes for wheel.

## Draw-prefix formula — 35/35 exact matches

The existing `cooker_diff` alignment was applied to every draw record, then
the prefix fields were decoded and checked directly:

| Role | Checked | Matches | Mismatches |
|---|---:|---:|---:|
| car | 15 | 15 | 0 |
| complete | 15 | 15 | 0 |
| wheel | 5 | 5 | 0 |
| **Total** | **35** | **35** | **0** |

For every record:

```text
rev131: A B C | u32 X | u32 texture_slot_count
rev135: u32 1 | u32 0 | float32 1.0 | A 00 B C | u32 X | u32 texture_slot_count
```

This is `CONFIRMED_BY_BYTES` for these same-source Forester files. It extends
the Trooper evidence from 47 records to 82 records across two vehicle asset
families; it does not establish that every revision-131 resource uses this
layout.

## Structural comparison

| Property | car | complete | wheel |
|---|---|---|---|
| positions / normals / colors / UV arrays | byte-identical | byte-identical | byte-identical |
| texture-reference suffixes and shared draw core | equal | equal | equal |
| local index order | changed | changed | changed |
| oriented triangle multiset per draw | equal | equal | equal |
| relocated global-index table bytes | identical | identical | identical |
| collision and recognized trailing bytes | identical | identical | identical |
| recognized collision tags | tag101 | tag102 | tag102 |

The comparison accounts for the normalized rev131→official-rev135 changes.
The official outputs' canonical parser reports a stored-global-index mismatch
at 5,449 car, 6,644 complete, and 675 wheel covered positions. This matches
the observed pattern: official rev135 local order changed while the global
table bytes stayed the same. It is a parser diagnostic about that pairing,
not a claim of retail failure.

## Existing prototype candidates

The unchanged generic R-COOKER1.1 converter consumed only each rev131 DX.
No official rev135 bytes were copied into candidate output. All candidates
have the official rev135 file size, parse as revision 135 with no errors or
warnings, and reconstruct their global indices consistently.

| Role | Candidate SHA256 | Size | Draws / vertices / triangles | Candidate vs official changed bytes | Changed uint16 values | Local-index array range |
|---|---|---:|---|---:|---:|---|
| car | `11433415ebeb4f4864a78e64ae2de9e0462b14fcf16b1b63e56313015e1a1086` | 128,522 | 15 / 2,459 / 1,864 | 7,134 | 5,449 | `[88548, 99732)` |
| complete | `852d2188d8ee3913ea366a684ca818b1e51bed61e4c4b685308dee3939153aa7` | 138,687 | 15 / 2,649 / 2,328 | 8,221 | 6,644 | `[95388, 109356)` |
| wheel | `ce2b6557cbd8975ec14d1c20a4d3df902512a3433c713dc3822f09bfd35ca01c` | 13,002 | 5 / 220 / 252 | 675 | 675 | `[7944, 9456)` |

Every differing candidate/official byte lies inside the listed local uint16
index array. Candidate and official rev135 draw regions, geometry attributes,
global tables, collision payloads, and recognized tails are byte-identical.
Oriented triangle multisets match per draw; candidate index order differs in
all 15 car draws, all 15 complete draws, and all 5 wheel draws. The exact
changed-value counts and ranges are machine-recorded in
[`prototype-results.json`](prototype-results.json).

## Runtime handoff state

The ignored package
`.research-output/r-cooker1_2/forester-runtime-candidate/` contains
`car.dx`, `complete.dx`, and `wheel.dx`. See
[`runtime-test-plan.md`](runtime-test-plan.md). Runtime status remains
`PENDING` until the operator tests the candidates in retail.
