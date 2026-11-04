# ATMOSPHERE2.2 — кузов, баннеры, candidate-runtime-003

## Подтверждено записанным прогоном

DLL aaa84583… и metadata-002. PID 35932: five complete F10; восстановленный
rock-tga теперь получает material_capability_and_live_geometry и normal hints.
Скала затемняется вместе с окружающей поверхностью. Этот процесс целиком был
Seam-Debug, поэтому свет кузова был выключен даже после выбора другой машины.

Отдельный PID 11964 — Body-Debug. Four complete F10 (1200/3692/7897/10272).
Native owner/material route допускает пять paint материалов Patrol и семь Tata,
в сумме все 12 первоначальных capabilities. Sidecars содержат 5/7 диапазонов × 8 samples, то есть
40/56 samples; во всех изменён diffuse. Текстуры/alpha/UV/normals не меняются.
Успешное повторное применение зарегистрировано в четырёх race epochs при
переключении между Patrol и Tata. Конкретный тип каждого перехода не выводится
только из счётчика поколения. Healthy native PC route подтверждён; PS2 fleet
route, повреждённые деревья и полный Reset ещё не подтверждены этим прогоном.

Скриншоты MRallye_9SzPiRRw1X / QusIlH2jOx / 8Ej5JjxqP6 / h1xfA0ENRT
показывают затемнение основных панелей обоих кузовов и оставшиеся яркие части.
QPC median активных world/sky окон около .413 мс/кадр; median body delta между
соседними окнами около .264 мс/кадр. Это разные CPU метрики, не GPU/FPS и не
контролируемое сравнение производительности. Счётчики body_ticks cumulative.

## Причина оставшихся светлых частей

- Patrol: logowhite64 + whitepaint — 12 исходных faces, logoblue64 + whitepaint —
  42 faces. По оригинальному car.dx это окрашенные расширители крыльев, а не
  HUD/logo overlay. Одно лишь слово logo в primary ошибочно исключало их.
- Tata: tataplasticbump / tataplasticbump2 + perspex — 196/262 исходных faces,
  отдельные непрозрачные пластиковые детали кузова. Общий допуск perspex
  небезопасен: этот secondary используется также у других типов поверхностей.
- Колёса/шины/диски, spare-wheel cover и отдельные lamp/glass/sticker passes
  намеренно остаются native в рамках исходного задания. Их яркость не является
  подтверждением сломанного paint route. В этой сборке освещение колёс не добавлено.

## Изменения candidate-runtime-003

**BLM2:** явная роль Paint или OpaqueTrim на material capability. Старый BLM1
по-прежнему читается как Paint. Paint требует whitepaint/silverpaint secondary;
OpaqueTrim — perspex и отдельной явной capability. Все текущие owner/resource/
descriptor/texture/pass/world/alpha/depth guards остаются. Unknown role и
glass/wheel/tire/lamp/glow/brake/sticker/driver исключаются. BLM2 содержит
16 записей: прежние 12 + два fender material Patrol + два trim material Tata.
Никаких geometry SHA. Файлы модели, текстуры, колёса и отражения не заменяются.

**Баннеры:** подтверждённая причина пропуска в F10 — native_material_excluded
для goodrich/masterlogo/fujitsu/go и других рекламных панелей. Они являются
opaque plain Course geometry (FVF142, cull3, alpha-test0, stage1 disabled), но
default эвристика названия не назначала им static role. В SDK добавлена явная
роль signage; файл signage-roles.json задаёт семь source material bindings на
трёх трассах, независимо от количества объектов/вариантов draw. Новые панели
автор задаёт той же ролью через SDK; изменения Proxy не нужны. Это не допуск
всех текстур с logo или всех plain draws. HUD и специальные проходы не проходят
runtime world guard. Winding нативный CW; подходящие authored normal hints
используются, остальные дают геометрический fallback.

LSM1: 326 записей; LNH1: 90 493 записей / 13 845 505 bytes. Новые role правила
прошли 5 SDK tests; обе metadata таблицы читаются native x86 parser. Полные
24 baseline / 46 port CTest / 186 Python tests PASS для новой DLL. Это офлайн
проверки, не игровой PASS дополнительных четырёх частей или баннеров.

## Что осталось проверить

003 DLL + BLM2 + новые LSM1/LNH1 в игре: баннеры и четыре дополнительные части;
PS2-on на принятом Reflection4/VehicleLighting1 профиле и исходной ориентации,
оба кузова/damage; Turkey2/Turkey3; modified render layout той же DLL/metadata;
полная FreeCam/HUD/water/physics/collision/reset/standalone матрица и FPS.
Ночь и фары не разрабатываются. Sun FX выключены: до PS2 stability/occlusion
контроля не заявляются ни disk/halo, ни отсутствие flare через препятствия.
