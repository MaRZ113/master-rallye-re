# R-COOKER2 — Revision-131 vehicle corpus coverage

**Evidence: `CONFIRMED_BY_BYTES`.** The report covers vehicle DX grammar
only. It does not cover course, sky, marker, or arbitrary DX resources.

## Revision-131 scan

- 38 DX files were checked: 21 supplied under `inputs/` and 17 in the
  read-only Demo 9.3.1 vehicle corpus.
- Seven families are represented: Forester, Jump, NewRav, Rav4, Tata,
  Trooper, and Wildcat.
- The production converter accepted 38/38 with no parser or collision
  warnings/errors. No unsupported vehicle draw variants were found.
- The 38 file copies contain 624 draw-record instances. The canonical parser
  does not expose a distinct material-record count; it remains unavailable.
- All 21 input-folder DX files were converted and staged under ignored
  `.research-output/r-cooker2/runtime-candidates/<family>/`. The 17 external
  corpus outputs were analyzed in memory and were not materialized. DXT and
  all other non-DX files were not copied.

## Paired generation outputs

The input folders provide 12 paired rev131/rev135 roles across Forester,
Jump, Trooper, and Wildcat. Ten pairs have byte-identical GXM source and were
compared; two `complete` pairs were blocked because their source GXM differs.
Across the 10 compared pairs, all 135 draw records match the rev135 prefix
formula. Six pairs have byte-identical complete GXI sidecar inventories; the
other four still have exact GXM matches, but GXI sidecar differences are kept
explicit in the machine report.
The JSON also records per-file name, size, and SHA256 for all 280 GXI
sidecars across the 12 supplied generation folders.

| Family | Role | Draws checked | Prefix matches | GXI inventory | Candidate vs official rev135 byte delta |
|---|---|---:|---:|---|---|
| Forester | car | 15 | 15/15 | identical | 7,134 bytes, local indices only |
| Forester | complete | 15 | 15/15 | identical | 8,221 bytes, local indices only |
| Forester | wheel | 5 | 5/5 | identical | 675 bytes, local indices only |
| Jump | car | 22 | 22/22 | differs | 5,794 bytes, local indices only |
| Jump | complete | — | blocked | differs | not compared: source GXM differs |
| Jump | wheel | 5 | 5/5 | differs | 675 bytes, local indices only |
| Trooper | car | 22 | 22/22 | identical | 6,367 bytes, local indices only |
| Trooper | complete | 20 | 20/20 | identical | 7,413 bytes, local indices only |
| Trooper | wheel | 5 | 5/5 | identical | 675 bytes, local indices only |
| Wildcat | car | 21 | 21/21 | differs | 7,869 bytes, local indices only |
| Wildcat | complete | — | blocked | differs | not compared: source GXM differs |
| Wildcat | wheel | 5 | 5/5 | differs | 675 bytes, local indices only |

In each of the 10 eligible pairs, positions, normals, colors, UVs, texture
references, collision/tail bytes, and global-index sections were accounted
for. The official 9.10.0 local triangle order differs from the minimally
upgraded output, while per-draw oriented triangle multisets match. The
candidate-to-official changed bytes are confined to the local uint16 index
array. These findings do not assign runtime semantics to any sidecar
difference.

The two blocked source identities are:

| Family / role | Demo 9.3.1 GXM SHA256 | Demo 9.10.0 GXM SHA256 |
|---|---|---|
| Jump / complete | `71979cfb0217e8cbc7edaed5e8dd69d88f4b6482bee79029701c9075f11e5bb1` | `e001670f5dc825a359cc6e035a55035fa0a67f60f820c4d6f1d34cf6310dca0d` |
| Wildcat / complete | `97502eb8fa8c86d329d53bd1d016579cfec7cfcc14f33e05451b484afd8ffb4b` | `5b47f57ca9c31102ff5fafef687dce420cda2ff1affb199bac9bb0fa4db709c2` |

## Runtime scope of staged packages

The staged Trooper and Forester `car`, `complete`, and `wheel` files have
SHA256 values identical to their previously runtime-tested candidates and are
therefore recorded as `CONFIRMED_BY_RUNTIME_IDENTICAL_SHA256`. Jump, NewRav,
Rav4, Tata, and Wildcat packages are `STATICALLY_SUPPORTED_RUNTIME_PENDING`.
No runtime claim is inferred from parser acceptance.

Per-file source/output hashes, counts, preservation checks, pair comparison
details, and runtime package hashes are in
[`corpus-coverage.json`](corpus-coverage.json).
