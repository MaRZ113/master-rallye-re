# Master Rallye DX Upgrader

This tool converts supported revision-131 **vehicle DX** files to revision
135. It uses the observed deterministic draw-prefix transition and validates
the result with the project's canonical DX parser. It does not modify the
input file.

## Supported scope

The converter supports the flat tag-2 vehicle draw grammar found in the
current ignored inputs/ corpus. The reproducible scan covers 21 rev131 file
instances from seven families, representing 20 unique DX payloads. It also
validates 15 existing rev135 file instances. See the
[coverage report](../research/r-cooker2/corpus-coverage.md) for instance
counts, unique payload counts, hashes, and source-verified pairs.

Unknown draw variants, malformed counts, out-of-range indices, truncation,
and revisions other than 131 are rejected by conversion. Newly generated
rev135 output receives strict validation, including exact local/global index
sequence consistency. The external rev135-input policy permits the observed
9.10.0 local/global ordering divergence only when per-draw oriented triangle
multisets still agree and all other structural checks pass.

Runtime compatibility evidence was collected against the verified retail
executable SHA256:

```text
bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4
```

Other retail executable builds have not been established as supported.

Revision 135 inputs are rejected by single-file conversion as already
converted. Vehicle-directory mode validates an existing rev135 role under
the external-input policy and copies its bytes unchanged with status
already_rev135_copied. A malformed rev135 role is rejected and is not copied.

## Conversion performed

The converter changes the header revision from 131 to 135 and replaces each
11-byte pre-core prefix:

```text
byte A | byte B | byte C | u32 X | u32 texture_slot_count
```

with the verified 24-byte prefix:

```text
u32 1 | u32 0 | float32 1.0 | byte A | byte 0 | byte B | byte C
| u32 X | u32 texture_slot_count
```

The draw core, texture-reference suffixes, vertex attributes, local uint16
triangle/index order, global index table, collision data, and trailing bytes
are checked after conversion. Generated output must parse as revision 135
without diagnostics and with exact local/global index sequence consistency.

The official 9.10.0 local triangle reorder is intentionally not reproduced.
Trooper and Forester each passed retail testing with their minimal converted
`car.dx`, `complete.dx`, and `wheel.dx` files, without that reorder. This is
runtime evidence for those exact packages, not a guarantee for every DX
resource or asset combination.

## Requirements

- Python 3.10 or newer.
- No third-party Python packages are required by the upgrader.

## Single-file use

```powershell
python tools/upgrade_dx_131_to_135.py .\car.dx -o .\car.rev135.dx
```

The command writes a JSON report next to the output as
`car.rev135.dx.report.json`. Select another report path with `--report`.
Use `--help` for the complete options and `--version` to print the tool
version.

Outputs are separate from the input, and existing output or report files are
refused by default. `--force` atomically replaces existing single-file
outputs; it never permits input/output identity.

## Vehicle-directory use

```powershell
python tools/upgrade_dx_131_to_135.py `
  --vehicle-dir .\Trooper `
  --output-dir .\Trooper-rev135
```

Directory mode recognizes direct `car.dx`, `complete.dx`, and `wheel.dx`
files, including case variants. It writes the available roles and a
`manifest.json` into a new output directory. The output directory must not
already exist. The directory is staged beside its destination and installed
only after every role validates.

DXT and all other non-DX files are ignored: they are neither converted nor
copied. Use the original compatible texture package separately. This tool
does not implement DXT conversion.

## Reports and safety

The JSON report records source/output hashes and sizes, source/output
revisions, transformed draw count, parser results, collision tags, and
preservation checks. It marks the individual output runtime status as
`NOT_ASSESSED_BY_CONVERTER`; the converter does not infer a runtime result
from parser acceptance. Package-specific hash matches to prior runtime tests
are documented in the corpus report.

Single-file writes stage and flush both DX and JSON report before installing
either. With --force, an older report is removed before replacing the DX so
an install failure cannot leave stale metadata; if the new report cannot be
installed, the CLI reports that the DX exists without a report. Directory
mode builds in a sibling staging directory and renames it into place after all
DX roles and the manifest are ready. Normal failures do not leave a partial
DX or package at the requested destination.

The conversion preserves the rev131 index order, while official rev135
cooker output can retain the older trailing/global index sequence while
reordering local indices. This is a known valid external rev135 pattern, not
by itself corruption. The current inputs scan found 10 verified same-GXM
role-pairs; for all ten, generated candidates differ from official rev135
only in local index ordering while retaining each draw's oriented triangle
multiset. Two filename-matched complete.gxm pairs have different source
hashes and are excluded from direct source-to-output claims.

Regenerate the committed coverage reports from the ignored corpus with:

~~~powershell
python tools/scan_dx_131_135_corpus.py inputs --json research/r-cooker2/corpus-coverage.json --markdown research/r-cooker2/corpus-coverage.md
~~~

## Evidence limits

- Retail runtime compatibility is confirmed for the tested Trooper and
  Forester car, complete, and wheel candidate hashes.
- Only the exact Trooper and Forester candidate hashes are runtime-confirmed.
  Other unique rev131 payloads convert and pass strict structural validation,
  but remain structurally supported only.
- The corpus scan includes vehicle DX only; course, sky, marker, and other DX
  grammars are outside the supported contract.
- The canonical parser does not expose an independent material-record count.
- Output is not byte-identical to the official 9.10.0 cooker because local
  triangle/index order is preserved from rev131.
- GXM source hashes were used to gate paired cooker comparisons. Some GXI
  sidecar inventories differed; those differences are recorded separately.

For detailed per-file hashes and pair comparisons, see
[`research/r-cooker2/corpus-coverage.md`](../research/r-cooker2/corpus-coverage.md)
and its JSON companion.
