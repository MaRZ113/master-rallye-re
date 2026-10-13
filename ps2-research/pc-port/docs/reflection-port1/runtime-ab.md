# One-car reflection A/B

Use the PS2-enabled DLL in an isolated PC test setup. Installation is manual.
Keep a copy of the current proxy. Supported original MRallye.exe SHA:
bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4.
Enable the game's original Reflections option. In MRRRenderer.ini set
[VehicleReflections] Mode=0 (Stock); the pilot does not override ViewDependent2D.

The source tool uses the user's canonical private corpus:

```powershell
python ps2-research/pc-port/tools/prepare_reflection_pilot.py `
  --ps2-input-root "D:\Game\Master Rallye PS2" `
  --pc-retail-root "D:\Game\Master Rallye\corpora\retail\Data.sma_unpacked" `
  --sdk-root "D:\Game\Master Rallye\master-rallye-re-course" `
  --asset-out ps2-research/pc-port/.assets/reflection/PS2EnvSource64x64.gxi `
  --report-out ps2-research/pc-port/.analysis/reflection-port1/source-recheck.json
```

The original GXI is excluded from the handoff. Keep it local. Set
ReflectionSourceGXI to the extracted file's absolute path, or copy it manually
beside PS2Port.ini. Only payload SHA
aa15159a5f3f668244dd3b1c5c7b8322d8f41ac626c3a1741222b797252ad1e4 is accepted.

1. Start a fresh France1 race with the Tata vehicle and an undamaged body. Let
   native vehicle draws run for several seconds so the existing body oracle can
   establish wheel/body ownership. Save one Free Camera bookmark showing the
   bonnet. Use the same paint, lighting, resolution and quality settings.
2. First run with PS2Port.ini beside MRRRenderer.ini:

```ini
[PS2Port]
FoliageMode=0
PixelProbe=0
Diagnostics=0
ReflectionMode=0
ReflectionConfigVersion=1
ReflectionSourceGXI=<absolute path to verified PS2EnvSource64x64.gxi>
ReflectionDiagnostics=1
```

3. Restart with only ReflectionMode=1 changed. Restore the same bookmark and
   capture the bonnet. A second nearby orientation can show normal-based image
   motion. Keep the game's Reflections option and Stock coordinate policy fixed.
4. Retain the log and optionally one F10 capture for each run. Confirm a mode-1
   config record with effective_mode=1 and a material record with
   override_applied=true, exact geometry SHA, native draw result and successful
   restore result. Compare bonnet pattern/color, nearby body panels, glass,
   wheels and HUD. Only one bonnet material is affected.

Mode 1 emits one ps2_reflection_config event. ReflectionDiagnostics=1 permits
at most one rejected exact-geometry record and one applied record per device.
An initial vehicle_body_unverified may be followed by a successful application
after ownership warm-up. Restore failures are always reported.

If no applied record appears, retain the capture and reason; do not loosen
the classifier. Check the asset, executable, game's Reflections option,
coordinate policy, damage state and body oracle first.

Expected difference: the original PS2 static environment contribution on this
bonnet. Brightness improvement is not guaranteed. The 37.5% framebuffer term,
PS2 body grayscale and complete GS/VU behavior remain unimplemented.
Actual PC success and visual acceptance remain pending this controlled run.
