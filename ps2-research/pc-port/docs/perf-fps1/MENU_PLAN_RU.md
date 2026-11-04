# Нативное меню настроек — план размещения (на оценку)

## Что установлено про меню игры

* Экран — XML-сцена `DataScene/FrontendScreens/*.xml` (подменяется loose-файлом), логика — класс `gaFEScreen...AI` в EXE.
* Пункт-переключатель — egg `enUITextButtonAI + gaFrontendMultistateAI` с тремя ключами Broker:
  `StringList*` (список значений), `Value*` (индекс), `CurrentText*` (текущая подпись). Списки заполняет код экрана.
* Graphics Options = `GraphicsMain.xml` (`gaFEScreenGraphicsMainAI`): кнопки `Options` → Advanced Options,
  `CardSetup` → Video Setup (`PCGraphicsCardSetup.xml`, всплывающие списки `gaFrontendPopupAI`).
* Пауза = `Hud0.xml`/`Hud1.xml`, egg `PauseMenuChooser` (`gaFrontendPauseMenuAI`): `Race/PauseMenu/List|Index|Text|Enabled`.
* Экраны фронтенда в гонке не загружены, поэтому «из паузы в Graphics Options» без выхода из гонки — нереально.
  Реально: подменю настроек внутри самой паузы (тот же список паузы с переключателями ◀ ▶).

## Предлагаемое размещение

### OPTIONS → GRAPHICS OPTIONS
ADVANCED OPTIONS (как есть) · VIDEO SETUP (как есть) · **RENDERER OPTIONS** (новый) · **PS2 PORT** (новый)

### RENDERER OPTIONS (ваш концепт; применяется после перезапуска, отмечено *)
| Пункт | Значения | Ключ |
|---|---|---|
| ANTI-ALIASING * | OFF / 2X / 4X / 8X MSAA | Quality.AntiAliasing |
| ANISOTROPIC FILTERING | OFF / 2X / 4X / 8X / 16X | Quality.Anisotropy |
| WINDOW MODE * | STOCK / WINDOWED / BORDERLESS / EXCLUSIVE | Display.Mode |
| REFRESH RATE * | DESKTOP / 60 / 75 / 120 / 144 … (из режимов монитора) | Display.RefreshRate |
| WIDESCREEN | STOCK / CENTERED 4:3 / WIDESCREEN | Quality.Widescreen |
| FIELD OF VIEW | STOCK / 50…90° шаг 5 | Quality.FOV |
| SHADOW MODE | STOCK / OFF | Quality.Shadows |
| REFLECTION MODE | STOCK / ENHANCED | VehicleReflections.Mode |
| FREE CAMERA | OFF / ON | FreeCamera.Enabled |

«SHADOW MODE PS2» с концепта появится, когда будет PS2-вариант теней; сейчас только STOCK/OFF.
В VIDEO SETUP игровой FULLSCREEN при WINDOW MODE ≠ STOCK показывать как «BY RENDERER».

### PS2 PORT (экран-хаб из 4 кнопок; в нативном экране помещается ~10 строк)
* **VEHICLES:** Models (PC / PS2) · All cars · Menu models · All menu cars · Lighting · Content fixes · Brake glow · Reflection (PC / PS2 LIVE) · Reflection coverage
* **COURSE:** Grass · Shrubs · Ground detail (PC / PS2 / PS2 FAST) · Forest fix (PC / PS2 / ALPHA TEST) · Water · Moving objects · Birds · Props · Checkpoint barrels
* **HUD:** Damage · Map · Dial art · Hide PC-only · Time list · Split flash
* **PICTURE & SOUND:** Motion blur · Colour curve · TV output · Checkpoint sound · Finish music · All race modes · Split screen

### Пауза
CONTINUE · **CAMERA FOV ◀ 75° ▶** · **SETTINGS ▸** · QUIT

SETTINGS ▸ подменяет список паузы только настройками, которые применяются на лету:
FOV · HUD · Motion blur · Ground detail · Forest fix · Grass/Shrubs · Birds/Moving objects · Colour curve · TV output · BACK.
(Флот, отражения, AA, режим окна — только из главного меню.)

## Что нужно сделать (по этапам)

1. Запись в Broker из прокси: регистрация ключа-строки-списка и int-индекса (сейчас прокси Broker только читает).
2. Loose-XML: `GraphicsMain.xml` (+2 кнопки), `RendererOptions.xml`, `PS2Port*.xml` по шаблону `GraphicsOptions.xml`;
   подписи кнопок — строки языкового файла.
3. Хук `gaFEScreenGraphicsMainAI` на переход по новым кнопкам; экранный класс для новых экранов
   (свой обработчик Accept/Back) — нужен реверс, переиспользовать `gaFEScreenGraphicsOptionsAI` небезопасно.
4. Сохранение: Apply пишет `MRRRenderer.ini`/`PS2Port.ini` атомарно (temp + MoveFileEx, как V-SET1).
5. Пауза: хук сборки `Race/PauseMenu/List` и обработки ◀ ▶ в `gaFrontendPauseMenuAI`; живое применение
   через уже существующие флаги (FOV — проекция, эффекты — как F7-обход).
