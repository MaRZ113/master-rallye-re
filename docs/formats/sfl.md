# `.sfl` format notes (R0)

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
