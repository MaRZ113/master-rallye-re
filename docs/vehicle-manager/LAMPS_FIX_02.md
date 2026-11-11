# Roster V4 lamps and Mercedes glass — fix02

Private candidate: `.research-output/hosts/host-roster-fix-02`.
Parent: the actual `host-roster-fix-01` transaction/resources. Original hosts,
Pristine, EXE, Extra Options and saves are not modified. The rebuilt renderer
is included only in the new private candidate. No automatic installation or
gameplay acceptance is implied.

## Forklift description

The original EXE has two separate authorities:

* `0x45A150`, ID25 case at `0x45A282`: Bonus2 (unlock flag15), or the existing
  UnlockCars/UnlockAll bypasses.
* `0x4819B0`, locked-description branch: ID25 selects localization group6,
  index26. The row at `0x6C9E20` points to `0x6CFFD8`, the literal
  `UNLOCK BY WINNING 1 T1 CUP`. This is the misleading text in the screenshot.

REA/Ghidra and independent x86/native emulation confirmed those paths. The
inspected normal award routines do not set Bonus2; the original reset routine
clears it. No new Cup reward is invented. The candidate substitutes
`UNLOCK WITH UNLOCK CARS CHEAT` only for the locked ID25 description. Bonus2
and UnlockAll still work. All34 other description branches and all unlock
rules remain unchanged. The added message is English; original localization
tables are untouched.

The description shim chains the existing RVP bridge and resumes the native
string setter at `0x481B64`. It occupies unused executable payload space,
outside the existing writable pages, within the original512KiB allocation.
MRVR1/RVP1/MRVC1, physical IDs and descriptor maps are unchanged.

## Blazer lamps

Nine authored native addon models now use the original retail ChevyBlazer ON
core and glow topology, UVs, colours, normals, material states and textures:
Mercedes, ImprezaProto, LancerEvo4, Trooper, ForesterSTI, Rav4, Tomcat,
Evo2FourRunner and HeritageNewRav. Each side is positioned and uniformly scaled
to that model's existing lens bounds. The Lancer's existing high centre strip
gets a separate fit preserving its horizontal footprint. These are adapted
Blazer effects, not claimed historical addon-specific lamp originals.

The original OFF lenses remain, including under the ON overlay. Non-brake
geometry, UVs, material states, glass alternatives and collision are preserved
through the Vehicle SDK scene/native-state APIs. Serialization can change
vertex/index layout; tests compare actual triangle attributes and logical
state selectors, not raw file equality.

Forklift has yellow body panels and a rear grille, with no optical surfaces.
Following the owner's explicit choice, its model stays unchanged and both
glow presets have no effect on it.

The existing global `PS2Port.ini` setting is reused:

* `BrakeGlow = 0`: PC Glow. Native Blazer core/halo textures and blending;
  no renderer extension is needed for the native PC lamp assets.
* `BrakeGlow = 1`: PS2 Glow. The existing stock renderer transaction uses
  its PS2 core/glow assets and additive halo, as on the reference Blazer.

This is independent of MODEL PC/PS2. Restart the candidate when changing the
glow preset. The two supplied launchers set only this existing setting and
refuse to edit it while this candidate is running. They do not touch other
hosts or require a new Extra Options build.

## Mercedes glass

The source model had no native glass switch. Vehicle SDK `auto_features.derive`
identifies its separate translucent `windscreen32` draw. Native-state
authoring creates screenfront, screenleft and screenright alternatives and
uses the original stock cracked-windscreen texture. The intact/off triangle
attributes/materials and collision are verified against the source. Brake
lenses are selected explicitly from rear `mblight64` triangles; automatic
redness selection is deliberately avoided because it also catches red paint.

## Optional renderer catalog

`MRMods/Vehicles/active/addon-brake-lamps.tsv` starts with `MR-ADDON-LAMPS 1`.
Each record contains family, layer (0 core /1 glow), vertex/triangle counts,
and geometry/position-UV binding digests. It is generated from the final SDK
models. There is no compiled list of addon IDs or texture SHA permissions.
Texture/livery edits do not invalidate a lamp binding. Geometry or UV edits
require regenerating the binding with the model.

