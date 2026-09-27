# Master Rallye DX 131 to 135 Upgrader

This tool converts supported revision-131 **vehicle DX** files to revision
135. It uses the observed deterministic draw-prefix transition and validates
the result with the project's canonical DX parser. It does not modify the
input file.

## Supported scope

The converter supports the flat tag-2 vehicle draw grammar found in the
available Demo 9.3.1 vehicle corpus. The scan covered 38 revision-131 files
from seven families; see the [coverage report](../research/r-cooker2/corpus-coverage.md).
Unknown draw variants, malformed counts, out-of-range indices, truncation,
parser diagnostics, and revisions other than 131 are rejected.

Runtime compatibility evidence was collected against the verified retail
executable SHA256:

```text
bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4
```

Other retail executable builds have not been established as supported.

Revision 135 inputs are rejected by single-file mode as already converted.
Vehicle-directory mode accepts a revision-135 role only after validation and
copies its bytes unchanged.

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
are checked after conversion. The output must parse as revision 135 with no
canonical or collision diagnostics and a consistent global index table.

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

Single-file writes use a fully written sibling temporary file and an atomic
install. Directory mode builds in a sibling staging directory and renames it
into place after all DX roles and the manifest are ready. Normal failures do
not leave a partial DX or package at the requested destination.

The conversion preserves the rev131 index order, while the official rev135
cooker output reorders local indices. The current corpus comparison found
that every other measured difference in same-GXM pairs was accounted for by
the draw serialization and index-order change. Two `complete.gxm` pairs had
different source hashes and were excluded from same-source comparison.

## Evidence limits

- Retail runtime compatibility is confirmed for the tested Trooper and
  Forester car, complete, and wheel candidate hashes.
- Other generated family packages are statically parsed candidates and have
  not been individually runtime tested.
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
