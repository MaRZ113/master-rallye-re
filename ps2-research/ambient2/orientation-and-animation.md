# Visual assets, orientation and wing animation

Bird allocation creates an en2d visual, not a skinned PSM bird. `1b0410` clears commands, sets bank from manager+28, world mode+64=0, billboard+74=1, flags+78|=6. Fly selection appends key0 and installs `gaImageBankSwitcher` in entity AI slot1; grounded selection appends key3. Slot0's FlyBird controls translation independently.

| Canonical named resource | Decoded size | Role |
|---|---:|---|
| `\TNG\DATAPSM\MISC\ANIMALS\BURDYBROWN.PSB` | 720 | Default image bank, four keys |
| `\TNG\DATAPSM\MISC\ANIMALS\BURDYWHITE.PSB` | 720 | Alternate branch if manager+94==0 |
| `\TNG\DATAPSM\MISC\ANIMALS\BURDYBROWN_000.GXI` | 16392 | Brown bank's64×64 atlas |
| `\TNG\DATAPSM\MISC\ANIMALS\BURDYWHITE_000.GXI` | 16392 | White bank's64×64 atlas |

Both F001/version125 PSBs map keys0/1/2/3 to corresponding images; each image has two authored triangles. Flight animation selects one of three alternative quads, not all eight source triangles at once. Initialization separately appends all four keys to the first free entity; its visible effect is not captured and must not be assumed invisible. Local bounds are frame0 `[-8,-3,8,13]`, frame1 `[-8,-12,8,4]`, frame2 `[-7,-12,9,4]`, frame3 `[-8,-11,8,5]`. Exact banks/atlases, offsets, texture references and SHA values are in `bird-resource-inventory.json`; full assets remain ignored. GXI's tested simple13039 format is RGBA; both alpha distributions are0/255,176 nonzero pixels. The reported channel interpretation is inherited from UI1's original visual/format study, not a live GS texture capture.

The bank chain is `1b0410 ->2062a8` identifier assignment; draw`337a98 ->305038` lookup; existing bank manager`380a08 ->380998 ->386d28` loads PSB; `387478 ->2fd7d0 ->2f84f0` resolves referenced GXI. Key lookup and `3376c0 ->311c50` texture binding connect actual Burdy bank records to the world sprite path. This is CONFIRMED_BY_BOTH for resources/consumer structure; selected live handles/VRAM format remain unknown.

`gaImageBankSwitcher` ctor`1b16a8` allocates0x20 bytes. Init`1b1770` clears commands and selects first key0. Update wrapper`1b17d0` calls`1b17e8`: when a visual exists, test `threshold3 < current_counter`; if true reset counter and call`1b1838`, otherwise increment. Thus a fresh counter0 advances key on the fifth invocation, then every five invocations; key cycles0→1→2→0. Ground key3 is outside that flight cycle. No skeletal joint, wing-bone rotation or UV animation is needed by this observed bank representation. A wall-clock flap frequency requires scheduler capture.

Renderer`337a98` handles mode0/billboard1 via`330530`. World-camera preparation`3387c8 ->36fc18` populates renderer+220..+25c from current camera data. For that matrix's row2 X/Z:

```text
F = (cameraRow2.x, 0, cameraRow2.z)
if both horizontal components are within +/-1.1920929e-6: F.x = 1
U = (0,1,0)
R = (F.z,0,-F.x)
linear rows = (R,U,F) scaled by the preserved uniform0.1
translation = previous en2d translation; W=1
```

The helper does **not** normalize F. The basis is Y-locked camera-dependent billboard orientation, separate from bird flight direction. Synthetic camera cases verify vertical fallback, zero vertical component in forward, preserved scale and camera-rotation dependence. Actual camera matrix values and resulting apparent size require a captured frame.

```text
FlyBird carrier XYZ --1b0508--> en2d XYZ
camera source --3387c8--> renderer+220 --330530--> Y-locked en2d basis
bank name + image key --337a98 PSB lookup--> paired triangles / atlas rect
paired triangles --337a98--> four CPU vertices --3376c0--> textured quad
```

There is no heading-to-billboard arrow: no such dependency was found. HAWK.PSM is a44-byte resource stub and is not assigned in this allocator; its name is not treated as the flight model. No visual species or live frame count is inferred from resource names alone.
