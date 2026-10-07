# R-GFX5-4 — финальный ретест двух исправлений

Кандидат: `.build-msvc/Release/d3d8.dll`; точный хеш/размер — [build.json](../../data/build.json). Агент DLL не устанавливал и игру не запускал. Сохраните рабочую DLL/INI для отката; после изменения INI перезапускайте игру. EXE и ассеты не меняются.

Предыдущая база R-GFX5-3 принята как broadly successful по вашему отчёту. Проверяем только Windowed maximize/restore и стабильность PreserveMargins; AF16, MSAA4, preview, FOV/culling, отражения, cursor/exit остаются регрессиями.

| Проверка | Действия | PASS |
|---|---|---|
| A Normal | Display.Mode=1, Width=1280, Height=720 | Нормальный клиент1280x720, окно центрировано |
| B Maximize/Restore | Стандартная кнопка Maximize → Restore, повторить несколько раз; один раз в гонке | Окно остаётся maximized, backbuffer/depth следуют actual client; aspect/FOV корректны. Restore возвращает центрированный1280x720. Нет snap-back, Error2010 или Reset loop |
| C HUD | InterfaceMode=2; гонка15–30с, индикатор места, время, damage/status, GPS, тахометр, progress bar | Нативная анимация сохраняется, компоненты не прыгают между центральной и краевой позицией. F10: C-hud-stable |
| D Decorations | Main Menu и Quick Race; переход туда/обратно, следить за полупрозрачными квадратами | Движение плавное, нет прыжков ±half. Центрированные элементы после смены экрана не наследуют чужую привязку |
| E Diagnostics | F10 во время остаточного twitch; сохранить session и frame с меткой экрана | Видны anchor_id/direction/source, current_rule_match, engine_x/y, effective_x, ui_epoch и invalidated reason |
| F Combined | Borderless/native1920x1080 + PreserveMargins + AF16/MSAA4; Quick Race → race → Alt+Tab → Quit | Нет регрессии lifecycle, preview, UI или ранее подтверждённых game-specific возможностей |

Windowed: `normal_target` должен оставаться1280x720 даже при `window_state=maximized`. В `window_state_transition` и quality сравните `actual_client` с `effective_backbuffer`. При рабочей MSAA один genuine Reset проходит в native; эквивалентные self-commit echoes остаются suppressed. Максимизированное размещение не должно сопровождаться renderer SetWindowPos возвратом к normal target.

PreserveMargins: LEFT/RIGHT хранится как семантика identity, не как замороженный X. `engine_x` должен двигаться, а `effective_x-engine_x` сохранять ±half. `retained_anchor_without_current_rule_match > 0` показывает сохранение привязки после отхода от точного authored anchor. Пропуск полного consumer-frame, packet/mode/content-storage replacement, Reset или validated frontend/race epoch требуют нового admission. Это консервативная политика, не наблюдение настоящего heap generation; полностью одинаковый reuse без наблюдаемого изменения остаётся неразличимым.

F10 включает три кадра, максимум64 diagnostic identities/256 записей lifetime на устройство. При исчерпании бюджета перезапустите игру. Сообщите отдельно Normal, Maximize, Restore, HUD, Decorations/переход экрана и Combined: PASS/FAIL; при FAIL приложите session + F10. Если anchor стабилен, а twitch остаётся, это повод следующего анализа draw-local offset; сейчас Present restore boundary не заменяется.

BACKDROP_ASSET_EXTENSION_REQUIRED сохраняется. После человеческого PASS — R-GFX5 closeout, затем R-CAM1 → F-PHOTO1 → HD UI. Эти этапы сейчас не начинаются.

## Исторический R-GFX5-3 handoff (заменён текущим)

Кандидат: `modernization/renderer/.build-msvc/Release/d3d8.dll`; точный SHA/размер — в `../../data/build.json`. Агент игру не запускает и DLL в игровую папку не устанавливает. После смены INI перезапустите игру. Сохраните предыдущую DLL/INI для отката; EXE и ассеты сохраняются. Числовые и текстовые значения эквивалентны.

