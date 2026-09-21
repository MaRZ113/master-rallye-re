# `.dxt` format notes (Phase R1, orientation correction)

Status: **CONFIRMED** uncompressed wrapper; channel order **HIGH**; stored raster
row orientation **HIGH**; raster-corrected glTF UV policy **HIGH**. The two
vertical transforms are documented separately.

Despite the extension, these files are not DDS containers and do not contain
DXT1/DXT3/DXT5 block-compressed payloads.

## Layout

| Offset | Representation | Interpretation | Confidence |
|---:|---|---|---|
| `0x00` | `uint32 0xFEED` | magic | **CONFIRMED** |
| `0x04` | `uint32 1` | constant, possibly version | value **CONFIRMED**, meaning **LOW** |
| `0x08` | `uint32` | unknown identifier/hash/checksum candidate | **UNKNOWN** |
| `0x0C` | `uint32 W` | width | **CONFIRMED** |
| `0x10` | `uint32 H` | height | **CONFIRMED** |
| `0x14` | `W * H * 4 bytes` | one uncompressed 32-bit pixel plane | **CONFIRMED** |

All 6,960 archive files have the magic, word `1`, and exact size
`20 + W*H*4`. No stored mip tail is present.

## Raw pixels and channels

`parse_dxt_bytes()` preserves the payload exactly in `DxtTexture.bgra`; it does
not reorder channels or rows. Brake-light samples and alpha-bearing light/window
samples support BGRA at **HIGH** confidence. Synthetic tests independently prove
BGRA-to-RGBA conversion without involving vertical transforms.

## Stored raster rows versus PNG rows

The stored DXT row sequence is vertically inverted relative to a conventional
visually upright PNG presentation. This was checked on multiple asymmetric
Astero textures:

- `mastersticker263-tga`: only a vertical raster-row reversal makes `MASTER`
  and `263` simultaneously upright;
- `asteropanels128-tga`: sponsor text/panel elements reverse top-to-bottom;
- `asteroleftdoor1-tga` and `asterorightdoor1-tga`: door details and asymmetric
  contours occupy the coherent top/bottom positions only after row reversal.

The reusable encoder exposes two explicit policies:

- `preserve-stored`: PNG row 0 receives stored row 0;
- `flip-vertical` (default presentation policy): PNG row 0 receives stored row
  `H-1`, continuing until stored row 0 becomes the last PNG row.

The transform occurs only during PNG encoding. `DxtTexture.bgra` remains the
forensic raw plane. glTF and OBJ exporters pass `flip-vertical` explicitly.

## Independent UV experiment

After fixing PNG presentation rows, Astero `complete.dx` was exported and
rendered again in both coordinate modes:

- upright PNG rows + direct V placed the number above the sponsor mark and put
  door details in vertically inconsistent locations;
- upright PNG rows + `V' = 1 - V` placed `MASTER` above the readable `263`, put
  door handles/details in the expected upper-door region, and kept panels,
  windows, lights, and body stripes coherent.

Therefore the R1 glTF preview policy remains `V' = 1 - V`, now at **HIGH**
confidence from a raster-corrected experiment. This is independent of the
required DXT-to-PNG row reversal. Both UV modes remain available for research.

## Export behavior

The exporter caches each decoded texture once per operation, applies the
explicit `flip-vertical` PNG policy, and records both `texture_raster_row_policy`
and selected `uv_mode` in metadata. Only first-non-`Null` preview bindings are
decoded; other slots remain metadata.

## Unresolved

- meaning/derivation of header word `0x08`;
- whether word `1` is a version, type, or flags field;
- linear versus sRGB runtime sampling;
- runtime multi-texture combination semantics.
