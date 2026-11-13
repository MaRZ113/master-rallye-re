# Master Rallye Menu Builder 1.1

WYSIWYG editor and native runtime for the Master Rallye PC frontend. Layouts are designed on the
real scene files with the game's own sprites, fonts and icons, compiled to native
`DataScene/FrontendScreens/*.xml` scenes and served to the unmodified retail `MRallye.exe` by the
dinput8 loader. Sizes, positions, focus navigation, hitboxes and actions seen in the editor are the
ones the game uses: preview and runtime share one layout model and the runtime reads the live eggs.

| Part | Location |
|---|---|
| Core library (formats, scene model, compiler, validator, renderer, installer, editor session) | `tools/menu-builder/MenuBuilder.Core` |
| Editor `MenuBuilder.exe` (WPF, .NET 8) | `tools/menu-builder/MenuBuilder.App` |
| CLI / machine API `mrmenu.exe` (JSON) | `tools/menu-builder/MenuBuilder.Cli` |
| Python API | `tools/menu-builder/python/mr_menu_builder.py` |
| Native runtime (dinput8 loader module) | `src/native/rmod1/menu_builder_runtime.{hpp,cpp}` |
| Tests: headless core tests, in-game autotests, game driver | `tools/menu-builder/MenuBuilder.Tests`, `tools/menu-builder/test` |
| Example project | `examples/menu-builder/demo.mrmenu.json` (MAIN MENU edit, OPTIONS > MENU BUILDER, QUICK RACE > VEHICLE CONFIG) |
| MENU-STUDIO1 report | `docs/menu-builder/MENU-STUDIO1-REPORT.md` |
| Reproducible build | `tools/build_menu_builder.py` |

## 1. How the native frontend works (research summary)

All addresses are for the retail image `bf8aef32…` (MRallye.exe 3,121,214 bytes).

* **Scenes.** Every frontend screen is a scene `DataScene/FrontendScreens/<Name>.xml`
  (`EggLists_Version4`): a list of *eggs* (`en2d Matrix` row 3 = authored position, 640×480,
  y up; rows 0/1 = scale; `en2d Model Name` = 2D image bank; `Draw Priority`, higher = further
  back) each with up to four *AIs* (`gaFrontendStandardButtonAI`, `enUITextButtonAI`,
  `gaFrontendMultistateAI`, `enUIFormattedTextAI`, …). Optional `<Name>.hnt` lists textures to
  preload. 47 of the 54 table entries exist as scenes.
* **VFS.** The file open `0x64D530` first calls `CreateFileA` on the relative path (call site
  `0x64D573`, `FF 15 [0x68F1E0]`), so a loose file wins over `Data.sma`.
* **Screen table.** 54 `enString` names at `0x6F5BD8`, built at `0x448C60`. `GetScreenName`
  `0x449CF0` (`thiscall(out, id)`, `RET 8`) rejects IDs ≥ `0x36`; the screen change
  `0x45D6C0` builds `"FrontendScreens/" + name` and loads it (call `0x45D865`).
* **Screen AIs.** Each screen egg carries a `gaFEScreen<Name>AI` whose init creates a command
  helper `{screenId, pending, ready}` (`0x45D610`, restores `Frontend/LastActive%d`) and whose
  tick calls `GetCommand` `0x45D930` (`thiscall(helper, sound)`, `RET 4`) and requests screens with
  `0x45D910`; the change is committed by `0x45D6C0`. `GetCommand` reads `UI/Control`
  (7 up, 1 down, 2 left, 3 right, 4 accept, 5 back, …) and `UI/Active`, returns the focused
  Button ID on accept (`-3` back, `-2` accept without focus, `-1` nothing) and plays the frontend
  sounds. Screen AI init/tick take one stack argument (`RET 4`).
* **Focus.** Each `gaFrontendStandardButtonAI` stores Up/Right/Down/Left paths (`0x5257B0`) and,
  when focused, moves `UI/Active` on `UI/Control` (`0x45C6D0`). Its tick selects the button image by
  state (`0x45C420` → `0x525630`: 0 normal, 1 focused, 2 disabled, 3 disabled+focused) and pulses
  alpha. A `gaFrontendPopupAI` shares the Button ID of its `ButtonEgg` and registers its own paths;
  when the ButtonEgg has no button AI (VehicleSetup RESET) the popup *is* the focus target.
