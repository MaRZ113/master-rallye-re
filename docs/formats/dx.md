# `.dx` format notes (R0)

Status: **HIGH** for the leading geometry arrays; **UNKNOWN** for complete
material/draw/hierarchy reconstruction.

## Archive invariant

All 160 `.dx` files begin:

```text
0D D0 00 00  87 00 00 00  39 05 00 00
```

Evidence: `inventory.json`, all 160 records. This proves a shared format family.
The meanings of the constants `135` and `1337` are **UNKNOWN**.

## Confirmed leading layout

All integer and float values below are little-endian.

| Offset | Representation | Interpretation | Confidence |
|---:|---|---|---|
| `0x00` | `0D D0 00 00` / `uint32 0xD00D` | format magic | **CONFIRMED** |
| `0x04` | `87 00 00 00` / `uint32 135` | constant, meaning unknown | **CONFIRMED** value / **UNKNOWN** meaning |
| `0x08` | `39 05 00 00` / `uint32 1337` | constant, meaning unknown | **CONFIRMED** value / **UNKNOWN** meaning |
| `0x0C` | `uint32 N` | vertex count | **HIGH** |
| `0x10` | `N * 3 * float32` | XYZ positions | **HIGH** |
| `0x10 + 12N` | `N * 3 * float32` | XYZ normals | **HIGH** |
| `0x10 + 24N` | `N * 4 bytes` | per-vertex color-like values | **HIGH** |
| `0x10 + 28N` | `uint32 U` | UV-set count (`1` in five probes) | **HIGH** |
| next | `U * N * 2 * float32` | UV pairs | **HIGH** |
| next | `uint32 I` | index count | **HIGH** |
| next | `I * uint16` | triangle index buffer, grouped/local | **HIGH** representation / **MEDIUM** addressing |
| next | variable records | draw/material records with texture stems | **MEDIUM** |

## Field evidence

### Astero `wheel.dx`

- `0x0C`: `DC 00 00 00` = 220.
- `0x10..0xA5F`: 220 plausible XYZ triples.
- `0xA60..0x14AF`: 220 normal triples; measured mean length is 1.0.
- `0x14B0..0x181F`: 220 `FF FF FF FF` color entries.
- `0x1820`: `01 00 00 00` = one UV set.
- `0x1824..0x1F03`: 220 UV pairs.
- `0x1F04`: `F4 02 00 00` = 756 indices = 252 triangles.
- `0x1F08..0x24EF`: `uint16` indices.
- `0x24F0`: unresolved `uint32 1`.
- `0x24F4`: `05 00 00 00`; five variable records follow. This equals the five
  sidecar materials, but its exact type is still **MEDIUM**.
- `0x2524`: length-prefixed ASCII `asterowheel64-tga`, followed by
  `rubber-tga` and `Null`, matching `wheel.txt` slots.

Reasoning for vertex count: the computed boundaries land exactly on normals,
colors, UV count, and index count; all indices fit `uint16`; the sidecar span is
252, exactly the decoded triangle count. Confidence: **HIGH**.

### Differential validation

| File | N at `0x0C` | Parsed triangles | TXT mesh span | UV sets | Normal mean | First trailing words |
|---|---:|---:|---:|---:|---:|---|
| Astero `car.dx` | 2543 | 2021 | 2089 | 1 | 1.0 | `1, 27` |
| Astero `complete.dx` | 2657 | 2423 | 2423 | 1 | 1.0 | `1, 24` |
| Astero `wheel.dx` | 220 | 252 | 252 | 1 | 1.0 | `1, 5` |
| Bruno `car.dx` | 2455 | 2014 | 2062 | 1 | 1.0 | `1, 19` |
| Ufo `complete.dx` | 837 | 670 | 670 | 1 | 1.0 | `1, 6` |

The changing `N`, bounding boxes, and index counts are vehicle-specific payload;
the section ordering and constants are format structure. **HIGH**.

The maximum raw index is much smaller than `N` in the probes (for example 71
versus 220 in Astero wheel), while records after the index buffer contain
ranges/offset-like integers. Therefore indices likely use per-draw local vertex
bases. This is **MEDIUM**, and is why the R0 tool does not emit faces/OBJ.

## TXT correlation

TXT sidecars contain mesh names and hierarchy; targeted searches found no
`shell` or `paintwork` strings in Astero binaries. Conversely, DX draw records
contain texture stems such as `underdash-tga` and `asterowheel64-tga`.
Interpretation: hierarchy naming is sidecar-only while rendering records retain
texture bindings. **HIGH** for observed samples, not yet an engine-wide rule.

## Prototype

`tools/prototypes/dx_mesh_probe.py` parses only the confirmed leading sections,
checks normal lengths/index bounds, and outputs compact JSON. It deliberately
stops before interpreting variable draw records.

## Unresolved

- exact meaning of header words at `0x04` and `0x08`;
- draw-record field schema and local vertex-base application;
- correspondence between every TXT mesh span and binary draw group;
- material flags, hierarchy/transform storage, collision or skinning data;
- whether the same record variants apply to large course `.dx` files.
