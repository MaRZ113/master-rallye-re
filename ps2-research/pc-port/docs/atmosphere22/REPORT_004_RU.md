# ATMOSPHERE2.2 — candidate-runtime-004

Статус новой DLL: OFFLINE_VERIFIED, игровой результат PENDING. В игру пакет
не установлен. Original/PS2 исходники не изменены. Откат: rollback-runtime-003.

## Что подтверждено на 003

Три точные сессии 45556/33024/384, DLL 5b219cc7…, 13 F10. Loose PS2 Course
подтверждён текущими SHA исходников и сообщением пользователя. В 33024 есть
оба кузовных пути native_owner_material и certified_ps2_fleet. В 384 наблюдался
native_owner_material, поэтому не называем каждый кадр PS2-моделью машины.
Пользователь подтвердил отсутствие артефактов PS2-отражений и указал проблемы
кузова, Turkey3, травы Turkey2, баннеров и маркеров. Это НЕ приёмка 003.

QPC mixed/debug окна, медиана мс/кадр (world / body): 45556 — 0.403 / 0.342;
33024 — 0.611 / 0.320; 384 — 0.397 / 0.121. Это не парное FPS-сравнение.
Пиковый кэш соответственно 1 138 439 / 2 979 148 / 1 539 487 байт.
Подробные admissions, эпохи и исходные F10: runtime-003-evidence.json.
Снимки comparison-screenshots относятся к 003, не к новой DLL.

## Изменения 004

1. SDK распознаёт большие ground-поверхности по CW геометрии; небольшие
   связные вертикальные панели — по плоскостности, размерам и ориентации.
   Не нужны список брендов или SHA геометрии. Неоднозначные формы остаются
   native, исключения воды/стекла/glow/колёс/отражающих shaders приоритетны.
   Живые shader/resource/pass guards Proxy сохраняются.
2. Turkey2 basegrass: комбинация plain + base_noise больше не считается
   конфликтом, если ground-контекст доказан. Объединяются только совместимые
   category/winding/flags. Реальные противоречия и DENY не снимаются.
3. LNH экспорт объединяет близкие authored normals через UV/material boundaries
   и PC/PS2 варианты при общем XYZ (1 мм), полный кластер dot > .97.
   Острые грани сохраняют отдельные кластеры. Это optional shading metadata,
   не допуск мешей. Runtime-поиск только при cache miss/rebuild.
4. PrelightContrast=0.35 уменьшает контраст исходного baked directional term,
   сохраняя оттенок vertex RGB, alpha и чёрную окклюзию. Значение 1 возвращает
   прежнюю формулу. Это художественная компрессия prelight; она не исправляет
   UV/texture seams и не является новой системой теней.
5. Для допущенных кузовов дополнительный stage2 умножает итоговую сумму
   diffuse + reflection на WorldBrightness (0.68). Это уменьшает несогласованный
   яркий additive reflection на верхних панелях. Reflection=4, VehicleLighting=1,
   texture1/его UV/ориентация, capture и исходные модели остаются прежними.
   Меняется интенсивность отражения на этих панелях, не его ориентация.
   Stage2 и TFACTOR восстанавливаются через retry-safe Pending; каждый отказ
   восстановления блокирует следующий draw до repair. Неподдержанный pipeline
   сохраняет исходный draw после успешного repair. Проверка glass/wheel/lamp
   обязательна в игре. Новое событие atmosphere_body_exposure подтверждает
   фактическую установку этапа, а не только запрос body lighting.
6. Верх Tata tatalogo — отдельный paint binding. Его source bounds Y=1.54…1.65,
   Z=-2.01…-0.70 перекрывают верхнюю панель; добавлен в внешний BLM2. Номерные
   sticker passes, стёкла, шины, диски и лампы исключены. Текстуры/UV не изменены.
7. F10 budget увеличен с 64 до 160 ranges: старый лимит обрезал terrain после
   foliage. В обычных кадрах выгрузки геометрии нет.

Метаданные: 326 LSM1, 89 263 LNH1, 17 BLM2. Количество — material records и
normal hints, а не число объектов. Новых per-object geometry SHA нет.

## Проверка вне игры

24/24 baseline CTest, 46/46 PS2 CTest, 186 Python; SDK 8/8.
Нативный парсер принял новые LSM1/LNH1/BLM2, cold load ~106 мс один раз.
Изолированный системный D3D8 HAL: ADD diffuse+env → stage2 gain → отключение
stage2. RGB 0x304880 → 0x213157 → 0x304880, ValidateDevice: один проход.
Это GPU-проверка арифметики, не игровой кузов/производительность/совместимость.
Unit fault injection покрывает все 8 новых restore slots и последующий retry.

## PENDING

Новая 004 в игре: тот же Patrol wing/bonnet, верх Tata, чекпоинты и все баннеры,
Turkey2 basegrass, PS2 Turkey3 (швы нельзя объявлять исправленными по exporter).
Baseline/PS2 A/B, Restart/Re-entry, FPS и QPC после stage2, изменённый layout,
FreeCam/HUD/water/physics/collision/standalone. Старые подтверждения нельзя
автоматически переносить на новую DLL. Краткий тест — RUN_TEST_RU.md;
расширенная матрица — FULL_VALIDATION_RU.md.

SunDisk/Halo/Flare выключены. Мир/кузов пока не прошли новую приёмку.
Дополнительный технический gate солнца: ещё не доказан момент использования
текущего world depth перед HUD с полной scoped state restoration и окклюзией
горы/деревья/тоннель. CPU depth readback не объявляется обязательным: возможен
GPU depth-tested прототип. Ночь, фары, новые облака не разрабатывались.
