# PS2-COLOR1 — opt-in PS2Color tone curve

User request (2026-10-17): after LIGHT2 the car is close, but the PS2 picture looks more "processed";
add an opt-in key with a tone curve fitted to screenshot pairs. This is an approximation of the PS2
picture, **not** a recovered PS2 material/light contract, so it is off by default (`PS2Color=0`).

## Curve and fit

Per channel, `y = (1 - k) x + k x^2` (k = 0 unchanged, k = 1 is x^2). `fit_tone_curve.py` compares
quantiles (5..95 %) of matched regions (`pairs.json`) and solves k per channel by least squares.
Pixels are never compared one to one: PS2 framing, FOV, grass and HUD differ.

Six pairs (Turkey hill, U3 start, Eldorado, BFGoodrich start x2, replay gate), 20 regions
(`fit-result.txt`):

| | k_R | k_G | k_B | RMSE (0..255) |
|---|---|---|---|---|
| fit | 0.426 | 0.384 | 0.364 | 27.3 -> 18.6 |

* Every environment region in all six pairs is darker on PS2; the fit removes 30-70 % of the error on
  sky, rock, road, ground and banners.
* A separate saturation term was tested on region means and gives no gain (best s = 0); the extra
  saturation the user sees is the curve itself (darker mid-tones, same highlights).
* Residual left: PS2 dirt roads are darker and more saturated than any global curve gives
  (road saturation 0.36 -> 0.45 on PS2, 0.39 after the curve).
* **Conflict:** the LIGHT2 car body already matches PS2 (Turkey: R 89 vs 87); the global curve makes
  it ~20 % too dark (66). The world, not the output, is what is brighter on PC. A proper fix is the
  course prelight/material contract (PS2 course vertex colours), which stays the recommended next
  research step; PS2Color is the requested stop-gap.

## Renderer

`renderer/ps2_color.hpp`, called once per `Present` (patch 0001, quality_wrappers Present hunk) with
the scene closed and the backbuffer as the current target:

1. `CopyRects` backbuffer -> private D3DPOOL_DEFAULT render-target texture (pow2-padded when required;
   MSAA only as a same-size whole-surface resolve, like the reflection capture).
2. Pass A: `dest *= (1 - k)` — SRCBLEND ZERO, DESTBLEND SRCCOLOR, colour = TEXTUREFACTOR.
3. Pass B: `dest += k * copy^2` — SRCBLEND ONE, DESTBLEND ONE, stage0 TEXTURE*TEXTURE, stage1 *TFACTOR.
4. All 45 touched states, viewport and stream 0 are restored in reverse order; a failed restore stays
   pending and is finished by the existing `repair_reflection()` chain (`native_states_pending`).

Fixed-function only (MODULATE, SELECTARG1/2, two stages, ZERO/ONE/SRCCOLOR blends, point filter).
The texture is released in `ps2_port_reset_begin` before `Reset`. Session log: one `ps2_color`
record whenever the outcome changes (`graded`, or the skip/failure reason).

Applies to the whole frame including HUD and menus. Not reproduced: PS2 video output/TV encoding.

## Keys

```
PS2Color=1
PS2ColorCurve=0.426,0.384,0.364   ; optional, R,G,B in 0..1; invalid -> default
```

Baseline lock: patch 0001 sha256 updated (Present hook, reset release, `ps2_color_contracts` test).
