# ATMOSPHERE2.1 — Universal Scene Lighting & Golden Hour

Статус: реализация и OFFLINE-проверка нового кандидата. Новая DLL ещё не проверена
в игре. Результаты ATMOSPHERE2 runtime-002/003 не распространяются на эту сборку.
Рабочий runtime-003 сохранён отдельным неизменяемым пакетом для отката/сравнения.
Расширение atlas runtime-004 прекращено после смены задачи; устанавливать его не нужно.

## Resolver

Универсальный путь не загружает ATS2 и не хеширует геометрию каждого объекта.
Он использует существующие live race/course certificate, render-thread/pass,
backbuffer, fixed-function shader/state и buffer provenance. Обычный мир допускается
только при identity world matrix; текущая vehicle classification дополнительно
исключает известные автомобили. HUD, меню, transformed props и специальные проходы
не получают общего tint. Неизвестные/неполные/poisoned buffers остаются native.

Материалы имеют категории road/terrain/vegetation/static либо exclude. Неоднозначные
plain/secondary материалы остаются native. Дополнительные метаданные LSM1 содержат
только материал, course, content identity текстуры, shader capability и winding:
326 записей для PC/PS2 France1/Turkey2/Turkey3, около 77 KB. Сравните с прежним
atlas 4192 geometry records, 11.25 MB и обязательным compiled digest. Хэш LSM1 —
контроль целостности файла, не compiled allowlist; texture SHA читается один раз на
resource generation для установления идентичности материала, не геометрии объекта.

Без SDK/метаданных AutoGround допускает только opaque base_noise с точной нативной
noise-stage identity, непрозрачной texture0, CW-front/cull контрактом, identity world,
актуальными индексами и >=75% upward ground faces. Это conservative terrain-class
вывод, не доказанное semantic road имя. Неизвестные plain vegetation/static исключены.
Повреждённый присутствующий LSM1 отключает этот маршрут; отсутствие файла допускает
независимый AutoGround-контракт. Нельзя ослабить shader/pass proofs через metadata.

Кеш ключуется по поколениям VB/IB/texture, конкретным byte ranges, stride/min,
alpha/noise/cull, race и owner lifetime. Проверяется существующее зеркало CPU:
initialized coverage, available/not poisoned, revisions. При прежних ревизиях
повторного чтения/анализа геометрии нет. После других записей в общий буфер только
точное сравнение диапазонов определяет, изменились ли данные этого draw; SHA не
используется. Изменённый диапазон заново получает normal/class/color расчёт.
Кеш ограничен 2048 диапазонами / 48 MiB; при превышении — native fallback.
Restart/re-entry и Reset очищают кеш. LSM1/config читаются при новом процессе.
Текстуры считаются обычными managed asset textures; их identity-кеш инвалидируется
поколением ресурса/Reset. Произвольные same-generation texture rewrites не являются
поддержанным способом runtime-authoring метаданных.

Телеметрия раз в 120 frames: QPC hook CPU, calls, cache hits/misses/rebuilds,
content comparisons, reset count, memory, принятые/пропущенные submissions и число
cached ranges по категориям. Ranges/draws не выдаются за unique game actors.

## Свет и нормали

WorldBrightness отдельно управляет затемнением мира. Рекомендуемый GoldenHour:
0.72, cool ambient (0.60/0.70/0.94)*0.60, warm sunlight (1.50/1.00/0.55)*1.10,
Exposure 1.05. Дополнительный darker-профиль 0.58. Baked vertex colors не заменяются
белым: их RGB модулируется с сохранением alpha и исходной видимости тёмных участков.
Непотреблённые вершины сохраняются. Это статический directional prelight, не новые
динамические тени и не screen filter. Fog имеет отдельный контролируемый scoped state.

Нормали курса восстанавливаются из текущих triangles с area weighting; winding
материала проверяется по исходным authored normals SDK. Неоднозначный winding
отключает материал. Это геометрические нормали, не тождественные artist smoothing.
Двусторонняя vegetation не гаснет из-за взаимного уничтожения back/front normals.
Не-identity transforms общего мира пока исключены; inverse-transpose реализован и
проверен для отдельного body prototype. Singular/non-finite данные отклоняются.

Скайбоксы GT3 Deep Forest/Grand Valley — ровно прежние source-derived пары, с теми
же alpha/UV-проекцией. WorldBrightness/ambient/sun не меняют небо. Результат их
предыдущей адаптации к MR не объявляется точным воспроизведением GT3 runtime.
Ночь, фары и новые sun FX не разрабатываются, все соответствующие флаги off.

## Композиция PS2

