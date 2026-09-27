# R-COOKER1.1 — Minimal rev131 to rev135 prototype

**R-COOKER1.1 status: PASS — CONFIRMED_BY_RUNTIME.** This follow-up refines
the initial R-COOKER1 draw-prefix `UNKNOWN`; it does not rewrite what was
known at that phase. The byte and runtime evidence here is limited to the
controlled Trooper `car`, `complete`, and `wheel` resources.

## Same-source provenance

The supplied files under `inputs/9.3.1_dxTrooper/` and
`inputs/9.10.0_dxTrooper/` have matching source snapshots:

| Source | SHA256 in both generation folders |
|---|---|
| `car.gxm` | `5caed6da1213f17e2638d0ee47860cf521d4715475418e028bfd13f7c0e87642` |
| `complete.gxm` | `122d84a45a6b2f81989e645c18ecfd7a32392bf029c7503698fb5fc900eb5c34` |
| `wheel.gxm` | `ade8e42e4e1c4c946b2bf726c722494b31854ee0ebd2e16384db675a7595aa65` |
| paired `Black-tga.gxi` | `f1e8c064908150ef3a0b354bfa2ae6de8493d2b43b895fb803987dc23cdac8a8` |

The rev131 and rev135 GXM/GXI copies are byte-identical per resource. DX input,
candidate, and official-output hashes are machine-recorded in
[`prototype-results.json`](prototype-results.json). No source or DX asset is
tracked by this report.

## Draw-prefix mapping — `CONFIRMED_BY_BYTES`

The formula was checked against every paired draw record using the input
bytes and canonical rev135 record boundaries:

| Resource | Records checked | Exact matches | Mismatches |
|---|---:|---:|---:|
| car | 22 | 22 | 0 |
| complete | 20 | 20 | 0 |
| wheel | 5 | 5 | 0 |
| **Total** | **47** | **47** | **0** |

For these records, the first 20 bytes of the shared draw core and the
length-prefixed texture-reference suffix (including terminal zero) are
unchanged. The 11-byte rev131 prefix parses as three opaque flag bytes `A B C`,
`u32 X`, and `u32 texture_slot_count`. The matched 24-byte rev135 prefix is:

```text
u32 1 | u32 0 | float32 1.0 | bytes A 00 B C | u32 X | u32 texture_slot_count
```

This proves a byte mapping for this Trooper set. It does not assign broader
semantics to `A`, `B`, `C`, or `X`, or establish that all resources use it.

## Rev131-only candidate transformation

[`src/master_rallye/dx_revision_upgrade.py`](../../src/master_rallye/dx_revision_upgrade.py)
and [`tools/upgrade_dx_131_to_135.py`](../../tools/upgrade_dx_131_to_135.py)
implement an analysis-only transformation. It reads only the rev131 input,
changes header revision 131 to 135, serializes the verified draw prefix, and
preserves local uint16 index order and every other source byte. It does not
read official rev135 output and does not optimize or reorder triangles.
For example, reproduce the car candidate with:

```powershell
python tools/upgrade_dx_131_to_135.py `
  inputs/9.3.1_dxTrooper/car.dx `
  .research-output/r-cooker1_1/runtime-candidate/car.dx --overwrite
```

| Resource | Candidate size | Candidate SHA256 | Official rev135 SHA256 | Changed bytes vs official | Differing uint16 values |
|---|---:|---|---|---:|---:|
| car | 124,854 | `04a9aa09b813a0893953e6813b2d8ec4ac63a5545b987e12a29e692773de06e1` | `c2f44f09e116dad7d9ad16d026b13109c1631360151e4aa2be5b62a333ebcc40` | 6,367 | 5,552 / 5,733 |
| complete | 134,609 | `a8ceffebf7f6fc8b8af489e1e4c7f62ca5ef3b537db4af3f8048e687997629bc` | `85c3f74ca062acb994bd23722dfe1c774845d3db33a85cc5aadd7ab3f3fa242e` | 7,413 | 6,730 / 7,125 |
| wheel | 12,989 | `1a1aa4605e0319dd0d3fc68691845ed34559d1635c320986b23f9fe5750406ab` | `236853cb1d8f1cf068f3639b90e8b372fdab1b9c3b40b3d8793bc959931e7b5c` | 675 | 675 / 756 |

All three candidates have the official rev135 file size. Every differing byte
is confined to the candidate's local uint16 index-array byte range:

| Resource | Half-open byte range | Changed bytes |
|---|---:|---:|
| car | `[83184, 94650)` | 6,367 |
| complete | `[90024, 104274)` | 7,413 |
| wheel | `[7944, 9456)` | 675 |

The JSON report lists the exact changed-index ordinal runs, with corresponding
two-byte field ranges, plus hashes and byte counts. Positions, normals, colors,
UVs, draw texture references, global-table bytes, and all post-global-table
bytes compare equal between each candidate and official rev135 output. This
includes the parsed collision tails (car tag101; complete and wheel tag102).

## Local and global index observation

For each pair, the rev131 trailing global-index table is byte-identical to the
official rev135 table after accounting for its relocated offset. The candidate
retains both the rev131 local order and that unchanged table. The canonical
parser reports that the candidate's local/global indices reconstruct
consistently, with complete-disjoint coverage and no warnings. For the
official outputs, the same parser reports the known local/global mismatch
after the local order changes. This records parser and byte behavior only; it
does not assign runtime semantics to the trailing table.

The candidate also parses as revision 135 with no parser or collision errors
or warnings. Parser acceptance is not evidence of retail runtime acceptance.
The canonical reader exposes draw records and their texture slots but no
separate material-record count for these files; the output manifest therefore
records `material_count` as unavailable rather than treating draw count or
texture-slot count as a material count.

## Runtime closeout — `CONFIRMED_BY_RUNTIME`

The project operator reported a successful retail test of all three
rev131-derived candidates in
`.research-output/r-cooker1_1/runtime-candidate/`:

- `complete.dx`: frontend complete model works.
- `car.dx`: race car model works.
- `wheel.dx`: wheel model works.
- Textures/material appearance and geometry were reported correct, with no
  visible model deviations; the vehicle remained operational in retail.
- Collision and damage behavior were not separately reported in this result.

For these tested Trooper resources, the official 9.10.0 local triangle/index
reorder is **not required for retail compatibility**. The demonstrated
compatibility transform is revision 131 to 135 plus the verified draw-prefix
reserialization while preserving rev131 local index order. This does not prove
the same rule for every rev131 asset or establish a production upgrader. See
the [runtime closeout](runtime-test-plan.md) and
[`prototype-results.json`](prototype-results.json).
