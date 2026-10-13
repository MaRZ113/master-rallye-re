# Source preparation validation

Executed in the primary master worktree. Existing dirty port work and earlier
research were preserved. Read-only Course SDK HEAD:
`4244fa0c4d878523c9947f54816bf377cdfb2589`, clean.
`modernization/renderer/` had no working changes during the source checks.

The following command was executed three times using the canonical original roots:

```powershell
python ps2-research/pc-port/tools/prepare_shrub_pilot.py `
  --ps2-input-root 'D:\Game\Master Rallye PS2' `
  --pc-input-root 'D:\Game\Master Rallye\corpora\retail\Data.sma_unpacked' `
  --sdk-root 'D:\Game\Master Rallye\master-rallye-re-course' `
  --asset-out ps2-research/pc-port/.assets/grass/Turkey3Shrubs.ps2grass `
  --report-out ps2-research/pc-port/docs/grass-port2/source-contract.json
```

All three artifact writes passed byte-equality verification against the existing
file; the last two compact reports were directly hash-compared and equal:

| Artifact | SHA-256 |
|---|---|
| Private Turkey3Shrubs.ps2grass | `688947a32776ffab67c553b4adc95e4597c399f2d70ece37534fd682044752b4` |
| Compact source-contract.json | `67ea89faf587f99a1d58221be37c932e114ffce95f1d5dd670cba001d7bd524c` |
| Preserved first Turkey3Grass.ps2grass | `6af6393c444a485b2c648c2a6973a91bd5783db3c0f90269a0d653b2f089cfad` |
| Preserved prepare_grass_pilot.py | `1c255df7409f6dfcb0ca213c8ceb9b48c8b36c2c7799a7007bf1fbc588050cff` |

The new private artifact is 1,871,784 bytes, with 146,498 reconstructed points
and 6,849 spatial bins. It uses the existing version-1 grass artifact parser
with different BUSH1 source identity. The new output guard prohibits writing
the first grass filename or arbitrary destinations, and refuses a different
existing artifact. It never writes playable game files.

Focused synthetic suite:

```powershell
python -m unittest discover -s ps2-research/pc-port/tests -p test_shrub_asset.py -v
python -m compileall -q ps2-research/pc-port/tools/prepare_shrub_pilot.py ps2-research/pc-port/tests/test_shrub_asset.py
git diff --check
```

**10/10 PASS**, compileall PASS, diff-check PASS. Tests verify deterministic
shared layout, separate BUSH1 identity, first-grass rejection, corruption,
original singular/uppercase parsing, duplicate ordering, malformed/nonfinite
inputs, output confinement and equal horizontal density/jitter with only the
proved lift change on a synthetic surface. The first execution exposed an
incorrect winding in that synthetic fixture; it was corrected to the original
caller C,B,A order. No production decoder or geometry rule was changed.

Fresh canonical Rabbitizer 1.16.2 `InstrCategory.R5900` checks validated all
46 compact instruction words in instruction-probes.json using independently
parsed ELF32 PT_LOAD mapping. Frozen GRASS1 function contracts supplied the
broader owner/resource/draw references; this did not reopen broad decompilation.

The earlier first-grass source anchor independently reproduced 2,797 exact
PC-matched eligible triangles and 64,900 points. The shrub comparison used the
same bridge and independently validated 420 route anchors at zero residual.
Private full points, source triangle IDs and raw instruction windows stay
ignored under ps2-research/data/grass2; no original geometry/image is included
in this documentation or the source/test handoff.

These checks establish source preparation and static reconstruction. Native
build/state transaction results and the new second layer's gameplay visibility
must be reported separately by the implementation pass. PS2 VU/GS parity remains
unconfirmed.
