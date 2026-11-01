# V-SET1 — In-process livery and tire setup pilot

## Delivered boundary

V-DEF4.1 is **USER_RUNTIME_CONFIRMED**, from the owner's report that all runtime
tests succeeded. This does not independently resolve the previously recorded
Randomizer F3 hook conflicts. V-SET1 is a **new offline-qualified candidate**;
original-game startup, selection, tire consumption and controller hardware are
still **PENDING_OWNER**. No game was launched during implementation.

The pilot targets existing physical **CarID21, SCHLESSER BUGGY 1997 / SeatBuggy**,
single-player Quick Race only. There are no new vehicles or IDs. The accepted
33-row 8/12/13 roster, custom ordering and Forester/RAV4/TOMCAT resources remain
unchanged. Other cars use their accepted native rendering and Stock physics.

Private launcher, relative to this checkout:
`.research-output/vehicles/v-set1/pilot-01/delivery-final/Launch-V-SET1.cmd`.

## Menu and deployment

From the original Vehicle Setup **Gearbox page**, press **F6**. A small owned
Win32 modal runs inside the game process: Paint/Livery, Tires, Apply, Defaults,
Cancel. This is a windowed fallback, **not a newly authored MR-rendered frontend
screen**. It requires a captioned game window; exclusive fullscreen is not
qualified. Native keyboard dialog navigation works in the own-process test.
WinMM joystick POV/button navigation is implemented; physical controller tests
remain pending. F6 entry requires a keyboard in this pilot.

Apply atomically saves the two independent choices under
`host/VehicleSetupState/mr-seatbuggy-ps2-v1.ini`. Cancel does not write; Defaults
changes the draft until Apply. Schema, identity, CarID and preset-contract hash
are checked on reopening. Changed contracts require explicit review/reset;
championship and accepted player saves are never migrated or rewritten.

The private host contains a byte-identical EXE copy and a privately built
extension of the accepted PS2-enabled renderer. The installed Proxy and its
source worktree are untouched. A separate EXE location is required by Windows'
DLL search order; this is not a duplicated game installation. Existing sealed
CMD resource-root handling is reused, with 424 immutable hardlinks and separate
copies of options.xml/PlayerState.xml. Do not edit linked resource files.
The inherited 414-resource index and 264-operation addon plan match exactly.
The wrapper hash gate remains disabled; relevant native preimages are checked.

The builder requires an accepted native/Stock fleet baseline and rejects other
wrapper composition, rather than silently disabling an existing full PS2 fleet.
The PS2 assets remain owner-local in `D:/Game/Master Rallye Pristine/PS2Vehicles`.
To disable the pilot, set `Enabled=0` in the private `host/VSET1.ini`: no setup
hooks are installed and native Stock rendering remains. Do not remove that
marker or launch the private EXE directly; the supplied CMD checks its presence.
General DLL installation/version coverage and Randomizer composition remain
separate milestones.

## Livery evidence

Original SeatBuggy CAR.PSM SHA256:
`3244c3decf33634d035cae682fa886acd9d86982250cbc64060a65109585c3f7`.
The existing converted CAR assembly has 3131 vertices, 1813 triangles, 19 draws,
18 textures; its complete file SHA256 is
`63fdd21c0dfdee697edac6dd406e338e12c786321a228620e43d4de04a061b4b`.
The selected PSM was reread through the existing PackFS reader and matched.

| Choice | Provenance and coverage |
|---|---|
| PS2 original | Unchanged original geometry, UVs, textures and material ownership |
| PC sponsor panels (reconstructed) | Original retail PC RGB on two individually checked receiving PS2 panels; original PS2 alpha retained sample-for-sample |

`seat07-tga` has 675/675 receiving PS2 corner coordinates witnessed in PC UVs;
the reverse witness is 674/675, so topology/corner-multiplicity parity is **not**
claimed. `seat02-tga` has identical 111-corner UV multisets. Stored PC rows are
explicitly inverted for the PS2 renderer's coordinate convention. The transfer
changes only RGB of these two maps. `seat06-tga` has only609/2954 receiving
corners witnessed and is **excluded**. All geometry/index/UV data, other maps
and alpha remain original. Owner inspection must still confirm panel appearance.

This is **not a recovered complete second shipped PS2 livery**. It is a bounded
RECONSTRUCTED PC/PS2 combination with authentic sponsor pixels. Full original
skin selection remains unresolved. No missing decals were painted or stretched.
Private `livery-panels.png` shows exact original/derived panel differences.
Runtime replacement requires family, texture index, dimensions and full original
pixel equality; unrelated atlases cannot receive a global substitution.

Pixel coverage is deliberately modest: seat07 changes3344/16384 RGB pixels;
seat02 is already identical after row normalization (0/4096 changed). The second
choice demonstrates scoped sponsor-panel replacement, not a different complete
body paint scheme. The user's remembered second full SeatBuggy skin remains
unlocated; this prerequisite is not promoted to a historical livery PASS.

## Tires and original native consumers

SeatBuggy Stock is **FrontTest / RearTest**, not harddirt. These original XML
selectors have no complete explicit five-record coefficient table in the XML.
Stock is therefore `NATIVE_PASSTHROUGH`: no writer override at all. It is not a
guessed reconstruction of the native defaults. The alternate is original
retail **gravel**, all five records ×12 fields, with exact source strings and
table hash `89f45e36393af33a1dd5a09c416db0255407cf7b5546ecf59b772bd1480a375b`.
No tire coefficients, mass, suspension, hubs or source family are modified.

