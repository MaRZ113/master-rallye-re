# X-Trail static CAR + original WHEEL A/B

Close the game before manually installing the new DLL. Keep the accepted COMPLETE/CAR resources and all existing graphics settings. Copy local XTRAIL-WHEEL-DRAW.ps2model beside the active root PS2Port.ini. Do not use XTRAIL-WHEEL.ps2model: that is the unsplit research resource, not this runtime format identity.

Retain in [PS2Port]:
```ini
RacePS2ModelMode=1
RacePS2ModelVersion=1
RacePS2ModelAsset=XTRAIL-CAR.ps2model
RacePS2ModelParts=1
RacePS2ModelDiagnostics=1
ReflectionMode=4
```

First test trim with RacePS2WheelMode=0. Additional black trim should fill the missing body portions. The shared driver draw keeps its38 native triangles and replaces only four proven trim triangles. Parts mode0 remains the control for the already accepted original1712-face chassis; parts1 now reaches1832 originalCAR faces excluding helmet/conditional branches.

Then restart with:
```ini
RacePS2WheelMode=1
RacePS2WheelVersion=1
RacePS2WheelAsset=XTRAIL-WHEEL-DRAW.ps2model
RacePS2WheelDiagnostics=1
```

Use a single-participant X-Trail race. Wheels require current accepted chassis plus four source signatures per current wheel owner and a completed warmup frame. Multiple participants or unknown owners remainStock. No wheel physics are replaced. Test steering left/right stationary, moving forward/reverse, suspension over bumps, front/side/rear cameras, braking, damage, restart, menu return and real windowReset/MSAA4x. Check wheels roll and steer independently rather than staying frozen under chassisWORLD. Look for doubles, gaps, wrong spin/UV, missing rubber or reflections on tread. Capture F10 with steering and again after Reset.

Bounded events: ps2_race_model_replacement private_faces1726 whenparts1; part events cover18glass/28lamp/14lamp/34mixedtrim/8trim/4trim. MixedPC17 also forwards38 original native triangles. Wheel events: ps2_wheel_warmup source_records4 per slot, ps2_wheel_replacement native_wheel_world_preservedtrue, source_geometry_verifiedtrue, successful draw/restore HRESULT. Per-wheel sourceparts72/36/54/90 faces,252 total; fourwheels1008 total. Warmup/frame logs and F10 are the authority; absence is Stockfallback, not invisible success. Gate0race/chassis,1owner/world,2bindings,3owner slot,4sourcehash,5warmup,6materialsource,7statepreflight. Records are capped per reset lifetime.

Driver helmet/body and conditional brake/intact/cracked screens remain native. Frontscreen branches share identical geometry/UV/normals and require current texture identity. Do not infer PS2 parity from the static source match. New trim/wheels await runtime validation; previous chassis/glass/lamp paths are user-confirmed.
