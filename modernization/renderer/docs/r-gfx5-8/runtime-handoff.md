# R-GFX5-8 — короткий runtime handoff

Статус: **READY_FOR_DIAGNOSTIC_RUNTIME**. Windowed исправлен по подтверждённой причине и проверен синтетически. В Exclusive добавлена диагностика владельца и порядка восстановления; исправление Error 2010 пока не заявляется. Игра в этой сессии не запускалась.

## Кандидат и provenance

DLL: `modernization/renderer/.build-msvc/Release/d3d8.dll` в `master-rallye-re-general`. SHA256 `fda771e03dc3bc5457d995ea755933f9a3982fc280ece061d5b6329ad9f3f543`, размер **1 531 392 байта**, PE32/I386. Заголовок нового session JSONL должен содержать `proxy_version=R-GFX5-8` и этот `proxy_sha256`. EXE/INI и прежний кандидат сохраняются; автоматического развёртывания здесь не было.

Для нового теста использовать собранный текущий DLL, содержащий PC-VISUAL-PILOT1 upload provenance. Не подменять его старым pre-foliage DLL. Исходники, тесты и документация собраны в [source handoff](R-GFX5-8-handoff.zip); DLL и игровые материалы в этот архив не входят.

## Windowed W1–W6

Начать с `[Display] Mode=1, Width=1280, Height=720`. AA/UI — Stock, FOV выключен, foliage diagnostics выключены. Для W1/W2 сначала ничего не максимизировать и не сворачивать.

| Тест | Действие | PASS |
|---|---|---|
| W1 | Сразу после старта тянуть правый край | ширина/нативный backbuffer следуют HWND, высота 720 остаётся; нет snap-back/2010 |
| W2 | Новый старт; сразу тянуть угол | обе оси следуют HWND без начального Maximize/Restore |
| W3 | `Width=0, Height=0`; новый старт и горизонтальный resize | прежний рабочий auto-size путь сохранён |
| W4 | Сначала вручную изменить нормальный размер, затем несколько Maximize/Restore | maximized — размер OS client; restore — последний пользовательский normal target |
| W5 | Minimize/Restore, затем ещё один обычный resize | нет 0×0 target, старого pinning или Reset-loop |
| W6 | Широкий клиент примерно 1734×480, затем узкий | backbuffer/аспект без накопления ошибки; позже отдельная проверка PreserveMargins |

Новый `windowed_resize_admission` должен показывать исходные requested dimensions == actual client, `initial_window_commit_complete=true`, `decision=accepted_hwnd_client_change`, обе оси normalized_logical == новый клиент. Следующий `display_native_attempt` Reset должен послать эти размеры и вернуть S_OK. Решение admission само по себе ещё не доказывает native успех. Если отказ остаётся, приложить соответствующую запись с decision/previous_committed_style/exstyle и реальным результатом.

## Exclusive E1–E6

Первый короткий запуск: `[Display] Mode=3, Width=640, Height=480, RefreshRate=0`; AA/UI Stock, FOV off, MenuFreezeFix off, foliage Mode=0/Diagnostics=0. Остальные условия не менять в ходе одного контрольного запуска.

| Тест | Действие | PASS |
|---|---|---|
| E1 | Frontend не менее 60 секунд | настоящий Windowed=FALSE; startup/initial Reset успешны, нет самопроизвольного 2010 |
| E2 | Один Minimize/Alt+Tab и Restore | настоящее восстановление устройства, без Error 2010 |
| E3 | Только после E2 PASS: повторить несколько циклов | нет накопления Reset/resource/focus ошибок |
| E4 | Поддерживаемый перечислением режим 1920×1080, повторить E1–E3 | восстановление истинного Exclusive на высоком разрешении |
| E5 | Только после консервативного PASS включить MSAA4 | native capability/reset без регрессии |
| E6 | Frontend → Quick Race → race → frontend → quit | рабочее устройство, штатный выход |

Если E2 снова даёт Error 2010, остановить этот запуск и передать **один самый короткий полный session JSONL из `MRRRenderer/logs/`**, соответствующий INI и указание действия/момента сбоя. E4–E6 и большие F10/RAM/VRAM dumps тогда не нужны. Желательно pristine retail для read-only game owner; на modified EXE message/native diagnostics работают, а новый owner tap честно остаётся unknown. Это не меняет существующую feature-local совместимость.

## Что выяснит новый capture

1. `display_window_message`: первый WM_STYLECHANGING с old/new и `transition_stack` показывает возможного автора изменения стиля. Stack — свидетельство конкретного вызова, не автоматический causal verdict.
2. Перед/после WM_SIZE фиксируют, находится ли Reset внутри игрового WndProc и какие activation/focus события уже пришли.
3. `window_context.game_window_owner` на валидированном pristine: +0x1C (`windowed`), PP.Windowed, HWND, saved_style, flags. `windowed=1` одновременно с `native_windowed_flag=0` подтвердит рассогласование native owner/presentation.
4. `display_reset_readiness` фиксирует реальный cooperative HRESULT непосредственно перед native Reset. DEVICELOST означает раннюю попытку при недоступном устройстве; DEVICENOTRESET перед failed Reset требует другого объяснения. Сам probe не изменяет результат.
5. `display_native_begin` → readiness → `display_native_attempt` задают параметры/результат; общий event_sequence и device_lifetime_id/epoch позволяют сопоставить их с окнами/фокусом. Нативная ошибка остаётся настоящей.

`transition_owner=renderer_window_commit` отделяет собственную постановку Windowed/Borderless от неатрибутированного `game_or_os_unresolved`. `display_watch=pre_and_post_observer_installed` должен быть в quality metadata; при partial/unavailable или `display_message_budget_exhausted` это ограничение нужно сохранить вместе с логом.

Можно получить компактную сводку:

```powershell
python modernization/renderer/tools/audit_quality_runtime.py "PATH\session-R-GFX5-8.jsonl"
```

Поле `observed_reset_while_device_lost` не является визуальным PASS/FAIL: оно сохраняет и readiness, и настоящий native result. Исходный JSONL нужен для первого style/focus события.

## Общая регрессия после независимых PASS

Прежний стабильный Borderless/Windowed режим: PreserveMargins, AF16, MSAA4, Gameplay FOV, MenuFreezeFix, ViewDependent2D. Frontend → Quick Race → гонка с AI → pause/unpause → смена камер → Alt+Tab → frontend → quit. Проверить отсутствие HUD jitter, прежний preview/FOV/culling, стабильные AI reflections, brake lamps, курсор и штатный выход. Foliage diagnostics оставить off. Backdrop остаётся BACKDROP_ASSET_EXTENSION_REQUIRED.

Для ответа достаточно: W1/W2/W3/W4/W5/W6 PASS/FAIL; E1/E2 (затем E3–E6 при успехе); Error 2010 yes/no; combined PASS/FAIL. R-GFX5 closeout возможен только после human PASS обоих режимов. R-CAM1/фотография/HD UI сейчас не начинаются.
