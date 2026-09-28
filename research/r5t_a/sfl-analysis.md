# SFL and historical FL/SF analysis (R5T-A)

Retail has **36** ICont SFL files; all **68/68** scanned SFL files across available builds satisfy the exact 20-byte header + W×H payload length.

| Build | SFL files | Valid exact-size parse |
|---|---:|---:|
| Demo 8.4.1 | 0 | 0/0 |
| Demo 9.3.1 | 2 | 2/2 |
| Demo 9.10.0 | 30 | 30/30 |
| Retail | 36 | 36/36 |

Header word 0 is `float32 3.0` in the observed files. Width/height values and the 20-byte + W×H relation are corpus-confirmed; meanings of the other three header floats/fields and payload bytes remain UNKNOWN.

## France1 / Italy1 and variant comparisons

- France1: identical payload hashes across every present build = **False**.
- Italy1: identical payload hashes across every present build = **False**.
- francew vs francewflip: dimensions equal=True, header bytes equal=True, payload hash equal=False.
- italym1 vs italym1flip: dimensions equal=True, header bytes equal=True, payload hash equal=False.
- italys3 vs ITALYS3FLIP: dimensions equal=False, header bytes equal=False, payload hash equal=False.
- spains1 vs SpainS1flip: dimensions equal=True, header bytes equal=True, payload hash equal=False.
- spainw vs SpainWflip: dimensions equal=True, header bytes equal=True, payload hash equal=False.
- turkeys2 vs Turkeys2flip: dimensions equal=True, header bytes equal=True, payload hash equal=False.

## Demo 8.4.1 FL/SF

The older FL/SF candidates use a different payload width in this corpus: their 20-byte headers store float32 version/width/height/unknown/unknown, and listed France1/Italy1 files satisfy 20 + width×height×4 bytes. This is structural evidence only; no cell meaning is assigned.

- `DataScene/France1.fl`: 1755956 B, 819×536, parse=20-byte-header-plus-4-byte-cells, bytes/cell=4.0.
- `DataScene/France1.sf`: 1755956 B, 819×536, parse=20-byte-header-plus-4-byte-cells, bytes/cell=4.0.
- `DataScene/ICont/France1.fl`: 1734340 B, 815×532, parse=20-byte-header-plus-4-byte-cells, bytes/cell=4.0.
- `DataScene/ICont/France1.sf`: 1755956 B, 819×536, parse=20-byte-header-plus-4-byte-cells, bytes/cell=4.0.
- `DataScene/ICont/France2.fl`: 1121140 B, 539×520, parse=20-byte-header-plus-4-byte-cells, bytes/cell=4.0.
- `DataScene/ICont/Italy1.fl`: 768600 B, 415×463, parse=20-byte-header-plus-4-byte-cells, bytes/cell=4.0.
- `DataScene/ICont/Italy2.fl`: 1210372 B, 572×529, parse=20-byte-header-plus-4-byte-cells, bytes/cell=4.0.
- `DataScene/ICont/Italy3.fl`: 1635920 B, 665×615, parse=20-byte-header-plus-4-byte-cells, bytes/cell=4.0.
- `DataScene/ICont/Turkey1.fl`: 749192 B, 419×447, parse=20-byte-header-plus-4-byte-cells, bytes/cell=4.0.
- `DataScene/ICont/Turkey3.fl`: 1051796 B, 498×528, parse=20-byte-header-plus-4-byte-cells, bytes/cell=4.0.

The old France1FL/France1SF TGA headers report 819×536, matching the DataScene-root FL/SF dimension candidates. The .gxi/TGA pairings are listed in JSON; spatial meaning is UNKNOWN.

## Diagnostic previews

Raw byte-order grayscale previews are written under `.research-output/r5t_a/sfl` (ignored research output). Rows are displayed in stored order and are not labeled as height or surface data.
