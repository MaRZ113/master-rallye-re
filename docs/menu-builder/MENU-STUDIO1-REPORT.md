# MENU-STUDIO1 — Final Integration, Safety & Reliability Pass

Branch `feature/menu-studio1` (worktree `master-rallye-re-menu`), based on `integration/base` a882c48 (Roster V4 fix 03,
the current Extra Options loader). Builder 1.1.0, runtime 1.1.0 (layout format 2, extension ABI 2).

## 1. What was wrong and what changed

| Area | Finding (review of `master-rallye-re-menu.zip` and this pass) | Change |
|---|---|---|
| Integration | `build_menu_builder.py` linked the "integrated" runtime against EXTRA-SET2 / SDK33 generated headers; the current loader already carried Menu Builder (cce283d/37d9d09) but the tool did not build it | integrated product = the current loader pipeline (`build_extra_capacity_candidate.py --menu-builder`, roster-independent V-CAP3/Roster V4); standalone product compiles from repository sources only (`RMOD_MENU_BUILDER_STANDALONE`, no Randomizer plan, no roster, no generated headers); exports @17 `MRMenuAbiV2`, @18 `MRMenuRegisterValueV1` |
| Integration | Vehicle Manager serves `VehicleSelect`, `QuickModeSelect`, `VehicleSetup3` from `MRMods/Vehicles/active/resources`; neither the editor nor the runtime saw that overlay, so an edited page would have replaced the roster page | `GameData` resolves overlay → loose → `Data.sma`; runtime `base_ok` asks `vehicle_roster::redirect` and serves a layout page only over the exact page it was compiled from |
| Integration | retail `Data.sma` ends with `SM\x05\x06` instead of the ZIP `PK\x05\x06`; the editor could not open an unmodified game (only re-packed archives worked) | `SmaStream` presents the signature as ZIP while reading; the file is never modified |
| Installer | `Directory.Delete(dir, true)` before writing; `SafeName("")` could address `Layouts` itself; names silently rewritten (collisions) | validated names (no empty/dot/reserved/invalid characters, no rewriting), sandboxed paths, no link traversal, staged compile + verification + atomic directory swap + rollback, interrupted-swap recovery, project identity guard, atomic `MenuBuilder.ini`, outcomes Installed / Updated / Validation Failed / Rollback Completed / Installation Failed |
| Compiler | element failures became `Notes` → warnings; the element vanished and the build went on | every failure is an ERROR with screen, element, type, operation, reason and fix; a requested element missing from the result is an ERROR; errors block every install path (CLI `--force` removed) |
| Editor | `OnGameFolder()` created a new `EditorSession` (history and dirty state lost; unsaved project could be shown as saved) | `EditorSession.Rebind` keeps project, path, dirty state and undo/redo; dirty state tracks the saved state; Save / Don't save / Cancel on New/Open/Close/Exit; atomic save; resource report after a folder change |
| Native elements | delete/rename of native elements unchecked; "Hide" (`en2d Visible=False`) left a native button drawn (verified in game) | dependency classes (Native Required / Optional, User Created, Unknown Dependency) with blocking + Hide/Disable alternatives; Hide parks the egg off screen, no hitbox, focus rerouted, command swallowed; Disable greys and swallows |
| Actions | free-form extension names; a fake `PAINT` demo; static caption for MODEL | typed catalog, required/optional bindings, one owner per ID, callbacks must be module code; live values from Extra Options (`vehicle.model_source`, `vehicle.tyres`); planned `vehicle.build/paint/apply` served disabled with fallback text |
| Mouse | a cursor resting over a button stole the focus when a screen loaded; click = focus + confirm in one frame was occasionally dropped | hover only after real movement; click focuses, confirms on the next frame |
| UX | resize showed only an outline; no snapping to neighbours; only project screens listed | live re-render while moving/resizing, eight handles with fixed opposite edge, smart guides; every frontend screen listed and opened on demand |

## 2. Test results

Builds: `.research-output/menu-builder/mb-1.1-studio1` (see `BUILD-PROVENANCE.json`).
Integrated `dinput8.dll` `ba04805d…` + runtime core `9146493e…` (owner-tested core, same sources as the rebuilt one);
standalone `dinput8.dll` `01f77caa…`. Evidence: `.research-output/menu-studio1-evidence/`.

### Unit Tested (headless, `MenuBuilder.Tests`, 149/149 on the owner's installation and on a host with the retail `Data.sma`)

* Installer safety: empty, blank, `.`, `..`, slashes, drive paths, reserved names, spaces, dots, over-long and
  non-ASCII names; `LayoutDir` refuses `..` and empty; collision with another project's layout (refused, explicit
  replace); failure injected at *staged*, *backed-up*, *published*, *activated* (previous layout byte-identical,
  `MenuBuilder.ini` unchanged, no temporary folders left); failed first install leaves nothing; interrupted swap
  recovery; read-only files; locked file (Installation Failed with the reason, layout unchanged); junction as layout
  folder, inside a deleted tree and as the Layouts folder (never followed, target intact); the Layouts root and the
  game folder cannot be deleted; neighbour layout untouched; uninstall of the active layout switches to Classic.
* Compiler: a failing element is an ERROR with screen/element/operation/fix and blocks installation without touching
  the installed layout; invalid identifier, missing retail egg, required action without handler, address-like action
  ID are errors; optional planned actions are warnings only; installed `project.mrmenu.json` reopens identical; value
  bindings and optional flags reach the runtime table; legacy action name maps to its catalog ID; unchanged retail
  screens are not served.
* Editor state: clean on open, dirty after an edit, clean again after undo to the saved state; every frontend screen
  (47) opens and renders without dirtying the project; rebind to the same and to a wrong game folder keeps path,
  dirty state and history and reports missing resources; Save As; reopen identical; a failing edit is rolled back
  and not recorded; two sessions stay independent; a new project is dirty.
