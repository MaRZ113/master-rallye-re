# Конфиги (FPS1, нужен PS2-прокси с поддержкой v2/v3)

Положить рядом с `d3d8.dll`: `MRRRenderer.ini`, `PS2Port.ini` и при необходимости `RendererDiag.ini`.
Старые файлы (без `[General] ConfigVersion`) читаются как раньше.

## MRRRenderer.ini (ConfigVersion = 2)

* Прежние секции и имена ключей там, где соответствие один к одному: `[Display]`, `[HUD]`, `[FreeCamera]`,
  `[FreeCameraKeys]`, `[ProbeTeleport]`, `[PhysicsObserver]`, `[Compatibility]`, `[Diagnostics] CrashLog`.
* `[Quality]`: `Preset` (0 Stock / 1 Classic+ / 2 значения ниже), `AntiAliasing` 0/2/4/8, `Anisotropy` 0/2/4/8/16,
  `Widescreen`, `GameplayFOV` + `VerticalFOVDegrees`, `Shadows`; `[Diagnostics] Trace` 0/1.
* Базовый рендер читает из этого файла представление v1 — `MRRRenderer\config-v1.ini`, которое создаётся при каждом
  запуске (`renderer/renderer_config_v2.hpp`). Редактировать нужно только `MRRRenderer.ini`.
* Убрано: телепорт машины на дорогу France1, `[PS2FoliagePilot]`, `[VehicleReflections]` (Stock).

## PS2Port.ini (ConfigVersion = 3)

* Секции `[Scope] [Vehicles] [Reflections] [Course] [HUD] [Picture] [Rules]`, ключи без приставки `PS2`.
* Все переключатели 0/1: `Reflection = 1` (раньше 4), `FrontendModel = 1` (раньше 2 + `PS2FrontendAllCars = 1`).
  Многозначные: `GroundDetail` 0/1/2, `ForestFix` 0/1/2.
* Пути ассетов не пишутся: PS2Vehicles, PS2Grass, PS2Hud, Data.sma (`renderer/ps2_config.hpp`, `v3::default_value`).
* `RendererDiag.ini` — отладка, тонкая настройка, CollisionDebug и совместимость; без файла действуют умолчания
  (ReflectionWorldFirst = 1, BaselineAllRaceModes = 1, RetailDerivativeBuilds = 1, CollisionDebugMode = OFF, остальное 0).
* `BaselineAllRaceModes = 1` включает и `RaceAllModes` (FreeCam/скрытие HUD во всех режимах опираются на тот же сертификат).
* `[HUD] HiddenAtStartup` всегда передаётся явно: прежний `CleanViewEnabled = 1` больше не прячет HUD при старте.
* Убрано: CourseObjects (лужи Turkey3, уступают Water) и Foliage (bush01 France1, заменён ForestFix).
