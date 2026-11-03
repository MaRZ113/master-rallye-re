# COURSE-ALIVE4: PS2 checkpoint barrels, PS2-AUDIO1: checkpoint sound and finish music

Three separate opt-in options of `PS2Port.ini`, default 0 = Stock:

| Option | What | Mechanism |
|---|---|---|
| `PS2CheckpointBarrels=1` | the 432 yellow PS2 checkpoint barrels (12 per course, all 36 courses) as physical props that the cars knock over; the PC checkpoint boards of that race are not drawn | COURSE-ALIVE3 proxy-side World (same asset, same physics, same draw) |
| `PS2CheckpointSoundOff=1` | no sample when a checkpoint is passed (the CHECKPOINT and split time texts stay) | three bytes of MRallye.exe (two sites), byte-verified |
| `PS2FinishMusic=1` | the race music keeps playing after the finish: no finish jingle, no fade-out of the music | five bytes of MRallye.exe, byte-verified |

## 1. Who makes the barrels physical on the PS2 (closed)

RIGID-PORT1 / CDELTA1 left this open: the 431 checkpoint model Eggs have no AI owner and are not `gaAiRigidBody` Eggs.
The owner is the split-time AI itself (SLES_509.06, static reverse, Ghidra EER + Rabbitizer):

| Address | What |
|---|---|
| `181dd0` | `gaRaceSplitTimeAI` init (vtable `473dd0` slot +0x34): nearest RaceLine marker, split arrays, then **owner+0x24 = 1** (barrels pending) |
| `181988` | update (slot +0x2c): `if (owner+0x24) 1822c0();` then the radius test of the cars |
| `1822c0` | for i = 0..3: `sprintf("%s-%d", own Egg name, i)` (`0x46fc10`), `21e9c0` finds the Egg by name in the scene; not found -> `"Splitpoint marker %s not found\n"` (`0x46fc40`), no barrel. Found -> `2ad408(0x3c)` + `19fcd0` = a new **gaAiRigidBody** owner with **+0x10 Casts Shadow = 1, +0x14 Mass = 500.0, +0x18 Trigger Distance = 5.0, +0x1c MOI = (487.5, 900.0, 487.5)** (words `43fa0000`, `40a00000`, `43f3c001`, `44610000`), then `262f88` sets the Egg's model to `misc\objects\checkpoints\checkpoint` (`0x46fc18`) and `21e620(egg, 0, owner)` attaches the owner to AI slot 0. Finally owner+0x24 = 0 |

From there the barrel is an ordinary RIGID1 prop: `19ff18` resolves `gaPhysicsManager` and creates the body from the
model's tag101 hull, `1a0258` runs activation / far decay / rest exactly as for the hay bales. So the PS2 checkpoint
barrel = hay bale physics with mass 500 and MOI (487.5, 900, 487.5) (the long axis Y gets 900).

Consequences:
- Every course: 3 splits x 4 Eggs = **12 barrels on each of the 36 courses, 432**. CDELTA1 counted 431 checkpoint model
  Eggs because SpainWFlip `SplitTime1-3` authors the Nessie stub; `262f88` overwrites it, so the PS2 shows a barrel there
  too (the port does the same).
- Barrel geometry `MISC\OBJECTS\CHECKPOINTS\CHECKPOINT.PSM` (4,924 bytes): meshes `drum` (c-point-tga + aluminium-tga,
  16 triangles) and `top` (top-tga + aluminium-tga, 12), both `$shader(metal)`; tag101 representation B = octagonal prism
  along Y, 16 points / 10 faces, radius 0.578, height -0.812..0.830 (base centre (0, 0.009, 0)).
- `$shader(metal)` = `3aeb00` (vtable `487c28`): mode 3 like `dull` (`3aeb50`), but **no** vertex colour auxiliary
  (the PSM prelight 0x8a stays) and no forced secondary: the secondary is the mesh's second texture, aluminium. Mode 3
  secondary = `Cd + Cs` (REFL1 gs-state-and-blending: FIX 128), environment coordinates from the view-space normal.
- PC has none of this: MRallye.exe has no `"%s-%d"` / `"Splitpoint marker"` string; the PC checkpoint is the board
  model `misc\checkpoints\checkpoint` (`i2a_planks2-tga` 48 triangles, `stamp_01-tga` 4) with no physics owner.

## 2. Port of the barrels

The COURSE-ALIVE3 route (the game knows nothing of the props):
- `tools/prepare_rigid_props.py` adds the family `checkpoint`: the PS2 PSM triangles directly (PC corner order, two-sided
  copies, PSM colours, PS2 UV), the three PS2 GXI textures in PC DXT row order (aluminium-tga: PC DXT rows == flipped GXI
  rows, exact), aluminium as the environment layer, the tag101 hull; and for each course the barrels by the `1822c0`
  rule from the PS2 RaceTest XML (Egg matrix, the constants above). Prop flag bit 1 = barrel. Asset `PS2RigidProps.ps2rgd`
  now: 36 courses, 515 props (83 + 432), 219,372 bytes, SHA-256
  `12750a3d8ea43976fd15555175b7a7b4094aa79bbe7acb42ffc4092ae3fa53da` (pinned). Inventory: [inventory.json](inventory.json).
- `RigidProps=1` selects hay bales and tumbleweeds, `PS2CheckpointBarrels=1` the barrels; each works without the other.
- Material `metal` = object pass (opaque, MODULATE, fog, depth written) + the additive environment pass (aluminium).
  Port contact coefficients (not PS2): restitution 0.3, friction 0.5, rolling resistance 1.5 / s.