* Dependencies: retail Quit blocked for delete and rename, screen controller Native Required (not hideable), new
  element User Created; Hide gives no hitbox, reroutes navigation, blocks the button in the runtime table, keeps the
  egg and parks it off screen in compiled pages; a path into a hidden element is an error; deleting a user element
  leaves no navigation reference; Disable keeps the hitbox but blocks the command.
* Smart guides (edge, centre, threshold, resized edge), roster overlay precedence, retail archive signature.

### Integration Tested

* GUI self-test (`MenuBuilder.exe --selftest`, real pointer handlers, on the isolated host): 10/10 — all frontend
  screens listed, move snaps to a neighbour line, live resize keeps the left edge, Shift+corner proportional, game
  folder change keeps dirty state/path/undo, blocked delete. Snapshots `studio1-editor-selftest/`.
* CLI/Python: `install` outcomes, `edit` with dependency guard (blocked delete exits 1 with the dependency list),
  `deps`, `actions`, Python `Project.new` name check, transactional install via the API.
* Patch-site audit of the integrated loader (`patch-site-audit.json`): 368 sites, 0 preimage mismatches, 6 known
  overlaps between other owners, none with Menu Builder (`vfs-createfile 0x64D573`, `screen-name 0x45D865`,
  `host-init-slot 0x690540`, GetCommand detour `0x45D930`).

### Game Runtime Tested (isolated hosts; never the owner's game folder)

Host `mb-integrated` = copy of `host-roster-v4-01` (Roster V4 roster, renderer, Extra Options INI) with the
integrated loader of this build; host `mb-standalone` = retail data + renderer + standalone loader.

| Configuration | Result |
|---|---|
| Extra Options + Menu Builder + Renderer (`studio.autotest`) | 24/24: all modules ready (Randomizer `BOOT_B_READY`, `SDK_BINDING_PROFILE_MATCH`, `REGISTRY_READY count=35`, Extra Options and Ghost ready, roster overlay 469 files, Menu Builder ready); VEHICLE CONFIG values `MODEL: PS2`, `TYRES: STOCK`, `BUILD/PAINT: NOT AVAILABLE`; MODEL SOURCE and TYRES change the Extra Options state (`APPEARANCE_SELECTED … source=menu-builder`, `TIRE_SELECTED … source=menu-builder`) and the values follow; BUILD/PAINT/APPLY served disabled and pressing them does nothing; hitboxes; VEHICLE SETUP opens the native Vehicle Setup through `native.forward`; Back/BACK button |
| Hidden/Disabled on a retail screen (`runtimechecks.autotest`) | 14/14: hidden Progress not drawn, not focusable (Options ↓ Quit), no hitbox, click does nothing; disabled Multiplayer greyed and refused; planned PAINT served disabled |
| Widescreen matrix (`run_ws_matrix.ps1`) | 5/5 cases (Preserve margins 16:9, Centered 16:9, Stock 16:9 borderless 1920×1080; Preserve margins 4:3 window 1024×768; Preserve margins 21:9 window 1680×720): served variants 16:9/16:9/4:3/4:3/21:9, autotest 6/6 each, a real OS mouse click on MODEL SOURCE hits the button and runs the action in every case; game captures and editor renders at the same size align (`compare-*.png`) |
| Quick Race from the Menu Builder frontend (`race.autotest`) | race starts; Randomizer `START ADMITTED` + `AI_ROSTER_FINAL` (player CarID 26, add-on pool reported), Extra Options in race. `TIRE_BINDING_PENDING` appears identically with the published loader 80561f21 (A/B), i.e. not a Menu Builder regression |
| Extra Options without Menu Builder (no `MenuBuilder` folder) | boot, SDK profile, native install, registry, Extra Options, Ghost all ready; the folder is not created |
| Menu Builder switched to Classic | `CLASSIC … native frontend unchanged`; all modules ready |
| Old runtime (published loader 80561f21) + format-2 layout | `LAYOUT_FORMAT unsupported` → Classic (no partial serving) |
| Standalone Menu Builder + Renderer, retail data (`standalone.autotest`) | 13/13: Extra Options actions served disabled, values `MODEL: N/A`, `TYRES: N/A`, navigation, Back, Credits |
| Retail save from another roster | a `PlayerState.xml` with an add-on CarID crashes the plain game at `MRallye.exe+0xD162A` on Quick Race — identically with Menu Builder in Classic (A/B); not a Menu Builder defect |

### Owner Test Pending

* Physical gamepad navigation on the new and edited screens (all scripted input went through `UI/Control`).
* Everyday mouse use by a person (hover/click/right-click Back) in the owner's own installation and renderer
  settings; the scripted matrix used one real OS click per configuration.
* The original Master Rallye without the D3D8 renderer (exclusive fullscreen of the retail D3D8) with the standalone
  runtime; covered only by Menu Builder 1.0 runs (`q4-no-renderer`).
* 21:9 on a real 21:9 monitor (tested in a 1680×720 window).
* Extra Options + Menu Builder in the owner's full Definitive Edition install (Atmo-copy/owner hosts), including
  Ghost and five difficulties in a race, DEMO model variants from VEHICLE CONFIG, and the AI/extra car distribution
  over several races.
* Editor usability on the owner's display (DPI) — the self-test runs at 1600×1000.

## 3. Known limits

* Car names (Broker strings) cannot be shown by a text element on a custom screen yet; the catalog has no
  vehicle-name value (tried in game: renders `N`).
* PrintWindow captures of a running race are blank; race checks rely on the module logs.
* `vehicle.build/paint/apply` remain planned until V-CONFIG1 registers them; the demo shows them as unavailable.
