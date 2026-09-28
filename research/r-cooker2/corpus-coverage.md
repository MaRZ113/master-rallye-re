# R-COOKER2.1 DX Corpus Coverage

Generated deterministically from the ignored DX/GXM corpus. Paths are relative to the scan root.

Regenerate with:

~~~powershell
python tools/scan_dx_131_135_corpus.py inputs --json research/r-cooker2/corpus-coverage.json --markdown research/r-cooker2/corpus-coverage.md
~~~

## Inventory

| Measure | Count |
|---|---:|
| Vehicle families | 8 |
| DX file instances | 36 |
| Unique DX payloads | 35 |
| rev131 file instances | 21 |
| Unique rev131 payloads | 20 |
| rev135 file instances | 15 |
| Unique rev135 payloads | 15 |
| rev131 draw-record instances | 347 |
| Draw records across unique rev131 payloads | 342 |

Families: Forester, Jump, NewRav, Rav4, Simmbugghini, Tata, Trooper, Wildcat

## Source-verified pairs

Verified same-GXM pairs: 10; unverified filename pairs: 2; unpaired outputs: 12.

Direct paired draw records: 135; formula matches: 135; mismatches: 0.

| Family | Role | rev131 source SHA256 | rev135 source SHA256 | Pair status | Direct records | Formula | Minimal candidate vs official |
|---|---|---|---|---|---:|---|---|
| Forester | car | 3d27573a2358f379de1c1914fb6a17ac525a5a709bd62ab824736d05ac4c2535 | 3d27573a2358f379de1c1914fb6a17ac525a5a709bd62ab824736d05ac4c2535 | VERIFIED_SAME_SOURCE | 15 | PASS | ONLY_LOCAL_INDEX_ORDER |
| Forester | complete | 3fa2cff8c100b66236b1f076c164a402ac199fe3502838e0bc18be8a381b790f | 3fa2cff8c100b66236b1f076c164a402ac199fe3502838e0bc18be8a381b790f | VERIFIED_SAME_SOURCE | 15 | PASS | ONLY_LOCAL_INDEX_ORDER |
| Forester | wheel | 2f1542430065108649a4629f613493de85332e15a7755dda96ce66d79ea3e48d | 2f1542430065108649a4629f613493de85332e15a7755dda96ce66d79ea3e48d | VERIFIED_SAME_SOURCE | 5 | PASS | ONLY_LOCAL_INDEX_ORDER |
| Jump | car | 55bd09e1f8c9c647c82381dba463bb555dfcc51c6b2d63b9e8e39c55231da17e | 55bd09e1f8c9c647c82381dba463bb555dfcc51c6b2d63b9e8e39c55231da17e | VERIFIED_SAME_SOURCE | 22 | PASS | ONLY_LOCAL_INDEX_ORDER |
| Jump | complete | 71979cfb0217e8cbc7edaed5e8dd69d88f4b6482bee79029701c9075f11e5bb1 | e001670f5dc825a359cc6e035a55035fa0a67f60f820c4d6f1d34cf6310dca0d | UNVERIFIED_SOURCE_PAIR | 0 | — | — |
| Jump | wheel | 68c084024eb7df133e133b47739991a0f25440452c6e9259facc51250d963245 | 68c084024eb7df133e133b47739991a0f25440452c6e9259facc51250d963245 | VERIFIED_SAME_SOURCE | 5 | PASS | ONLY_LOCAL_INDEX_ORDER |
| Trooper | car | 5caed6da1213f17e2638d0ee47860cf521d4715475418e028bfd13f7c0e87642 | 5caed6da1213f17e2638d0ee47860cf521d4715475418e028bfd13f7c0e87642 | VERIFIED_SAME_SOURCE | 22 | PASS | ONLY_LOCAL_INDEX_ORDER |
| Trooper | complete | 122d84a45a6b2f81989e645c18ecfd7a32392bf029c7503698fb5fc900eb5c34 | 122d84a45a6b2f81989e645c18ecfd7a32392bf029c7503698fb5fc900eb5c34 | VERIFIED_SAME_SOURCE | 20 | PASS | ONLY_LOCAL_INDEX_ORDER |
| Trooper | wheel | ade8e42e4e1c4c946b2bf726c722494b31854ee0ebd2e16384db675a7595aa65 | ade8e42e4e1c4c946b2bf726c722494b31854ee0ebd2e16384db675a7595aa65 | VERIFIED_SAME_SOURCE | 5 | PASS | ONLY_LOCAL_INDEX_ORDER |
| Wildcat | car | 4b739b19f8ec4f1ff859832939d9a1d7b906037e1ba1e2ba19f30d291daba74a | 4b739b19f8ec4f1ff859832939d9a1d7b906037e1ba1e2ba19f30d291daba74a | VERIFIED_SAME_SOURCE | 21 | PASS | ONLY_LOCAL_INDEX_ORDER |
| Wildcat | complete | 97502eb8fa8c86d329d53bd1d016579cfec7cfcc14f33e05451b484afd8ffb4b | 5b47f57ca9c31102ff5fafef687dce420cda2ff1affb199bac9bb0fa4db709c2 | UNVERIFIED_SOURCE_PAIR | 0 | — | — |
| Wildcat | wheel | 8eae7e35a61afd39db14b86299d0f18d4a032bfc7dc5a3b000225bdcbe4cb6b4 | 8eae7e35a61afd39db14b86299d0f18d4a032bfc7dc5a3b000225bdcbe4cb6b4 | VERIFIED_SAME_SOURCE | 5 | PASS | ONLY_LOCAL_INDEX_ORDER |

## Draw-prefix pattern coverage

Unique ABC: 3; unique X values: 3; unique slot counts: 1; unique full tuples: 4.

| A,B,C | X | Slots | File instances | Unique payloads | Direct oracle occurrences | Evidence |
|---|---:|---:|---:|---:|---:|---|
| 0,0,1 | 5 | 3 | 34 | 29 | 20 | DIRECTLY_ORACLED |
| 0,1,1 | 3 | 3 | 81 | 81 | 37 | DIRECTLY_ORACLED |
| 0,1,1 | 7 | 3 | 208 | 208 | 70 | DIRECTLY_ORACLED |
| 1,1,1 | 7 | 3 | 24 | 24 | 8 | DIRECTLY_ORACLED |

## Conversion regression

Unique rev131 payloads attempted: 20; converted: 20; rejected: 0.

Every successful unique payload was generated with the production converter and its strict generated-rev135 checks. Runtime confirmation is limited to generated hashes matching the Trooper or Forester runtime candidates.

## Existing rev135 policy

Unique rev135 payloads checked: 15; accepted: 15; valid ordering divergences: 15; rejected: 0.

The existing-input contract permits only the known local/global ordering divergence when each draw retains the same oriented triangle multiset. Generated output remains subject to exact local/global sequence agreement.

## Minimal candidate vs official rev135

Verified pairs compared: 10; only local index order differs: 10; byte-identical: 0; additional/unresolved differences: 0.

## Evidence scope

- Trooper and Forester candidate hashes are runtime-confirmed.
- Same-source draw-prefix mappings require byte-identical GXM source hashes.
- Other accepted rev131 payloads are structurally supported only.
- DXT is not converted by this tool.

The JSON companion contains per-file hashes, source provenance, per-payload preservation checks, and pairwise comparison details.
