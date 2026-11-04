# FPS1 — где PS2-слой тратит кадр (поверх candidate-runtime-005, DLL c3a03214)

Источник: session-20261104-012550-5084 (DLL 04cec698, полный PS2Port.ini: Reflection=4, весь флот,
PS2 HUD, трава/кусты, GroundDetail, вода, птицы, сплайны, RigidProps, бочки, MotionBlur,
Diagnostics=1, ReflectionStageDiag=1, CollisionDebug=1, PS2PerfTiming=1) и F10-кадр
frame-5084-d1-00018521 (FranceS1, пауза + FreeCam). `ps2_perf_timing` до FPS1 не содержал
времени кадра, поэтому ниже — CPU-стоимость входов PS2-слоя, а не FPS.

## Найдено

| Сцена | Что | мкс/кадр | Пик |
|---|---|---|---|
| Пауза + FreeCam + H | `race_certificate` 487 вызовов/кадр: clean-view admission базового рендера спрашивает `live_race_certificate` на каждый UI-draw (464 UI-draw в кадре), BASELINE-ALL-RACES отправляет это в некэшированный PS2-сертификат | 4 600–4 800 | — |
| Старт гонки, 4 машины в кадре | `race_entry`/`fleet_car` (~200 вызовов) + `wheel_entry`/`fleet_wheel` + `lamp_entry` | ≈ 2 700 (вложенные категории не суммировать) | 27–29 мс в одном кадре (`fleet_car` max) — повторная идентификация модели с хешированием |
| Обычная гонка, машины вдали | то же | ≈ 600–800 | 1,5 мс |
| Меню / демо | `race_certificate` 1 вызов, но 530–600 мкс каждый; `frontend_entry` 24 вызова | ≈ 1 100 | 15 мс |

Не измерялось (CPU-таймеров не было): захват кадра для Reflection=4 (резолв 1920×1080 MSAA ×4 каждый кадр,
`capture.attempts` = числу кадров гонки), MotionBlur (копия кадра), трава/кусты, GroundDetail (второй проход
на ~150 draw), вода, птицы, отладочные слои (CollisionDebug, Diagnostics, `[Trace] Enabled=1` в MRRRenderer.ini —
базовый trace пишет каждый D3D-вызов в теневое состояние и frame_summary каждые 60 кадров).

## Изменения FPS1

1. `ps2_perf_timing`: `frame_time` окна (fps, avg/p50/p95/p99/max мс), поле `bypass`, новые категории:
   atmosphere, water, ground_detail, xtrail, xtrail_glass, vehicle_partition, reflection_note, hud_capture,
   ui_grass, ui_spline, ui_birds, ui_rigid_props, ui_collision, ui_course_objects, ui_reflection,
   present_pass, baseline_certificate.
2. DIAGNOSTIC `PS2PerfBypassKey` (VK, по умолчанию 118 = F7; только при PS2PerfTiming=1): шаги
   none → grass → ground_detail → water → live_objects → motion_blur → all. Обход возвращает нативный draw
   или пропускает лишний draw; машины, отражения, HUD не трогаются.
3. Исправление: `baseline_frame_certificate` — один PS2-сертификат на кадр/камеру для потребителей базового
   рендера (как PERF2.1 для PS2-путей). Ключ кадра публикуют первый indexed draw и каждый UI-draw;
   без публикации — повторное чтение через 50 мс.

## Прозрачность леса FranceS1 (кадр 18521)

Курсовые draw (`0x57707e`) с текстурами 128×128 A8R8G8B8 (serial 1140, 1187) идут с
`ALPHABLENDENABLE=1, ZWRITEENABLE=1, ALPHATESTENABLE=0`. Состояния выставляет сама игра (draw переданы
без изменений), т.е. это поведение PC-движка: почти прозрачные пиксели полосы леса пишут глубину, и всё,
что рисуется позже за ней (другие полосы леса, склон), вырезается — «слой перекрывает слой».
У соседних материалов деревьев (serial 1137/1139/1152/1182) — alpha test 128 без смешивания, они чистые.
Предлагаемое исправление (`ForestFix`): только для курсовых draw с этой тройкой состояний на время draw
включить `ALPHATESTENABLE=1, ALPHAFUNC=GREATER, ALPHAREF≈8–32` (прозрачные пиксели не пишут Z,
полупрозрачные края по-прежнему смешиваются) — эквивалент PS2 alpha test с записью только в кадр.
Не реализовано в FPS1 (отдельный шаг с визуальной проверкой): нужна своя транзакция состояний на draw,
как у GroundDetail, и подбор ALPHAREF по скриншотам.

