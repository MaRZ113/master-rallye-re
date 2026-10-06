# Selected cloud geometry, fog palette and future swap seam

**CONFIRMED_BY_EXE:** aiSky parameter reader `0x004B10A0` reads `Sky/fog color`
and bottom-height/style controls. Initialization `0x004B1180` reads SkyQuality,
disables layers above its quality limit, and assigns a model via `0x004F5B70`.
Layer0 uses CloudNumber or CloudNumberReplay depending Race/PlaybackReplay and
formats `Misc/Sky/cloud%d/clouds%d` with the same selected number twice. Later
layers use CloudNumberUsed and `Misc/Sky/cloud%d/layer%d`, likewise the selected
number twice in the verified pushes. Scene layer index is not that resource suffix.
The routine records replay/used selection and advances CloudNumber for a later
initialization; full track/event chooser ownership is unresolved.

Protected retail corpus contains cloud0..cloud6 `.dx` and `.dxt` resources.
Cloud3's diagnostic text identifies `Cylinder01` (196 source mesh items) and a
material `cloud $shader(sky)` with Cloud3.tga. This is a source-resource observation,
not a cubemap API or a proved active sky pass owner. The `.dx` files were not
rewritten; compiled flags/layout are derived below.

Palette RGB0..6 set in initialization:
0=(.87,.86,.86), 1=(.57,.66,.8), 2=(.47,.53,.59), 3=(.56,.36,.24),
4=(.27,.33,.4), 5=(.88,.94,.98), 6=(1,0,0). The float constants and resource paths
are confirmed; labels such as sunset/overcast need visual/corpus confirmation.
Layer0 supplies fog enabled/span.9 and ViewDist class through renderer virtual+0x38.
Sky packet mode+0x5C becomes2, and packet fog-enable bit3 is cleared.

**STATIC_INFERENCE:** shared world-transform mode2 in `0x00561A40` centers sky X/Z
on camera while preserving Y; shared compiled geometry should submit it through
`0x0054C9D0` / `0x00576970`. A unique renderer call site, exact depth writes/cull,
and semantic draw order remain to be observed; cooked family selection is derived below. Do not
equate sky with an environment reflection texture or assign a forced first pass.

Future seams: resource selection before model load; compiled texture/material
identity after load; sky entity packet; renderer fog preset. Initialization-time
swaps are supported by the structure. Safe live ownership/release/reload requires
more tracing. Time-of-day can coordinate sky/fog here; native sun/ambient and
exposure have no established common preset owner yet.

## Compiled resource evidence and CloudNumber producer

The protected retail sky DX corpus was read with the existing parser, without
writes or parser changes: 15 resources validated. [Resource metadata](data/sky-resources.json)
records individual hashes, raw flags/masks and ordered slots. All have mask1 and
only slot0. Clouds0..5 flags are `00000001`; layers0..6 and clouds6 are `01000001`.
The extra cloud5/cloud5.dx and selected clouds5.dx share the same structural family.

**STATIC_INFERENCE from corpus plus confirmed selector `0x00580360`:** those
cooked inputs select `shader/base` or `shader/base_alpha`, despite diagnostic TXT
label `$shader(sky)`. No runtime shader named sky is required by this selector.
The base pass constructor `0x00586560` and descriptor builder `0x005781B0` yield
XYZ|TEX1 (FVF0x102, stride20) for these no-diffuse, UV-enabled records. Fog is
explicitly disabled on the sky packet; its mode2 uses camera-relative X/Z. Generic
packet constructor `0x004F5A80` starts enable/depth/fog flags with low bits0xF;
sky initialization clears only fog bit3, and compiled instance constructor
`0x00583940` defaults ZWRITE1. These are initialization/default facts; an unseen
controller/state override or resource substitution can alter the final draw.
Sky semantic order/depth must still be observed rather than forced to a first pass.

**CONFIRMED_BY_EXE:** network state writer `0x004343C0` reads CloudNumber into a
message byte; reader `0x00433EC0` writes it back for corresponding session states.
Sky layer initialization advances the ordinary selection with wrap0..5, preserves
CloudNumberReplay and reuses CloudNumberUsed. Thus selection is not exclusively a
hardcoded per-track texture choice. Exact initial local/event chooser and visual
sunset/overcast labels remain unresolved. Runtime resource/cache substitution must
be logged before assuming these protected-corpus files are the loaded bytes.
