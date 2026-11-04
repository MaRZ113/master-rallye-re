# ATMOSPHERE2.2 — разбор записанного A/B PID 44172

Проверена DLL `aaa845833237531e177fbfce621493002356a46d11b647bc7a87aa2ce2138640`,
первоначальные LSM1/LNH1 из candidate-runtime-001. Это анализ пользовательского
прогона, не самостоятельное выполнение игры агентом.

| Точка | WorldLighting on | WorldLighting off | Полнота F10 |
|---|---:|---:|---|
| Скала | 4028 | 5284 | оба complete, 561 draws |
| Дорога | 12757 | 12481 | оба complete, 613 draws |

В каждой паре побайтно совпадают записанные view matrices, effective projection,
аргументы всех DrawIndexedPrimitive, последовательности sky texture overrides
и fog overrides. Общие аргументы DrawPrimitive отличаются у 481 HUD submission
из-за иных offsets кольцевого VB; пропавшая геометрия из этого не следует.

Ранние изображения: MRallye_ETlYqeY1D8.jpg (on), MRallye_VGmbCOwlMm.jpg (off).
Поздние: MRallye_ikIkmkJtfR.jpg (off), MRallye_27Do4YXFWF.jpg (on).
Исходники лежат в C:/Users/MaRZ/Documents/ShareX/Screenshots/2026-11.

## Что локализовано

1. **Lit/native граница действительно есть.** Четыре sampled range `rock-tga`
   получили `native_material_excluded`, category 0; их source/effective ARGB
   одинаковы при включённом свете. Соседние grass/road/transition ranges приняты.
   Для rock: FVF 0x242, cull=3, alpha-test=0, stage1=MODULATE2X; shader base_noise
   уже подтверждён runtime-guard. Это не повод расширять допуск на воду/стекло.
2. Причина — ошибка экспорта/объединения material capabilities. PC rock имеет
   1836/1 голосов направления source normals, PS2 — 1721/353. SDK превратил
   второй случай в DENY из-за порога 90%, а конфликт общей текстуры отозвал
   допуск и у PC. Смешанные smoothing normals не являются неоднозначностью
   самого материала. Аналогичная причина затронула 12 base_noise bindings
   трёх трасс. Это ошибка общей политики, не список новых объектов/SHA.
3. **Не вся большая грань вызвана этим исключением.** На снимке WorldLighting off
   остаются грани формы и границы исходного материала/UV/prelight. Центральные
   grass-поверхности уже допущены и используют normal hints; нельзя обещать
   исчезновение реальной острой геометрии после включения rock.
   Отдельный offline ray/source projection по записанной камере локализует
   маленькую левую вертикальную скалу примерно в pixel (450,350) как rock;
   центральные контрольные pixels — grass. Это геометрическая привязка исходника,
   не per-pixel GPU capture и не доказательство shader parity.

## Нормали, cache, время

В конце сеанса: 12 313 успешных normal-hint lookup, 433 fallback (96.6% от
попыток поиска hints, **не процент всех объектов**). Cache максимум 154 ranges /
1 117 654 bytes; changed-geometry rebuilds=0, cache resets=3. Счётчики cumulative.

Среди активных session windows CPU world/sky hook median .355 мс/кадр, P95 .490.
Окна смешивают паузу, FreeCam, on/off и debug F10; это не строгое performance A/B,
не GPU time и не FPS. Кузовный свет в этом профиле выключен: body_calls=0.
Видимый яркий Patrol здесь ожидаем и не проверяет новый кузовный путь.

## Исправление metadata-002 — та же DLL

Для подтверждённых base_noise capabilities winding берётся из нативного CW
геометрического контракта. Source normals — необязательные hints с facing check;
неподходящие hints дают текущую геометрическую нормаль. Правила shader/material
exclusions, alpha, vehicle, water/glass/glow и runtime pass guards не изменены.
Plain/static неоднозначность остаётся fail closed.

LSM1 остаётся 326 records; 12 bindings восстановлены, иных изменений нет.
LNH1 дополнен нормалями этих материалов: 88 343 records / 13 516 555 bytes.
Никаких geometry SHA или изменений C++/DLL. SDK экспорт изменённого France1
снова даёт побайтно тот же исправленный LSM1. Реальные LSM1/LNH1 прочитаны
тем же native x86 parser; четыре новых SDK regression tests и пять прежних
resolver tests PASS. Однократное чтение таблиц пробником ~98 мс; это не CPU/кадр.

## RUNTIME_TESTED / PENDING

RUNTIME_TESTED: две контролируемые пары on/off, работа authored normal hints,
материал rock исключён, сохранение неба/fog и indexed draw sequence; paused
FreeCam/HUD hidden видимы в этом конкретном прогоне.

PENDING: metadata-002 в игре; отдельные body пути Patrol/Tata, PS2-on/R4/VL1,
damage, три трассы/edited layout, полный Reset/FreeCam/HUD/water/collision/
standalone контроль; FPS. Sun остаётся выключенным до этих проверок и окклюзии.