Native queue ownership, buffer generations/revisions, material tokens and
texture lifetime remain mandatory. Healthy witnesses are stored per
participant/profile, including duplicate cars, and discarded on race/device
reset. An unqualified damaged mesh falls back to native rendering. Stock lamp
profiles are unchanged. Missing/invalid catalogs also keep native rendering;
diagnostics report the catalog status once.

The parser admits at most2MiB/4096 draw-role records and validates ambiguity,
counts and syntax. These are defensive resource budgets, not vehicle-capacity
or engine limits. The registry is optional and creates no required DLL-to-DLL
dependency.

## Reproduction

From the BASE checkout, Python3.11 with Pillow, Capstone, Unicorn and NumPy:

```powershell
py -3.11 tools/vehicle_lamp_authoring.py --source-host .research-output/hosts/host-roster-fix-01 --output-host .research-output/hosts/host-roster-fix-02 --sdk ../master-rallye-re-vehicles
py -3.11 ps2-research/pc-port/overlay/build_overlay.py
```

Use a fresh output directory. Copy the resulting **PS2-enabled** renderer from
`ps2-research/pc-port/.build/ps2-enabled/Release/d3d8.dll` into the new candidate
only; preserve the source host's DLLs. The overlay builder checks the accepted
immutable renderer baseline and applies the current port sources. No stale
staging source files are substituted into the working source tree.

```powershell
py -3.11 tools/verify_vehicle_lamps.py --source-host .research-output/hosts/host-roster-fix-01 --candidate .research-output/hosts/host-roster-fix-02 --sdk ../master-rallye-re-vehicles
py -3.11 tools/test_vehicle_lamp_native.py --candidate .research-output/hosts/host-roster-fix-02 --sdk ../master-rallye-re-vehicles --output .research-output/vehicle-fixes-02
```

## Validation and remaining visual gate

* Native caller emulation: all 35 registry initializers identical to fix01,
  including every Progress Bar colour; four Bonus2/cheat combinations pass.
* Forklift message shim executes correctly; all 34 other locked-description
  branches retain their previous native results.
* Nine models preserve body/glass triangle attributes and collision. Mercedes
  additionally passes SDK intact/off equivalence and has three glass zones.
* Actual C++ parser accepts all 18 generated bindings and rejects malformed,
  ambiguous, unsupported and over-budget data.
* Native C++ checks match all 18 actual geometry/UV fixtures, reject corrupted
  geometry/UVs and wrong owners/textures, and exercise damage, duplicate
  participants and reset invalidation.
* Warm geometry-catalog lookup is approximately 0.06 microseconds per layer in
  the local CPU fixture benchmark; uncached matching is approximately 145.
  This is not a gameplay frame-time measurement. Owner/material proof is
  deliberately repeated at every draw.
* Renderer build: baseline 24/24 CTest; PS2-enabled 47 passed,1 skipped;
  Python integration 208 tests,6 skipped. Proxy export verification passed.

Status: **OFFLINE_VALIDATED / OWNER_GAMEPLAY_PENDING**. No game was started by
the authoring, validation or build tools.

Use the two `Launch-roster-fix-02-*-Glow.cmd` files under the hosts directory:

1. Forklift with cheats off: correct description and blocked selection; with
   existing UnlockCars enabled, selection remains available. No lamp effect.
2. Trooper, Rav4 or ForesterSTI: brake released/pressed in PC Glow, then PS2
   Glow, comparing halo shape/brightness with the reference Blazer.
3. Mercedes: front/left/right glass damage; released/pressed brakes in both
   presets. Confirm there are no disappearing body surfaces or stray glow.
4. One race containing multiple addon cars: player/AI ownership and damaged
   lamp continuity. Use diagnostics if a layer falls back to native rendering.

The precise perceived brightness, placement, glass break triggers and
alternate MODEL appearances remain owner visual/runtime gates. Current data
covers the native model resources authored in this candidate; a future model
with different lamp geometry needs its own generated bindings.

Current reports and source/build hashes are in the candidate root. Parent
fix01 reports are retained under `provenance/presentation-fix-01` as history.
