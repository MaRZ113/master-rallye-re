# R-GFX5-2 — короткий ретест

**READY_FOR_HUMAN_RUNTIME.** MSAA4 и pristine MenuFreezeFix уже приняты по предыдущему runtime. Не повторять широкие тесты этих функций: сейчас нужны display/UI и их сочетание. Агент игру не запускал и DLL не развёртывал.

Кандидат: `D:\Game\Master Rallye\master-rallye-re-general\modernization\renderer\.build-msvc\Release\d3d8.dll`. SHA256 `525d92cc0b4961221b5aab240ec85f2d05984f1dad9d8170c0653d9b037cffd0`, размер **1 196 032 байта**, PE32/I386. Сохраните рабочие DLL/INI и используйте тестовую копию. Основные A–F — на pristine EXE SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.

INI рядом с DLL: `MRRRenderer.ini`, ConfigVersion=1. После правок перезапуск. Начните с [example](../../MRRRenderer.ini.example); остальные прежние настройки держите неизменными при сравнении. VehicleReflections.Mode=Stock. Файлы patcher/script не запускать, EXE на диске не править.

| Этап | Настройки и действия | PASS / что записать |
|---|---|---|
| A Borderless boot | Display.Mode=Borderless, Width=Height=0; UIStock, AAStock; MenuFreezeFix=true. Открыть меню и гонку. | Нет startup crash, рамок/заголовка/exclusive switch; точный выбранный монитор, рабочее меню. Если crash — session и последний display_breadcrumb. |
| B Centered4x3 | Только после A: InterfaceMode=Centered4x3. Меню/preview и гонка/HUD; F10 `B-centered-menu`, `B-centered-race`. | 4:3-контент центрирован, preview нормален, 3D не растянут. PROJECTION с actual returnRVA0x00161ED3: requested640x480, effectivewide, widescreen_applied=true, source=validated_ui_projection_owner. |
| C PreserveMargins | Только после визуального и trace PASS B: InterfaceMode=PreserveMargins, те же экраны; F10 `C-margins`. | Стабильные крайние элементы, нет осцилляции. Старый INVALID_TEST_STATE не засчитывается как результат C. Если ошибка остаётся, прислать F10/скриншоты для отдельного анализа packet timing. |
| D Windowed1280x720 | Display.Mode=Windowed, Width=1280, Height=720; UIStock, AAStock. При необходимости один resize/maximize и штатный game Reset. | Обычная рамка, client/backbuffer1280x720, окно внутри work area; Reset не переопределяет target. После ручного изменения следующий успешный Reset возвращает заданный размер. Нет роста за монитор. |
| E combined | Borderless0/0 + Centered4x3 + AF16 + Mode=MSAA/Samples=4; reflectionsStock. Меню/preview/гонка; F10 `E-combined`. | Устойчивое изображение, effective WindowedTRUE, monitor-native backbuffer/depth, MSAA4/DISCARD, UIwide. Samples=4 при ModeStock AA не включает. |
| F task switching | Настройки E; несколько minimize/restore и Alt+Tab в меню/гонке. | Нет crash/black frame/потери HUD/AA/UI. Сопоставить actual successful Reset и следующий quality descriptor; Alt+Tab сам по себе не доказывает Reset. |
| G modified EXE, optional | Одна уже имеющаяся легитимная изменённая копия; ничего не патчить для теста. | UNKNOWN_BUILD не означает глобальный запрет. MenuFreezeFix: fingerprint SUPPORTED / ALREADY_PATCHED / локальный UNSUPPORTED. Centered UI может пройти независимо; camera/packet margins/shadow/vehicle сохраняют exact-profile gate. Не создавать новый профиль ради прохождения. |

Если A/B не прошёл, зависимые этапы не засчитывать. Не повторять A–J из старой инструкции. PreserveMargins исходник не изменён: оценивать его можно только поверх доказанного wide UI. Split-screen/mixed-DPI/monitor migration остаются отдельными непроверенными случаями.

Прислать INI, session, указанные F10 и короткие ответы: Borderless boot; Centered/menu/HUD; margins стабильны; Windowed client1280x720 без роста; combined MSAA4/AF; Alt+Tab/Reset; optional modified-EXE capability. При отказе важны последнее breadcrumb, feature-local reason, window_commit_status и реальные размеры GetDesc/viewport. Raw captures не коммитить.

На16:9 ожидается virtual_width853.3333, extra213.3333, center_offset106.6667; effective UI _11=0.00234375 и _41=-0.75 при прежнем _22. Наличие metadata-математики без изменённой матрицы не является PASS. Build/static/synthetic проверки также не заменяют визуальный результат.

После human PASS — закрытие этого continuation; следующий возможный этап R-GFX5 HD UI replacement/upscale, затем отдельные gamma/LOD-доказательства. R-CAM1/F-PHOTO1, новый свет, cubemaps, postFX и weather здесь не начинаются.
