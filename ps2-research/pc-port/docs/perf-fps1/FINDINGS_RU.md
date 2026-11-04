# FPS1 — находки, которых не было в документации

Дополняет README.md (замеры, изменения FPS1–FPS1.3) этой папки. Источники: session-логи 5084, 38220, 28724, 24288,
46200…36188, 36652/36188, 12732 (MRRRenderer\logs), F10 frame-5084-d1-00018521, исходники master.

## Производительность

* Игра упирается в CPU: RX 6600, 1080p, ~117 FPS в статичной сцене. Отладка (`Diagnostics`, `ReflectionStageDiag`,
  `CollisionDebug`), `[Trace] Enabled=1` и Reflection=4 дают разницу в пределах шума.
* Цепочка обработчиков DrawIndexedPrimitive (патч 0001): lamp → water → checkpoint board → ground/forest → X-Trail glass →
  race body/part → wheel → X-Trail → frontend → vehicle partition → reflection. Каждый обработчик зовётся на каждый draw:
  вода ~2 мкс, фары 1–3 мкс на любой draw, а не только на «свой».
* PS2 HUD: ~340 UI-draw на кадр × ~1 мкс (`hud_capture`, разбор egg через живую память) = 0,33 мс постоянно.
* Флот при машинах рядом: lamp/wheel/race entry ≈ 2,5 мс/кадр; разовые пики 27–29 мс — переидентификация модели с хешем.
* Меню: один вызов `race_certificate` стоит 0,5 мс (снимок race_epoch для `course_for` вне гонки).

## Правило для будущих курсовых эффектов

Ландшафт, машины меню (COMPLETE), машины гонки и Egg-модели рисуются одним циклом `0x57707e`. Обработчик курса
обязан проверять единичную WORLD, иначе он перехватит draw машин раньше их обработчиков (так ForestFix ломал модели
меню, FPS1.3). GroundDetail защищён контрактом `base_noise` + PC noise-текстурой.

## Скрытые правила конфигов (проверено по коду)

| Где | Поведение | Статус |
|---|---|---|
| MRRRenderer `[FreeCamera] CleanViewEnabled` | без `[HUD] HiddenAtStartup` = «скрыть HUD при старте» (наследие); больше ни на что не влияет | исправлено FPS1.5: v1-вид всегда пишет `HiddenAtStartup`, ключ убран из шаблона |
| MRRRenderer `[FreeCameraKeys] ToggleCleanView` | подменяет `[HUD] ToggleKey`, если тот не задан | убран из шаблона |
| MRRRenderer `[HUD] PreservePause` | умолчание 1 | в шаблоне явно 0 |
| MRRRenderer `[Camera] VerticalFOVDegrees` | умолчание 75, не 60 | v1-вид пишет всегда |
| MRRRenderer `[Compatibility] MenuFreezeFix` | без ключа выключено | FPS1.5: в v2 без ключа включено |
| MRRRenderer `[Trace]` | без секции trace ВКЛЮЧЁН | v1-вид пишет явно |
| MRRRenderer `[ProbeTeleport]` | молча не работает без `[PhysicsObserver] Enabled=1` | описано в шаблоне |
| PS2Port `BaselineAllRaceModes=1` | включает и `RaceAllModes` — `RaceAllModes=0` тогда не действует | описано в шаблоне; развязка требует проверок в каждом эффекте |
| PS2Port `CollisionDebugMode` | умолчание SURFACE — оверлей виден сразу | FPS1.5: умолчание OFF, F11 включает (как F9 у машин) |
| PS2Port `PS2FrontendAllCars=2` (старые INI) | код ждёт `1`, значение 2 молча игнорировалось | в v3 влит в `FrontendModel` |
| PS2Port `GrassMode=1` (legacy) | только Turkey3; `Grass=1` (v2/v3) — все 36 курсов | — |

## Меню игры (для нативной интеграции, MENU_PLAN_RU.md)

* Экраны — XML-сцены `DataScene/FrontendScreens/*.xml` (подменяются loose-файлом), логика — классы `gaFEScreen…AI`.
* Переключатель = `enUITextButtonAI` + `gaFrontendMultistateAI` с ключами Broker `StringList*`, `Value*`, `CurrentText*`;
  списки заполняет код экрана. Video Setup — `gaFrontendPopupAI` (всплывающие списки).
* Пауза — `Hud0.xml`/`Hud1.xml`, `PauseMenuChooser` (`gaFrontendPauseMenuAI`): `Race/PauseMenu/Enabled|List|Index|Text`.
* Экраны фронтенда в гонке не загружены: переход «пауза → Graphics Options» без выхода из гонки невозможен.

## PS2-паритет

* TREEBLEND1: treeblend (mode 2) = ABE1, ATE0, ZMSK1 — смешивание без записи глубины; tree (mode 6) = alpha > 64/KEEP,
  что равно PC ALPHAREF 128 (GS-альфа 0..128). PC-конвертер переносит treeblend как blend с записью глубины → ForestFix.
* Off-course reset (LOGIC-PORT): PC 8 сэмплов + таймер 5, PS2 1 сэмпл + таймер 2 → PS2ResetTiming (подтверждено в игре).
* Покрытие курсов: всё, что зависит от трассы, работает на всех курсах, где оно есть на PS2 (таблица в README.md).

## Сборка

* `build_overlay.py` требует, чтобы имя ветки совпадало с `baseline_branch` в `overlay/baseline-lock.json`;
  lock хранит SHA-256 патчей — правка патча 0001 требует правки lock.
* Свежий worktree с autocrlf меняет переводы строк архивных файлов `docs/build-policy` → `test_build_roots` падает;
  их нужно копировать байт в байт.
* Хунк патча: строка контекста = пробел + исходная строка (у исходников с отступом в один пробел — два пробела).
