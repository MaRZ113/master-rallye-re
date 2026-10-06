# Camera findings for R-GFX3 closeout

Camera/Setup XML is captured in Observatory continuation_lines; it is not a scalar Broker value. closeout-evidence.json records 12 input hashes and extracted values, including 20261006-165543_gfx3-c_racefov-80-cam1.json. All have three Follow and two Fixed cameras, all authored FOV90. Camera/SplitSetup has separate parameters and is outside the runtime gate.

CONFIRMED_BY_EXISTING_RESEARCH: pristine helper VA0x004F2350 /RVA0x000F2350 uses authored angle unchanged when W<=H, otherwise angle*H/W (frozen modernization/renderer-recon/camera-pipeline.md). This is not a horizontal-FOV trigonometric conversion. CONFIRMED_BY_RUNTIME_TRACE: race VFOV67.50000031 at640x480 and48.14062244 at1920x1027; preview33.74999835 and24.07031241 respectively. Reconstructed source families90 and45; maximum error0.000002804 degrees over all captured symmetric projections. Policy tolerance is explicitly0.01 degrees, over3500 times measured error but far from45 or unknown source families.

| Human selector | Likely owner | Approximate local XYZ from supplied snapshot correlation |
|---|---|---|
| default | Follow0 | (-0.19,1.53,-6.51) |
| cam1 | Follow1 | (-0.18,2.14,-8.29) |
| cam2 | Follow2 | (-0.39,1.46,-6.97) |
| cam3 | Fixed0, hood-like | (0,1.60,2.12) |
| cam4 | Fixed1, low bumper/ground-like | (0,0.44,2.26) |

Mapping and positions: user-supplied STRONG_CORRELATION / LIKELY, not confirmed dispatch ownership. These rounded relative coordinates are historical snapshot observations; they were not recalculated by this closeout tool. They are not authored offsets or a reconstructed follow algorithm. Follow0: Smooth Camera Multi0.30, UsePitchSystemFalse, AccelTrue. Follow1:0.70, True, Pitch Limit80, AccelTrue. Follow2:0.30, False, AccelFalse. These values are independently extracted from Broker XML in the digest.

The fix reads only the final original projection. It does not write Broker, VIEW, camera position/roll, authored setup, smoothing or culling. An unknown source family forwards stock. A future consumer using the same90 family and callsite cannot be distinguished by this rule; replay/split-screen and other untested modes must not be called validated.
