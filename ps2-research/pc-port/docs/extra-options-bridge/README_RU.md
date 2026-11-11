# Extra Options и актуальный Atmosphere Renderer

Дата: 2026-11-09. Статус: **сборка и ограниченные offline/process проверки пройдены; игровая проверка владельцем ожидается**.

Приватный пакет: `master-rallye-re-general/.research-output/extra-options-bridge/candidate/`.
Текущий renderer: `master` HEAD `a377fe7fe2fd76c0c8be33fb5d533a63496bd3c3`, включая Atmosphere 6.16, ночь, свет/блики фар и последующую оптимизацию `beb3967`. Native Extra Options: `research/extra-ghost1` HEAD `1347f9f522e59c19da17abaa5967d05971b86a83` плюс узкое исправление независимого MODEL при Tires=0. Изменения оставлены незакоммиченными.

## Разрыв и перенос

Старый `build_extra_options_candidate.py::stage_graphics` копировал готовый `.staging/ps2-enabled` и менял его текстовыми заменами. Сохранённый extra-set2-03 отличается от текущих исходников renderer в 53 общих файлах; среди них Atmosphere, свет/лампы, damage, reflection, HUD, foliage/props. Эти файлы не переносились назад и не заменялись старым снимком.

Перенесены только необходимые точки:

| Файл | Изменение |
|---|---|
| `renderer/extra_options_bridge.hpp` | Необязательное обнаружение уже загруженного dinput8, проверка ABI, queries, late loading и управление таблицей указателей |
| `renderer/fleet_frame_policy.hpp` | PC choice отключает PS2 replacement только для доказанного текущего участника; собственная логика Atmosphere остаётся независимой |
| `renderer/frontend_model_native.hpp` | PC choice сохраняет нативный COMPLETE draw в меню |
| `renderer/frontend_model.hpp/.cpp` | Поддержка старого texture-binding API, private copies и безопасная инвалидация upload |
| rmod1 `tools/build_extra_options_candidate.py` | Убраны копирование старого staging и все текстовые инъекции; сборка идёт через текущий canonical overlay workflow |

Файлы `atmosphere*`, регистры света, damage, CarSheet/SIDE HUD и геометрия автомобилей не изменялись. Baseline renderer tree остаётся `46663a8db86922443e74f4fb760b29b2d8ae6978`, закреплённый исходный commit `c357e8b780734b1505acb86f723a0e1b57f3c8a8`; он полностью совпадает с renderer tree текущего HEAD. В lock исправлено только имя ветки `perf/ps2-fps1 → master` и digest расширенного CMake patch. Добавление `.def` в build manifest закрывает учёт исходника тестового ABI fixture.

Canonical pipeline сохраняет прежнюю проверку git tree/dirty frozen source, исходных байтов, SHA патчей, deterministic generator, owned staging и workflow lock. Staging заново выводится из immutable baseline и **нынешнего** `pc-port`; отдельный устаревший source snapshot больше не является входом Extra Options сборщика.

## Независимость модулей и ABI

У renderer нет статического импорта `dinput8.dll`, вызова `LoadLibrary` для него или обязанности устанавливать Extra Options. Поиск относится только к уже загруженным модулям с именем dinput8.dll. Проверяется marker `0x45583201`; обычный системный DirectInput и неизвестный ABI не становятся провайдерами.

Сохранены существующие Win32/stdcall экспорты:

| Экспорт | Ordinal | Назначение |
|---|---:|---|
| `MRExtraSdkBindingAbi` | 7 | Прежний opt-in SDK binding marker |
| `MRExtraOptionsAbi()` | 8 | `0x45583201` |
| `MRExtraVisualV1(family,participant,phase)` | 9 | Старый PC/native query |
| `MRExtraRevisionV1(family,participant,phase)` | 10 | Ревизия selection/texture upload |
| `MRExtraTextureV1(family,index,w,h,src,dst,bytes,participant,phase)` | 11 | Старые exact-atlas private pixel bindings |
| `MRExtraVisualV2(family,participant,phase)` | 12 | 0/not applicable, 1/PC, 2/PS2, 3/legacy texture variant |

Шесть DirectInput exports/ordinals 1–6 сохранены. Нового публичного ABI и нового skin catalogue не вводилось. Kind3 сохранён для совместимости, но текущий MODEL по-прежнему предлагает только PS2/PC.

