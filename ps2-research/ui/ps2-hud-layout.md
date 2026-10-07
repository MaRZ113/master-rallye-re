# PSB geometry, authored placement and screenshot correlation

PSB images are local triangle compositions, not whole HUD screens. There are
no standalone color, alpha, z/order, named pivot or screen-anchor fields in the
supported PSB stream. Local origin is implicit (0,0); geometry can extend to
negative XY. Runtime entity transforms, owner updates, image indices, tints
and viewport state must be treated separately.

HUD-TEMPLATE references exactly `hud-template_000` through `_007`. Its 11
images have identity keys 0–10 and **34** triangles: image 0 has eight, image 1
has eight, and images 2–10 have two each. All 17 textured quads are validated
by geometry/UV and offline reconstruction.

| Image | Local bounds [xmin,ymin,xmax,ymax] | Identified content | Evidence for role |
| ---: | --- | --- | --- |
| 0 | [-64,-63,64,65] | Tachometer dial, red high-rev band, gear window | Visual reconstruction; HUD0 SpeedDial index 0 |
| 1 | [-47,-47,49,49] | Circular radar grid and central vehicle | Visual reconstruction; active selection not established |
| 2 | [-8,-55,8,9] | Dial needle | HUD0 SpeedNeedle index 2 plus visual reconstruction |
| 3 | [-5,-6,8,10] | Race-progress car marker | HUD0 ProgressCar0..7 index 3 |
| 4 | [-3,-7,5,9] | Green vertical marker | Shape confirmed; precise runtime role UNKNOWN |
| 5 | [0,-7,2,9] | Race-progress split tick | HUD0 ProgressSplitPos0..2 index 5 |
| 6 | [-3,-7,5,9] | Checkered finish marker | HUD0 ProgressFinish index 6 |
| 7 | [-7,-16,9,0] | Green GPS direction pointer | Visual reconstruction; consumer unresolved |
| 8 | [0,-15,32,17] | Left progress-strip cap | HUD0 ProgressBar index 8 plus reconstructed outline |
| 9 | [0,-15,8,17] | Middle progress-outline segment | Visual reconstruction / STATIC_INFERENCE about dynamic stretching |
| 10 | [0,-15,32,17] | Right progress-strip cap | Visual reconstruction; dynamic composition unresolved |

HUD0.XML explicitly authors SpeedDial at Row3 `(557,98,0,1)`, PaceNotes at
`(320,418,0,1)`, rank at `(22,401,0,1)`, timer at `(494,430,0,1)`, and
ProgressBar at `(320,55,0,1)`. Map has model `Null`, position `(-65,-87,0,1)`
and gaHudAiMap owner. Zero positions on needles/progress markers are authored
initial values, not evidence that those dynamic elements appear at screen (0,0).
The five damage icons use HUD-DAMAGE indices 0–4 and x=440,475,510,545,580,
y=380, with index-5 overlays at the same authored positions.

The authored HUD rows and captures are consistent with a **640×480 authoring
space and bottom-origin entity translation**, while the reconstructed PSB
images have local Y increasing down. For example, the authored dial center
`(557/640, 1-98/480)` falls near the lower-right gauge in both race captures;
the timer's `1-430/480` is near the upper time display. This is
**STATIC_INFERENCE / SCREENSHOT_CORRELATION**, not a confirmed transform law.
The exact local-to-entity conversion, split-screen viewport, active scene,
screen-center adjustment and runtime owner overrides remain UNKNOWN.

The six supplied historical JPEGs were inspected, with filename, SHA256 and
dimensions retained in `screenshot-correlation.json`. The two full race HUDs
are `Master Rallye_SLES-50906_20251213161001.jpg` (1763×984) and
`Master Rallye_SLES-50906_20260415224620.jpg` (1920×1072). They corroborate:

- NEWHUD/HUD-TEMPLATE dial outline, small gear window and red rev band;
- the complete NEWHUD large rank-numeral family, including 2 and 4;
- HUD-DAMAGE/NEWHUD steering, engine, suspension, gearbox and tyre symbols;
- elongated progress outline, moving colored markers, and rectangular dynamic
  course minimap with vehicle arrows.

The circular radar assets and striped world-map asset are structurally
available, but neither should be declared the visible course minimap from
name resemblance. The four replay captures do not expose a full race HUD;
one also shows a floating rank numeral, whose world-space placement is outside
this pass. No new emulator session or gameplay test was performed.

Offline assembly uses only PSB-local coordinates and actual UV samples. It
does not manually place sprites to imitate the captures. The V inversion was
validated across all ten large NEWHUD digits, all four NUMS images, the radar
parts, MASTER_TEMPLATE and 24 pace-note diagrams. First treating GXI rows as
V increasing down produced broken glyphs; the resulting contradiction led to
the corrected row rule, preserved in the format/diagnostic documentation.

Authored values, owners, visibility, `Draw Priority`, `en2d 2dGlobal`, file type
and matrix rows are retained verbatim as metadata in `hud-elements.json`.
Their activation and draw behavior are explicitly marked `runtime_selection:
UNKNOWN`. Source data is not upgraded to runtime proof by a matching picture.
