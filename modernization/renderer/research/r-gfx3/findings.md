> Closed by the user's final short retest on DLL44a76a3a…; see ../r-gfx4/r-gfx3-final-baseline.json. The following records the preceding preparation and remains historical.

# R-GFX3 findings

**READY_FOR_SHORT_RETEST.** Human results for DLL307a5fe4… establish default-off parity, usable AF/race FOV, isolated shadow Off and pristine Reset. They also expose a frontend 3D preview FOV leak. The final fixes keep MAG stock and add the source90 camera-family gate. New DLL runtime is pending; see closeout.md and runtime-handoff.md.

CONFIRMED_BY_EXISTING_RESEARCH: projection returnRVA0x0013FA75 /VA0x0053FA75 differs from VIEW returnRVA0x00161A26 /VA0x00561A26. Shadow is DrawPrimitive returnRVA0x001881EB /VA0x005881EB, not DrawIndexedPrimitive. Stock/Off is preserved; opacity remains DEFERRED.

CONFIRMED_BY_RUNTIME_TRACE: source angles90 for all five race camera captures,45 for frontend preview; resolution-independent reconstruction error below0.000003 degrees. HUMAN_REPORTED: visual A–F outcomes in the closeout request. Camera selector mapping is STRONG_CORRELATION rather than exact dispatch proof. No new lighting, reflections, weather or backend work began.
