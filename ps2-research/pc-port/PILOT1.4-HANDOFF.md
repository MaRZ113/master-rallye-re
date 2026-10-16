> Historical checkpoint: old build paths/hashes below are preserved provenance. For current builds use overlay/README.md and dist/current/build-report.json.

# PC-VISUAL-PILOT1.4 handoff

Status: `IMPLEMENTED_PENDING_USER_RUNTIME`. The one-pixel color probe is ready
for a controlled France1 run. It does not yet identify why the bush becomes
occluded, and no PS2 parity is claimed.

## PS2-enabled DLL

Built from the immutable renderer baseline at
`3f837f4ddcb27ee1034a4b0753634c92009360ec`, using the existing deterministic
overlay:

`ps2-research/pc-port/.build-overlay-pilot14-final4/ps2-enabled/build/Release/d3d8.dll`

SHA-256: `715314c58edc621b3c0405394b94ca008dc9874febbea684563841506f1da7f8`

Manually use this DLL only in the existing isolated PC test setup, preserving
the current proxy so it can be restored. No automatic install or game-asset
change was made. Keep `PS2Port.ini` beside the renderer INI.

## Same-bookmark A/B

Choose one pixel just inside the bush silhouette from the same backbuffer size.
Use the same France1 Free Camera bookmark, camera, resolution and game settings
for both runs. Keep verbose diagnostics off.

First run:

```ini
[PS2Port]
FoliageMode=0
PixelProbe=1
PixelX=<same backbuffer pixel X>
PixelY=<same backbuffer pixel Y>
PixelLaterDrawOrdinal=-1
Diagnostics=0
```

Repeat with only `FoliageMode=3` changed. Mode 0 is Stock (`override_mask=0x00`).
Mode 3 changes only `D3DRS_ZWRITEENABLE=FALSE` (`override_mask=0x10`); the
original alpha-test, alpha-blend, source-blend and destination-blend states
remain in effect.

Compare the single `ps2_pixel_probe` record's `before_target_draw`,
`after_target_draw` and `before_present` colors. If color changes after the
target but later returns, set `PixelLaterDrawOrdinal` to a measured zero-based
indexed draw between those checkpoints and repeat the same bookmark. Only name
an occluding draw after a checkpoint records the actual pixel change at its
draw boundary. If target pre/post colors match, inspect the logged alpha,
texture-stage, Z, color-write and framebuffer data; one unchanged pixel is not
proof that the complete bush produced no visible color.

The event reports the frame and target identity, matrices, viewport, render and
texture-stage states, source/target descriptors, sampled RGB(A), and native
HRESULTs. There are at most four 1×1 source copies and one 4×1 scratch-to-system
memory copy per captured frame. The D24X8 depth surface is described but never
read. A standalone same-parameter D3D8
probe passed, but support on the game's live device is confirmed only by this
run's `ps2_pixel_probe_config` and per-checkpoint HRESULTs.

Full method, failure statuses, schema and interpretation notes:
[pilot1.4-pixel-provenance.md](docs/pilot1.4-pixel-provenance.md).

## Validation

- Baseline serial Release build: PASS; CTest 24/24; proxy exports PASS.
- PS2-enabled serial Release build: PASS; CTest 25/25; proxy exports PASS.
- PS2 port Python tests: PASS 10/10; `compileall`: PASS.
- Generator repeated twice per staged variant: deterministic; no generated
  baseline files rewritten.
- `git diff --check`: PASS; `modernization/renderer/` unchanged.

The baseline and PS2-enabled DLLs are separate proxy builds. Neither was copied
into the game directory. In-game pixel capture and cause classification remain
pending the user's A/B run.
