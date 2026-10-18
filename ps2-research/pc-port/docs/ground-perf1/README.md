# GROUND-PERF1: GroundDetail cost per course draw

The user reported that `GroundDetail=1` costs about 20 FPS in a normal race. It costs as much in split screen
with `PS2SplitScreen=0`, because GroundDetail is gated by the exact PC noise texture, not by the race
certificate.

## Cause

F10 frame 30009 (one view) has 151 `shader/base_noise` course draws (caller 0x57707e, stage1 MODULATE2X).
For each one, the native path issued:
* about 17 `Get*` calls for the contract check;
* one `GetDeviceCaps` call;
* 22 `Get*` calls for the transaction capture;
* 3 sampler `Get*` calls;
* about 21 state writes, plus 21 restores, each also recorded through `Trace::after`;
* 2 draws.

That is about 13k extra D3D calls per frame per view.

## Change (identical output)

* The contract checks, the sampler reads, the pixel shader and the transaction capture use the proxy's
  tracked native state (`Trace::effective_shadow`). It is updated by every forwarded write and by every
  native-only write of the PS2 layers. The device is read only for a value that is not tracked.
* The device caps are checked once per native device.
* `GroundDetailTransaction::set` skips a value that equals the captured one. Such a state is neither written
  nor restored.
* The two-pass PS2 subtract stays. The second pass is the PS2 contract: noise is subtracted after fog,
  unfogged. Folding it into stage1 `SUBTRACT` would apply fog to the noise, so that is not done.

## Runtime A/B

Same scene, `GroundDetail=1`, compare the FPS with dist/perf2: normal race and split screen. Then set
`GroundDetail=0` to see the remaining cost. The ground look must be unchanged.
