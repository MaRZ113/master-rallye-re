# PS2-UI1: HUD image banks

Status: **COMPLETE for the bounded content/format pass**. Byte parsing, exact
texture resolution, glyph reconstruction and historical screenshot correlation
are complete. Live PS2 execution, dynamic minimap geometry and final screen
transforms remain unverified/outside this pass.

Ten exact HUD PSBs share the same F001/version-125 packed stream. They contain
120 images and 444 triangle records: 418 textured records and 26 `Null` records.
All bytes are accounted for; there is no trailing section or record alignment.
The necessary scalar loader path confirms the byte model. See
[format](psb-format.md), [ELF map](elf-ui-map.md), and [validation](validation.md).

The significant corrections are:

- `HUD-NUMS` has ten character keys but four images, visibly digits **1–4**.
  Its aliases are real serialized data: `0,1 -> 0`, `2 -> 1`, `3 -> 2`,
  `4..9 -> 3`. It is not a complete ten-digit font.
- `NEWHUD` has distinct large digits **0–9**, plus ten small digits and the
  dial, radar, progress-strip and damage-icon families visible in user captures.
- The four serialized atlas integers enclose an allocated cell. The actual UV
  rectangle can be narrower/shorter; treating allocation width as glyph width
  corrupts several assembled digits.
- Raw GXI row zero corresponds to PSB **V=1**. Correct crop rows are
  `(1-vmax)*height .. (1-vmin)*height`. Local PSB Y increasing down reconstructs
  whole upright glyphs and the dial. This is visual evidence, not an assertion
  about every stage of the runtime screen-coordinate pipeline.
- `Null` triangle UV fields contain NaN/Inf in canonical files. Texture lookup
  is suppressed; the fields remain uninterpreted and are preserved as exact
  bits rather than normalized or discarded. Null drawing behavior is unverified.
- `MAP128STRIPED1-TGA.GXI` is an opaque striped world-map background, 128×128.
  It is visually different from the course-path minimap in the racing captures.
- `WATERSURFACE2.GXI` alpha is **4–131**, with **128 distinct values**. The
  prior all-255 assertion is contradicted by this canonical extraction.

87 targeted GXI textures match the strict 8-byte-header, four-byte-pixel format.
RGBA byte interpretation is corroborated by green radar pixels, red dial pixels,
alpha cutouts and assembled images. This does not certify all 3177 GXI files.
All seven requested bonus resources exist, including both render-target names;
their static stored pictures do not prove live render-target update behavior.

The six user-supplied screenshots include two race HUDs and four replay images.
Their filenames are not executable provenance. They corroborate the asset
families, but do not establish exact-frame bank selection, UI tint, transforms,
anchors or draw order. The authored XML relationships are retained separately
from runtime selection in [layout](ps2-hud-layout.md).

Evidence labels: `CONFIRMED_BY_BYTES`, `CONFIRMED_BY_ELF`,
`CONFIRMED_BY_BOTH`, `CONFIRMED_BY_VISUAL_RECONSTRUCTION`, `STATIC_INFERENCE`,
`SCREENSHOT_CORRELATION`, `UNKNOWN`. Each labels the stated observation, not
the entire rendering behavior. Inputs/hashes and every selected range are in
the JSON reports; proprietary payloads, PNGs and decompilation remain ignored.

No PackFS behavior changed. No original file, PC renderer/UI, grass/water/
reflection implementation or historical research tree was modified.