Original PC evidence uses PE32/base0x400000 and bounded REA disassembly. Addresses
below describe the investigated build, not universal patch locations:

- Gearbox vtable0x690b60: **Tick +0x10 /0x690b70 →0x483d20**;
  **Init +0x14 /0x690b74 →0x4839d0**. Both roles are checked. The Tick hook
  forwards its opaque argument and original return value without float guesses.
- 0x4938c0 calls front0x496d20 at0x493935 and rear0x498090 at0x493942.
  Both original publishers always execute first. The original0x493600 builds
  `Vehicles/CarN`; only exact `Vehicles/Car0` can receive the override.
- The original broker setter0x4d85f0 writes front/rear instance `TyreType`
  after publication and before wheel initialization. No owned source strings or
  shared named-vehicle profiles are patched. Singleton0x4d8ec0 has no arguments.
- Original0x490720/0x490920 consume TyreType and publish/default tire records;
  0x441ac0 initializes native defaults. Full wear/cache/force-law behavior is
  not claimed recovered. The next-race consumer remains an owner test.

Nine native API signatures, both complete call instructions, both menu vtable
roles and image layout are validated before mutation. Partial installation
attempts roll back exact writes. Python and native code use one adapter table,
not an EXE-SHA allowlist. Out-of-scope mode, split-screen, attract/replay, AI
PlayerType0, non-Car0 and other physical IDs cannot receive tire overrides.
No per-frame solver writes or live tire changes are introduced.

## Reusable authoring

`vehicle_setup.py` defines bounded `vehicle-setup/1` contracts, independently
selected liveries/tires, source pins, alpha preservation, explicit material/stage
ownership and complete original coefficient records. Dropped secondary stages
are rejected. `setup_sources.py` reads the existing converted PS2 interchange;
it is not a second PS2 importer. Source DWORD vertex colors remain typed DWORDs.

Vehicle Studios → **In-game Setup pilot** opens separate asynchronous package
authoring. It supports labels, stable family/ID, original-table selection,
defaults, recipe import/export and private panel preview. The open vehicle is
not edited. Per-car source mappings are in `research/vehicles/vset1`, not hook
logic. This first native proof compiles a validated package descriptor; a fully
dynamic arbitrary-package loader is future work. Optional per-livery menu/HUD
artwork and marker metadata are retained by the contract; this pilot does not
replace accepted artwork/marker resources.

## Mégane follow-up evidence

Schlesser `megane` remains separate from Michelin Mégane F2. Original PS2
CAR.PSM SHA256 `6ee866b563309d1a9205cd99b2706fa3c7471d984daa3b4d954fa60e33bd0248`,
3630 vertices /1992 triangles. Some PC atlas coordinates correspond, but whole
livery replacement is unqualified: sblogo128414/423, rplogo6466/66,
sdoors128198/198 (reverse194), logostrip6472/96 receiving coordinates witnessed.
The retained complete Demo Audit records 8.4.1 2732/1922; its rebaked copy has
the same surface fingerprint. Later9.10.0 and retail geometry differ. Those
Demo counts are historical audit evidence, not freshly decoded by V-SET1.
Available inventoried9.3.1 sources have no Mégane family: **MISSING INPUT**, not
proof it never existed. No Mégane restoration/import was attempted.

## Validation and owner checklist

- Focused Python: **66 PASS**, including malformed presets, dropped stages,
  alpha, path containment, deterministic state and player/mode guards.
- Full Python suite: **1388 run, zero failures/errors, two explicit skips**:
  private J.2 reentry bundle and private vmesh412 fixture unavailable.
- Complete private renderer CTest: **44/44 PASS**.
- Own Win32 modal: create/confirm/cancel/default/persistence and mock native
  publisher/scope/pixel tests PASS. Actual Tk authoring window smoke PASS.
- Prior protected inventory: **1160/1160 unchanged**, including originals and
  accepted builds. Native resource/patch plan index unchanged. Adapter accepts
  unrelated EXE-byte changes but rejects required API/call/vtable conflicts.

All original-game results below are **PENDING_OWNER**:

1. Launch the supplied CMD in windowed mode. Check the accepted vehicle order
   and Forester/RAV4/TOMCAT still appear. Select SCHLESSER BUGGY 1997, Quick Race.
2. On Vehicle Setup/Gearbox press F6. Check keyboard, Cancel and Defaults; test
   controller POV/buttons if supported. Confirm no frozen input on return.
3. Compare PS2 original versus reconstructed PC sponsor panels in frontend and
   the next race. Check decals, glass, wheels and accepted damage fallback.
4. Compare Stock versus gravel. Inspect private log for separate front/rear
   `APPLIED ... Car0` lines; log writes alone do not prove tire forces. Confirm
   AI and another vehicle retain Stock. No mid-race switching is offered.
5. Finish a race, Results, return/re-entry, relaunch and verify sidecar choices.
   Check disposable candidate save/resume independently; championship mode is
   not enabled for setup. Test Enabled=0 as a separate launch.

Stop here. No new import, capacity increase, original shader parity claim,
in-game fullscreen frontend redesign, runtime tire switching or publication.