* **Labels.** `enUITextButtonAI` (`0x524EB0`, layout `0x525440`/`0x525280`) justifies its text in
  the egg image box (`0x52EB20`: 0 left/top, 1 centre, 2 right/bottom), draws icon `Icon-1` of
  `Frontend\Icons\ButtonIcons` at local (4, −5); fonts come from the font table `0x6CD2F8`
  (1 Arial_12, 2 Arial_16, 3 Arial_24, …), texts from the gaLocal tables (`0x485C20`,
  rows `{group, index, char*}`, English `0x6C9A60`). The egg matrix scale applies to sprite, label
  and icon alike (verified in game).
* **Assets.** `.dxb` tag-125 image banks: `u32 0xF001, 125, N, N×{code,image}, M` images of
  triangles `{6×f32 uv, 6×i32 xy, u32 len, texture}`; local y grows downward, screen_y = egg_y −
  local_y. All 113 retail banks parse exactly. `.dxt` = 20-byte header + BGRA rows (bottom-up).
* **No native mouse.** The retail frontend has no pointer input; the runtime adds hover/click on
  top of the same focus mechanism using the compiled hitboxes.

## 2. Quick start (everyday use)

1. Start `MenuBuilder.exe`, pick the Master Rallye folder (the one with `MRallye.exe` and `Data.sma`; the retail
   archive and re-packed archives are both read, nothing in the game folder is modified).
2. **Screens** lists the project's edited screens and below them **every frontend screen** of the installation;
   clicking one opens it (it becomes part of the project only when you edit it).
3. Drag a button with the mouse. Smart guides snap its edges and centre to the other elements and to the screen
   (magenta lines); `Shift` locks the axis, `Alt` disables snapping, the grid step applies when no guide matched.
4. Resize with any of the eight handles: the scene is re-rendered live while dragging, the opposite edge stays in
   place, the label shows size and percentage; `Shift` keeps proportions, `Alt` scales from the centre.
5. *Insert* adds a new element (long/curved buttons, option rows, arrows, texts, live value text, images, panels).
6. In the property panel choose an **Action** (e.g. `navigate.screen`, `native.forward`, or a typed game action such
   as `vehicle.model_source`) and, for a value text, a **Live value** source with a format like `MODEL: {value}`.
7. Switch *Aspect* (4:3, 16:10, 16:9, 21:9, any window size) and *UI mode* (Stock, Centered 4:3, Preserve margins)
   to preview the widescreen layout; *Edit this aspect only* writes geometry to that variant.
8. Save (`Ctrl+S`), check the **Validation** list (`F7`): ERRORs block installation, WARNINGs do not.
9. *Game → Install & activate* (`F8`) publishes the layout transactionally and reports Installed / Updated /
   Validation Failed / Rollback Completed / Installation Failed.
10. Start the game (*Game → Launch*); *Switch to Classic menus* returns to the native frontend.

No XML, EXE or hook configuration is edited by hand at any step.

## 3. Projects

A project (`*.mrmenu.json`, `format: "mr-menu-project"`, `version: 1`) is a **delta** over the pages the game
loads; the retail baseline is never copied or modified. Schema: `docs/menu-builder/project.schema.json`.

