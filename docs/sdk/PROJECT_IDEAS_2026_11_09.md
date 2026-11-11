# Master Rallye — идеи проекта и техническая готовность, 9 ноября 2026

Это запись пожеланий владельца и проверка существующих исследований, а не реализация всего списка. Приоритет: работающий результат → рефакторинг → косметика. Идеи со скриншота `C:/Users/MaRZ/Documents/ShareX/Screenshots/2026-11/msedge_r7pzD8ggIX.png` сохранены ниже как backlog. Текст вложения не использован как самостоятельное разрешение на установку, перенос всех ресурсов или изменение игры.

Проверены текущие исходники и история чата **Continue Source Garage research (2)** (`01a194da-fa5b-71e1-bcb4-0f19cb7bad78`), включая исходную переписку о Forester/RAV4/TOMCAT. Старые документы содержат исторические `PENDING`: последующее подтверждение владельца имеет приоритет в пределах проверенной им сборки.

## Уже реализовано

По сообщению владельца от 2026-11-09, сохранить как реализованные функции:

- Пять уровней сложности: **Xtra Easy, Easy, Medium, Hard, Xtra Hard**, нативный выбор в меню.
- Полный **Ghost mode**, нативный выбор в игре.
- Нативный выбор **PS2/PC** на экране выбора машины.
- Выбор шин на вкладке **GENERAL** меню настройки машины.

Текущая кодовая линия: `master-rallye-re-rmod1`, `research/extra-ghost1` и `research/extra-set2`; свежие коммиты `e12ee38`, `9732f03`, `1347f9f`. Последний исправляет конфликт MODEL с каруселью, сохраняет SDK VehicleSelect и читает семейство из актуального реестра. Старые GEARBOX/F6, выбор частичных SeatBuggy sponsor panels и публикация одной строки TyreType не являются текущим пользовательским сценарием.

Статус четырёх функций — **OWNER_REPORTED_IMPLEMENTED**. В этом исследовании игра не запускалась. Сообщение владельца не подменяет отдельный замер эффективности шин, регрессию всех режимов/двух игроков или проверку произвольной PS2-модели, отсутствующей в ресурсах.

## Актуальная база и DLL

На момент исследования HEAD:

| Контекст | HEAD | Состояние до работы |
|---|---|---|
| `master-rallye-re-vehicles`, `research/vehicles` | `f2f8e47` | Есть незакоммиченные изменения SDK/launcher и документы Extra Options; сохранены |
| `master-rallye-re-rmod1`, `research/extra-ghost1` | `1347f9f` | Чистое дерево |
| `master-rallye-re-general`, `master` | `a377fe7` | Неотслеживаемые roadmap/log; сохранены |
| `master-rallye-re-course`, `research/r5t-course-archaeology` | `4244fa0` | Есть значительный незакоммиченный Course SDK/Invitation; сохранён |

DLL — генерируемые артефакты, а не автоматически подтверждённый результат одного HEAD. Для дальнейшей реализации брать свежие исходники этих контекстов, воспроизводимую сборку и сопутствующие ресурсы/ABI. Не выбирать DLL только по дате файла и не подменять действующие установки.

Проверенные SHA-256:

| Место | DLL | SHA-256 |
|---|---|---|
| `D:/Game/Master Rallye` | d3d8 | `e6b794bb58293b83925c3c69798a453b7a505202d8eb82f9889cc437b110a017` |
| то же | dinput8 | `8712b1379709d4d86936b429199b9c02e8603f7288f934f434358e17ed3b5a22` |
| `D:/Game/Master Rallye Pristine` | d3d8 | `c21343e4dc1887be8369b7245fa1c146943a19e96ae2c2b5602588be7acad3d0` |
| то же | dinput8 | `52ee1332e7a587878ea846a19dd7fcd5ca4cdd41694355558ee47e72c9c77c36` |
| SDK `.research-output/vehicles/extra-set2/extra-set2-03/host` | d3d8 | `8528a62d045c2ea614065695b5efaf5c1fd8783e84959dba30c13f5829f24c83` |
| то же | dinput8 | `f8d950a2f905c8408ffdf2aa57b8197b5cfdc32be0036360edb1394c87321093` |

