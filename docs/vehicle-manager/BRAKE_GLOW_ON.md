# Brake Glow-ON module (Vehicle SDK)

Branch `feature/brake-glow-on` (cut from `integration/base` 98e83ef). Tools:
`tools/brake_lamps/` (module), `tools/brake_lamp_sdk.py` (CLI),
`tools/brake_lamp_studio.py` (editor), specs in `tools/brake_lamps/specs/`.
Resource-only: no renderer or loader change.

## Why the lit layer sank into the body (verified)

`tools/vehicle_lamp_authoring.py` (`transfer`) copied the retail ChevyBlazer
ON core and halo onto each car by the lens bounding box: one uniform scale,
Z pinned to the rearmost lens plane. The Blazer layer is flat; the target
lenses are curved or tilted. Measured on the owner base host `host-grime-g0-01`
(ray casts from every layer sample toward the camera, against the opaque
surfaces drawn while braking):

| car | core hidden from straight behind | deepest buried point | core vs lens |
| --- | --- | --- | --- |
| Trooper | 58 % | 12.6 mm | 5.8 mm under ... 9.9 mm over |
| Tomcat | 67 % | 25.3 mm | 16.4 mm under ... 15.6 mm over |
| Mercedes | 8 % | 6.7 mm | 5.7 mm under ... 26.8 mm over |
| Rav4, HeritageNewRav | 0 % | - | 13 ... 33 mm floating over the lens |

Native D3D9 renders (both BrakeGlow modes) show the OFF glass poking through
the lit core as dark "teeth" on Trooper and Tomcat
(`.research-output/brake-lamps/before/`).

The PS2-glow depth state is not the cause. `LampTransaction`
(`renderer/lamp_transaction.hpp`) never touches ZENABLE/ZFUNC/bias: the core
keeps native ZWRITE on, the halo pass sets ZWRITE off, ONE/ONE. The PC path
(BrakeGlow=0) draws both layers natively (`fleet_lamp_native.hpp` requires
ZWRITE on, SRCALPHA/INVSRCALPHA for the halo). Any part behind the body is
depth-rejected in both modes, so the fix is geometric; no renderer depth flag
is needed (`depth.halo` accepts only `native`).

A second finding shaped the default: the retail Blazer ON core is its own OFF
lens geometry (same vertices, new UVs) and its halo is a ring grown from the
lens outline. `from_glass` reproduces that construction on every car.

## brake_lamps.json

Schema `mr-brake-lamps/1`, documented in `tools/brake_lamps/spec.py`. Per lamp:
lens reference (stable face IDs: SHA-256 of the sorted float32 corner bits,
first 16 hex, the renderer's face hash; `draw` = `blight`, `any` or a draw
index), ON source (`blazer`, `ps2`, `custom`, `from_glass`), transform
(offset, rotation, scale, normal offset) in the lens frame, fit
(`plane`, `project`, `shrinkwrap`, `none`; offset 0.5-5 mm, default 1.5 mm,
auto-raised in 0.5 mm steps up to `max_offset_mm`), halo (size, PC tint
colour/brightness), depth mode, body set (`ANY`/`PC`/`PS2`), L/R mirror.
Importers can emit only `family` and lens faces (or a `custom` mesh); the
painted-on tail lamps of imported cars without a `blight` group use a body
draw index, and the faces are extracted into a new brake group through the
SDK's `author_states`.

## Auto-fit and checks

* core: `from_glass` copies the lens faces and pushes each vertex 1.5 mm along
  the smoothed lens normal; donor sources (`blazer`/`ps2`/`custom`) are mapped
  from their own lens frame onto the target frame, tessellated to
  `max_edge_m` and projected (or shrink-wrapped) onto the lens.
* halo: tessellated to `halo_max_edge_m` (3 cm) and lifted onto a smooth
  conservative envelope of lens + body (probe grid, highest surface within one
  halo edge) so no triangle sags under a crease; where the
  envelope climbs more than 12 mm above the lens top (bumper shelf, panel seen
  edge-on) the ring is shortened radially and smoothly, never inside the core
  outline.
* check: every layer sample is ray-cast against the opaque ON-state surfaces
  along the lens normal and from 8 views (rear, yaw +/-30, +/-60, high 25,
  low 10, chase 12). A layer is buried when more of it is hidden along the
  lens normal than of the lens itself. `check --heat-dir` writes before/after
  heat maps (green = visible from all 8 views, red = hidden from all 8).

