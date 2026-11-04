# ATMOSPHERE2 — текущая граница доказательств

Статус: разработка, **RUNTIME_PARTIAL**, не candidate-verified. После повторного
прогона на PC-трассе world lighting подтверждён на France1; первоначальные отказы
вызваны PS2-версией course DX, отсутствовавшей в первом atlas.

Основной кандидат `candidate-runtime-001`, DLL
`77ca7db6e2f9527cdd1d3805432ea6696615494098c9f4b41cb90bef4cb8c9b6`:
24/24 baseline CTest, 46/46 PS2 CTest, 180/180 Python tests PASS.
Исходная часть BL1 selector/bridge/guards сохранена по SHA256.

## Первый прогон с PS2 course override и PC-only atlas

В сеансах 50056/14884/34196 Original/Deep Forest/Grand Valley на France1:

- Оба слоя каждого нового неба фактически допущены в D3D8. Источники — исходные
  GT3 Reverse course sky GTM1/Tex1, с проверенным VIF и texture binding.
  Это source-derived адаптация к геометрии неба MR, не заявление о parity GT3.
- Скриншоты подтверждают смену неба. GoldenHour света на трассе пока нет:
  почти все source-draw identities отклонены. Только маленький rock draw
  совпал после движения; road/vegetation/static не подтверждены.
- Fog в стартовых F10 остался исходным. Успешная загрузка atlas не означает
  допуск материала или изменение итогового света.
- Средняя измеренная стоимость Atmosphere begin по 120-frame windows:
  Original 0; Deep Forest около 0.746 мс/кадр; Grand Valley около 0.763 мс/кадр.
  Это QPC CPU hook time, не полный GPU/frame benchmark. Дорогой повторный
  анализ неизвестных draws предстоит оптимизировать после исправления identity.
- Restart/menu/re-entry пока не подтверждены: успешные sky events имеют только
  race generation 6. Turkey2/3, Reset/MSAA/FOV/FreeCam и PS2-on ещё не пройдены.

Это результаты первого прогона с подменённой трассой, а не итог повторного теста.
Точные сеансы, SHA и события: `candidate-runtime-001-analysis.json`.
Источник atlas и неба: отдельные provenance JSON в этой папке.

## Повторный прогон после временного удаления PS2 course override

Тот же DLL `77ca7db6...`, сеансы 52208 (Grand Valley), 30364 (Deep Forest),
28004 (Original). В обоих GoldenHour подтверждены изменения vertex colors
road/terrain/vegetation/static объектов. Для Grand Valley записаны два race
generation (6/10); конкретные Restart/menu этапы целиком ещё не сертифицированы.
В F10 каждого GoldenHour — 51 успешная scoped установка fog пресета и 51
возврат исходного `FF8E5B3D`. Original таких установок не содержит. Все три
F10 завершены без truncation/dropped records. CPU: около 1.677 / 1.954 мс/кадр
соответственно, Original 0; это измерение обработчика, не GPU benchmark.

Причина первого отказа проверена по данным: geometry SHA `4134a2ef...666a9c`
найден без перестановок и ослабления проверок в исходном PS2 override France1,
`course.batch.14.0`, bark. Этот исходный DX имеет SHA
`89b96c102c622065bf13bd3506cab55cfb6207d4768c447da76b726ecc5a76c7`,
в отличие от PC `a6bfcef9...caf07d5`.

Точные результаты: `candidate-runtime-001-pc-course-recheck.json`.
Новый объединённый atlas содержит 1558 записей PC и имеющихся PS2 override
France1/Turkey2/Turkey3. SHA `1c583e5c...b8b62ef0`, повторная генерация побайтно
совпала. Для отсутствующей loose-текстуры используется точная одноимённая
оригинальная PC-текстура из архива; live texture SHA всё равно обязателен.
Совпавшие geometry/material с разными нормалями запрещены при генерации.
Новые PS2 записи пока SOURCE/OFFLINE, не runtime admission.

Следующая сборка кеширует только результат CPU-расчёта света внутри конкретной
подтверждённой записи. На каждом draw сохраняются проверка актуальной геометрии,
texture identity, owner/lifecycle/render state и private upload. Другой порядок
индексов или настройки света пересчитывают кеш; непотреблённые вершины остаются
исходными. Это оптимизация с ещё не измеренным runtime выигрышем.

Отдельная резервная диагностика сохраняет существующий admission. Явный
`SceneDiagnostics=1` записывает максимум 16 образцов отклонённой геометрии на
race/reset epoch, по одному на texture SHA, не больше 512 triangles каждый.
Читаются только уже имеющиеся зеркала vertex/index buffers. Образец содержит
XYZ/prelight/UV0 для сравнения с оригинальным DX; он не разрешает изменения
неизвестного draw. Обычные профили диагностику не включают.

`tools/analyze_atmosphere_scene_samples.py` проверяет SHA/размер снимка, отдельно
сравнивает позиции, prelight, UV, состав треугольников и полный исходный record.
Так можно отличить перестановку/подмножество треугольников от изменения компонентов.
Проверка анализатора на исходном bark record с переставленным подмножеством
6 triangles прошла; это проверка инструмента, не доказательство поведения игры.

Прямой свет кузова ещё не реализован; отделяется от влияния окружения на
существующие отражения. SunDisk/Halo/Flare подавляются без current-frame occlusion.
Новые тени, ночь, фары и динамическое время суток не реализованы.

## Кандидат runtime-002

