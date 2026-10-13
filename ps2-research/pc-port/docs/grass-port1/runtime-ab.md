# Turkey3 grass preview: manual A/B

Use the newly built PS2-enabled DLL in an isolated test installation, manually.
Keep the old DLL and INIs. The build installs nothing. The original executable,
course DX/TXT, RaceTest XML and textures are not replaced. This feature is only
admitted on the verified original PC build and live RaceTest/Turkey3 camera.

The private source-derived asset already exists locally:
`D:/Game/Master Rallye/master-rallye-re-general/ps2-research/pc-port/.assets/grass/Turkey3Grass.ps2grass`.
Expected SHA256 `6af6393c444a485b2c648c2a6973a91bd5783db3c0f90269a0d653b2f089cfad`.
It contains copyrighted image/derived coordinates and is deliberately excluded
from Git and the handoff. Supply this path locally; do not redistribute it.

Place PS2Port.ini beside MRRRenderer.ini. First isolate grass:

```ini
[PS2Port]
FoliageMode=0
PixelProbe=0
ReflectionMode=0
CourseObjectsMode=0
GrassMode=0
GrassConfigVersion=1
GrassAsset=D:/Game/Master Rallye/master-rallye-re-general/ps2-research/pc-port/.assets/grass/Turkey3Grass.ps2grass
GrassSpriteHalfSize=0.33
GrassDiagnostics=1
```

1. Start Turkey3 with the same vehicle, weather and renderer quality settings.
   Save a Free Camera bookmark at the start area in the supplied screenshots.
   Capture GrassMode0. This run keeps the new feature Stock.
2. Exit the game, change only GrassMode to1, restart and restore the bookmark.
   Keep FOV/resolution/lighting unchanged. Capture the same view and one F10 frame.
3. Move the camera along the road and inspect near/far tufts, terrain intersection,
   foreground occlusion and fading. Check that cars, original HUD, menus and
   original vegetation keep their prior state. Test pause and one real display
   Reset if convenient; changing course must stop the Turkey3 grass pass.
4. If no grass appears, retain `ps2_grass_config`, `ps2_grass_gate` and
   `ps2_grass_draw` records. A configured/uploaded asset is not proof of a submitted
   batch. Require capture/apply/draw/restore HRESULT0 and candidate count>0.

Expected records are bounded: configuration once, first gate rejection and first
private submission per device, restoration failures always. `sprite_candidates`
counts submitted CPU rectangles, not measured visible plants. The driver clips
them; terrain depth and alpha may remove them. There is no per-frame log flood.
The original native UI draw is still once and retains its own HRESULT.

Compare source-height placement, silhouette and density first. Half-size0.33 is
an explicit PC projection adaptation, not the recovered PS2 renderer+11c scale.
Full-triangle activation, chosen nearest-even hash rounding, PC UV/projection/
alpha normalization and batching are also not exact live PS2 replay. No wind,
crossed quads, arbitrary height bias or terrain edits were added. The original
PS2 projected56 cap has not been mapped to PC pixels. Report near-camera artifacts
rather than changing many settings together to hide them.

Then compare the original PCSX2 reference with the same course/approximate view.
Different advertisements do not constitute a platform difference. Unequal camera,
resolution, gear and elapsed time limit screenshot comparisons. Visual acceptance
and PS2 parity remain separate from successful build/mock/package checks.
