> Historical checkpoint: old build paths/hashes below are preserved provenance. For current builds use overlay/README.md and dist/current/build-report.json.

# PC-VISUAL-PILOT1.3 handoff

The PS2-enabled build now has four per-draw diagnostic policies for the
verified France1 `bush01` geometry. The original geometry classifier, source
texture, draw ordering and logical state tracker are unchanged. The selected
policy is opt-in; mode 0 is Stock.

## Build provenance

- Repository branch: `master`.
- Locked baseline HEAD: `61cb84d5c7f28d3bd88a3f1f9a8ce16d4c178390`.
- Renderer baseline source is staged from that Git revision and remains
  unchanged in the working tree.
- [`overlay/patches/0001-renderer-integration.patch`](overlay/patches/0001-renderer-integration.patch)
  contains the seven staged renderer integration changes, including the
  masked state transaction and one-shot selected-mode diagnostic.
- [`overlay/patches/0002-interface-generator.patch`](overlay/patches/0002-interface-generator.patch)
  is staged-only and preserves the extension seam when interfaces are
  regenerated.
- [`overlay/baseline-lock.json`](overlay/baseline-lock.json) locks the
  baseline hashes, ordered patches and generated interface outputs.
- [`overlay/build_overlay.py`](overlay/build_overlay.py) verifies the exact
  baseline, stages two independent copies, runs the generator twice per
  variant, builds serially, runs CTest and verifies both proxy exports.
- `renderer/` and `tests/` contain only PS2 extension code and focused tests;
  no full renderer copy is committed.

## DLLs

The locally built PS2-enabled DLL is:

`D:\Game\Master Rallye\master-rallye-re-general\ps2-research\pc-port\.build-overlay\ps2-enabled\build\Release\d3d8.dll`

SHA-256: see [`overlay/build-report.json`](overlay/build-report.json) and the
ZIP manifest. It is a Win32 PE32 D3D8 proxy and exports
`Direct3DCreate8`, `ValidatePixelShader`, and `ValidateVertexShader`.

Verified PILOT1.3 DLL SHA-256:
`a0035c53b749bcbdb2135174ebc73fdac366b8545ab255b370b6bb1823af11f9`.

The Stock baseline is separately built at:

`D:\Game\Master Rallye\master-rallye-re-general\ps2-research\pc-port\.build-overlay\baseline\build\Release\d3d8.dll`

The two builds use the same proxy project; the baseline has no PS2 extension
source or link dependency. Neither DLL is installed automatically. The
handoff archive contains the PS2-enabled DLL and source/docs, but no original
game assets.

## Four-mode A/B

Use the PS2-enabled DLL in a separate test installation. Put `PS2Port.ini`
next to `MRRRenderer.ini`, with:

```ini
[PS2Port]
FoliageMode=0
Diagnostics=1
```

Use the same France1 Free Camera bookmark and game settings. Restart the game
after changing the mode. Capture each mode from the same bookmark, then check
`ps2_port_mode_selected` for the configured mode and `ps2_port_draw_identity`
for the exact target's requested and actually applied mask. Mode 0 has no
active material request, does not mirror buffers, and therefore has no target
draw identity event; its one device-configuration record reports mode 0 and
mask 0. Modes 1–3 each produce at most one target identity record per device.

| Mode | Mask | States changed only around the exact target draw |
|---:|---:|---|
| 0 | `0x00` | Stock; no request |
| 1 | `0x1F` | Alpha test off; alpha blend on; SRCALPHA/INVSRCALPHA; depth write off |
| 2 | `0x0F` | Same alpha/blend changes as mode 1; depth write untouched |
| 3 | `0x10` | Depth write off; all alpha/blend states untouched |

The mask gates validation, native Get/Set, partial rollback, and post-draw
restoration. The draw is submitted once and retains the native HRESULT.
Full step-by-step capture and interpretation guidance is in
[`runtime-ab.md`](runtime-ab.md).

## Evidence boundary

The user supplied runtime evidence from the earlier mode-1 run: 5,364
successful identity events, the target draw
`DrawIndexedPrimitive(4,11940,28,22944,48)`, successful temporary state
changes/restoration, and the same draw in Stock. The foliage appeared mostly
occluded/invisible. The target appeared early in a 704-draw frame with many
later depth writers. These are user-reported runtime observations; the raw
capture files are not in this checkout. The draw-order/depth-write and
alpha/texture-stage explanations remain competing hypotheses. PILOT1.3
separates the policies but does not resolve the cause until the user compares
the four runs.

Build/test success does not establish visual parity with PS2. No automatic
installation or push was performed.
