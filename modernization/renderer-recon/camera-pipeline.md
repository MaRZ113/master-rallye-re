# Final camera, aspect, viewport and world transforms

**CONFIRMED_BY_EXE:** current camera setter `0x0056BAF0` stores the camera in
`[singleton+0x38]+4`; getter `0x0056BB50` returns it. Final 3D camera seam is
`ApplyCamera_005614A0`. It interpolates old/new camera bases (+0x38..+0x60 and
+0x88..+0xB0) and position (+0x68..+0x70 and +0xB8..+0xC0), normalizes/orthogonalizes
as needed, and constructs an inverse view for SetTransform(VIEW2).

Aspect is calculated as camera width+0x80 / height+0x84. Helper `0x004F2350`
returns the stored angle when width<=height, otherwise angle*height/width; conversion
constant VA `0x00690F54` is radians per degree. This is the stock linear aspect
rule, not an assumed atan-based horizontal-FOV conversion. `0x005D681F` constructs
a left-handed perspective matrix: cot(fov/2), far/(far-near), homogeneous w=z.
SetTransform(PROJECTION3) goes through `0x0053F9E0`.

Parameter setter `0x0056D020`, getter `0x0056D100` (renderer+0x54), fixes near=0.2.
ViewDist0/1/2 selects scalar=300/400/500. Ordinary projection far=2*scalar;
renderer flag+0x7C can select far=100000. Fog end/CPU visibility also use the scalar.
These are original values, not widescreen-patched behavior.

Viewport owner `0x005613E0`, reached by tail jump from `0x0056BB90`, copies camera
X/Y/Width/Height at +0x78/+0x7C/+0x80/+0x84 and depth range0..1 to cached SetViewport
at `0x0056148B`. Frame owner `0x00653080` reads client width/height through
`0x0064DD10` each frame, assigns rectangles for one/two/four cameras, and restores
the first camera to full-client dimensions before EndFrame. There is no separate
hardcoded gameplay aspect in that seam. Device mode/reset fields are separate:
fullscreen preference changes call `0x00541E90` and `0x0053F350`; windowed loss
refreshes the adapter format before Reset. Logical UI dimensions remain 640x480.

Orthographic seam `0x00561DF0` / `0x00561A40` uses logical 640x480, near/far
-1000/+1000 and identity view. Some text/sprite packets choose the 3D seam instead.
Do not replace every projection at Present or classify all text as screen-space.

World matrices: `0x00583B90` interpolates entity packet transforms into instance
+0x44, bypassing interpolation for a static flag. `0x00561A40` chooses 3D/2D,
handles camera-facing modes, and binds WORLD256; mode2 substitutes camera X/Z while
preserving object Y (useful sky lead). Debug `0x0058AD40` can attach to a scene
entity/2D packet or use identity. Vehicles and wheels enter this shared seam;
ordinary body/wheel matrices come from AISimulateeTransform `0x004F5440` reading
`Physics/<entity-name>/Transform` into packet+0x1C..+0x58. Entity creation and the
separate replay wheel path are detailed in [vehicles](vehicle-renderer.md).

**CONFIRMED_BY_EXISTING_RESEARCH:** G1's camera parameter readers at VA
`0x004B7FB0`, `0x004B8930`, `0x004B8C10` read fixed/follow records. Protected retail
Cameras.xml supplies FOV90 for several cameras. Mapping RaceTest Cameras markers
to those readers remains UNKNOWN. Gameplay/replay/frontend convergence to the
renderer is plausible, but their complete producer chains are not proved.

Future freecam/FOV/roll seam: override the final matrix pair at this boundary.
**STATIC_INFERENCE:** renderer-only overrides must also update/bypass CPU camera
culling and sky positioning. Pause-independent movement needs an application
clock/input seam still unresolved. No proven existing developer freecam was found;
camera editor flags are not treated as a working freecam.
