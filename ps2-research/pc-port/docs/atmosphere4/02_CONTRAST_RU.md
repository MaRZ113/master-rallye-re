# Контраст и диапазон света

IMPLEMENTED / OFFLINE_VALIDATED; RUNTIME_TESTED=false. `SurfaceTone=1`, `ToneContrast=1.08` (0.5–1.5), `ToneShoulder=1` (0–3) вводят мягкую кривую ЭНЕРГИИ освещения основных scene surfaces. Кривая зависит от ambient/sun/нормали, не от исходного vertex RGB: одинаковые normals получают одинаковый gain, материал/текстурная компенсация по обе стороны стыка сохраняется. Есть тест пропорции prelight 2:1. Нельзя нелинейно тонировать vertex RGB до текстуры — это вновь создало бы швы.

Это LDR response curve, не HDR framebuffer и не глобальный tone mapper. Холодный ambient и тёплый SunDir остаются раздельными. Alpha и чёрная окклюзия сохраняются; environment factor не получает вторую tone-кривую. Автомобили сохраняют Natural Lighting, без повторного body/environment exposure.

Профиль Contrast-Only уменьшает FogStrength до .45 и выбирает менее яркий FogColor=0x766654; это регулирует цвет fog, а не переписывает native fog distance/range. Горизонт не отключается. SurfaceTone=0 и прежние FogStrength/FogColor возвращают старый вид. Все значения LiveTuning. Региональный каталог намеренно выключен в этих A/B-профилях, чтобы регион не заменял FogStrength.

GT3 screenshots рассматриваются как художественный ориентир: тёмные читаемые окружения, сохранённый цвет автомобиля, локальные светлые блики. Технология реального GT3 не реконструирована и визуальное совпадение не заявляется. Риски: native prelight разных ассетов, quantization и насыщенные текстуры требуют сравнения в игре; не корректировались индивидуальными SHA.
