# `.sfl` and historical FL/SF format notes (R5T-A)

Status: **HIGH** for container shape; payload semantics **UNKNOWN**.

All 36 files have a 20-byte header followed by exactly one byte per grid cell:

| Offset | Representation | Interpretation | Confidence |
|---:|---|---|---|
| `0x00` | `00 00 40 40` / `float32 3.0` | constant/version/type candidate | **CONFIRMED** value / **UNKNOWN** meaning |
| `0x04` | `uint32 W` | raster width | **HIGH** |
| `0x08` | `uint32 H` | raster height | **HIGH** |
| `0x0C` | `float32` | coordinate/origin-like value | **LOW** |
| `0x10` | `float32` | coordinate/origin-like value | **LOW** |
| `0x14` | `W*H bytes` | 8-bit raster/grid payload | **HIGH** structure / **UNKNOWN** semantics |

Evidence examples:

- `France1.sfl`: W=845, H=558, size=471,530 = `20 + 845*558`.
- `France2.sfl`: W=565, H=545, size=307,945 = `20 + 565*545`.
- `francem.sfl`: W=1570, H=356, size=558,940 = `20 + 1570*356`.

The same equality holds for all 36 files. The smooth-looking byte sequences and
course naming are compatible with a sampled field (surface/height/control map),
but choosing among those meanings would be speculation. No decoder is provided
in R0.

The R5T-A parser checks truncation, exact payload length, header values, and
byte distribution. Grayscale and false-color diagnostics live under the ignored
`.research-output/r5t_a/sfl/` directory; pixels are shown in stored row order
and are not labeled as height or surface values.

## Historical `.fl` / `.sf` candidates

Demo 8.4.1 has no matching SFL files, but it contains ten France1/Italy1 and
nearby `.fl` / `.sf` candidates. Each scanned candidate has a 20-byte header
with the same broad five-field shape and exactly four payload bytes per cell.
For example, `DataScene/ICont/Italy1.fl` is 415×463 and 768,600 bytes; France1
has root and ICont variants with dimensions 819×536 and 815×532. The root
France1 `.fl` and `.sf` each have an associated TGA visualization reporting
819×536.

Retail SFL instead has exactly one byte per cell. France1 SFL is 845×558 and
471,530 bytes; Italy1 is 439×486 and 213,374 bytes. Dimensions and payload
hashes differ from the old FL/SF candidates. This supports a historical format
change but does not prove identical semantics or direct cell conversion.
Header floats beyond the observed first value 3.0 and all per-cell meanings
remain **UNKNOWN**.

The full counts, paths, hashes, TGA pairings, payload distributions, and
flip/reverse comparisons are in
[`research/r5t_a/sfl-analysis.md`](../../research/r5t_a/sfl-analysis.md).
