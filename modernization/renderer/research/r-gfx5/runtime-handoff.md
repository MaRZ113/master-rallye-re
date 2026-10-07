# R-GFX5 — проверка человеком

**READY_FOR_HUMAN_RUNTIME**, версия R-GFX5-1. R-GFX4 принят пользователем; новые режимы в игре ещё не подтверждены. Игра агентом не запускалась, DLL не развёрнута.

Кандидат: `D:\Game\Master Rallye\master-rallye-re-general\modernization\renderer\.build-msvc\Release\d3d8.dll`; hash/size в [validation](validation.md) и [build.json](../../data/build.json). Используйте тестовую копию с pristine MRallye.exe SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. Сохраните рабочие DLL/INI. Сторонний patcher/script не запускайте: пропатченный EXE отключит exact-build функции.

INI рядом с DLL: MRRRenderer.ini. Настройки читаются один раз; после каждого изменения перезапуск. Начните с [example](../../MRRRenderer.ini.example), затем меняйте параметры текущего этапа. [stock-plus.ini](stock-plus.ini) — финальный opt-in профиль. Одинаковые трек/машина/камера, VehicleReflections.Mode=Stock для основных сравнений.

| Этап | Действия | PASS / FAIL, F10 |
|---|---|---|
| A Stock | DisplayStock,UIStock,AAStock,freezefalse; для чистого контроля AF/FOV выключены | Меню/preview/гонка/HUD/выход нормальны. `A-stock`. Если база не работает, дальнейшие сравнения не засчитываются. |
| B Borderless | ModeBorderless,Width=Height=0; остальное какA | Нет рамок, полный выбранный монитор. На1920x1080 client/backbuffer/полный viewport именно1920x1080, не1920x1027. `B-borderless`. Увеличенная640x480 картинка/несовпадение GetDesc — FAIL. |
| C UI | Отдельные запуски Centered4x3 и PreserveMargins | Проверить главные/подменю, preview, loading, HUD, текст/иконки/шкалы/края. Centered сохраняет формы/центр; Margins корректно прижимает известные элементы. `C-centered-menu/race`, `C-margins-menu/race`. Обрезание/сдвиг текста, restore_failures/overflow — FAIL конкретного режима. |
| D AF | Borderless+выбранныйUI,AFtrue,Max16,AAStock | Косые текстуры чище какR-GFX3; MAG/MIP/stage1 Stock. `D-af`. |
| E MSAA | При одинаковых размерах сравнить AAStock и MSAA Samples4; AF/FOV неизменны | Реальные samples>0 и согласованные color/depth. Машина/колёса/столбы чище; world/HUD/menu без мусора. Unsupported Stock fallback допустим, но не «MSAA включён». `E-msaa`. Alpha-test листья могут остаться зубчатыми. При проблеме AAStock+перезапуск. |
| F Stock+ | Предложенный INI: Borderless,Centered4x3,AF16,MSAA4,VFOV80,shadowStock,reflectionStock,freezefalse | Камеры/backview/края, preview45 не меняется от GameplayFOV, геометрия не пропадает из-за frustum. Исходные цвета/свет/ассеты сохранены. `F-stockplus-race/preview`. |
| G Alt+Tab/Reset | Несколько сворачиваний/возвратов в меню и гонке | Нет crash/black frame/потери HUD; выбранные размеры/AA/UI сохраняются. Нужны actual successful Reset и следующий quality descriptor. Если Borderless не вызывает Reset, отметить «не наблюдался» либо использовать уже известный безопасный game Reset-путь. Alt+Tab сам по себе не доказывает Reset. |
| H Freeze отдельно | После здоровойA, одна воспроизводимая последовательность false/true с перезапуском | True-журнал: exact context/applied, EXE hash на диске прежний. Если исходный freeze не воспроизводится — эффективность не проверена. Не смешивать media/loading/Attract. |
| I High-res опция | Если доступно native2560x1440/3440x1440/3840x2160 или Windowed client-размер; сначала AAStock | Подтвердить GetDesc/viewport/UI, не спутать масштабирование с rasterization. Borderless всегда native monitor; arbitrary supersampling не реализован. DPI/другой монитор отдельно. |
| J Exclusive опция | Поддерживаемые Width/Height,RefreshRate0 либо известный режим; AA отдельно | Log WindowedFALSE/выбранный режим, task switch/восстановление. Отказ режима фиксировать как fallback. Разницу яркости записать, desktop gamma не править. |

Если используются split/multi-camera — отдельно полно/половины/четверти, HUD и PreserveMargins. Арифметика проверена, UI packet timing по камерам ещё нет. Миграция монитора и125/150% DPI — отдельные непроверенные случаи.

Прислать INI, session JSONL, выбранные F10 и краткий результат A..J (optional можно «не запускал»). Нужны версия/hash DLL/EXE, monitor_rect, physical_backbuffer/depth, effective viewport, requested/logical_baseline/effective PP, native failures, ui restore_failures/overflow. Raw captures не коммитить.

Закрытие требует подтверждённого изображения и стабильной работы. После результатов возможен узкий R-GFX5 follow-up; R-CAM1/F-PHOTO1 сейчас не начинать.
