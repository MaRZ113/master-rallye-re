# Master Rallye Menu Builder

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
| Example project | `examples/menu-builder/demo.mrmenu.json` |
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

## 2. Projects

A project (`*.mrmenu.json`, `format: "mr-menu-project"`, `version: 1`) is a **delta** over the
installed pages; the retail baseline is never copied or modified. Schema: `docs/menu-builder/project.schema.json`.

```json
{
  "format": "mr-menu-project", "version": 1, "name": "Demo",
  "settings": { "mouse": true, "aspects": ["4:3", "16:10", "16:9", "21:9"], "language": 0 },
  "styles":     { "MenuButton": { "textOffsetX": 110, "vJustify": 1 } },
  "components": { "LongButton": { "template": "MainMenu/OnePlayer", "style": "MenuButton" } },
  "screens": [
    { "name": "MainMenu", "kind": "retail", "base": "MainMenu", "defaultFocus": 1,
      "elements": [
        { "name": "Options", "base": "Options", "patch": { "x": 300, "y": 233, "scaleX": 0.9, "scaleY": 0.9 } },
        { "name": "MB_Credits", "template": "component:LongButton",
          "patch": { "x": 252, "y": 125, "buttonId": 10, "up": 4, "down": 5, "text": "CREDITS" },
          "action": { "type": "navigate.screen", "screen": "Credits" } } ],
      "aspects": { "16:9": { "MB_Credits": { "x": 260 } } } },
    { "name": "ModMenu", "kind": "custom", "base": "GraphicsMain", "title": "MENU BUILDER",
      "back": { "type": "navigate.back" }, "elements": [ … ] } ]
}
```

* **Elements.** `base` names an existing egg (edit, rename, `deleted: true`); elements without
  `base` are new and copy a `template` egg (`"Egg"` of the base screen, `"Screen/Egg"` of any
  retail screen or `"component:Name"`). `patch` fields: `x y scaleX scaleY model bankIndex
  drawPriority visible buttonId up down left right enabled text textId textIndex textKey font
  textOffsetX textOffsetY icon hJustify vJustify anchor raw` (`raw`: `"AIName/Value Name" → value`
  for any other AI value). Precedence: component → style → element patch → aspect override.
* **Screens.** `kind: retail` edits a native screen (its own screen AI keeps all retail commands).
  `kind: custom` creates a new screen (native ID 64+, scene `MB_<Name>`) whose visual base is any
  retail scene; its controller is replaced by the host AI `gaFEScreenGraphicsMainAI`, which the
  runtime keeps from acting on its own commands.
* **Aspects.** Variants are compiled for every `settings.aspects` key. `anchor: left|right` moves an
  element by ∓/± half the extra width ((480·aspect − 640) / 2; 106.67 at 16:9); `aspects[key][egg]`
  patches only that variant. 4:3 is always produced and used when the renderer stretches.
* **Exchange.** Screens export/import as `*.mrscreen.json` together with the styles and components
  they use.

## 3. Typed actions

Every focus target gets a compiled binding; the validator refuses a button without a working one.

| `type` | Fields | Executed by |
|---|---|---|
| `native` | `command` (default: own Button ID) | the screen's own AI (retail buttons; a new button can reuse a retail command of its screen) |
| `navigate.screen` | `screen` (retail name or custom screen) | runtime → `RequestScreen 0x45D910`, return stack push |
| `navigate.back` | – | runtime, pops the return stack (default MainMenu) |
| `native.forward` | `screen`, `command` | runtime: opens the retail screen and hands it `command` on its first tick, so the native preparation runs (e.g. QuickRace 5 = Vehicle Setup) |
| `broker.set_int` / `broker.toggle_bool` / `broker.cycle_int` | `key`, `value` / `min max step` | runtime, Broker `0x4D8000/0x4D7AA0/0x4D6760` |
| `extension` | `extension`, `args` | provider registered with `MRMenuRegisterActionV1`, or built-in (`game.quit`, `extra_options.model_source`) |
| `none` | – | shown disabled |