## FPS1.1 (DLL d45c17b8) — по прогонам 38220 / 28724 / 24288

Статичная сцена FranceS1, ~117 FPS (8,6 мс). F7-обход, прирост FPS:
GroundDetail +13 (≈0,9 мс CPU, ~150 лишних draw), вода +4..5 (когда видна), трава/живые объекты/motion blur ≈0,
все сразу +15..18. Отладка+trace (B vs A) и Reflection=4 (C vs B) — в пределах шума. Машины рядом: −25..30 FPS
(lamp/wheel/race entries ≈2,5 мс). PS2 HUD постоянно 0,33 мс (340 UI-draw × ~1 мкс). Пауза+FreeCam: 142 FPS,
исправление подтверждено.

Изменения:
* `GroundDetail=2`: один проход, stage1 SUBTRACT с PS2-шумом вместо MODULATE2X — без второго draw; отличие от PS2:
  шум затуманивается. Текстуры транзакции берутся из отслеживаемого состояния (без нативного GetTexture).
* `ForestFix=1`: контракт PS2 treeblend (ps2-research/treeblend1: mode 2 — ABE1, ATE0, ZMSK1) — запись глубины
  выключается на draw курса с SRCALPHA/INVSRCALPHA+ZWRITE+без alpha test; `ForestFix=2`: alpha test GREATER
  `ForestFixAlphaRef` (32). Небо (Z off) не затрагивается.

Следующие кандидаты: кэш фар/колёс/кузова флота на кадр (≈2,5 мс при машинах рядом), PS2 HUD (кэш egg на кадр),
вода (поиск курса по строке на каждый draw).

## FPS1.2 (DLL 2619a8bc) — пилоты и паритет PS2 по трассам

Прогоны FPS1.1: ForestFix=1 — лучший вариант (принят), ForestFix=2 оставляет белые кромки. GroundDetail=2: CPU
1,05 → 0,21 мс/кадр (SpainS2), дальние потемнения ушли, ближняя земля без изменений (принят).

Обход фаз PS2-порта на ограничения по трассам:

| Функция | Покрытие | Итог |
|---|---|---|
| Grass/Shrubs | 36 курсов (72 ассета установлены) | всё |
| PS2Water, лужи, водопады | 34 курса с водой (Italy1, Turkey1 без воды и на PS2) | всё |
| SplineObjects | 24 объекта, 17 курсов — все, где они есть на PS2 | всё |
| PS2Birds | 36 курсов; на PS2 летают только 10 с MillList | как на PS2 |
| RigidProps | 83 объекта, 9 курсов — все | всё |
| Checkpoint barrels | 432, 36 курсов | всё |
| GroundDetail, ForestFix | все курсы (по состоянию draw) | всё |
| CourseObjects (лужи Turkey3) | пилот, уступает PS2Water (`superseded_by_ps2_water`) | убран из конфига |
| Foliage (France1 bush01) | пилот, заменён ForestFix (treeblend на всех курсах) | в диагностику |
| Off-course reset (LOGIC-PORT) | не был применён нигде | **PS2ResetTiming=1**, все курсы |
| Дымовые эмиттеры (CDELTA1: 81 aiSpawnParticle, 25 курсов) | не портировано | отдельная фаза, нужен реверс частиц |
| Road teleport (FreeCam T) | France1 (448 маркеров в базовом рендере) | инструмент разработки, не PS2 |

`PS2ResetTiming=1`: две проверенные правки immediate в MRallye.exe, как PS2-AUDIO1:
`0x4cde6c 83 3c 07 07 → …00` (LimitState 2 с первого сэмпла за границей) и `0x4cd4ba bf 05 → bf 02` (таймер сброса 2).

## FPS1.3 (DLL 98b25bce) — COMPLETE-модели в меню

Длинные прогоны SpainS2 (36652 / 36188): GroundDetail=2 — средний кадр 7,80 мс против 8,80 мс при GroundDetail=1
(138 против 124 FPS в среднем, 118 против 106 по медиане), CPU ground_detail 0,23 против 1,05 мс/кадр.

Пропажа PS2 COMPLETE-моделей во фронтенде: регрессия FPS1.1. Все сессии с ForestFix=1 (46200…36188) без
`ps2_frontend_model_warmup`, все без него — с заменой. Машины меню рисуются тем же циклом 0x57707e; ForestFix
забирал их смешиваемые части (стёкла), фронтенд-модель не видела все 25 исходных draw и оставалась PC.
Исправление: ForestFix только при единичной WORLD (ландшафт курса; F10 FranceS1: draw 40–50 — identity).