Таблица ABI публикуется целиком через release/acquire; выбранный provider удерживается ссылкой на модуль. Без provider поиск ограничен одним повтором за 250 мс, а не snapshot модулей на каждый draw. Поздняя загрузка input DLL обрабатывается. V1 renderer-query fallback остаётся доступен при отсутствии V2; неполная таблица обязательных exports и неверный marker не подключаются.

Текстурный ключ учитывает revision/phase/participant **только** для реально подменяющего pixels kind3. Отсутствующий provider, обычные PC/PS2 и AI используют исходные uploads без постоянных сбросов при смене участника. Временная замена не изменяет decoded asset; API rejection сохраняет оригинальные pixels. Pending transaction не сбрасывается ради смены textures. Reset, материал, освещение и native alpha остаются в текущем renderer pipeline.

**Границы самостоятельной работы:** input-only использует системный D3D8 и предоставляет свою игровую логику. Atmosphere/PS2 rendering без renderer там не ожидаются; MODEL может хранить выбор, но не реализует PS2 renderer самостоятельно. Renderer-only не предоставляет Ghost/GENERAL/сложности. SDK33 в приватном пакете по-прежнему устанавливает существующий suspended-process launcher; автономная DLL-загрузка самого Vehicle SDK не объявлена реализованной.

## Доказанная необходимость узкого исправления dinput8

Исходный EXTRA-SET2 публиковал `race_player/race_car` из `refresh_race`, вызываемого только через активный tyre path. При `Tires=0` wheel hook не устанавливался, поэтому MODEL мог работать в preview и терять owner в race.

Сначала добавлен тест на production callback: он завершился ошибкой **`appearance race identity refreshes with Tires=0`**. После исправления тот же случай проходит: общий существующий wheel call сохраняется при `Liveries=1`, обновляет прежний race cache, но не применяет compound при Tires=0. Original wheel update всегда выполняется первым. Ни формулы шин, ни выбор машин, ни Ghost/сложности не переписаны. Максимальный набор прежних семи customization hook sites не увеличился; при выключенных шинах изменяется только активность уже известного wheel site.

Из-за этого исправления итоговый dinput8 отличается от extra-set2-03. Randomizer core, Ghost payload и их семантика сохранены. Контрольная сборка до этого исправления воспроизвела исходные DLL побайтно; финальная версия отдельно прошла native/binding/forwarding проверки.

## Сохранность SDK33

Пакет создан из последнего интегрированного extra-set2-03. **Все 8016 файлов runtime скопированы побайтно**, включая 8004 resource entries и служебные планы/индексы. `addon-plan.json`, `native-patch-manifest.json`, extension, operations и resource manifest сохранены. Это сохраняет классы/порядок/IDs0–32, данные AI, физику, art и native states; это не новый игровой результат.

ID30 DefForester/T2, ID31 DefRav4/T2, ID32 DefTomcat/T3 не переназначались. Данные accepted V-DEF4.1 и working SDK/Course worktrees не изменялись. Night/GoldenHour, PS2 assets и glare masks скопированы из `Master Rallye Atmo-copy` в приватный пакет; оригинальная установка не является местом записи. Между двумя приватными renderer hosts asset-файлы hardlinked только **внутри** пакета; конфигурации/состояние отдельных hosts независимы.

## Конфликты и ограничения

`conflict-report.json` содержит оригинальные PE bytes/address mappings и конкретные spans. Проверены G1 17 operations, SDK33 263 mapped operations, Ghost/Difficulty19, Customization7 и 18 явно инвентаризированных renderer sites (sky, queue, FOV/camera, menu/attract, UI, race observer).

- Два известных несовместимых SDK/G1 Challenge overlaps по RVA `0x50111..0x50113` и `0x5ec38..0x5ec3a` остаются отражены в исходном `preimage-audit.json` как **CONFLICT**. Рабочий opt-in binding использует уже существующие composed stubs с relocated SDK displacement, а не последовательную перезапись hooks. Скрипт и compiled harness проверяют именно выбранную композицию.
- SDK `collection_delta_070` и renderer attract guard пересекаются на RVA `0x64f69`, но имеют одну замену `e9d8ffffff`. SDK владеет записью до resume; renderer распознаёт `already_redirected_unowned_no_overwrite`, не переписывает её и не присваивает владение.
- Других пересечений в указанном объёме не обнаружено. Новый query bridge renderer сам **не добавляет EXE patch sites**.
- Это ограниченный static audit. Он не заменяет runtime install order/семантику, проверку произвольных модов, всех опциональных physics/probe/Broker guards и других EXE. Их существующие signature/preimage/rollback gates сохранены. Частичный SDK или занятые SDK/Ghost regions должны отклоняться прежними проверками.