```json
{
  "format": "mr-menu-project", "version": 1, "name": "Demo", "id": "5f0c1d1e6a8b4e0c9a7d3b2a1c0e9f01",
  "settings": { "mouse": true, "aspects": ["4:3", "16:10", "16:9", "21:9"], "language": 0 },
  "styles":     { "MenuButton": { "textOffsetX": 110, "vJustify": 1 } },
  "components": { "LongButton": { "template": "MainMenu/OnePlayer", "style": "MenuButton" } },
  "screens": [
    { "name": "MainMenu", "kind": "retail", "base": "MainMenu", "defaultFocus": 1,
      "elements": [
        { "name": "Options", "base": "Options", "patch": { "x": 300, "y": 233, "scaleX": 0.9, "scaleY": 0.9 } },
        { "name": "Progress", "base": "Progress", "patch": { "visible": false, "enabled": false } },
        { "name": "MB_Credits", "template": "component:LongButton",
          "patch": { "x": 252, "y": 125, "buttonId": 10, "up": 4, "down": 5, "text": "CREDITS" },
          "action": { "type": "navigate.screen", "screen": "Credits" } } ] },
    { "name": "VehicleConfig", "kind": "custom", "base": "GraphicsMain", "title": "VEHICLE CONFIG", "elements": [
        { "name": "VC_Model", "template": "component:LongButton", "patch": { "x": 20, "y": 372, "buttonId": 1, "text": "MODEL SOURCE" },
          "action": { "type": "extension", "extension": "vehicle.model_source", "args": "1" } },
        { "name": "VC_ModelValue", "template": "QuickRace/ModeText",
          "patch": { "x": 360, "y": 386, "valueSource": "vehicle.model_source", "valueFormat": "MODEL: {value}" } } ] } ]
}
```

* **Name and identity.** `name` is the layout folder: letters, digits, `-`, `_` (max 48, not a device name such as
  `CON`); it is validated, never rewritten. `id` identifies the project, so a layout of the same name installed by
  another project is not replaced silently.
* **Elements.** `base` names an existing egg (edit, rename, hide, `deleted: true`); elements without `base` are new
  and copy a `template` egg (`"Egg"` of the base screen, `"Screen/Egg"` of any retail screen or `"component:Name"`).
  New and renamed element names: `[A-Za-z_][A-Za-z0-9_]*`, max 63. `patch` fields: `x y scaleX scaleY model
  bankIndex drawPriority visible buttonId up down left right enabled text textId textIndex textKey font textOffsetX
  textOffsetY icon hJustify vJustify anchor valueSource valueFormat valueFallback raw`. Precedence: component →
  style → element patch → aspect override.
* **Screens.** `kind: retail` edits a native screen (its own AI keeps all retail commands). `kind: custom` creates a
  new screen (native ID 64+, scene `MB_<Name>`, name `[A-Za-z][A-Za-z0-9]*`) hosted by `gaFEScreenGraphicsMainAI`.
  A retail screen without edits is not served at all.
* **Aspects.** Variants are compiled for every `settings.aspects` key. `anchor: left|right` moves an element by
  ∓/± half the extra width ((480·aspect − 640) / 2; 106.67 at 16:9); `aspects[key][egg]` patches one variant only.
  4:3 is always produced and used when the renderer stretches (Stock). Nothing is stretched to 16:9 unless you
  anchor or override it.
* **Exchange.** Screens export/import as `*.mrscreen.json` with the styles and components they use.

## 4. Element safety: dependencies, Hide and Disable

Every element has a class shown in the property panel and by `mrmenu deps`:

| Class | Meaning | Delete / rename |
|---|---|---|
| Native Required | screen controller or camera; name looked up by `MRallye.exe`; referenced by another egg (popup `ButtonEgg`, `Tiles`, any AI value); driven by Extra Options (`Frontend/ExtraOptions/*`) | blocked by default |
| Unknown Dependency | retail focusable whose Button ID is a command of the native screen AI | blocked by default |
| Native Optional | retail decoration or static text without known references | allowed |
| User Created | added in this project | allowed; focus paths that pointed at it are rerouted |

A blocked operation shows the dependencies and offers **Hide instead**, **Disable instead**, the forced operation or
Cancel (CLI: exit 1 with the list; `--force` to override).

* **Hide** keeps the egg with its name, Button ID and native links. It is not drawn: compiled pages park it outside
  the screen because native button AIs redraw their eggs whatever `en2d Visible` says (verified in game). It has no
  mouse hitbox, focus paths and the default focus are rerouted around it, and the runtime swallows its command, so an
  invisible active button cannot exist. A path that still leads into a hidden element is an ERROR (`NAV_TO_HIDDEN`).
* **Disable** keeps the element in place; buttons with a native `Enabled` state are drawn greyed; the runtime
  ignores the command in every case.

## 5. Typed actions and live values

Every focus target gets a compiled binding; a button without a working one is an ERROR (`UNBOUND`).