Source/owner preflight стекла, моделей, ламп, физических объектов и replacement
passes видит оригинальные буферы. Для обычного материала Universal применяется
перед конечным native draw, после этих решений. Подтверждённый base_noise грунт
может быть освещён перед существующим GroundDetail: его два прохода/UV/текстуры
остаются прежними; pass2 не использует diffuse. World-lighting buffers и fog
восстанавливаются существующей retry-on-failure транзакцией. Unproven PS2-specific
passes остаются native/своим принятом эффектом. Ни копирование reflection framebuffer,
ни ориентация/mapping/тайминг Reflection4 не менялись. VehicleLighting1 не выключается.

В пакет входят снимки текущего Atmo-copy PS2-Off и существующего Pristine PS2-on
(Reflection4/VehicleLighting1). Это готовые конфигурации для отдельных проверок,
не заявление о runtime совместимости новой DLL. FreeCam/Collision Debug/physics
код не изменён, но новые сочетания требуют регрессии в игре.

## Body prototype

Только opt-in BodyPrototype=TataBonnet: исходный healthy PC Tata record19,
48 vertices / 55 triangles, tatabon+whitepaint; известный исходный geometry witness
и точная tatabon texture identity. Дополнительно — текущий native race owner/model
selected tree, descriptors, buffers/generations, world matrix, opaque shader/pass.
Private damage tree, стекло, колёса, off-lamp/glow и PS2 model replacements не
допускаются. Применяется только цвет FVF152 diffuse; нормали переводятся в world
inverse-transpose, normals/UV/texture/render reflection states не меняются.
Хук расположен после reflection preflight, VB/IB восстанавливаются перед его cleanup.
Свидетель: docs/reflection-port1/material-source-contract.json. Прототип пока
RUNTIME_PENDING; это не universal lighting всех автомобильных кузовов.

## SDK / изменённая конфигурация

src/master_rallye/course_lighting.py — необязательное расширение Course SDK.
CLI tools/atmosphere_lighting_metadata.py экспортирует source DX material capabilities.
Неизвестным авторским plain материалам можно задать exact role в JSON; dangerous
shader/material exclusions имеют приоритет. --base сохраняет stock/другие материалы,
позволяя добавить новый course без чтения stock SDK sources. Source geometry hashes
в LSM1 не записываются. Proxy DLL не пересобирается. Новый game course всё равно
нуждается в корректном scene/lifecycle/menu/route ресурсе самой игры.

Контрольная edited France1 render configuration: 1180 road vertices с UV0 u+0.125
и RGB prelight*0.9; внутри road draws изменён порядок triangles. Positions/normals,
triangle multiset, bounds и collision/route suffix побайтно сохранены. Размер DX
сохранён, исходный файл не изменён. Экспортированная metadata побайтно совпадает с
обычной: без регенерации/нового SHA объекта/пересборки DLL. Это изменённая render
конфигурация, не доказательство нового маршрута/physics authoring.

## Проверки и граница принятия

Core tests: новая/изменённая topology без source object hash; out-of-range indices,
NaN/degenerate данные, two-sided normals, непотреблённые vertices/alpha; normal transform
и singular matrix; provenance revisions/byte changes; metadata checksum/parser и новый
course name; water/glass/glow exclusions; bounded cache; восстановление всех four
pending slots и retry; BL1 source prefix; original sky alpha/UV asset identities.
Integration tests проверяют положение хуков после PS2 replacement preflight.
SDK round-trip/append/tamper и экспорт modified layout проверены отдельно офлайн.

Финальная сборка: DLL 40e630dbee5163fbeea89de626cdee4e8b9b35a30d3d36b6961bd6c1cdd00885;
24/24 baseline CTest, 46/46 PS2 CTest, 186/186 Python PASS. Package/source hashes
и отдельные SDK/installer checks — в validation.json. Все игровые A/B Baseline/PS2, CPU/FPS, cache-reset lifetimes, modified layout,
body prototype и compatibility нового кандидата пока RUNTIME_PENDING. Старые
ATMOSPHERE2 логи сохранены как отдельный предыдущий baseline, не как новый PASS.

Body prototype не входит в QPC таймер universal begin; его производительность отдельно не измерена.

## Уточнение по последующим логам, 2026-11-04

DLL 40e630...: PID 50280/42324/29412 и шесть полных F10 подтверждают записанные
Original/GoldenHour France1/Turkey2/Turkey3 и длительный France1.
Статус: RUNTIME_WORKING_VISUAL_CALIBRATION_PENDING. Стыки и яркость Nissan
подтверждены скриншотами; их причинная связь с отдельными draw пока не доказана.
Приведённый выше RUNTIME_PENDING относится к состоянию при упаковке, а не к
этим последующим сессиям. Полная PS2-on/edited-layout/body/compatibility матрица
не повышается автоматически. Новая работа — docs/atmosphere22.
