# User runtime checks

Close the game before replacing the DLL or copying assets. This task deploys
nothing automatically. Save the previous DLL/configuration and install the new
PS2-enabled proxy manually into the isolated PC test installation.

## Vegetation resource installation

The game already has GrassMode2/ShrubsMode2 and the correct directory setting.
However, only6/72 resources are installed. Copy **all72 `.ps2grass` files** from:

`D:\Game\Master Rallye\master-rallye-re-general\ps2-research\pc-port\.assets\grass\`

into:

`D:\Game\Master Rallye Pristine\PS2Grass\`

This is a manual file-copy instruction, not an executed deployment. All files
were verified against source hashes. Preserve the existing matching six files;
the66 missing names/hashes are in `vegetation/deployment-inventory.json`. They
are private original-source assets and are not included in the public/source
handoff. Directory contents are read at process initialization, so start a new
game process after copying. No original DX/DXT/XML/EXE file is edited.

Keep these keys in the existing `[PS2Port]` section, preserving all other settings:

```ini
[PS2Port]
FoliageMode=0
PixelProbe=0
ReflectionMode=4
ReflectionCoverage=1
ReflectionDiagnostics=1
GrassMode=2
ShrubsMode=2
GrassAssetDirectory=PS2Grass
```

Use the existing valid ReflectionSourceGXI path and previously accepted
ReflectionTargetPrecision/MSAA settings. Mode0 remains the general default.

## Reset reflection test

1. Start Tata or Kia in a race, confirm Mode4 reflection and capture a fixed
   Free Camera view/F10 before changing window state.
2. Restore/maximize the window using the same route that previously caused
   failure. Return to the same camera/lighting after the device is operational.
3. Capture F10 and an image after reset, then restart the race once. Do not
   interpret transient device-loss/invalid race frames as accepted draw identity.
4. Collect the new session log. Look for `ps2_buffer_mirror_reset` counts and
   a new capped `ps2_reflection_material` applied record after successful reset.
   A native Reset failure suspends the effect; an internal reset echo never
   advances the PS2 generation or repairs failed Reset admission.

Two identity records per vehicle can recur after a real successful Reset;
there is no new per-frame logging. The mirror Reset event occurs once per
wrapper Reset and only when reflection diagnostics are opted in.

## Course checks

First load France2, Italy1, Spain1 and Turkey1, then another previously missing
course. Compare GrassMode0/ShrubsMode0 with bothMode2 at the same location, away
from the main road if necessary. Not every terrain triangle is eligible. Then
switch courses, restart and return to menus; check FPS and HUD hiding. Existing
Turkey3/France1/ItalyS1 should remain unchanged. Full-course visibility/performance
after installing all files is pending user runtime, not implied by72 source files.

## Remaining vehicle and lamp boundary

The six mixed/unjoined principal body groups are not newly activated. Do not
expect this Reset correction to repair their entire painted surface. The new
source findings show that dynamic body reflection must not be blanket-applied
to glass/carflat or lamp-on/glow subsets. See `body-lights/findings.md`.
Frontend models are feasibility-only; no menu replacement is enabled.