| `type` | Fields | Executed by |
|---|---|---|
| `native` | `command` (default: own Button ID) | the screen's own AI |
| `navigate.screen` | `screen` (retail name or custom screen) | runtime → `RequestScreen 0x45D910`, return stack push |
| `navigate.back` | – | runtime, pops the return stack (default MainMenu) |
| `native.forward` | `screen`, `command` | runtime: opens the retail screen and hands it `command` on its first tick (e.g. QuickRace 5 = Vehicle Setup) |
| `broker.set_int` / `broker.toggle_bool` / `broker.cycle_int` | `key` (`Group/Name`), `value` / `min max step` | runtime, Broker |
| `extension` | `extension` (typed ID), `args`, `optional` | catalog handler or a module registration (below) |
| `none` | – | does nothing (reported) |

**Catalog** (`mrmenu actions`, `MenuBuilder.Core/Actions.cs`, runtime `owned_id`):

| ID | Owner | Action | Value |
|---|---|---|---|
| `vehicle.model_source` (legacy `extra_options.model_source`) | Extra Options | steps PS2/PC/DEMO of the Vehicle Select car (`args` 1 / -1) | `PS2`, `PC`, `DEMO` |
| `vehicle.tyres` | Extra Options | steps the tyre compound of that car (same state as GENERAL TYRE TYPE) | `STOCK`, `TARMAC`, … |
| `vehicle.build` | planned (V-CONFIG1) | – | fallback |
| `vehicle.paint` | planned (V-CONFIG1) | – | fallback |
| `vehicle.apply` | planned (V-CONFIG1) | – | – |
| `game.quit` | built in | quits the game | – |

An action without a handler at run time (planned ID, another module not loaded, Extra Options disabled or the
standalone runtime) is **served disabled** (greyed, refused natively, `ACTION_UNAVAILABLE_SERVED` in the log); the
editor preview greys it the same way. `optional: false` turns a missing handler into an installation-blocking ERROR.
A live value text shows `format` with `{value}` replaced by the provider's current value, or by `valueFallback`
(default `N/A`) when no provider answers; values are written into the Broker Name `MenuBuilder/<scene>/<egg>` when
the scene loads and on every change (`VALUE …` in the log). Nothing is a hard-coded demo caption.

### Extension API (C, exported by the dinput8 loader, ABI 2)

```c
typedef int (WINAPI* MRMenuActionV1)(const char* args, int screen, int button);  // non-zero = performed
typedef int (WINAPI* MRMenuValueV1)(char* buffer, int size, int screen);          // length, <= 0 = unavailable
unsigned WINAPI MRMenuAbiV1(void);                                  // 0x4D4D0001
unsigned WINAPI MRMenuAbiV2(void);                                  // 0x4D4D0002 (values, ownership rules)
BOOL     WINAPI MRMenuRegisterActionV1(const char* id, MRMenuActionV1 action);
BOOL     WINAPI MRMenuRegisterValueV1(const char* id, MRMenuValueV1 provider);
int      WINAPI MRMenuQueryV1(char* buffer, int size);              // "abi=2 version=1.1.0 installed=1 layout=… format=2 …"
```

Rules: IDs are lower-case dotted names; the first valid registration owns an ID (`EXTENSION_CONFLICT` otherwise);
IDs owned by Menu Builder or Extra Options cannot be taken over; a callback must be executable code inside a module
image loaded in the process (never an arbitrary address). Providers run on the game thread inside the frontend tick.
V-CONFIG1 is expected to register `vehicle.build`, `vehicle.paint`, `vehicle.apply`; the Vehicle Configuration demo
then enables those buttons and shows their values without a layout change.

## 6. Installation (transactional)

`Install & activate` / `mrmenu install` / `Workspace.Install`:

1. Validate the project and the layout name; any ERROR → **Validation Failed**, nothing is written.
2. Recover an interrupted earlier install of this name (restore its backup) and remove stale temporary folders.
3. Refuse a same-name layout of another project unless replacing it was confirmed (`--replace-foreign`).
4. Compile into `Layouts/.mb-stage-<name>-<id>` (same volume), verify every file against `layout.json`, the runtime
   table and all variants.
5. Rename the live layout to `.mb-backup-<name>-<id>`, rename the staging folder into place, write
   `MenuBuilder.ini` atomically, then delete the backup → **Installed** / **Updated**.