Ранее подтверждены Borderless/Alt+Tab, native resolution, Centered4x3, AF16, MSAA4 и MenuFreezeFix. Общая база: Display.Mode=2, Width=0, Height=0; InterfaceMode=1; AF=true/16; AA.Mode=1/Samples=4; отражения Mode=0. AF/FOV не меняйте в середине сравнений.

| Этап | Действия | PASS / FAIL |
|---|---|---|
| A Windowed | Mode=1, Width=1280, Height=720. Boot → frontend → race → minimize/restore → frontend → Quit | Клиент1280x720, внешний прямоугольник центрирован; нет Error2010/двойного native Reset; чистый выход |
| B Borderless exit | Mode=2/native. Alt+Tab туда/обратно; Alt+F4 во frontend. Отдельный запуск и Quit из меню | Оба выхода без ошибки/звука/краша; Alt+Tab сохранён |
| C Preview | Borderless16:9, Quick Race. Сравнить масштаб со stock4:3; скриншот. По возможности16:10 | Машина в authored preview-панели, не огромная/крошечная. Gameplay VFOV на эту коррекцию не влияет |
| D HUD margins | InterfaceMode=2, гонка, наблюдать HUD; F10, метка D-hud-margins | Нет чередования centred/edge HUD. При FAIL — F10 и session с ui_packet_lifetime |
| E Backdrop | Main Menu + Quick Race16:9; дополнительно QuickModeSelect/Results | BACKDROP_ASSET_EXTENSION_REQUIRED: боковой art НЕ расширен. Не объявлять покрытие исправленным. Центральная art не растянута, элементы не обрезаны |
| F Cursor | AutoHideCursor=1, delay1500. Idle внутри игры, движение; Alt+Tab на desktop и обратно | Idle скрывает, движение показывает, desktop cursor нормальный. Если focus-loss без Present оставляет курсор скрытым — FAIL, сообщить точный сценарий |
| G Hardened EXE | Текущий hardened391d5d86…; включить GameplayFOV и при желании ViewDependent2D. F10 гонки | Startup FOV/VehicleSemantics SUPPORTED по локальным владельцам; FOV меняется с culling sync. Reflection только proven vehicle0x152, wheels/brakes/glass/world Stock |
| H Combined | Несколько минут Borderless/native + UI/AF16/MSAA4, камеры, Alt+Tab, нормальный Quit | Нет lifecycle ошибок, мерцания HUD/AI; лампы/стёкла/колёса неизменны |

Для D diagnostic ID не является persistent game-object ownership. Hook стоит у потребителя0056D110; sorter00509A21 больше не меняется. Session поля: packet/entity, first/current/previous/restored frame, observed/original/effective X, engine_rewrite, consume_count; максимум256 записей. F10 включает диагностику на три последовательных кадра с номерами Trace, чтобы меню при старте не исчерпало бюджет до HUD. Для нового окна диагностики при исчерпании бюджета перезапустите игру. Same-value engine rewrite неразличим. Если HUD всё ещё чередуется, не объявлять double buffering доказанным без этих данных.

Для A/B ищите reset_policy.reset_request_source=window_commit_echo, echo_equivalent=true, native_reset_called=false, result0. Outer native Reset и его ресурсная invalidation ровно один раз. Отличающийся вложенный запрос отклоняется; deferred_resets означает отклонение, не скрытую очередь. Настоящий native HRESULT не маскируется. После final Release не должно быть SetWindowPos/оконного restore.

Сообщите A/B exit и Error2010, C preview, D HUD, F idle/move/desktop, G FOV/reflections, H combined: PASS/FAIL с коротким наблюдением. Приложите session + F10 с названием этапа. Backdrop E — отдельная art-граница. SUPPORTED в статическом аудите сам по себе не визуальный PASS.

После человеческого PASS кодовых этапов — closeout R-GFX5. Следующий приоритет: **R-CAM1 → F-PHOTO1 → HD UI**. Ни один из них сейчас не начинается.
