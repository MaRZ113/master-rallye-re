# PILOT1.3 runtime correlation

## Inputs and pairing

The four user-provided images are in
`C:\Users\MaRZ\Documents\ShareX\Screenshots\2026-10`; matching session and
F10 files are in `D:\Game\Master Rallye Pristine\MRRRenderer\logs`.
Screenshots `0.jpg`–`3.jpg` have increasing filesystem times from
22:14:01 to 22:15:43 (+10:00), all 1920x1080. Their order is paired with the
session-selected modes by user capture sequence and file times; the images
do not embed the mode. Each session reports France1 and a load of camera
bookmark slot 2. Camera pose bytes are not embedded in the screenshot or
session mode events, so exact camera equality is not asserted.

The session JSONL logs include 27, 27, 15 and 22 malformed/truncated lines
for sessions 1–4 respectively; their relevant mode and identity rows still
parse. The session's `capture_written` paths do not exist under their original
basenames. The four supplied frame files were matched by the terminal frame
number and their internal capture IDs (`d1-f5291`, `d1-f2909`, `d1-f1876`,
`d1-f1580`). Every supplied F10 file is complete, has zero dropped records,
and zero malformed lines.

## Target identity and single draw

All four frames contain exactly one
`DrawIndexedPrimitive(4,11940,28,22944,48,...)` at zero-based draw index 45.
The call returns `0` (`D3D_OK`). The active modes 1–3 each have one
`ps2_port_draw_identity` event with `TARGET_IDENTITY_CONFIRMED`,
`override_applied=true`, and `pre_draw_restore_ok=true`. All three share:

* geometry SHA-256 `2b60b1f044601052bb5eaeca074615abe3947fdc1b0769c17d300a0b3b3e6f7d`;
* vertex buffer generation 624, revision 248;
* index buffer generation 625, revision 337.

This ties the four experiments to the same geometry/resource generation, not
merely the `bush01` texture name. Mode 0 selects Stock with mask 0 and has no
PS2 identity event.

## Native state changes around the target

All logged native `SetRenderState` calls below use feature mask 128,
`native_only=true`, `forwarded=true`, and HRESULT `0`. The F10 draw record
retains the pre-draw logical state snapshot; separate `native_override`
records show the temporary native writes and their later restoration.

| Mode | Target frame/sequence | Native state writes immediately before | Writes after draw | Restored to frame snapshot? |
|---|---|---|---|---|
| 0 Stock | 5291 / 147 | none | none | n/a |
| 1 all states | 2909 / 150 | ATEST=0, BLEND=1, ZWRITE=0 | ZWRITE=1, BLEND=0, ATEST=1 | yes |
| 2 alpha bundle | 1876 / 149 | ATEST=0, BLEND=1 | BLEND=0, ATEST=1 | yes; no ZWRITE event |
| 3 depth only | 1580 / 148 | ZWRITE=0 | ZWRITE=1 | yes; no alpha-state event |

Unchanged SRCBLEND=5 and DESTBLEND=6 already matched the requested values, so
they did not need native `SetRenderState` calls. The frame-audit tool verifies
that every state actually changed before the target has a post-draw write
back to its pre-draw snapshot. The target draw occurs once in each capture.

The generic frame field `native_override_applied` remains false in these
records because the PS2 extension reports its own identity event; it is not a
reliable indicator of the extension. The sequence of native-only state writes
and the extension event are the evidence used here.

## Visual observation

The screenshots show:

* **Mode 0:** the foreground bush is visible with the original PC cutout look.
* **Mode 1:** the foreground bush is largely absent.
* **Mode 2:** the foreground geometry appears as bright/white rectangular
  foliage cards, with the bush image visible on portions of the cards.
* **Mode 3:** the foreground bush is again largely absent, while surrounding
  trees and course objects remain visible.

This is USER_RUNTIME_OBSERVATION with SCREENSHOT_CORRELATION. Mode 3 changes
only depth writing and reproduces the disappearance in this view, so
disabling ZWRITE is sufficient for that symptom. Mode 2 leaves ZWRITE enabled
and exhibits a separate alpha/texture-stage artifact. Some surrounding scene
details also differ between stills. The selected bookmark is consistent, but
the camera pose is not recorded byte-for-byte, so these images do not support
pixel registration. Neither result proves which later draw covers any bush
pixel or why the PS2 path works with ZMSK=1.

## Ordering clue, not an overdraw proof

The separate earlier F10 frame 7608 has 704 draw records and places the same
source call at draw 46. 658 records follow it. Those later records are not
reliably classified as landscape foliage, and the capture does not record
per-pixel coverage. It therefore shows that later draws exist, not that any
particular one overwrites the bush. See [next.md](next.md).