Новые модели/ливреи, лимиты IDs, рендер произвольной PS2-модели без её ресурсов, независимый shader parity и FPS-улучшения не заявлены. Для неизвестной PS2 family остаётся существующий native fallback.

## Автоматические проверки

| Проверка | Результат / предел |
|---|---|
| Canonical baseline | 24/24 CTest PASS |
| Текущий Atmosphere + bridge renderer | 48/48 CTest PASS |
| Port Python regression | 201 tests, 0 failures/errors, 3 явно обозначенных optional skips |
| Новые ABI/process fixture tests | wrong/missing ABI, V1 fallback, atomic publication, late loading, PC/PS2/AI ownership, private alpha-preserving binding, revision PASS |
| Production FrontendModel upload с настоящими PS2 Tata textures | late provider, private pixels, неизменный source, same-revision reuse, AI restoration, revision change и Reset PASS на instrumented device; **не GPU/gameplay** |
| rmod1 Python | 9/9, включая пять новых provenance/build tests и четыре composition tests |
| Native production callbacks | GENERAL, оба игрока, MODEL/carousel, human-only compounds, Tires=0 regression PASS |
| SDK provider/composed stub harness | valid/reject cases, изменённые/частичные данные, writable-state и participant default PASS в собственном x86 процессе |
| DirectInput forwarding | все 6 name/ordinal exports, DirectInput8Create/joystick format совпадают с system DLL |
| Ghost plan | `--check`: page/hook bytes воспроизводятся из сохранённых листингов |
| DLL load/factory smoke | Renderer-only, input-only, renderer-first и input-first PASS в собственных процессах; factory и ABI, **без игры и GPU scene rendering** |
| SDK33 preflight | combined/input-only suspended preflight; renderer-only resource verification PASS. `game_thread_resumed=false` |

Optional private source probes без доступных env fixtures в CTest сообщают `NOT_PERFORMED`; общий PASS не превращает их в выполненные проверки. Новому production upload test явно передан `MRR_EXTRA_FIXTURE_ASSET_DIR` с настоящими PS2 assets — он выполнен, не skipped.

Работающие установки, принятые пакеты и прежние незакоммиченные файлы сверены по `preservation-before/after.json`. Полные SHA-256 и финальные результаты — в manifests рядом с кандидатом. Игра не запускалась; suspended preflight и собственный probe-процесс не являются gameplay.

## Воспроизведение и выдача

Из rmod1, с новым уникальным именем:

```powershell
$env:MRR_EXTRA_FIXTURE_ASSET_DIR='D:\Game\Master Rallye Pristine\PS2Vehicles'
python tools/build_extra_options_candidate.py --name renderer-bridge-REBUILD
```

Сборщик записывает `graphics-source/inputs.json`, запускает canonical `general/ps2-research/pc-port/overlay/build_overlay.py`, проверяет неизменность входов/manifest и хеш DLL, затем копирует валидированный артефакт. Stale input/source или подменённая DLL отклоняются; это покрыто новыми тестами. `--package` остаётся прежним developer workflow; выданный пакет дополнительно сохраняет **нынешние** Night/GoldenHour assets и отдельные hosts.

Финальная native build: rmod1 `.research-output/extra-set1/renderer-bridge-03/`. Renderer собран в `renderer-bridge-02` и повторно использован в 03 только после точного равенства current renderer input manifests — исправление 03 затронуло лишь input. Provenance этого переиспользования сохранён явно.

Полные файлы выдачи:

- `candidate/Launch-Both.cmd`, `Launch-Renderer-Only.cmd`, `Launch-Input-Only.cmd` — подготовлены, автоматически не запускались.
- `candidate/Use-Day.cmd`, `Use-Night.cmd`, `Use-GoldenHour.cmd` — меняют только частные конфигурации данного пакета.
- `candidate/OWNER_TEST_RU.md` — ручная матрица.
- `source-build-manifest.json`, `changed-files.json`, `conflict-report.json`, `preservation-after.json`, `proxy-smoke.json` — конкретные источники, результаты и границы.
- `changed-source.zip` и `changes.patch` — изменения исходников без игровых активов; `source-build-manifest.json` ссылается также на полный проверенный staging source manifest.

Установка, публикация, merge, commit и push не выполнялись.
