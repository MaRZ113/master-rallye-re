# Черновик упрощения конфигов — соответствие ключей

Это ЧЕРНОВИК. Файлы в этой папке не установлены в игру. Чтобы они работали, прокси
должен понимать `ConfigVersion = 2/3` и переводить новые ключи в текущие (слой
перевода при чтении; старые файлы `ConfigVersion=1` читаются как раньше).

## Сжатие

| Файл | Было ключей / строк | Стало ключей / строк |
|---|---|---|
| MRRRenderer.ini | 94 / 233 | 13 / 53 |
| PS2Port.ini | 66 / 146 | 35 / 84 (+ PS2PortDiagnostics.ini: 26 / 43) |
| Atmosphere.ini | 38 / 40 | 6 / 20 |

Всё, что ушло из пользовательских файлов, — либо значения по умолчанию в коде, либо
инструменты разработчика. Их можно задать в необязательном `MRRRenderer.dev.ini`
(тот же формат, старые имена ключей); без этого файла действуют умолчания.

## MRRRenderer.ini

| Новый ключ | Старые ключи |
|---|---|
| Display.Mode / Width / Height | Display.Mode / Width / Height (RefreshRate=0 по умолчанию) |
| Quality.Preset | новый: 0 = всё Stock, 1 = Classic+ (AA4, AF16, PreserveMargins, FOV60), 2 = значения ниже |
| Quality.AntiAliasing = 0/2/4/8 | AntiAliasing.Mode + Samples (0 → Mode=0) |
| Quality.Anisotropy = 0..16 | Filtering.AnisotropicFiltering + MaxAnisotropy |
| Quality.Widescreen | Widescreen.InterfaceMode |
| Quality.FOV = 0 / 30..110 | Camera.GameplayFOV + VerticalFOVDegrees |
| Quality.Shadows | Shadows.Mode |
| HUD.ToggleKey | HUD.ToggleKey (ToggleEnabled=1, PreserveMenus=1 — умолчания) |
| FreeCamera.Enabled | FreeCamera.Enabled + AllowUnpaused=1 + CleanViewPilot/CleanViewEnabled=1 |
| Logging.Level = 0/1/2 | Trace.Enabled + Trace.FrameSummaries + Diagnostics.CrashLog |

В dev-файл (совпадают с умолчанием кода или нужны только разработке):
* `[FreeCamera]` скорости/сглаживания/FOV/крен/закладки (20 ключей) и `[FreeCameraKeys]` — все равны умолчаниям кода;
* `[Display] AutoHideCursor/CursorHideDelayMs` — умолчания 1/1500;
* `[HUD] HiddenAtStartup/PreservePause`;
* `[VehicleReflections]`, `[Compatibility] MenuFreezeFix`;
* `[ProbeTeleport]` — рабочий телепорт по точкам Ctrl+Alt+1..9 (в текущем файле секция встречается ДВАЖДЫ, оставить одну).

Удаляются совсем (устаревшие пилоты): `[PS2FoliagePilot]`, телепорт машины на дорогу France1
(`FreeCamera.VehicleTeleport*`, `ArmRoadTeleport`, `[PhysicsObserver] RoadTargetPreview*`); `[PhysicsObserver] Enabled`
остаётся в dev-файле только как зависимость ProbeTeleport.

## PS2Port.ini (v3, подробный)

Каждый пункт настраивается отдельно, имена ключей прежние — слой перевода не нужен, читатель только ищет ключ
во всех секциях файла. Пути ассетов убраны (фиксированные папки PS2Grass/PS2Vehicles/PS2Hud), вся отладка —
в отдельном `PS2PortDiagnostics.ini` (без файла — нули/умолчания). Новые ключи: `GroundDetail=2`, `ForestFix=1/2`.
Сжатие: 66 ключей / 146 строк → 35 ключей / 84 строки (+ 26 ключей в файле диагностики).

## Atmosphere.ini

| Новый ключ | Старые ключи |
|---|---|
| Atmosphere.Enabled | Enabled |
| Atmosphere.Sky | SkyPreset (+ CustomSet/CustomBase/CustomSkyUScale в dev) |
| Atmosphere.Lighting = 0/1/2 | LightingPreset + WorldLighting + профили GoldenHour / GoldenHour-WorldOnly |
| Atmosphere.Brightness | WorldBrightness × 100 |
| Atmosphere.Fog | FogEnabled (FogStrength/FogColor в dev) |

Цвета/направления солнца, Ambient*, Sunlight*, Prelight*, Exposure — внутрь пресета
Lighting; Sun/SunDisk/SunHalo/SunFlare/LightProbe/BodyPrototype/SceneDiagnostics/
SeamDebug/BodyDebug и пути метаданных — в dev-файл.