## Compile

`blight` OFF case unchanged; ON = OFF draws + one core + one halo draw
(native ON materials: flags `[layer,0,0,1]`, word 0x24 = 1, Blazer
textures). Registry rows `MR-ADDON-LAMPS 3`, policy `ANY_MODEL`; body-scoped
sets compile as in ForesterSTI fix 05 (ON = sets only, layer-2 OFF rows,
glass SPLIT rows kept when they still bind). Collision bytes are asserted
unchanged. ForesterSTI's compile reproduces its PS2 set and OFF/SPLIT rows
byte-identically, but by owner decision (2026-11-13) ForesterSTI is **not**
re-authored and keeps its fix-05 lamps.

## Re-authored cars

Mercedes, Trooper, Rav4, Tomcat, HeritageNewRav (`from_glass`, `project`,
1.5 mm). All lamps: 0 % of core and halo hidden along the lens normal and
from straight behind (`.research-output/brake-lamps/round4/check.json`).
ImprezaProto, LancerEvo4 and Evo2FourRunner keep their own native lamps
(owner decision in fix 03); ForesterSTI unchanged (owner decision).

Rav4/HeritageNewRav: the `blight` OFF draw is the middle strip of the tail
lamp; the rest of the red block is body texture. The default lights the
strip only; add the surrounding faces in the editor (Ctrl+click, `lens.draw`
becomes `any`) if the whole block should glow.

Cost: the renderer hashes every lamp draw on first sight per buffer revision
(`cached_addon_lamp_identity`; a damage deformation is a new revision). The
lens-following halo is denser than the Blazer ring (135-750 triangles per lamp
instead of 14): the offline uncached match rose from 172 us to about 1-2.6 ms
mean per layer in `addon_lamp_native_tests` (warm cache 0.1 us). With a 2 cm
halo it was 2.6 ms; 3 cm is the compromise. Not measured in a game frame.

Known residuals in the A/B renders: thin bright slivers where a ring strip is
shortened against a steep panel (Mercedes lower-left, Trooper right edge), and
the recessed housing walls of Tomcat/Trooper stay visible beside the core, as
in the OFF state.

## Editor

`tools/brake_lamps/studio_panel.py` is a PySide6 panel for the Material &
Glow Studio (Rally Workshop 2.0 `workshop/qt_editor.py`, tab
`Material / Glow`): `add_to_workshop(window, host)` inserts a compact
`Brake Glow-ON` tab next to it (viewport on top, controls scrolled, "Open in
own window"). `tools/brake_lamp_studio.py` runs it standalone, or with
`--workshop <workspace>` opens the SDK Workshop with the tab added; the SDK's
`qt_editor.py` itself is not modified. Tested 2026-11-13 with PySide6 6.12.0
on Python 3.11 (owner approved the install): load, lamp select, gizmo drag
(re-fit reports BURIED when the core is dragged off the lens), Shift+wheel,
Snap to lens, OFF/ON, lens face toggle, both native previews, Workshop mount.
Mouse input itself was driven through the slots, not by a person. Viewport with
OFF/ON toggle and heat colouring, lens-plane gizmo (RMB drag; Shift+wheel =
normal offset), numeric fields, Snap to lens, Ctrl+click lens face picking,
and native D3D9 preview for BrakeGlow=0 and 1.

## Native D3D9 preview

`tools/brake_lamps/native/lamp_preview.cpp` (built on first use into
`.research-output/brake-lamps/bin/`) renders a staged scene through Direct3D 9
with the renderer's lamp states for each mode: PC = native states, PS2 =
PS2BrakeOn core (SELECTARG1) and PS2BrakeGlow halo ONE/ONE, ZWRITE off. It is
a fixed-function preview without game lighting, fog or the race camera, not a
game capture.

## Commands

```
py -3.11 tools/brake_lamp_sdk.py check --host <host> --spec tools/brake_lamps/specs/*.json --report r.json --heat-dir out
py -3.11 tools/brake_lamp_sdk.py preview --host <host> --spec tools/brake_lamps/specs/*.json --out-dir out
py -3.11 tools/brake_lamp_sdk.py build --source-host <host> --output-host <new host> --spec tools/brake_lamps/specs/*.json
py -3.11 -m unittest tests.synthetic.test_brake_lamps
```