DLL `87d4faea7e019ecbb38160b98bc8eca55af621447614dc700b28e69cec65ec6c`,
combined atlas 1558 records. 24/24 baseline CTest, 46/46 PS2 CTest,
180/180 Python PASS; все 24 файла пакета проверены по SHA.
После замены старого atlas на новый runtime проверен на PS2 France1, renderer PS2-Off.
`candidate-runtime-002-validation.json` и `candidate-runtime-002-runtime.json` — точная граница.
Пакет `.research-output/atmosphere2/candidate-runtime-002`, отдельный RUN_TEST_RU.md.
Диагностический промежуточный DLL `7060404e...` пользователю не предлагался
и runtime-подтверждения не имеет. Следующий тест использует только runtime-002.

### Runtime-002: повторный прогон с правильным atlas

DLL `87d4faea...`, atlas `1c583e5c...`, PS2 France1 DX `89b96c10...`.
Сеансы 35932 / 4032 / 50504: Grand Valley / Deep Forest / Original.
В обоих GoldenHour допущены все четыре категории, с ненулевыми изменениями
vertex colors; оба sky-слоя применены. В каждом GoldenHour F10 — 40 установок
fog пресета и 40 успешных возвратов исходного значения; failed native writes 0.
Все три захвата complete, без truncation/dropped records.
CPU Atmosphere hook: Grand Valley 0.901 мс/кадр, Deep Forest 0.770; Original 0.
Это не прямой замер ускорения относительно прежней PC-геометрии.

Скриншоты просмотрены. Deep Forest снят с обрезкой до неба/холмов, поэтому
полный автомобильный A/B по этой паре не заявляется. Прямой свет кузова пока
выключен. Неизвестный материал `8131f9f4...` остаётся native по admission policy.

Старые сеансы 44024/10072 с тем же DLL имели atlas от runtime-001:
`scene_atlas_source_hash_mismatch`, допущенных world draws 0. Их низкие CPU
цифры НЕ результат работы кеша. Пользователь затем исправил установку.
Агент игровые файлы не менял: попытка замены остановлена проверкой до записи.

Во всех новых сеансах только race generation 6. Restart/menu/re-entry всё ещё
требуют отдельного подтверждения в одном процессе; точный короткий сценарий:
`.research-output/atmosphere2/runtime-002-checks/RUN_TEST_RU.md`.
Turkey, renderer PS2-on, Reset/MSAA/FOV/FreeCam, прямой свет кузова и sun occlusion
ещё не подтверждены. Статус RUNTIME_TESTED для указанной комбинации, не ACCEPTED
для всей ATMOSPHERE2; candidate-verified пока не создаётся.

## Runtime-002: lifecycle control passed

Session `session-20261103-095103-37844.jsonl`, same PID 37844:
race generations 6/10/15, owner lifetimes 1/2/3. Both sky layers and all four
course categories applied independently in each lifetime. This confirms the
requested cold/Restart/menu-re-entry path in live session evidence. Only two new
F10 files were actually saved, after transitions (frames 2588/3516), both complete,
zero dropped/truncated records, 40 fog sets + 40 restores. Cold F10 evidence is
from the prior run, with current-session cold admission logs also present.
Details: `candidate-runtime-002-lifecycle.json`.

The whole-session average includes menu/loading windows and is not a race-only
performance estimate. For windows with calls >= frames*100: median 0.828 ms/frame,
mean 0.970, range 0.755–1.806 (16 windows); the predicate is a heuristic.

## Candidate runtime-003: Turkey authoring coverage

Runtime-002 did not include Turkey road/terrain labels. Original source texture
pixels and DX bindings were reviewed; an explicit per-course authoring policy
now selects those source records. This is authored categorization, not recovered
original engine semantics. Live geometry/texture/owner/state proof is unchanged.
Water, boats, tyre-tread labels and reflective secondary materials stay excluded.
Evidence: `turkey-material-policy-review.json`.

Atlas 4142 records, SHA `78018804a8d522847020e651f498521b251ce0e13cc06bc0c88efdd6fe50bee0`.
All prior 1558 identities, categories and normals are retained; full reproduction
matches byte-for-byte. DLL `f0563ed1656fe864b6c3403e7c15dc3dc5341f6c7cabadeda092796b76a02d1a`.
24/24 baseline CTest, 46/46 PS2 CTest and 181/181 Python PASS; package 33 file
hashes verified. Runtime-003 still requires Turkey Original/GoldenHour and short
France1 regression. No current package is accepted for all ATMOSPHERE2 gates.

## Runtime-003: Turkey2 / Turkey3 tested

DLL f0563ed1..., sessions 31832 Original / 26276 Deep Forest / 31732 Grand Valley.
Both source sky layers admitted on both courses. Turkey2 categories 1/2/3/4;
Turkey3 categories 1/2/4. Turkey3 vegetation not observed and is not passed.
Six captures complete, no truncation/dropped records. GoldenHour fog writes and
restores: Turkey2 145/145, Turkey3 82/82, both presets. Original has no fog overrides.
CPU windows entirely inside each admitted race: Turkey2 mean about 2.55–2.57
ms/frame, Turkey3 about 1.16–1.17; these are hook QPC measurements, not GPU/FPS.
Whole-session averages include menu/loading and should not be used instead.
Visual comparisons show changed sky, terrain and distant fog. Direct body light
remains off; no claim of complete scene/art acceptance or PS2-on regression.
No France1 short capture was saved for runtime-003. Exact evidence:
`candidate-runtime-003-runtime.json`.

Turkey3 source mismatch narrowed: PC uses shrub/shrub1; loose PS2 DX uses
shrubtrig2 (11680 triangles). That exact label was missing in Turkey3 authoring.
Original loose texture BGRA SHA 25c49c9a2a10b3650b2c639a6f23f6aa77d164060be49472734d0454093424bb
was inspected; adding its exact category-3 source records does not relax admission.
Next atlas 4192 records, 50 added; all previous 4142 identities/normals/categories
retained and full atlas reproduced exactly. Runtime of added records is pending.
