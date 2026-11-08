# GHOST1 — Ghost Mode: что осталось в ритейле и как его вернуть

Дата: 2026-11-08. Статус: **статический анализ, в игре ещё не проверялось.**
Retail EXE SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` (Ghidra 12.1.4,
headless-декомпиляция; адреса = VA при image base 0x400000).

## 1. Что известно от владельца

- Ghost Mode работал в demo 8.4.1 и 9.3.1. Три режима: **Steel Monkeys Best**, **Best This Session**, **Best Ever**.
- Призрак — это отдельные `*Alpha`-версии машин, поэтому адаптировать любую машину просто.
- После заезда появляется файл `Ghosts/<трасса>.<режим>.<класс>.ghost`. Образец:
  `D:\Game\Master Rallye Nov 2001\Ghosts\Italy1.bestever.t2.ghost` (20637 байт, машина Jump, Italy1).

## 2. Главный вывод

**В ритейле Ghost Mode не удалён — у него отрезан только вход из меню.** В EXE остались вся цепочка
записи, сохранения, загрузки и воспроизведения, строки имён файлов и строки меню. Не хватает только:

1. того, кто ставит Broker-флаги `Race/Car0/RecordSpline` и `Race/GhostPlayback` в 1 (в ритейле их
   только сбрасывают в 0);
2. пункта меню, который задаёт `Frontend/QuickRace/Ghost` (тип призрака);
3. ресурсов `DataGx/Vehicles/<Car>Alpha/` — в ритейле их **нет** (в Data.sma и в распакованных данных), а в
   demo 9.3.1 (GXM-исходники) и в Nov 2001 (собранные DX) есть для Forester, Jump, Trooper, Wildcat, newRav, rav4.

## 3. Карта кода в ритейле

| Адрес | Что это | Роль |
|---|---|---|
| `0x449100` | конструктор `gaFrontendAI` | сбрасывает в 0 `Race/GhostPlayback`, `Race/Car0/RecordSpline`, `Race/Car1/RecordSpline`. Кроме этого, в ритейле в эти ключи ничего не пишет |
| `0x48EB40` | генератор стартовой сетки | для каждой машины: если `Race/Car%d/RecordSpline` == true, создаёт сущность `SplineRecorder%d` с ИИ-компонентом `gaVehicleSplineRecordAI` (ctor `0x4C0B20`, vtable `0x691220`) |
| `0x4C0B20` | `gaVehicleSplineRecordAI` | читает `Race/Car%d/CarType`, `Race/RaceName`, регистрирует запись в SplineManager (`0x4BC590`); слушает `Car%d`, `Controller/Car%d`, `Race/Car%d/Time`, `Race/Car%d/Finished` |
| `0x4BCA30` | синглтон **SplineManager** (`DAT_006F69E0`, 0x30 байт) | две коллекции записей по 0x7C байт: загруженные (+4/+8) и текущие записи (+0x14/+0x18) |
| `0x48E9C0` | создание призрака при старте гонки | если `Race/GhostPlayback` == true: `SplineManager::Load` (`0x4BD750`), затем `Race/Ghost/StartPosition`, сущность `GhostCar` с `gaVehicleSplinePlaybackAI`. Если позиция = -1, флаг GhostPlayback сбрасывается |
| `0x4BFA10` | `gaVehicleSplinePlaybackAI` (vtable `0x6911E8`) | находит запись по `Race/RaceName`; шаг 0x3DCCCCCD = **0.1 с** |
| `0x4BFE00` | метод playback (vtable+0x14) | грузит `Vehicles/%sAlpha/car` + 4 × `Vehicles/%sAlpha/wheel` (`0x4BFFA0` — колёса), ставит флаг прозрачности |
| `0x4BD750` | загрузка призрака | имя файла: `0x4BDA70` → `0x4BBD10` (трасса + тип из `Frontend/QuickRace/Ghost` (`0x4AE0F0`) + класс); чтение `0x4BBA00`; разбор `0x4BCEB0` |
| `0x4BBA00` | чтение файла | `fopen`, проверка magic **0xAB59D02E** и версии **3**, размер, затем данные |
| `0x47D4C0`, `0x4CF3D0` | конец гонки (режимы 1/2/3 и 7) / выход из attract | вызывают `SplineManager::Commit` (`0x4BC3C0`) |
| `0x4BC3C0` | Commit | для каждой текущей записи финишировавшей машины: берёт `Race/Car%d/Time`, сплиты (`0x4BC2B0`, `Race/SplitTime%d/Car%d`), лог `SplineManager: %d %f`; если не split-screen (`0x4AE2D0`) → `0x4BD1B0`. Потом очищает записи |
| `0x4BD1B0` | сравнение и запись | сравнивает с best ever (`0x4BC030`) и session best (`0x4BC170`); при улучшении пишет файл(ы) через `0x4BBD10` + `0x4BB8E0` |
| `0x4A74A0` | маркер прогресса на HUD | ветка для призрака: цвет (1,1,1,0.5), `Race/Ghost/Progress` |
| `0x4ABCE0` | регистрация Race-ключей | среди них `Race/GhostType` |

Строки в ритейле (без прямых ссылок на код — скорее всего, достаются через таблицы текста/форматирование):
`steelmonkeys` `0x6DF348`, `bestever` `0x6DF358`, `sessionbest` `0x6DF364`, `STEEL MONKEYS BEST` `0x6CDCAC`,
`BEST EVER` `0x6CDCC0`, `BEST THIS SESSION` `0x6CDCCC`, `GHOST TYPE` `0x6CEEFC`, `GHOST`; глобальные
std::string `.ghost` (`0x6F6994`) и `Ghosts` (`0x6F69D4`). Их инициализаторы — `0x4BB3B0` и `0x4BB500`.
`0x4BD5F0` при сохранении делает `SetCurrentDirectoryA` на пользовательскую папку игры (`0x5417D0`).

Что осталось во фронтенде ритейла: в `DataScene/FrontendScreens/QuickRace.xml` (а также QuickRace2, PS2QuickRace,
NetworkHost) есть egg `GhostText` с текстом `Frontend/QuickRace/GhostTypeString`. Строк меню
`Frontend/QuickModeSelect/Ghost` и `GhostList` в ритейле **нет** (в 8.4.1 и 9.3.1 они есть).

## 4. Формат `.ghost` (предварительно, по образцу Italy1.bestever.t2)

Заголовок (читает `0x4BBA00`):

| Смещение | Значение в образце | Смысл |
|---|---|---|
| 0x00 | `2E D0 59 AB` | magic 0xAB59D02E |
| 0x04 | 3 | версия |
| 0x08 | 0x5091 (20625) | размер полезных данных = размер файла − 12 |

Полезные данные (порядок из десериализатора `0x4BCEB0`, значения из образца):

| Поле | Образец | Комментарий |
|---|---|---|
| float время (+0x10 записи) | 173.56 | время финиша, по нему сравнение best ever / session |
| блок `0x4BCB00` | `03 00 00 00 | 00 32 24 AD 42 00 24 DF 42` | не расшифровано (3 + два float ≈ 86.6 / 111.6?) |
| строка (len u32 + байты) | `Jump` | CarType → призрак грузит `Vehicles/JumpAlpha` |
| строка | `RaceTest/Italy1` | RaceName — ключ поиска записи |
| 8 полей по 4 байта | 0, 1, 2.5f, 0, 0, 1.7f, 1.7f, 0.1f | +2,+3,+5..+10; последнее 0.1 = шаг записи 0.1 с (совпадает с playback) |
| u32 число сэмплов + сэмплы | 0x3B8 = 952 | ключевой кадр = 3 float позиции (например −2457.1, 163.2, −913.4), затем дельта-кадры по 13 байт; ключевой кадр примерно каждые 10 сэмплов |
| u32 N + N × float | хвост файла | монотонно растущие float (~178…183) — вероятно прогресс/время по сэмплам или сплиты (`+0x40`) |
| 1 + 4 + 16 + 4 + 1 + 1 байт | хвост | флаги/цвет/параметры (+0x13…+0x69) |

Точную раскладку сэмпла и блока `0x4BCB00` нужно добить по `0x4BB160`, `0x4BF560`, `0x4BCB00` и по writer `0x4BB8E0`.

## 5. Различия demo ↔ retail (уже известно)

- Строки `Frontend/QuickModeSelect/Ghost` / `GhostList` есть в 8.4.1 и 9.3.1 и отсутствуют в ритейле → пункт
  выбора режима убрали из меню. `master.steelmonkeys.com` есть в 9.3.1 — вероятно, источник
  «Steel Monkeys Best» (файлы `*.steelmonkeys.*.ghost` ни в одной сборке не поставлялись).
- В 9.3.1 и в ритейле совпадают имена строк `.ghost`, `Ghosts`, `bestever`, `sessionbest`, `steelmonkeys` и
  magic/версия файла → формат, скорее всего, не менялся. **Проверка совместимости:** ритейл должен прочитать
  `Italy1.bestever.t2.ghost` из Nov 2001.

## 6. План возвращения

**G1 — включение без меню (минимальная проверка, дёшево).** Поставить перед стартом Quick Race
`Race/Car0/RecordSpline=1`, `Race/GhostPlayback=1`, `Frontend/QuickRace/Ghost=<тип>` (через proxy/Broker
setters, как в PAUSE-MENU1, или патчем констант в `0x449100`). Положить `JumpAlpha` (DX из Nov 2001) и
`Ghosts\Italy1.bestever.t2.ghost` рядом с игрой. Ожидание: на Italy1 у Jump появляется призрак, после финиша
пишутся `Ghosts\Italy1.bestever.t2.ghost` / `sessionbest`.
Риски: индекс типа в `Frontend/QuickRace/Ghost` (0/1/2 → steelmonkeys/sessionbest/bestever — порядок не
подтверждён); `Race/Ghost/StartPosition` = -1 отключает призрак — нужно понять, кто его выставляет.

**G2 — Alpha-машины для всего ростера.** Шесть машин есть в демо; для остальных (и SDK-машин) сделать генератор
`<Car>Alpha` из `car.dx`/`wheel.dx` (по демо: облегчённая модель без экипажа и с упрощёнными материалами;
прозрачность ставит код, флаг в `0x4BFE00`). Сравнить JumpAlpha и Jump в Nov 2001, чтобы повторить рецепт.

**G3 — нативное меню.** Вернуть выбор Ghost в Quick Race (OFF / Steel Monkeys Best / Best This Session / Best
Ever) по образцу `QuickModeSelect.xml` из 9.3.1 и обработчика из демо-EXE (найти, кто там пишет
`Race/GhostPlayback` и `RecordSpline`).

**G4 — Steel Monkeys Best.** Поставлять собственные эталонные `*.steelmonkeys.*.ghost` (или поддержать их
загрузку из папки мода).

## 7. Открытые вопросы

- Кто в демо выставляет `Race/GhostPlayback`, `Race/Car0/RecordSpline`, `Race/Ghost/StartPosition` (демо-EXE пока
  не декомпилирован).
- Точная строка имени файла: `0x4BBD10` берёт тексты по ID 0x5A (тип) и 0x4F (класс) из текстовой таблицы
  `0x485CF0` и разделитель `DAT_006DD600`; формат `<RaceName без RaceTest/>.<type>.<class>.ghost` выведен по
  образцу и не подтверждён по коду.
- Какие режимы гонки пишут запись: Commit вызывается для режимов 1/2/3 и 7 в `0x47D4C0`.
- Сосуществование с PS2-портом: сертификаты гонки в proxy отклоняют ghost (`network_attract_ghost_or_replay`),
  поэтому с включённым призраком PS2-эффекты будут Stock, пока сертификат не научится допускать GhostPlayback.
