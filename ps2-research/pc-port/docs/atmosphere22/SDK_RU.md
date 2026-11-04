# Метаданные ATMOSPHERE2.2

Runtime не требует Python, Course SDK или Blender. Он использует native
owner/material/buffer proofs. Метаданные — отдельные файлы рядом с DLL.

Для нового Course SDK layout сначала выполнить обычный `sdk/export_lighting.py`
с `--base` существующего materials.lsm (см. sdk/README_RU.md). LSM1 — допуск
материалов; разрешённый материал не требует SHA каждого его объекта.

При наличии исходных авторских нормалей можно дополнительно выполнить:

```
python -B sdk/atmosphere_normal_hints.py --source E:/MyCourses --course MyLayout --materials E:/MyLighting/materials.lsm --base runtime-overlay/Atmosphere22/normals.lnh --output E:/MyNormals
```

`--base` сохраняет подсказки штатных трасс без их исходников/SDK-экспорта.
Заменяется normals.lnh, DLL не меняется. LNH1 — данные для shading, не admission.
Отсутствующие/перемещённые вершины используют геометрические нормали. Разбиение
draw, перестановки вершин/triangles и UV/prelight не требуют обновления LNH1,
пока позиции/авторское сглаживание прежние. При изменении формы экспортировать
актуальные hints; геометрический fallback не восстанавливает потерянное авторское
сглаживание через произвольные новые draw boundaries автоматически.

Для нового автомобиля `sdk/atmosphere_body_metadata.py` читает существующий
PS2MDL02 с его source material metadata. JSON `body-selection.json` содержит
family → список primary material names. Выбирать только подтверждённые чистые
paint-панели. Glass/wheel/light/logo/sticker и неподтверждённые secondary не
могут стать body capability через этот exporter.

```
python -B sdk/atmosphere_body_metadata.py --selection sdk/body-selection.json --assets E:/PrivatePS2Vehicles --output E:/MyBodyLighting
```

Добавление семейства/материала в JSON и замена body.blm не требуют новой DLL.
Сохраняйте в JSON уже поддержанные семейства для общего экспорта. Экспортёр
сверяет shader/texture bindings JSON с бинарными mesh rows и требует paint
secondary. Texture-scoped PS2 capability отключается при неоднозначной роли
тех же pixels; native route продолжает требовать exact primary/secondary.

BLM1 не даёт новому неподдержанному автомобилю PS2 geometry importer: работает
поверх уже существующей корректной PC-модели/PS2 fleet integration. Для SDK
PC-only автомобиля без PS2MDL02 потребуются подтверждённые source material
данные для авторинга BLM1; расширения Proxy для нового family не требуется.
Native runtime всегда проверяет resource/owner/tree/current descriptors/texture.
Перед заменой metadata полностью закрывать процесс. CRC/SHA служат проверкой
целостности файлов и материалов, а не реестром каждого меша.
