# VEHICLE-LIGHT1: PS2 vehicle lighting contract for PS2 models

User observation: transferred PS2 models look too bright/glossy compared with PS2
(PC body near full texture brightness with a strong blue environment sheen; PS2 shows
darker paint, readable decals and a visible but additive environment).

## Evidence (refl1, static EE reverse; no new RE claims)

- `body-reflection.md`, EE `322220`: carshiny and carflat source vertex colours are
  overwritten by a model-space normal-Y grayscale
  `gray = clamp(CVT((.225*ny + .4)*255), 2, 254)`, RGBA `(gray,gray,gray,254)`, cached at half
  (`31f4e0`); GS primary `TFX=MODULATE`, i.e. `tex * vcol / 128` → effective factor `gray/255`
  (≈ .18 underside … .40 vertical sides … .63 roof).
- `gs-state-and-blending.md`: mode3 secondary is `DECAL` with ALPHA `…29` = `Cd + Cs`: the
  environment adds in full, not weighted by the base alpha.
- All PS2 CAR/COMPLETE assets carry white source colours (`0xFFFFFFFF`, checked on Tata,
  NewRav, Ufo), so the port drew bases at factor 1.0 and used the PC-native
  `MODULATEALPHA_ADDCOLOR` (`Cur + Cur.a * Env`).

## Change (`VehicleLighting=1`, default; `0` restores the previous look for A/B)

- `FrontendModel` applies `ps2_prepared_vertex_color(ny)` to every mode 1/3 mesh of every PS2
  model (race CAR, COMPLETE, wheels, private OFF). Normals are the original source normals.
- The mode-3 environment stage becomes `D3DTOP_ADD` (Cd + Cs) for those models.
- Native PC bodies (Stock or damaged native fallback with Mode 4) are unchanged.

Test: `ps2_prepared_lighting_contract` (159/102/45 at ny = 1/0/-1, clamps, alpha 254, modes 1/3 only).

## Not changed yet / next

- Environment image mix (0.625 static + 0.375 flipped framebuffer) and its brightness.
- Glass mode 20: PS2 adds the static WINDSCREEN-REFLECT at 0.75 (`Cs*.75 + Cd`) with masked depth;
  the user noted strong glass reflections — next step.
- Fog on the primary layer (PS2 FGE=1), CVT rounding mode (nearest assumed).
No pixel parity is claimed; this ports the recovered equations.
