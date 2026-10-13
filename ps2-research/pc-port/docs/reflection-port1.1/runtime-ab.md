# Reflection A/B: one Tata body-panel material

Use the new PS2-enabled DLL only after manual installation in your test game.
Preserve the previous DLL and INIs so rollback is immediate. No original game
asset or executable is replaced. The supported original MRallye.exe SHA-256 is
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.

Use the game's original Reflections option. Keep `[VehicleReflections] Mode=0`
in `MRRRenderer.ini`; retain the original PC coordinate generator. For Mode 4,
turn MSAA off for this controlled test; unsupported multisampled source copying
must produce a fallback reason rather than silently change quality settings.

Place `PS2Port.ini` beside the renderer INI. Keep other experiments disabled:

```ini
[PS2Port]
FoliageMode=0
PixelProbe=0
Diagnostics=0
CourseObjectsMode=0
CourseObjectsDiagnostics=0
ReflectionMode=0
ReflectionConfigVersion=1
ReflectionSourceGXI=<absolute path to verified local PS2EnvSource64x64.gxi>
ReflectionDiagnostics=1
```

The GXI must match payload SHA-256
`aa15159a5f3f668244dd3b1c5c7b8322d8f41ac626c3a1741222b797252ad1e4`.
Use the existing `tools/prepare_reflection_pilot.py` and your canonical private
PS2 corpus to prepare it. The handoff deliberately excludes original image data.

1. Start France1 with the same Tata, paint and undamaged body. Let original
   vehicle draws run briefly so existing race/body ownership can establish.
   Save a Free Camera bookmark showing both the hood and roof. Keep resolution,
   weather, lighting, game options and bookmark fixed across runs.
2. Capture Stock (`ReflectionMode=0`) first. Restart after each mode change;
   restore the same bookmark. Do not compare a different vehicle/camera by eye.
3. Capture Mode 1: the previous weighted static ENV + ADD result. Mode 2 keeps
   that image but preserves original COLOROP. Mode 3 keeps the original image
   but changes COLOROP to ADD. These two controls separate image replacement
   from the combination operation.
4. Capture Mode 4: the mixed ENV/framebuffer experiment. Retain its first
   capture status and native HRESULTs. If allocation/copy/composition is
   unsupported, the target stays Stock; this is not a successful dynamic test.
5. Save one screenshot and one F10 capture for each run. Check hood and roof,
   windshield, bumper, other painted parts, wheels, HUD and background. At
   least one second camera orientation helps distinguish normal-based sampling
   from merely a fixed tint. It does not prove a PS2 environment camera.

Compare 0 against 4 for the full new result; compare 0 against 3 and 1 against
2 to isolate COLOROP. Compare 1 against 4 for the framebuffer-source change.
RGB changes alone do not prove a stronger or more faithful reflection.

Expected diagnostic evidence is bounded config/identity/capture reporting, not
thousands of per-frame records. Retain mode, actual override mask, source
classification, exact geometry signature, resource generations, frame ID and
native apply/draw/restore HRESULTs. For Mode 4 also retain copy/composition
result and source/target dimensions/format. A selected mode without successful
application is not an enabled reflection result.

The accepted target is compiled record 19, spanning hood and roof regions.
The historical `bonnet` classifier label is retained for compatibility; no
other materials are authorized by that label. Unknown owner/material/resource
state must fail closed.

Runtime statuses remain distinct: previous Mode 1 **technical success**;
new modes **pending live verification**; **PS2 visual parity not established**.
Do not infer that the 48/128 component matches original PS2 pixels: capture
timing, source framebuffer, projection, base shading and color precision differ.
Keep foliage PILOT1.4 and Turkey3 object testing separate from this comparison.
