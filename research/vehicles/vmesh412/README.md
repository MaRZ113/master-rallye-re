# V-MESH4.12 — final Subaru frontend and wheel pass

Branch: `research/vehicles`. Private candidate:
`.research-output/vehicles/vmesh412/v412-exp-006/`.
Baseline: immutable V411 `v411-exp-005-candidate.zip`, not its game-written
save/settings files. No game was launched in this pass.

## Vehicle Select alignment

**Fixed in the generated asset; runtime confirmation remains pending.**
The original CarSheet Navara frame 23 has visible alpha bounds
`[12,67,102,119)` inside a 128×128 texture. V411 centred the source drawing
across the whole canvas. The converter now contains the drawing in the stock
template bounds with a one-pixel inset and reports output bounds. DXB scalar
records, widget bounds, native selector patches and both bank indices remain
unchanged. The already working race thumbnail and its source PNG remain exact.

## Original GT3 icon: found and user-qualified

The user's `More_GTTools` directory supplied the useful alternate PMB path.
Inspected sources: `GT3PMBDumper/GT3PMBDumper/Program.cs`,
`GT3IMGRipper/GT3IMGRipper/Program.cs`, `GT3GTARExtractor/.../Program.cs`.
These are source tools; the bounded PMB reader implements the relevant table
logic without building or modifying that external checkout.

- Local VOL SHA256:
  `27c84369911bf2352bbe5f6ba21830357c23cd82fe529b25c38c22986d37fa88`.
- Member: `menu/US/arcade1.pmb`, VOL offset `3290114048`, length `2392316`.
- PMB zero-based texture index **282**, stored offset `1060340`, 616 stored
  bytes, 944 decoded bytes, one Tex1 image, **51×27** PNG.
- Tex1 SHA256:
  `e325c2cc706d115bca744707326dcdccf8806ad68a499328ad1795c28b2dfb94`.
- Decoder PNG SHA256:
  `b57dc11956d71b23ef66ccd9e4b600690213a83e76c0f813b7a97a6f2492a63b`.
- The user rejected entry 280 as another Impreza and explicitly identified
  entry 282 as correct. This is human visual qualification, not a universal
  vehicle-ID mapping inferred from nearby display-list strings.
- All 23 named IMGS banks were checked; seven regional arcade_menu banks
  reuse the same unrelated placeholder for this name. PMB is the useful path.

Reproduction (from this repository; supply your own VOL and decoder):

```powershell
$env:PYTHONPATH='src;tools;.'
C:/Python315/python.exe tools/gt3_ui_icon.py --vol '<GT3.VOL>' --bank-member menu/US/arcade1.pmb --pmb-index 282 --decoder '<GTPS2ModelTool.exe>' --background-key 126,126,126 --output '<new private directory>'
```

The source palette has opaque alpha (0x80 PS2, decoded 255), including its
flat grey background. Conversion explicitly keys exact border-connected
RGB(126,126,126), clearing 612 pixels while preserving internal islands and
every other colour. This is an authoring choice, not recovered native alpha.
The untouched source PNG remains beside the converted image. Converted PNG
SHA256: `0aa5c36414eb5515852ce5c659a34700fcdafaaa3fb9a80332e1f3d0422d96c2`.

The optional extraction workflow accepts IMGS names or explicit PMB indices,
and a caller-specified decoder. SDK builds still accept custom RGBA PNGs and
have no dependency on GT3 assets or tooling. No extracted images are included
in the source review archive. Their low native resolution limits sharpness.

## Reusable wheel layering rule

Measured stock Pajero `wheel.dx` uses five draws: outboard tyre annulus, tread,
inboard tyre, central wheel-face insert, separate metallic shelf. Face/shelf
join at radius 0.18686m, versus bead radius 0.23071m. Shelf radius ratios are
**1 / 0.89286 / 0.80992**; its inner edge is recessed about 0.03654m from the
outer bead. The central insert is raised towards its hub, not a flat plane.

`tools/vmesh_wheel_layers.py` optionally derives that profile from a caller's
stock reference and scales it to an admitted radial target rim. It keeps the
target bead radius and wheel envelope, clamps the centre to the existing
outer plane, and refuses unknown or already layered profiles. There are no
Subaru IDs, wheel hub positions or physics rules in this helper.

Subaru retains its existing four draw slots/materials. Face and shelf have
separate geometry vertices and UV domains **inside the existing opaque rim
draw**, avoiding a fragile native draw/material-table expansion. The shelf
uses a guarded 7×7 metallic swatch outside the circular face footprint; source
artwork is not stretched onto it or onto the tyre. Metal colour/reflection
alpha are sampled from existing reflective rim pixels, not guessed new flags.
Rim texture CRC32 refresh is opt-in; old texture builds retain their defaults.

The first stock-ratio preview had an overly broad shelf. Following user review,
`subaru-wheel.json` narrows the radial shelf width to **0.42** of that reference
and uses **0.90 UV scale** around the face centre (1.111× visual enlargement).
The texture's old perimeter is cropped under the rim instead of appearing as
a second ring. These are explicit editable authoring parameters; helper defaults
retain the reference profile. Tyre UVs and face opacity are unaffected.

Target bead radius stays 0.30096063m; recessed edge ratio becomes 0.9201664,
edge depth remains 0.04767123m. The existing 36 segments remain. Rim triangles change
108 → 180. Tyre radius **0.37620080m** and half-width **0.12852222m** are fixed.
The four frontend rim copies inherit their existing anchors. Race wheel
placement and all physics resources are untouched.

## Validation and deferred work

- Project validate/build/verify, runtime verify, launcher build and both
  launcher preflights pass. No process was launched into the game.
- Independent audit checks all 191 resources, DX structure, unchanged native
  material states, non-rim triangle attributes, shared face/shelf positions,
  normal lengths, opaque wheel face, texture CRCs and ZIP content integrity.
- All 190 focused SDK/converter regression tests pass (including explicit PMB
  selection, malformed spans, opt-in background key, CRC and profile limits).
- Final icon alpha bounds are `[14,68,99,118)`, strictly within the original
  `[12,67,102,119)` template region. This is an offline asset alignment result.
- Exactly four assets change: Subaru `wheel.dx`, `complete.dx`,
  `nevwheel-tga.dxt`, and appended frontend `carsheet_032_000.dxt`.
- `car.dx`, collisions, physics, tyre assets, body/livery, brake glow,
  headlamps, correct race thumbnail, DXB banks, scene and native operations
  remain unchanged. Prepared runtime Data.sma is also byte-identical to V411;
  its archive was omitted from the older review ZIP, so verified separately.
- Actual DX/DXT previews show before / after / stock wheel from two angles.
  Their simple diagnostic light does not reproduce native reflections.

Human checks: Vehicle Select icon alignment/containment and wheel appearance
in frontend/races, with reflections enabled and disabled. No new runtime
visual or physics success is claimed. Wheel positions/offsets and further
cross-model rules stay for the future Lancer/physics work; Evo IV is not started.

Candidate, checks, extracted assets and previews stay under ignored research
output. The source review archive contains this pass's source/docs/tests and
compact reports only. No original game EXE, d3d8.dll or game archive was edited;
no publication, staging, commit or push was performed.
