# ATMOSPHERE5 — единая папка Atmosphere и освещение оставшихся объектов

## 1. Единая папка `Atmosphere\`

Все ассеты атмосферы подключаются только ключами `Atmosphere.ini` (и A/B-профилей
`profiles\*.ini`), поэтому объединение = перенос файлов + переписывание ключей, без новой DLL.
Инструмент: `tools/atmosphere_unify_layout.py <папка игры>` (по умолчанию dry run,
`--apply` переносит, пишет журнал `Atmosphere-unify-*.json`, `--undo <журнал>` откатывает).

| Было | Стало | Ключ |
|---|---|---|
| `Atmosphere\sets\sunset`, `Atmosphere2\sets\r_*` | `Atmosphere\sky\<set>` | `CustomSet` |
| `Atmosphere25\materials.lsm`, `common.json` | `Atmosphere\materials\` | `LightingMetadata` |
| `Atmosphere22\normals.lnh` | `Atmosphere\normals\` | `NormalHints` |
| `Atmosphere29\vehicles.blm` | `Atmosphere\vehicles\` | `BodyMaterials` |
| `Atmosphere27\courses` | `Atmosphere\courses\` | `LightingPackageRoot` |
| `Atmosphere28\regions-*.ini` | `Atmosphere\regions\` | `RegionalAtmospheres` |
| `AtmospherePrivate\GT3` | `Atmosphere\private\GT3` | `SunRaysTexture` |
| `Atmosphere21`, `Atmosphere22\body.blm`, `Atmosphere2\scene.atlas`, `vehicles-legacy-002.blm` | `Atmosphere\legacy\...` | не используются |

Значения по умолчанию в `renderer/atmosphere.hpp` (Atmosphere21/22) не менялись: этот участок
защищён хеш-тестом BL1 (`tests/test_atmosphere2.py`), а установленный INI задаёт все пути явно.
`scene.atlas` нужен только при `SceneResolver=LegacyAtlas`.

## 2. Почему объекты оставались неосвещёнными (по логам PID 29080 / 19824)

Источник — `atmosphere27-*/admissions.jsonl` (F10-захват). Все проблемные объекты имели в
пакете трассы `Deny` (`resolver_excluded_material`): SDK классифицирует материал по словам в имени,
а авторские роли (`roles.json`) были только у France1/Turkey2/Turkey3.

| Трасса | Объект | Материал | Причина |
|---|---|---|---|
| Italy1 | ёлки | `pinus`, `pinus2`, `conniffer` | нет слова `tree` в имени |
| Italy1 | здания | `i_largevilla1/2`, `shelter1` | нет слова-признака постройки |
| Italy1 | баннеры | `bagoo`, `goodrich`, `schlesser`, `fujitsu`, `go`, `kaori`, `pathesport` | роль `signage` была только у трёх трасс |
| Italy1 | ящики | `crate1` | нет признака |
| France1 | столбы ЖД | `railpylon`, `f_railmisc1` (сигналы/флаги) | нет признака |
| France1 | сетчатый забор и мостки | `marina_alphas` | второй слой отражения `glass-tga`, не сертифицирован |
| France1 | ограждение | `raillings` | нет признака |

Italy1 FVF 0x112 (`Shader mismatch`) — это колёса машины игрока, не трасса.

## 3. Изменения

* SDK `course_lighting.py`: имена-признаки растительности (`pinus`, `conif`, `conni`, `hedge`,
  `vines`, `spruce`, `cypress`, `palm`) и построек (`villa`, `village`, `hotel`, `shack`, `shelter`,
  `tower`, `balcony`, `pylon`, `railing`, `railling`, `crate`).
* `roles.json`: общий блок `"*"` для всех трасс (баннеры спонсоров → `signage`; сено, брёвна,
  провода, фермы, лодки, грузовик MR, `marina_alphas` → `static`). Роли конкретной трассы важнее.
* `glass-tga` — допустимый вторичный слой отражения статики, но ТОЛЬКО для материала с явной
  ролью `static` (не по имени). DLL: сертификат `glass-tga` принимается парсером метаданных и
  проверкой environment-прохода; энергия отражения масштабируется тем же world environment factor,
  что и у aluminium.
* Базовая таблица `base-006.lsm` = `materials-005.lsm` без «пустых» Deny-записей (category 0, flags
  DENY): иначе старое исключение побеждало новую роль. Окно/стекло/вода/колёса исключаются заново
  из исходников.

Остаётся вне допуска (нужен отдельный разбор): `ctyre` (покрышки — слово `tyre`), `temp`, `Null`,
`darkgreen`, `lock`, `planealpha`, `s_light01`, смешанные plain+noise (`wall`, `f_conc`,
`canyon_no_line`, `pavement`).

## 4. Сборка и проверка

DLL `6474b0dbc992bac61d1e87ccae675c9d9720ca26dbf4260e4cc2f33964b7ed98` (baseline `91ede614…` без изменений),
CTest 24/24 baseline + 46/46 PS2, Python SDK тесты OK. Пакеты: `course_lighting_batch.py --roles docs/atmosphere25/roles.json
--base base-006.lsm`, 59 SceneID-пакетов. `package-diff-vs-005.txt`: только переходы Deny → Lit и новые сертификаты
`glass-tga`; ни одна ранее освещённая запись не потеряна (первый прогон закрывал `sign01` — роль убрана из общего блока).
normals.lnh выросли за счёт подсказок нормалей для новых материалов. Игровая проверка — за владельцем.
Откат установки: `rollback-463b0d0d` (d3d8.dll, courses, Atmosphere.ini) или журнал `Atmosphere-unify-*.json`.

## 5. ATMOSPHERE5.1 — забор на мосту, флажки, водопад, новые роли

Игровая проверка 5.0 (PID 19304, кадры f6479 / f29879 / f36283):

* **Italy1, забор на мосту** — освещён, но половина светлая, половина тёмная. У вершин были
  подсказки нормалей, и правило парных тонких объектов (35% солнечной + 65% теневой стороны)
  пропускалось: забор, обращённый к солнцу, получал полное низкое солнце, обращённый от него —
  только тень. Теперь любая парная (front/back) геометрия не-растительности всегда использует
  общую долю, независимо от подсказок (`scene_resolver.hpp`).
* **France1, флажки/сигналы ЖД** — `f_railmisc1` рисуется blended (SRCALPHA/INVSRCALPHA, ZWrite,
  без alpha test) и при `ForestFix=1` уходил в ForestFix до атмосферы, с исходным prelight.
  Теперь blended plain-проход (FVF 0x142, одна стадия) освещается, если у материала явная роль
  растительности или статичного cutout с флагом AlphaTest; RGB меняется, альфа/смешивание/глубина
  нативные. При ForestFix подготовка идёт до его перехвата (`world_lighting_before_replacement`).
* **Водопад с PC-водой** — отдельная карточка FVF 0x102 (без цвета вершин, с туманом, blended),
  поэтому полная яркость текстуры. Адаптер PC-воды брал только поверхность (0x252). Новый путь
  `pc_waterfall_draw`: только текстура, которую пакет трассы называет `*waterfall*`; стадия 1
  (нативно DISABLE) умножает RGB на ту же энергию PC-воды, fog color как у воды; альфа, UV, глубина
  без изменений, состояния восстанавливаются (`body_unit` = 1 для этого пути).
* **Новые роли** (`"*"`): `darkgreen` → vegetation; `lock`, `temp`, `planealpha`, `newtex` → static;
  `canyon_no_line`, `pavement` → terrain (обычный + noise проход одной роли).

Остаются закрытыми: `s_light01` (пустая белая текстура фонаря), `Null`, `ctyre`, а также
«Mixed source contracts» в объединённых трассах Inv* (balcony, brick, farm5, gate01, hay, vhut*) —
разные исходные модели дают разные контракты одного материала; нужен отдельный разбор.

DLL `2c108b869f5869cd0b64f89113b2344887e3bf6345dba3f7097817f2ee25776b`, CTest 24/24 + 46/46.
Пакеты `batch-003`: относительно 5.0 только Deny → Lit (`package-diff-5.1.txt`). Откат: `rollback-6474b0db`.
