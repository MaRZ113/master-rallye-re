# First runtime A/B: KiaSportage

Install manually only after closing the game. Copy this release d3d8.dll to the existing proxy location and files in assets/ to the existing PS2Vehicles directory. Keep other accepted assets. Do not replace original game data. Preserve existing working settings, including X-Trail asset paths, COMPLETE, grass/water and MSAA4x.

In [PS2Port], add:

```ini
RacePS2ModelMode=1
RacePS2FleetMode=1
RacePS2ModelAssetDirectory=PS2Vehicles
RacePS2ModelDiagnostics=1
ReflectionMode=4
RacePS2FleetCapture=1
```

The existing `RacePS2ModelAsset` must still point to accepted `PS2Vehicles\XTRAIL-CAR.ps2model` (or your existing valid path). RacePS2FleetMode=0 is the new fleet Stock comparison; the accepted X-Trail path remains active. Do not change successful wheel/crew/parts settings.

1. Select KiaSportage, enter a one-car practice race. Wait one full rendered frame for the native environment warmup. Use the same course, camera/bookmark, lighting and MSAA for both settings. F10 at rest, then drive/steer and F10 again. Inspect all sides: authentic CAR body/interior/crew should replace the full native body, while native wheels steer, rotate and suspend independently. No double people/body, floating sections or changed gameplay should appear.
2. Hold brake and F10, release brake and F10. OFF base, ON lamp and additive glow are separate surfaces. Reflection must not spread over the whole lamp. PS2 RGB-fade glow uses native original geometry; shape differences are documented.
3. Damage Kia and F10. New fleet policy intentionally returns the whole body to Stock on unsupported private/changed damage geometry. There must be no mixed/double PC/PS2 body. X-Trail's accepted damage support remains separate.
4. Restart, return to menu, select another vehicle, return to Kia, then Reset the window with MSAA4x and repeat. Menus/HUD should remain smooth. Exit normally to flush JSONL.
5. Compare with RacePS2FleetMode=0 after a full process restart. Then validate other families individually using coverage.md; never record a whole-family PASS solely from registry admission.

Bounded session records: `ps2_fleet_car_replacement` (family, asset SHA, current packet/instance, source count, submitted faces, draw/restore HRESULTs); `ps2_fleet_car_source` (F10 only, each source once per child, exact hash/current upload generations/revisions); `ps2_fleet_car_fallback` (gate, whole_frame_stock); `ps2_fleet_car_world_rejected` (exact packet modes); `ps2_fleet_car_invariant_failure` (not retroactive Stock); `ps2_brake_glow` (vehicle, exact current-upload identity, apply/draw/restore HRESULTs). Gate1 resource/init/matrix;2 cohort/private-tree;3 environment/Mode4;4 capture/stage compatibility;5 ValidateDevice;6 final current-owner/token check;7 ordinary owner WORLD contract. Existing probe capture is capped to32 F10 activations and64 rows per activation. No thousands of per-draw identity lines.

If Kia remains Stock, provide the normal-exit session JSONL and one F10. Do not loosen a hash or enable a guessed owner to force visible output. First acceptance is a real moving Kia with no duplicate body; all other family runtime rows remain pending until measured.
