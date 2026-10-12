# PS2 treeblend versus the PC pilot

## Static PS2 contract

The canonical France1 PSM material selects shader callback `treeblend`, runtime mode 2 and queue bucket 1. The handler writes texture option 1 and float32 `0.15`; the latter is a MIP/strip coefficient, not opacity. The common GS producer enables alpha blending, disables GS alpha test, masks Z writes, and selects `GEQUAL` in the controlled ZTST field. Its blend selectors implement `(Cs-Cd)*As/128+Cd`. See [material-and-gs-contract.md](material-and-gs-contract.md).

This is executable/static evidence. There is no captured PS2 GS packet for the France1 bush, no live micro-RAM capture, and no proved world-frame order between all opaque and treeblend groups.

## PC approximation and the four captured modes

The PC executable is identified in the sessions by SHA-256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`; the single D3D8 proxy is `a0035c53b749bcbdb2135174ebc73fdac366b8545ab255b370b6bb1823af11f9`. F10 and the extension identity event agree on one France1 `DrawIndexedPrimitive(4,11940,28,22944,48,...)` using VB generation 624/revision 248 and IB generation 625/revision 337 in modes 1–3. The exact compiled DX record remains source metadata, not API call ordinal. The runtime evidence is scoped to this single draw and these resource generations.

| Mode | Alpha test | Alpha blend | Source/destination | Z write | User-observed result |
|---|---|---|---|---|---|
| 0 Stock | enabled, `GREATER`, ref 128 | disabled | `SRCALPHA`, `INVSRCALPHA` retained | enabled | Original cutout bush visible |
| 1 | disabled | enabled | `SRCALPHA`, `INVSRCALPHA` | disabled | Bush largely disappears |
| 2 | disabled | enabled | `SRCALPHA`, `INVSRCALPHA` | original enabled | Bright/white rectangular foliage cards |
| 3 | original enabled, `GREATER`, ref 128 | original disabled | original factors retained | disabled | Bush largely disappears |

The override values are visible in native-only `SetRenderState` events, followed by successful restoration to the frame's pre-draw snapshot. Mode 2 emitted no ZWRITE write; Mode 3 emitted no alpha-state write. Each frame contains one target call and returns `D3D_OK`. Full selected state sequence and hashes are in [runtime-correlation.json](runtime-correlation.json).

## Interpretation boundary

Mode 3 shows that disabling Z writes is sufficient to produce the disappearance in the captured view. Since the call is early in a frame with hundreds of later draws, later depth-writing geometry is a plausible explanation, but no specific overlapping draw or pixel/depth transition was captured. Mode 2 keeps depth writes enabled yet produces the card artifact, so the alpha/texture-stage path also has a separate problem. The D3D8 stage-0 state modulates texture with diffuse color/alpha, stage 1 is disabled; the actual bound resource format and per-pixel sampled values were not captured.

The PC source DXT has 11,671 alpha-zero texels, but their RGB mean is approximately `(93.35, 104.90, 76.06)`, not white. Therefore stored transparent RGB alone does not explain the white cards. Runtime format conversion, texture binding/sample, diffuse alpha, and blend arithmetic remain candidates. The PS2 GS `As/128` equation is not equivalent to the D3D8 normalized `SRCALPHA` approximation.

The screenshots are paired to modes by user capture sequence and increasing filesystem times; the images do not encode the mode. France1 and camera bookmark slot 2 are reported in the session events, but identical camera pose bytes were not recorded. This is USER_RUNTIME_OBSERVATION with SCREENSHOT_CORRELATION, not PS2 parity evidence.
