# X-Trail frontend A/B

Close the game and detach the debugger before manually replacing the proxy DLL. Preserve the previous working DLL and INI. No installer is provided.

1. Copy dist/current/ps2-enabled/d3d8.dll manually to the existing proxy location. Keep existing Mode 4 reflection assets/settings.
2. Copy the local .assets/vehicles/XTRAIL-COMPLETE.ps2model beside the active PS2Port.ini (normally MRRRenderer). This private original-asset resource is intentionally absent from the handoff ZIP.
3. Add these keys to the existing [PS2Port] section without deleting grass/water/reflection configuration:

```ini
FrontendModelMode=0
FrontendModelVersion=1
FrontendModelAsset=XTRAIL-COMPLETE.ps2model
FrontendModelDiagnostics=1
ReflectionMode=4
FoliageMode=0
PixelProbe=0
```

Record Stock X-Trail selection from front/side/rear. Restart with FrontendModelMode=1; allow a complete warmup frame. Capture the same rotating views and F10. Compare body silhouette, wheel rim/tread, bumpers, interior and glass. This replaces COMPLETE only; race body/decal/headlight/Terrano brake behavior should remain unchanged.

Switch to another car and back, leave/re-enter selection, then perform the usual window Reset and repeat with supported MSAA. Other vehicles must retain Stock geometry. Check menu FPS and absence of duplicate models, detached wheels, missing glass or flickering. Record any offset or lighting mismatch rather than accepting it as PS2 parity.

Bounded log records: ps2_frontend_model_warmup (24 records), ps2_frontend_model_replacement (4636 private faces, draw/restore HRESULTs), ps2_frontend_model_suppression (24 source records). Missing replacement or fallback means Stock, not successful replacement. Save screenshots and the current session/F10 logs. No new x32dbg capture is required for this first A/B.