6. A failure after the swap renames the backup back and restores `MenuBuilder.ini` → **Rollback Completed**; a failure
   before it leaves everything untouched → **Installation Failed** (locked files are reported as such).

Every path is checked to be strictly inside `<game>/MenuBuilder/Layouts`; the Layouts root and the game folder are
never deleted; junctions and symbolic links are never followed (a link inside a deleted tree is unlinked, its target
stays; a layout folder or Layouts folder that is a link is refused). Uninstall moves the folder aside before deleting.
`mrmenu compile --out DIR` uses the same pipeline into `DIR/MenuBuilder/Layouts` without activating.

## 7. Native runtime

`menu_builder::initialize()` runs in the dinput8 loader after the Randomizer boot and Extra Options/Ghost (independent
of their result). Without `MenuBuilder/MenuBuilder.ini` or with `Enabled=0` nothing is installed (**Classic**; the
`MenuBuilder` folder is not even created). Otherwise it loads `Layouts/<Layout>/runtime.txt` (formats 1 and 2; a
format-1 runtime refuses format 2 and keeps Classic), verifies 14 retail API prologues, the two call sites and the
vtable slot, and installs four hooks in one rollback-safe transaction:

| Hook | Site | Purpose |
|---|---|---|
| CreateFileA call → `create_file_hook` | `0x64D573` | serve the layout's `FrontendScreens/<scene>.xml` variant and custom `.hnt`; write live values before the scene initialises |
| GetScreenName call → `screen_name_hook` | `0x45D865` | names for custom screen IDs, current-screen tracking |
| GraphicsMain init slot → `host_init` | `0x690540` | default focus of custom screens |
| GetCommand detour (7-byte trampoline) | `0x45D930` | typed actions, Back, `native.forward`, blocked buttons, mouse, values, live dumps, autotest |

**Hook ownership in the integrated loader.** The Vehicle Manager roster (DllMain) owns the `CreateFileA` /
`GetFileAttributesA` import slots; Menu Builder hooks the VFS call site and chains through whatever the import slot
holds, so roster resources keep working and a layout page is served only when the page the game would otherwise load
(roster overlay → loose → `Data.sma`) is the one it was compiled against (FNV-1a 64; `BASE_CHANGED` keeps the native
or roster page). Extra Options hooks only call sites and vtable slots (`0x483151` → GetCommand passes through the
detour unchanged, `0x4818C5`, `0x44385B`, GENERAL/Vehicle Select/display slots); Ghost and the Randomizer plan use
other sites. `tools/audit_base_patch_sites.py` lists every site of the integrated loader.

**Mouse.** Hit rectangles = compiled local rect + the egg's live translation (en2d `+0x4C`, row 3 at `+0x54`) + the
renderer's margin shift. Hover focuses only after the cursor moved on the current screen (a resting cursor never
steals the focus); a click on an unfocused button focuses it and confirms on the next frame; right click = Back.
Hidden/disabled buttons have no hitbox.

**Files.** `<game>/MenuBuilder/MenuBuilder.ini` (`Enabled`, `Layout`, `[Diagnostics] LiveDump`, `AutoTest`),
`Layouts/<name>/{runtime.txt, layout.json, project.mrmenu.json, <WxH>/<scene>.xml, MB_*.hnt}`, `MenuBuilder.log`,
`live/<scene>.txt`, `cache/` (served copies with unavailable actions disabled). Saves and game data are never written.

## 8. Builds and configurations

`python tools/build_menu_builder.py --name <name> --package` produces:

| Product | Contents |
|---|---|
| `Editor/` | `MenuBuilder.exe`, `mrmenu.exe`, Python API |
| `Runtime/integrated/` | the current Extra Options loader of this branch (`build_extra_capacity_candidate.py --menu-builder`: roster-independent Vehicle Registry / Roster V4 loader, Randomizer, Ghost, five difficulties, tyres, PS2/PC/DEMO MODEL) with the Menu Builder runtime, plus its runtime core |
| `Runtime/standalone/dinput8.dll` | Menu Builder only (`RMOD_MENU_BUILDER_STANDALONE`): no Randomizer plan, no roster, no generated SDK headers |
| `BUILD-PROVENANCE.json` | commit, dirty flag, SHA-256 of every product and source |

