# ATMOSPHERE2.2 — candidate-runtime-005

Новая сборка: OFFLINE_VERIFIED / GAMEPLAY_PENDING. 004 не принята визуально.
Исходные EXE/DX/PS2Vehicles и установленная игровая DLL не изменены.
Откат: rollback-runtime-004 плюс сохранённый пользователем Atmosphere.ini.

## Реально проверено на 004

Два session: 20261104-011308-50200 и 011852-25108, точная DLL f0598ec2….
Пользователь: PS2-карты, PS2-отражения выключены. Текущий PS2Port.ini:
Reflection=0 / VehicleLighting=1. Это НЕ подтверждение совместимости Reflection=4.
В логах native_owner_material (Patrol и Tata), а не certified_ps2_fleet.
Поэтому данный прогон не объявляется успешной проверкой PS2-моделей кузова.
Есть реальные события body_exposure gain=.68: установка этапа 004 работала.
Яркая крыша/номера/чехол запаски при этом оставались вне авторизованных ролей.

Просмотрены все 13 найденных новых файлов: 12 содержательных кадров/фрагментов
и PNG 8×5. MRallye_MVRL9iP64q имеет другое небо и не сопоставлен с точным F10;
не выдаём его за контрольную пару GoldenHour. Остальные показывают рельеф,
Patrol и запаску Tata. F10 sidecars содержат пары WorldLighting on/off;
обычный session-50200 достиг лимита 16 МиБ, поздние sidecars сохранились.
Не приписываем отсутствующие session-события последним кадрам.

QPC mixed/debug медианы world/body мс/кадр:
50200: .580 / .332; 25108: .293 / .397. Это не парное FPS сравнение.
Полные исходные пути и SHA снимков/session: runtime-004-evidence.json.

## Две структурные причины стыков

1. Обратные треугольники PS2 с одинаковыми индексами. Например, France1
   grass_rock_lft содержит [44629,44630,44631] и [44630,44629,44631].
   У них площадь ~637.58, нормали противоположны, authored normals направлены
   одинаково. Прежняя сумма взаимно уничтожалась; остаточная ошибка float
   давала произвольное направление. Это не индивидуальный пропущенный SHA.
   Runtime F10 France1 фиксирует совпадающий XYZ/source RGB, но нормали вниз
   или в сторону в соседних ranges: до ~99 RGB уровней перепада.
2. Исходный vertex RGB компенсирует текстуры материалов. В Turkey2/Turkey3
   встречаются одинаковые позиции и нормали с разными source RGB, которые в
   native изображении дают согласованный цвет. Компрессия PrelightContrast=.35
   в 004 и gain, зависящий от luminance, нарушали эту компенсацию. Это ошибка
   предыдущего художественного подхода; её исправляет формула 005.

## Изменения

- Восстановление нормалей исключает дубли треугольников ТОЛЬКО из расчёта света.
  Исходные IB, draw args, culling и геометрия отрисовки не меняются. Cross/sum
  считаются в double. Точные тройки локальных индексов — временное множество
  при cache miss/rebuild, не geometry SHA и не белый список объектов.
- Для доказанных front/back пар ориентация суммы не зависит от порядка пары:
  authored hint может выбрать сторону; без однозначного hint используется
  двухсторонняя diffuse-нормализация. Обычные односторонние поверхности и их
  hard-edge hints сохраняют прежнюю проверку facing.
- GoldenHour: PrelightContrast=1, PrelightVisibility=0. Исходный RGB остаётся
  множителем текстуры; gain зависит от ambient/sun/world normal, а не от RGB.
  Чёрная исходная окклюзия остаётся чёрной без дополнительного luminance-mask.
  Старые экспериментальные параметры доступны явно, штатный профиль их не
  использует. Fog/GT3 sky не менялись.
- В BLM2 добавлены typed роли opaque_panel (непрозрачные номерные/декоративные
  панели) и opaque_cover (неподвижный чехол запаски). Только явные metadata,
  штатный owner/car resource, mode3/непрозрачный shader и private buffers.
  Для cover требуется perspex secondary и имя типа wheelcover/wheelcoverside.
  Это не допуск шины/колеса/диска. Lamp/glass/glow/driver/helmet по-прежнему deny.
  Новые bindings: Patrol mastersticker243; Tata mastersticker48, tatareg,
  tatawheelcover/tatawheelcoverside. Текстуры и нарисованные номера не меняются.
- 004 scoped exposure после diffuse+reflection остаётся; Reflection UV/capture/
  ориентация и VehicleLighting=1 не переписаны. Совместимость Reflection=4 в
  005 требует отдельного игрового прохода.
- F10 теперь пишет duplicate_faces/opposite_faces для проверки причины в игре.

## Проверено вне игры

24 baseline CTest, 46 PS2 CTest, 186 Python PASS; SDK regressions 8 PASS.
Нативный parser: 326 LSM1 / 89 263 LNH1 / 22 BLM2 PASS, ~108 мс cold load.
Replay реальных трёх PS2 DX через новый C++ light_geometry: 1426 ranges,
410 с обратными парами; 6209 duplicate faces исключены из расчёта, 99 994
shaded vertices, 0 non-unit/nonfinite normals и 0 rejected ranges.
Это OFFLINE_SOURCE_REPLAY, НЕ игровой кадр и НЕ FPS измерение. Источники
связаны по материалу, не выданы за точные runtime draw-range границы.
Regression: front/back pair в обоих порядках, сохранение RGB компенсации,
новые typed roles и отрицательные wheel/glass/lamp проверки.

## PENDING

Новая DLL в игре: те же участки всех трёх карт; крыша/номера Patrol, номерные
панели и чехол Tata; Restart/Re-entry; CPU/FPS. PS2 fleet + Reflection=4,
PC Original/GoldenHour, modified layout, Reset/HUD/FreeCam/water/physics/
collision/standalone также не объявляются проверенными новой сборкой.
Старые изображения относятся к 004. Sun выключен: world/body ещё не приняты;
current-depth-before-HUD boundary и реальная окклюзия пока не доказаны.