Файлы пары extra-set2-03 совпадают с сохранёнными build outputs в rmod1 `.research-output/extra-set1/extra-set2-03`. Это последний найденный интегрированный кандидат этой линии, а не подтверждение его полной эквивалентности текущему renderer. Его `candidate.json` по-прежнему хранит историческое `owner_gameplay=PENDING`; текущее сообщение владельца отдельно подтверждает перечисленные функции.

**Обнаруженный интеграционный разрыв:** `tools/build_extra_options_candidate.py::stage_graphics` копирует уже подготовленный `.staging/ps2-enabled`, затем вносит Extra Options seams текстовыми заменами. Снимок extra-set2-03 отличается от нынешних renderer-исходников general во многих файлах, не только в четырёх местах интеграции; список/хеши сохранены в `audit.json`. В актуальных исходниках проверенных `frontend_model*` и `fleet_frame_policy.hpp` эта связка не встроена. Просто взять более новый d3d8 рядом с новым dinput8 недостаточно для утверждения совместимости. Следующий этап: перенести интерфейс в текущий renderer, собрать свежую согласованную пару и проверить MODEL/шины/Ghost/SDK33/свет/повреждения/Results. Старый rollback `0d85af66…` — исторический ориентир, не текущая обязательная DLL.

Retail EXE обеих установок и extra-set2-03 имеет SHA `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. Хеши здесь — идентификация и происхождение. Совместимость будущего мода проверять по PE/архитектуре, раскладке, оригинальным байтам/владению hooks и ABI, а не только по SHA.

## Все идеи со скриншота

«Можно сейчас» означает достаточно базы для ограниченной реализации/прототипа; это не обещание готового игрового результата без дальнейших проверок.

| ID | Пожелание | Что есть / что ещё требуется |
|---|---|---|
| I01 | Узнать настоящий hardcoded-предел ID машин | Принят **33-car roster 8/12/13**; известны записи 52 байта, отдельные RaceTest/UI/AI/save consumers. 33, 36, 128 и 256 не доказанные пределы движка. Можно продолжать измеримое расширение; универсальный максимум **UNKNOWN**. |
| I02 | Предел ID трасс | Известны **39 race registrations, ID0–38**, 36 уникальных основных course folders; это разные величины. Есть эксперимент IDs39/40 для пятиэтапного Invitation. Реальный общий предел и полноценная persistence/frontend поддержка новых IDs не установлены. |
| I03 | Шины и переключение PS2/PC | **Реализовано по владельцу**; шины GENERAL, MODEL Vehicle Select. Нельзя считать все прежние ограниченные прототипы текущим состоянием. |
| I04 | Новые классы после T1/T2/T3 | Расширение количества машин внутри класса уже есть. Четвёртая вкладка/класс — отдельное исследование: ID/classes, меню/локализация, AI, фильтры режимов, unlock, Results/save/replay. Готовой реализации не найдено. |
| I05 | Все демо-машины через Vehicle SDK, скины через нативный слайдер | Forester30/RAV4 31/TOMCAT32 приняты. Следующие полные источники перечислены ниже. Общего runtime-каталога ливрей и профиля roster34+ пока нет; это необходимые работы, а не простое копирование файлов. |
| I06 | Выбор соперников и мест на старте прямо в игре | R-MOD3 уже разделяет CarID/Class/DriverID/CarN и grid ordinal. Можно сделать ограниченный Quick Race PoC без повторяющихся IDs и перестановку нативных позиций. Нативный редактор, жизненный цикл событий и проверка каждого старта ещё нужны; произвольные мировые координаты заметно сложнее. |
| I07 | Новые категории спецучастков: импортированные/новый режим | Есть RaceTest/course entry и отдельные режимные владельцы. Можно прототипировать каталог/отдельный список существующих записей. Новый нативный тип категории с unlock, меню и маршрутизацией пока не квалифицирован. |
| I08 | Новые типы чемпионатов | Invitation retarget на три собственные сцены подтверждён владельцем; эксперимент пяти этапов имеется. Это база для нового event profile. Полностью новый режим требует points/standings/progression/save/UI, а не переименования Rallye Cup. |
| I09 | Перенос внешних/внутренних повреждений между этапами, сервисная зона, опция для обычных гонок | Известны damage/glass/runtime effects и championship persistence. Готовый перенос/восстановление целого состояния машины не найден в просмотренных материалах. Нужны карта solver/визуального damage, ресурсы деформации, идентичность машин, сериализация и порядок восстановления/ремонта. |
| I10 | Сервис: настройка, состав/очки, оценка повреждений, штрафы за ремонт; машина на улице, меню слева | Сейчас можно подготовить сценарий/макет и повторно использовать настройку шин GENERAL. Игровая зона, ремонтная экономика, standings и перенос damage зависят от I09/I08; уличная сцена с меню требует отдельного frontend/world ownership. Это пожелание интерфейса сохранено буквально. |
| I11 | Трассы RalliSport Challenge и Rally Trophy; объединить возможное | Собственные MR страны имеют общую систему координат; есть union/route/Invitation concept. Произвольный cross-game course importer не готов: нужны конкретные форматы, поверхности/коллизия/BSP, AI/limits, материалы, паковка и runtime. Декодер машин донора не доказывает поддержку трасс. |
| I12 | Глобальный перенос машин из RalliSport Challenge1/2, Dakar2, CMR04, Michelin Rally Masters, Rally Championship Extreme, 4x4 Evo1/2 | Source Garage/UVS, несколько адаптеров и принятые пилоты уже есть. Evo2 4Runner имеет исторический gameplay; Dakar2 material/native остаётся BLOCKED, Michelin RAV4 частично подтверждён, Mégane F2 требует нативных систем, RCX Astra — offline pilot. Остальные игры требуют отдельного per-format/per-car статуса; общий массовый импорт готовым не считать. |
| I13 | Удобное редактирование текстур/моделей, ручное размещение glare от фар через Vehicle SDK | Texture Studio/маски/замена PNG, geometry editor и материал/Glow authoring существуют. Можно добавить явные Export/Import и ручные типизированные lamp anchors в общий UI. Не все Studios перенесены в Qt; произвольное копирование Glow и полноценный native lamp ownership не закрыты. |
| I14 | Отключать glare, когда фара разбита | Есть damage feed, lamp registries и OFF/ON/glow groundwork; нужен подтверждённый сигнал поломки конкретной лампы, отдельно от тормоза/передачи/всей damage-зоны. Можно исследовать один stock case и связать с семантикой SDK. Универсальная per-lamp реализация не установлена. |
| I15 | Удобный Course SDK, редактирование/добавление трасс и конвертер в DX | Есть read model, Blender, StartArea/FinishArea/SplitTime; ограниченное редактирование RaceLine/limits и незакоммиченные GXM/BSP/new entry инструменты. Продолжать текущий course worktree. Произвольный законченный terrain/BSP/AI/material cooker и массовое добавление трасс не доказаны. |

## Демо-машины: восстановленный контекст

Полный предшествующий аудит — **101 snapshot / 429 model files**, а не 101 машина. Он проверял исходные 8.4.1/9.3.1/9.10.0, локальные rebakes и retail/SDK references. Повторно весь корпус не пересчитывался: сведения восстановлены из нынешних файлов аудита и истории, а не из памяти без проверки документов.

В чате после выдачи V-DEF4.1 владелец написал 2026-11-01T11:53:48Z: «теперь всё хорошо, все runtime тесты успешны». Это совпадает с `V_DEF4_1_FINALIZATION.md` / `V_DEF4_1_PROVENANCE.json: new_gameplay=USER_RUNTIME_CONFIRMED`.

| Машина | Принятая реализация |
|---|---|
| Demo/PS2 FORESTER | **ID30, DefForester, T2**, отдельный от retail PC Forester/WOOLDAND. Итоговая физика — полный отдельный retail WOOLDAND clone, не ранний Demo tyre hybrid. Darren Sutherland подтверждён; аутентичная боковая миниатюра и нативные glass/ON-core/halo прошли последующие исправления. |
| Бело-синяя Demo RAV4 | **ID31, DefRav4, T2**, отдельный от Newrav и Michelin RAV4. Полный retail Newrav physics clone; старые Demo коэффициенты — история. Исходные геометрия/текстуры; CarSheet и SIDE HUD сгенерированы. Daniel Nebot — editable REAL_FALLBACK, не доказанный оригинальный пилот. |
| Ранний синий PRIVATEER TOMCAT | **ID32, DefTomcat, T3**, оригинальное имя подтверждено 8.4.1, не выведено из каталога WildCat. Итоговая физика — полный retail Wildcat clone; исторический CarSheet сохранён, HUD реконструирован отдельно. |
| Остальные принятые в SDK33 | IDs26 Mercedes namespace,27 ImprezaProto,28 LancerEvo4,29 HeritageTrooper сохранены. Девять audit reference families — альтернативные принятые проекты, не девять одновременно свободных новых слотов. |

AI для подходящих addons: Quick Race/Cup/Master; TOMCAT также Invitation с обычным ограничением T3. Challenge сохраняет event-specific правила. Современная G1/SDK composition имеет отдельное доказательство; старый F3 conflict нельзя ни переносить автоматически на G1, ни считать исчезнувшим у произвольной пары mods.

### Что переносить дальше

| Очередь | Источник | Практическая готовность |
|---|---|---|
| D01 | **NewRav 9.3.1**, `corpora/demo-9.3.1/DataGx/Vehicles/NewRav` | Есть исходные car/complete/wheel и текстуры, историческая красная вариация. Первый кандидат на следующий перенос после проверки нового профиля вместимости. Нужны manifest, glass/lamps, независимая физика/identity/UI и новая игровая проверка. |
| D02 | **LandCruiser 8.4.1**, PCG rebake + оригинальный GXM | Полный набор; реальное отличие ранней формы/оснащения. Alias Mercedes того же оригинального GXM не считать второй машиной. |
| D03 | **Mégane/Schlesser ранний**, PCG + 8.4.1 | Полный набор и подтверждённые отличия; не Michelin Mégane F2. Сохранить исторические различия, не перекрашивать retail вместо восстановления. |
| D04 | **Tata 9.3.1** из оригинального corpus | Оригинальные три DX роли есть, даже если Nov-каталог GXM-only. Нужна квалификация нативных систем. |
| D05 | Jump, поздние KiaSportage/Wildcat/Navara | Сохранить как исторические варианты с отдельным анализом отличий. Изменённая топология/ливрея не всегда требует нового физического ID; различающуюся геометрию нельзя представить одним texture skin. |
| D06 | Rav4Alpha, JumpAlpha, Simmbugghini/local Nov Wildcat, прочие Alpha | Неполные assemblies, неподдержанная DX-граница и/или отсутствующая `mastersticker133-tga`. Нужны источники/форматы, иначе статус MISSING_INPUT/PARTIAL. Alpha aliases группировать по доказанным исходникам, не удаляя самостоятельные wheel/state различия. |

Mercedes/Copy of Mercedes и Trooper уже имеют соответствующие принятые native families: переносить недостающие варианты/состояния, а не автоматически дублировать identity. Канонический Forester из предыдущего переноса повторно не заменять альтернативным rebake.

**Первый технический blocker полного roster:** нынешний `tools/sdk_capacity_native.py` допускает текущий 512 KiB storage profile только при `count==33` с заданным порядком; per-class append ограничен 13 позициями. `count>=128` — ограничение signed imm8 emitter, а `kCars=256` — размер массива Extra Options. Ни одно число не равно доказанному пределу игры. Для NewRav34+ нужен новый явный capacity/storage/UI mapping profile, перенос владельцев полей и полная qualification; нельзя выдавать новый ID с помощью одной строки manifest. Существующие 0–32/сохранения/порядок должны остаться стабильны.

Практический процесс: отдельная исходная запись → восстановление через `addon_sdk.demo_restoration` / `restore_demo_vehicle.py` → независимый Workshop project → проверка геометрии/UV/текстур/коллизии/native states → физика/имя/цвет/две роли artwork → новый capacity/roster profile → свежий приватный пакет → игровая проверка выбора, race/AI, повреждений/света, Results, повторного входа и save/restart. При каждой новой машине повторять только затронутые проверки и разумную регрессию.

## PNG ↔ DXT: что есть уже сейчас

В этой игре `.dxt` исследованного PC-профиля — **собственная оболочка FEED и BGRA32**, не стандартный DDS/DXT1/DXT5/BC compressor: 20-байтный заголовок и `width*height*4` байт. PNG — upright RGBA8, строки DXT переворачиваются, B/R переставляются. Нельзя подменять эту операцию обычным DDS-конвертером.

Готовые API: `src/master_rallye/dxt.py`, `texture_authoring.py`; существующий CLI:

```powershell
# Выполнять из master-rallye-re-vehicles; вывод в отдельную staging-папку.
python tools/mrtool.py export-texture C:/staging/original.dxt --output C:/staging/edit.png
python tools/mrtool.py replace-texture C:/staging/original.dxt C:/staging/edit.png --source-sha256 SOURCE_SHA256 --output C:/staging/edited.dxt
```

Пути выше — пример, не созданные здесь файлы. Исходный DXT нужен как template. Safe mode сохраняет размеры и полный заголовок; неверный SHA и перезапись входов отвергаются. Декодер принимает noninterlaced RGBA8 PNG; RGB/palette/grayscale/interlaced надо явно нормализовать в UI через уже имеющийся Pillow, показывая итоговую альфу, а не молча угадывать её.

Legacy Workshop → **Texture Studio** уже имеет просмотр RGB/RGBA/Alpha, список всех использований, whole-texture multiplier, **Replace with same-size PNG**, Undo/Restore. `WorkshopProject.replace_png` переиспользует тот же codec. В Qt Widgets pilot есть geometry/materials/Glare groundwork, но полноценная Texture Studio/кнопки roundtrip ещё не перенесены; нельзя считать Qt заменой всех legacy Studios.

Нюанс интеграции: CLI `replace_texture` сохраняет весь header; `WorkshopProject._apply` пересчитывает word `+0x08` как CRC32 payload. Для GUI-конвертера явно выбрать существующую политику writer/report, сохранить template metadata и не обещать byte-identical no-op по пути, меняющему CRC. В текущей проверке побайтное совпадение получено для **codec/CLI**, не заявлено для произвольного GUI rebuild.

**Что можно доделать сейчас:** явная пара Export PNG / Import PNG рядом с выбранной текстурой, точный preview альфы/ориентации/размеров, batch export/import с manifest hashes, сохранение новой версии ливреи, список затронутых draws/material stages. Конвертер писать заново не требуется. Для standalone PNG→DXT без template сначала нужен отдельный writer policy метаданных, а не фиктивное сохранение исходного header.

Номер на двери — часть атласа. Для замены номера можно экспортировать соответствующую текстуру, отредактировать в графическом редакторе и импортировать; автоматически выделять цифры codec не умеет. Для перекраски использовать доказанную paint-mask (`register_paint_region` / `paint_region`) либо внешний редактор. RGB multiplier меняет и запечённые логотипы; shared atlas может менять кузов, шлем и другие детали. Alpha PNG берётся из пользовательского файла: сохранение исходной альфы для обычной окраски/номеров должно быть явной опцией, не неверным обещанием текущего replace API.

## Связь с текущим dinput8 и выбором скинов

Текущие роли следует сохранить: **dinput8 владеет выбором и persistence, d3d8 выполняет отрисовку, SDK создаёт и проверяет ресурсы**. Не вводить конкурирующий proxy/реестр.

Сейчас в `extra_options_runtime.cpp`:

- `Paint` — индекс пары PS2/PC, `Tire` — отдельное значение. State `MRallyeExtraOptions.state.ini`, `Car<id>` и `Player2Car<id>`.
- `MRExtraOptionsAbi=0x45583201`; `MRExtraVisualV2(family, participant, phase)` возвращает 0/no applicable,1/PC,2/PS2,3/старый PS2 с PC textures. UI EXTRA-SET2 предлагает **только PS2/PC**, старый вариант3 не является общим ливрейным слотом.
- Phase0 — menu car, phase1 — конкретный human race participant; семья сверяется с физическим реестром, чтобы same-family AI не получал замену игрока.
- `MRExtraRevisionV1` позволяет инвалидировать производные textures. `MRExtraTextureV1` умеет старую exact-pixel replacement binding, но таблица компилируется из pilot данных; это не динамическая загрузка любой DXT из SDK. Текущие Bindings не задают полноценный family/model/draw-stage ключ для произвольного каталога.

Предлагаемое расширение, **DESIGN_ONLY**, не существующее API:

1. Разделить **MODEL: PS2/PC** и **LIVERY: Stock/историческая/пользовательская…**. Нативный multistate-ряд LIVERY использует тот же проверенный frontend workflow. Модель не менять при переключении текстур; не добавлять CarID только ради номера/цвета.
2. SDK экспортирует versioned livery package: stable vehicle/package ID + family/physical binding, model variant, stable livery ID/label, template/hash/dimensions/alpha policy, texture key/role/slot, relative derived resources, provenance. Никаких абсолютных путей в переносимом descriptor. Одни и те же исходные DX/коллизия/физика переиспользуются только при доказанной совместимости варианта.
3. dinput8 читает проверенный каталог и сохраняет model/livery независимо. Мигрировать прежний Paint PS2/PC → model; неизвестный/удалённый skin → Stock с диагностикой. Не фиксировать пользовательский выбор только по порядковому номеру списка. Перепривязку CarID сверять со stable family/package identity.
4. Сохранить V1/V2 ABI и добавить optional versioned skin query/resource binding. d3d8 применяет private texture copies после проверки family, model role, texture/stage ownership, dimensions и generation. Для PC DX и PS2 texture bundle нужны **разные адаптеры**; совпадающее имя PNG/DXT и размер не доказывают равные UV.
5. Обновлять preview немедленно и race только нужного участника; сохранить AI изоляцию. Кэш ключевать model/livery/resource/device generation; не менять текстуру, которую используют AI/другая машина. Повторить lifecycle после damage, Reset и возврата в меню. Шины сохранять отдельным сценарием GENERAL.
6. Смена обычной RGB окраски не должна менять glass/brake/emissive alpha/stages. Автогенерацию миниатюр и marker colour можно использовать из уже имеющегося SDK, но сохранить выбранные MANUAL/HISTORICAL policies и различие CarSheet/SIDE HUD.

Первый ограниченный end-to-end pilot: один **уже принятый** автомобиль, две собственные текстурные ливреи одной модели, существующий physical ID; Stock + пользовательский номер/цвет. Сначала codec/UI/package/catalog и native selection, затем GPU/menu/race A/B, AI isolation, повреждения/свет, Results/re-entry/restart. Cross-model PC→PS2 atlas transfer и автоматическое распознавание всех зон не входят в этот минимальный proof.

## Рекомендуемый порядок дальнейшей реализации

1. Собрать текущий renderer + актуальную Extra Options интеграцию, сохранив четыре реализованные функции и SDK33; составить точный source/build manifest.
2. Доделать PNG roundtrip UI и versioned SDK livery packages; один нативный LIVERY pilot рядом с MODEL, без нового CarID.
3. Квалифицировать следующий capacity profile и переносить NewRav → LandCruiser → Mégane → Tata через общий manifest-driven workflow. Остальные snapshots учитывать в каталоге как варианты/дубликаты/неполные inputs, сохраняя все различия.
4. Параллельными по смыслу будущими направлениями остаются Course SDK/Invitation и ограниченный roster/grid UI; их source worktrees не смешивать с vehicle pilot.
5. Отдельные исследования: настоящий предел IDs/новые классы, per-lamp broken signal, persistent damage и сервис/новые чемпионаты, cross-game tracks и незакрытые donor formats.

Это порядок рекомендаций, а не новые приоритеты, отменяющие уже ведущуюся работу по освещению/производительности. Владелец просил сохранить идеи и исследовать готовность; игровые исходники/DLL этим этапом не изменялись.

## Проверка этого этапа

Свежий отчёт: `.research-output/vehicles/ideas-20261109/audit.json`; воспроизводимый скрипт рядом `audit.py`.

- **86/86** DXT из текущих DefForester/DefRav4/DefTomcat extra-set2-03: encode PNG → decode RGBA → encode DXT **byte-identical**.
- По одному большому template каждой из трёх машин: public `export_texture`/`replace_texture` roundtrip, **3/3 byte-identical**, неверный source SHA отвергается.
- **33/33** существующих теста `test_r4e`, `test_workshop`, `test_appearance_authoring` PASS; ноль ошибок/пропусков. Это выбранная проверка кодека/authoring, не полная регрессия всех SDK/DLL.
- **147 защищённых файлов** на время аудита без изменений: dirty исходники/документы в просмотренных worktrees, EXE/DLL/cores установок и 86 исходных textures. Git status до/после audit неизменен. Новые отчёт/память добавлены после этого snapshot; окончательная проверка сверяет их отдельно.
- Игра/GUI/GPU не запускались; новый ливрейный runtime, roster34+ и новые переносы не созданы. Никакой DLL не установлено, коммит/push не выполнены.

## Проверенные точки входа для продолжения

- Vehicles: `docs/sdk/V_DEF4_1_FINALIZATION.md`, `V_DEF4_1_PROVENANCE.json`, `V_DEF3_ROSTER_ORDER_RESULTS.md`, `DEMO_VEHICLE_AUDIT_RESULTS.md`, `DEMO_VEHICLE_IMPORT_SHORTLIST.md`, `DEMO_VEHICLE_COMPARISON_MATRIX.md`, `CLASS_SLOT_RESEARCH.md`, `NEW_CLASS_RESEARCH.md`.
- Restoration/build: `src/master_rallye/addon_sdk/demo_restoration.py`, `tools/restore_demo_vehicle.py`, `tools/sdk_capacity_native.py`.
- Textures/UI: `docs/texture-authoring.md`, `docs/sdk/help/en/textures.md`, `src/master_rallye/texture_authoring.py`, `dxt.py`, `workshop/service.py`, `workshop/gui.py`, `workshop/qt_editor.py`, `addon_sdk/vehicle_setup.py`.
- rmod1: `research/extra-ghost1/README.md`, `research/extra-set2/{README,RESEARCH}.md`, `src/native/rmod1/extra_options_runtime.cpp`, `extra_options_graphics.hpp`, `tools/build_extra_options_candidate.py`, `tools/extra_set2_frontend.py`, `research/r-mod3/gameplay-expansion/{README,forced-roster-and-grid,per-mode-opponent-counts}.md`.
- Course: `master-rallye-re-course/docs/course-new-entries.md`, `docs/course-sdk.md`, `research/course_marker_backlog.md` и существующие незакоммиченные course инструменты.
- Donors/editing: `docs/sdk/SOURCE_GARAGE_QUALIFICATION_MATRIX.md`, `WORKSHOP2_QT_RESULTS.md`, `MICHELIN_RAV4_NATIVE_RESULTS.md`; RCX private handoff `E:/RallyWorkshop_Sources/exclusive_research` остаётся offline/non-installable.