Statuses reported by the compiler: `NativeRetail`, `NativeRemap`, `Runtime`, `Extension`,
`Unbound` (error), `Disabled`. An `extension` whose provider is not present at run time is served
with its `Enabled` flag cleared (greyed, refused natively) and logs `ACTION_UNAVAILABLE`.

### Extension API (C, exported by dinput8.dll)

```c
typedef int (WINAPI* MRMenuActionV1)(const char* args, int screen, int button);
unsigned WINAPI MRMenuAbiV1(void);                                   // 0x4D4D0001
BOOL     WINAPI MRMenuRegisterActionV1(const char* name, MRMenuActionV1 action);
int      WINAPI MRMenuQueryV1(char* buffer, int size);               // "installed=1 layout=… screen=… variant=… mode=…"
```

Providers run on the game thread inside the frontend tick. Extra Options supplies
`extra_options.model_source` (`extra_runtime::appearance_step`, the PS2/PC MODEL choice of the
Vehicle Select car; its label is Broker `Frontend/ExtraOptions/PaintText`).

## 4. Native runtime

`menu_builder::initialize()` runs from the dinput8 loader after the Randomizer boot and Extra
Options/Ghost initialisation (independent of their result). With `MenuBuilder/MenuBuilder.ini`
missing or `Enabled=0` it installs nothing (**Classic**). Otherwise it loads
`MenuBuilder/Layouts/<Layout>/runtime.txt`, verifies 14 retail API prologues, the two call sites
and the vtable slot, and installs four hooks in one rollback-safe transaction:

| Hook | Site | Purpose |
|---|---|---|
| CreateFileA call → `create_file_hook` | `0x64D573` | serve `FrontendScreens/<scene>.xml` of the layout (variant by window aspect, 4:3 when the renderer stretches) and custom `.hnt`; base page re-check (archive: no loose page appeared; loose: FNV-1a 64 equal) else `BASE_CHANGED` and the native page is kept |
| GetScreenName call → `screen_name_hook` | `0x45D865` | names for custom screen IDs, current-screen tracking |
| GraphicsMain init slot → `host_init` | `0x690540` | default focus of custom screens |
| GetCommand detour (7-byte trampoline) | `0x45D930` | typed actions, Back, `native.forward`, mouse hover/click, live dumps, autotest |

It does not touch the Extra Options hooks (GENERAL/Vehicle Select slots, `0x483151`, `0x4818C5`,
`0x44385B`): Extra Options' GENERAL command call still reaches `0x45D930` and passes through the
detour unchanged. The D3D8 renderer is optional; when present, the runtime reads its interface mode
(`MRRRenderer.ini`, v2 `[Quality] Preset/Widescreen`, v1 `[Widescreen] InterfaceMode`).

**Mouse.** Hit rectangles = compiled local rect (from the same DXB image box the game draws) +
the egg's live translation (en2d object `+0x4C`, row 3 at `+0x54`) + the renderer's margin shift.
Hover sets `UI/Active`, left click sets `UI/Active` and `UI/Control = 4`, right click `UI/Control = 5`.

**Files.** `<game>/MenuBuilder/MenuBuilder.ini` (`Enabled`, `Layout`, `[Diagnostics] LiveDump`,
`AutoTest`), `Layouts/<name>/{runtime.txt, layout.json, project.mrmenu.json, <WxH>/<scene>.xml, MB_*.hnt}`,
`MenuBuilder.log`, `live/<scene>.txt` (eggs, live positions, hitboxes, focus), `cache/` (served
copies with disabled unavailable providers). Saves (`DataGame/PlayerState.xml`, `options.xml`) and
game data are never written.

## 5. Widescreen