- No drop shadow (as for the other props: the owner saw none on the PS2), though the AI writes Casts Shadow = 1.
- Course guard as COURSE-ALIVE3: only on an installed PS2 course package (the PS2 terrain).
- **PC boards hidden** (`rigid_props_native_integration.hpp: hide_checkpoint_board`, one line in patch 0001 in
  `draw_indexed_at` after the water draw): a native triangle-list draw is skipped when the race's World holds barrels,
  its stage-0 texture content is the PC `i2a_planks2-tga` (48 triangles) or `stamp_01-tga` (4 triangles) - SHA-256 of the
  locked 128x128 level 0, the GroundDetail rule - and its WORLD is not identity (an Egg model, not course geometry that
  shares the planks texture). Diagnostics: `ps2_checkpoint_board_hidden` (once), effect note `checkpoint_board_hidden`.
- Split timing is untouched: `gaRaceSplitTimeAI` of the PC still times the checkpoints, the barrels are only props.

## 3. PS2-AUDIO1

### Checkpoint sound (`PS2CheckpointSoundOff=1`)
PC `gaHudAiCheckPoint` (vtable `690de8`, update `4a4c30`): when `Race/Car%d/SplitPoint` grows it fades the CHECKPOINT
text (string 0xcd) in and, in the single block `4a4d2a..4a4d66`, sets the sample object (+0x10) to
`Sound/SFX/Volume x const` (`4f68f0`) and plays it (`4f66e0`). The PS2 ELF has no `gaHudAiCheckPoint`. Patch:
`4a4d28 74 3d` (JZ over the block) -> `eb 3d` (JMP). One byte written.

Game test 1 (owner, 2026-11-03): the patch was applied (`audio.checkpoint_sound_off.applied=true` in the session log) but
a checkpoint sound remained: the same event has a **second sample**. PC `gaHudAiSplitTime` (vtable `690f94`, update
`4a9050`, authored property `Audio Sound` at +0x10) prints the split time `%2d:%2d:%2d` when `Race/Car%d/SplitPoint`
changes and plays its sample in `4a912e..4a9168` (`4f68f0` / `4f66e0`, Sound/SFX/Volume x scale). Second patch of the
same option: `4a912e 68 e8` (PUSH 0x6af8e8) -> `eb 39` (JMP 0x4a9169, the epilogue; the block's x87 value is loaded and
stored inside it). The split time text stays. Remaining sample players near the HUD: `4a6840` = pace note HUD
(`Pacenote`), not a checkpoint event.

### Finish music (`PS2FinishMusic=1`)
PC `gaRaceFinishAI` (vtable `690c4c`): init `489af0` creates the sound object `Music/FinishJingle` (+0x1c). Update
`489ec0`, once the race counts as finished (+0x18): first time (+0x10 == 0) timer 0x546, `Sound/Music/FinishLoop = 1`,
jingle volume = music volume, `mov byte [jingle+0e], 1` at **`48a394`** (start), saved volume +0x38; then every tick
`Sound/Music/Volume -= step` while > threshold (`48a3ff..48a446`, written to the music player +0x24): the race music
fades out under the jingle. At the end-of-race transition the saved volume is written back.
PS2 `gaRaceFinishAI` update `17ed48`: same timer 0x546, log, end transition - **no** jingle (the string does not exist in
SLES_509.06), no FinishLoop write, no volume change: the race music goes on.
Patches: `48a394 c6 40 0e 01` -> `90 90 90 90` (one aligned 4-byte write) and `48a40a 75 3c` (JNZ to `FSTP ST0`) ->
`eb 3c` (the x87 stack stays balanced). `FinishLoop` is left as is: on PC it is only stored by the vehicle sound manager
(`408660` keeps the handle, nothing reads it), on PS2 only registered.

Both audio patches are applied once at proxy start (PS2PortExtension constructor), only when the image base is
0x400000 and every site of the option holds the original bytes (or already the patched ones). Verified sites: retail
`MRallye.exe` (SHA-256 `bf8aef32...5f96b4`), `MRallye_invitation5.exe`, `MRallye_cook_spain.exe`; `MRallye_patched.exe`
has other code there and stays untouched (reason `original_bytes_mismatch_untouched` in the status / disable log).
Status: `audio` in the PS2 port status JSON.

## Status
Offline: ctest `rigid_props_contracts` (barrel flag rules, member selection, metal coefficients, audio site rules;
private asset 36 / 515 / 432 when `MRR_RIGID_TEST_ASSET` is set). In game: **PENDING_USER**.
Private stress (`MRR_RIGID_TEST_ASSET` + each of the 36 installed course package DX, every prop kicked as by a car at
~15 m/s and 4 m/s up, 20 s): all 515 props start on their own PS2 ground; no NaN anywhere; 0 below ground on 35 courses;
TurkeyW: 2 of 12 barrels end under a higher ground layer (`ground()` finds a ground triangle 0.3 m above the centre) -
the COURSE-ALIVE3 contact code, which only pushes out of ground within 0.75 m, so the private run reports that FAIL.
Resting barrels lie on their side at 0.53 m (octagon inradius).
Not proved: the PS2 contact response (as COURSE-ALIVE3), the exact PS2 look of `metal` beyond the mode-3 contract.
