# Lamp scope revision - fix03

The owner confirmed working lamps and Mercedes glass breakage in fix02.
This revision restores the original ImprezaProto, LancerEvo4 and
Evo2FourRunner car.dx and applicable original lamp textures from fix01.
These independent addons are removed from the optional PS2 lamp catalog.
The twelve catalog layers for the six demo families remain unchanged.
Mercedes glass, Forklift behavior, vehicle identities and progress colors
are preserved. Forklift still has no lamps in either mode.

Build a fresh sibling host using Python 3.11:

```powershell
py -3.11 tools/vehicle_lamp_scope_revision.py --source-host .research-output/hosts/host-roster-fix-02 --original-host .research-output/hosts/host-roster-fix-01 --output-host .research-output/hosts/host-roster-fix-03
py -3.11 tools/verify_vehicle_lamps.py --source-host .research-output/hosts/host-roster-fix-01 --state-host .research-output/hosts/host-roster-fix-02 --candidate .research-output/hosts/host-roster-fix-03 --sdk ../master-rallye-re-vehicles
py -3.11 tools/test_vehicle_lamp_native.py --candidate .research-output/hosts/host-roster-fix-03 --sdk ../master-rallye-re-vehicles --output .research-output/vehicle-fixes-03
```

The resource baseline is fix01; the mutable state baseline is the actual,
owner-tested fix02. Its current saves and settings are copied, never reverted
to the older asset baseline. EXE, MRVR transaction and both DLLs are unchanged.
Only Data.sma is hardlinked; mutable files are independent copies.

## Configuration

The existing Renderer already reads `[Vehicles] BrakeGlow` from PS2Port.ini
v3: 0 retains native lamps, 1 enables PS2 Glow. ModelChoice does not force this
setting. Missing/invalid optional role data falls back to native rendering.
The BrakeGlow constructor reads this configuration at Renderer creation;
restart the game after changing it. This is not a live toggle.

Use `Launch-roster-fix-03.cmd` to preserve the existing configuration.
The older PC-Glow/PS2-Glow launchers explicitly write a preset before startup.
No new Renderer build is required for this resource-only revision.

## Verification

Automated checks compare every retained inherited file, original addon models,
native registry, all 35 vehicle initializers, collisions, demo lamps and
Mercedes glass state declarations. Native tests use actual twelve-layer
geometry, test rejection and owner/damage/reset behavior, and instantiate the
accepted Renderer BrakeGlow class with both v3 configuration states and real
PS2 assets, without a GPU or game process.

Owner visual check: inspect the restored three addons and one retained demo
car under BrakeGlow=0 and 1, restarting between settings. Prior fix02 glass
and lamp acceptance is retained; fix03 is offline-validated until tested.