Renderer interface modes: **Stock** (640×480 stretched), **Centered 4:3** (virtual width
480·aspect, authored area centred) and **Preserve margins** (Centered + per-packet shift). The
builder reproduces the renderer's `margin_direction` (`ui_margins.cpp`): 51 exact reference points
(±half), then the left band x∈[25,106], y∈[19,100)∪[259,340) for every packet (−half), Vehicle
Select carousel cards on y = 309 excluded. Example: on the native GEARBOX page (VehicleSetup4)
`GearRatio` at (40, 301) is in the band and jumps left while GEARBOX/RESET stay. The validator
reports `WS_MARGIN_RULE`; *Quick fix* (`mrmenu fix-margins`) nudges exact-point matches by one unit in
the wide variants or anchors the band match's column to the same margin. The editor previews every
mode at any aspect or window size and shows the visible range.

## 6. Editor

Screens (retail list + custom), elements in draw order (✎ edited, + new), live preview with
focus states, icons and scaled labels, drag to move, corner handle to scale, arrows/Shift+arrows to
nudge, grid/snap/guides, hitbox/navigation/safe-area overlays, aspect (4:3, 16:10, 16:9, 21:9,
any window size), UI mode, compare (original / split / onion), *Edit this aspect only*, typed property
panel (geometry, sprite, label, font, icon, justification, focus paths, action), styles and
components, insert templates (long/curved buttons, option rows, arrows, texts, images, panels, bars),
align/distribute/z-order/link navigation, copy/paste/duplicate/rename/delete, undo/redo, validation
list with quick fix, Interact mode (arrow keys follow the real paths, Enter shows the bound action),
install & activate, Classic, launch, and **Load in-game live dump** to overlay the hitboxes the game
reported (cyan) on the editor's.

## 7. CLI and Python API

`mrmenu <command>` prints one JSON document; exit 0 ok, 1 validation errors, 2 usage/IO error.
Commands: `screens inspect render compare validate compile install activate uninstall status
new-project add-screen export-screen import-screen texts fix-margins live api`
(`mrmenu --help`). `--exe` / `--target` support launchers whose data root differs from the EXE
folder (SDK resource roots). The Python module wraps every command and edits projects directly
(`Project.patch/add_element/add_custom_screen/set_action/style/component`).

## 8. Verification

* Core tests (`MenuBuilder.Tests`, 37 checks): all 113 DXB banks, EXE tables, byte-identical
  round trip of all 47 retail scenes, compiler/runtime table, aspect anchors, editor session
  (move, undo/redo, add/duplicate/delete/copy/paste, aspect-only edits), PreserveMargins rules,
  screen exchange.
* In-game (`tools/menu-builder/test/run_runtime_check.ps1`; input through `UI/Control` and the
  runtime hit test, screenshots by PrintWindow, no OS input):
  * `qualification.autotest`, 4:3, renderer present — 25/25: focus chain through the new button,
    moved/scaled OPTIONS hitbox and empty old area, new CREDITS → Credits, Options → new ModMenu →
    VehicleConfig, unavailable PAINT refused, APPLY/BACK return chain.
  * same without the D3D8 renderer — 25/25.
  * `integrated.autotest`, EXTRA-SET2 + SDK33 launcher + renderer, 16:9, Preserve margins — 7/7:
    Quick Race VEHICLE CONFIG, MODEL SOURCE through Extra Options (`APPEARANCE_SELECTED …
    source=menu-builder`), BUILD → native Vehicle Setup via `native.forward`, fixed GEARBOX column.
  * same without the renderer — 7/7. Classic (`Enabled=0`): native menu unchanged.
  * Preview vs game: 50 % blends of editor renders and game captures align (sprites, labels,
    icons, scaled buttons, margin shifts).

## 9. Limits

* Panels (`enUITileBox`, `enUIGradientBoxAI`), 3D models and animated effects are previewed only
  by their image banks/outline; Broker-driven texts show `{Key}` unless a preview value is set.
* Custom screens use the GraphicsMain host AI; screens that need their own native logic (carousels,
  sliders) should stay retail screens edited in place.
* Mouse hitboxes are added by the runtime; the retail frontend itself has keyboard/gamepad focus only.
* Only the retail EXE is certified; on another image the runtime refuses to install
  (`API_LAYOUT_UNSUPPORTED`) and the native frontend is unchanged.