There is one loader per installation: the integrated loader *is* Extra Options with Menu Builder support, and it runs
unchanged without layouts. The renderer (`d3d8.dll`) is optional for compiling and loading menus; the runtime reads
its interface mode from `MRRRenderer.ini` when it is present.

## 9. Widescreen

Renderer interface modes: **Stock** (640×480 stretched; the 4:3 variant is served), **Centered 4:3** (virtual width
480·aspect, authored area centred) and **Preserve margins** (Centered + the renderer's per-packet shift). The builder
reproduces `margin_direction` (`ui_margins.cpp`): 51 exact reference points (±half), then the left band x∈[25,106],
y∈[19,100)∪[259,340) for every packet (−half). The validator reports `WS_MARGIN_RULE` with a quick fix
(`mrmenu fix-margins`), `OFFSCREEN`, `HITBOX_CLIPPED` and, as an ERROR, an active hitbox entirely outside the visible
area (`HITBOX_OFFSCREEN`). The runtime picks the variant nearest to the window aspect and re-reads the window on every
scene load, so changing the resolution takes effect on the next screen.

## 10. Editor reference

Project lifecycle: New, Open, Save, Save As (`Ctrl+Shift+S`), Close project, Exit — every action that could lose edits
asks *Save / Don't save / Cancel*; saving writes a temporary file and renames it (a failed save never truncates the
previous file). *Game folder…* and *Reload game resources* (`F5`) re-bind the project to the installation without
touching the project, its file, the unsaved state or the undo/redo history, and list resources the project needs that
the installation lacks. The dirty mark follows the saved state (undoing back to it clears it).

Also: elements in draw order (✎ edited, + new, hidden/disabled marks), hitbox/navigation/safe-area overlays,
compare (original / split / onion), styles and components, align/distribute/z-order/link navigation,
copy/paste/duplicate/rename/delete/hide/disable, validation list with quick fix and *show info*, Interact mode
(arrow keys follow the real paths), install, Classic, launch, **Load in-game live dump** (in-game hitboxes in cyan).
`MenuBuilder.exe --game DIR --project P --selftest OUT` drives the real pointer handlers and saves snapshots.

## 11. CLI and Python API

`mrmenu <command>` prints one JSON document; exit 0 ok, 1 validation failed / blocked edit, 2 usage or IO error,
3 installation failed or rolled back. Commands: `screens inspect render compare validate compile install activate
uninstall status new-project add-screen export-screen import-screen texts fix-margins live deps edit actions api`.
`install` has no force: errors always block (`--replace-foreign` only for a same-name layout of another project).
`edit --hide/--show/--disable/--enable/--delete/--rename` applies the editor's dependency rules.
The Python module (`mr_menu_builder.py`) wraps every command (`install` returns the outcome; `edit`, `deps`,
`actions`) and edits projects directly (`Project.patch/add_element/set_action/bind_value/...`).

## 12. Verification

See `docs/menu-builder/MENU-STUDIO1-REPORT.md` for the current matrix (unit, integration, in-game and owner checks).
Commands:

```
dotnet run --project tools/menu-builder/MenuBuilder.Tests -c Release -- "<game>" examples/menu-builder/demo.mrmenu.json
powershell -File tools/menu-builder/test/run_runtime_check.ps1 -GameHost <isolated copy> -Test tools/menu-builder/test/studio.autotest -Out <dir>
powershell -File tools/menu-builder/test/run_ws_matrix.ps1 -GameHost <isolated copy with renderer> -Out <dir>
```

## 13. Limits

* Panels, 3D models and animated effects are previewed by their image banks/outline only.
* Custom screens use the GraphicsMain host AI; screens that need their own native logic (carousels, sliders) should
  stay retail screens edited in place.
* The retail frontend has keyboard/gamepad focus only; mouse hitboxes are added by the runtime.
* Car names are native Broker *strings* that a text element cannot show on a custom screen yet (verified in game: they
  render as `N`), so the catalog has no vehicle-name value.
* Only the retail EXE is certified; on another image the runtime refuses to install (`API_LAYOUT_UNSUPPORTED`).
