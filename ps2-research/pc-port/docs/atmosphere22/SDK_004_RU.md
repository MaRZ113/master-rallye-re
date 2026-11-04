# SDK 004

LightingMetadata и NormalHints необязательны для штатного native fallback.
Новый layout с изменением draw ranges/UV/порядка индексов не требует SHA мешей
или новой DLL. Для нового материала/новой трассы запустить export_lighting.py
по read-only Course tree; exporter узнаёт noise ground, vegetation, известные
static и теперь геометрические ground/вертикальные панели. Неоднозначные
материалы можно явно типизировать внешним roles JSON. shader/alpha/runtime
проверки при этом не обходятся. roles=exclude всегда приоритетнее геометрии.

Пример (новые пустые output directories):
```
python sdk/export_lighting.py --source E:/PrivateCourse --course MyCourse --output E:/MyLighting
python sdk/atmosphere_normal_hints.py --source E:/PrivateCourse --course MyCourse --materials E:/MyLighting/materials.lsm --output E:/MyNormals
python sdk/atmosphere_body_metadata.py --selection sdk/body-selection.json --assets E:/PrivatePS2Vehicles --output E:/MyBody
```

Для объединённого stock/custom metadata повторять --source и --course. Либо
использовать --base для materials; normal base уже содержит сглаженные hints,
поэтому полная регенерация предпочтительна после изменения smoothing policy.
Межматериальное сглаживание полного кластера: XYZ 1 мм, dot>.97; источник
нормалей не является authority допуска. Истинные острые грани не объединяются.

BLM2: family + native primary/secondary + typed paint/opaque_trim; PS2 texture
identity и подтверждённый fleet owner/pass. Не перечисляется geometry SHA.
Новые семейства требуют корректного native/уже поддержанного PS2 importer,
сам BLM2 не является importer. Лампы/колёса/стекло/sticker по-прежнему deny.
Tatalogo является именем исходной paint-панели, не отдельным sticker pass.

PrelightContrast: [0,1], default 1 (старый вид); sunset profiles .35. Уменьшение
снижает legacy baked directional contrast, не заменяет настоящие тени.
Кузовный stage2 использует WorldBrightness; scoped RGB exposure затрагивает
сумму diffuse/reflection допущенных paint/trim, сохраняя alpha и UV.
