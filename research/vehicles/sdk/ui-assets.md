# Optional custom UI frames

The default `stock_frame` policy is unchanged. A donor project can opt into one
appended frame per admitted UI bank using `project_frame`. The current runtime
collection supports the existing ID27 addon author project; composing several
independent custom UI projects is not implemented.

```json
"vehicle_select_art": {"policy": "project_frame", "frame": 32},
"smallcarsheet": {"policy": "project_frame", "frame": 30}
```

Add `ui-assets.json` beside `addon.json`:

```json
{
  "version": 1,
  "icons": {
    "vehicle_select_art": {"png": "ui/icon.png", "sha256": "<lowercase SHA256>"},
    "smallcarsheet": {"png": "ui/small-icon.png", "sha256": "<lowercase SHA256>"}
  }
}
```

Only opted-in roles belong in `icons`. PNGs must be noninterlaced RGBA8, have
visible pixels, remain inside the project and match their declared hashes.
Links, junctions and parent-path traversal are rejected. Separate images may be
provided for the two roles. Source content is cropped to its alpha bounds and
contained without stretching; premultiplied-alpha area filtering avoids dark
resampling fringes. Vehicle Select outputs remain 128×128, but the drawing is
contained within the original template's alpha bounds, with a one-pixel inset.
This preserves the stock lower-canvas alignment and native DXB geometry.
The 32×16 race image retains its existing one-pixel canvas margin.

Use ordinary `mrtool addon project-validate` / `project-build` with both
`--retail-data-sma` and `--retail-data-root`. The build emits two resources per
opted-in role and `ui-assets.report.json`. Runtime preparation independently
compares bank records against the qualified stock archive, verifies frame
names, dimensions, hashes and BGRA CRC32, and admits only those declared UI
resources. The Vehicle Select widget and native ID27 small-image selector use
the new indices. Original frames are not overwritten.

## Optional GT3 source extraction

`tools/gt3_ui_icon.py` is an optional research-input adapter. SDK builds do not
import it, invoke a decoder, or require a GT3 installation. Supply your own
local RoFS2.2 GT3.VOL and a compatible local GTPS2ModelTool Tex1 decoder:

```powershell
C:/Python315/python.exe tools/gt3_ui_icon.py --vol "<GT3.VOL>" --bank-member "menu/US/arcade_menu.imgs" --image-name "<exact IMGS image key>" --decoder "<GTPS2ModelTool.exe>" --output "<new private output directory>"
```

The adapter reads only the selected member, verifies bounds and decoded size,
parses the IMGS name/index table and sequential Tex1 spans, and delegates Tex1
decoding to the supplied tool. It refuses unknown layouts and existing output
directories. It writes `icon.png`, `icon.img`, `extraction.json` and the decoder
log. The report records source offsets/hashes, decoder hash and byte-identical
named textures. `SHARED_TEXTURE_REVIEW_REQUIRED` means that the named image
shares its bytes with other entries: inspect it before using it. A unique key
is also not proof that the pixels depict the intended vehicle.

After visual review, copy an appropriate PNG into the author project and pin
its SHA256 in the sidecar. The same workflow accepts your own PNG directly;
GT3 extraction is optional. No GT3 assets, third-party decoder or extracted
icons are bundled with SDK source.

### PMB textures (optional explicit index)

The local pez2k `More_GTTools/GT3PMBDumper` documents a second source path:
PMB header words 2/3 hold entry count/table offset, followed by decoded-size /
stored-offset pairs. The adapter also accepts `--pmb-index <zero-based index>`
instead of `--image-name`. It checks monotonic spans, bounded gzip size and Tex1
length before passing the texture to the user-supplied decoder. No automatic
mapping from a display-list string to this texture index is claimed.

For this locally qualified GT3 VOL, the user identified **arcade1.pmb entry
282** as the correct Impreza Prototype icon; entry 280 depicts another Impreza.
The named IMGS entry was a shared placeholder, so it must not be substituted.
See [V4.12 findings](../vmesh412/README.md) for hashes and exact extraction path.

`--background-key R,G,B` optionally clears only exact matching pixels connected
to the PNG border. It is explicit authoring conversion, not inferred GT3 alpha.
The untouched decoder output is retained as `decoder.png`. Interior disconnected
pixels and all other colours are retained. Omit the option for already suitable
transparent or intentionally opaque custom images.

## Optional MR-style preview generation (V4.13)

Set `"presentation": "mr-native-v1"` in each chosen `ui-assets.json` icon
record, alongside `png` and `sha256`. Omission preserves the V4.12 behaviour.
The profile is per role; it applies bounded exposure and a highlight shoulder,
premultiplied area reduction and a ground baseline rather than canvas centring.
No original vehicle picture is bundled or needed to apply the preset.

| Role | Source camera preset | Final composition | Tone reference |
| --- | --- | --- | --- |
| Vehicle Select | perspective, azimuth 138°, elevation 10°, distance 7m | 128×128, road-vehicle area `[12,65,104,123)`, bottom 121 | opaque-pixel luma P90 about 166 |
| smallcarsheet | orthographic side, azimuth -90°, elevation 0°, front right | 32×16, up to full width, bottom 15 | luma P90 about 203 |

Generate source PNGs from a user-owned MR vehicle family:

```powershell
$env:PYTHONPATH='src;tools;.'
C:/Python315/python.exe tools/generate_vehicle_ui_previews.py --vehicle-family '<folder with complete.dx and DXT resources>' --output '<new private directory>'
```

Use the two generated PNGs for their respective roles and pin their hashes in
the sidecar. Normal `project-build` performs normalization. Rendering remains an
optional authoring tool, not a compiler or runtime dependency. It uses bounded
512×320 source frames, vertex normals and simple diffuse lighting. It does not
reproduce the game's environment map, native lighting or perspective-correct
texture interpolation. Final small images are heavily reduced from the source.

GT3-extracted and custom PNGs use the same normalization option. A single PNG
cannot supply another camera viewpoint: provide a matching front-three-quarter
image for Vehicle Select and a right-facing side view for smallcarsheet, or use
the model renderer. Exposure is capped at 0.8–1.6 to preserve livery differences;
extremely dark sources require a better source render, not unlimited gain.

`tools/vmesh_ui_style.py` reads a supplied retail archive and writes corpus
contact sheets/statistics. `tools/calibrate_vehicle_ui_camera.py` estimates a
camera from a supplied original DX and DXT silhouette. These optional research
tools do not auto-discover or bundle game assets. The preset comes from the
Navara calibration and corpus measurements; it is an authored approximation,
not recovered native camera code. See [V4.13 findings](../vmesh413/README.md).

## Admitted formats and boundaries

- DXB profile: little-endian header words `0xF001`, `125`; identity index pairs,
  duplicated frame count; two parts per frame, each with 12 retained scalar
  words and a counted ASCII texture name. Names and scalar records of every
  existing frame are preserved verbatim. Unknown layouts fail closed.
- These observed CarSheet banks use separate frame textures, not packed cells
  in a shared bitmap. New records append after the 32 / 30 stock records.
- `.dxt` here is a 20-byte `0xFEED` header plus raw BGRA8, not BC/DXT block
  compression. Header word `0x08` matches CRC32 of stored pixels across all 62
  stock UI textures; new frames receive a fresh checksum. Stored rows are
  flipped when presented as upright PNG.
- The native selector ABI admits values through 127. This feature admits only
  the next stock-bank index, not arbitrary high indices or arbitrary banks.
- Extended-bank loading, native filtering, scene reentry and race/Results
  presentation require a game test. Offline validation is not runtime proof.
