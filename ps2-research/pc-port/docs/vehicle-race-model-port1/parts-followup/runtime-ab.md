# CAR static parts follow-up

Previous race chassis is now confirmed by user observation and F10 frame44168/6057:13 private draws/1712triangles/13 original suppressions, all successful HRESULTs. See runtime-confirmed-44168.json. This does not prove full CAR parity.

This opt-in extension adds PS2root5(28faces),root11(14faces) and root19glass(18faces). Exact source PC records21,22,10 respectively are validated by current queue owner, geometry hashes, resource generations/revisions, native bindings and chassis WORLD. Each private mesh replaces only its corresponding native draw at the same boundary. Glass uses mode20 and originalPS2UV; lamp surfaces retain mode3. All changed state restored; cached source identity is revalidated after resource updates. No draw ordinal or texture-only authority.

Close the game and manually install the new DLL. Keep XTRAIL-CAR.ps2model unchanged beside active PS2Port.ini. Keep RacePS2ModelMode=1/Version=1/Diagnostics=1 and ReflectionMode=4. Add RacePS2ModelParts=1. ModeParts0 retains the accepted1712-face chassis pilot; default0. Restart between controls.

Inspect X-Trail front lights and glass from front/side/rear while moving and steering. New bounded ps2_race_model_part events identify root5/11/19, source_geometry_verified, private_faces28/14/18 and successful draw/restore HRESULTs. They are additional to chassis events. Compare braking, camera angles, race restart, windowReset and MSAA4x; no duplicate or missing panels should appear. Save F10 and screenshot. Native wheels, driver, mixedblacktrim, brake-state/glow and conditionalwindows remainStock. Original assets and renderer unchanged; no automatic deployment.

New surfaces are IMPLEMENTED_PENDING_USER_RUNTIME. Headlight source material approximation and glass sampling are not PS2 visual parity. WHEEL source is unique in examined PC corpus, but current wheel-parent ownership still needs a bounded certificate before replacing four independently moving instances. Mixedtrim requires per-face masks across multiple PC groups, not whole-draw deletion. Those are exact remaining contracts, not implemented here.
