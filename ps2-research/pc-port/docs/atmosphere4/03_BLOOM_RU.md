# Surface bright-pass bloom

BLOCKED для runtime. Реализован только воспроизводимый CPU reference threshold/5-tap blur на синтетической LDR сцене; `analysis/bloom.json`, `bloom-reference.png`. Это не подключённая игровая функция. SunBloomIntensity в старом SunFX — солнечный sprite, не surface bloom.

F10 содержит 566 alpha-blended draw contracts, большинство ZWrite=0, до финального HUD. Доступный backbuffer уже смешивает мир с водой, стеклом и special transparent passes. Простая обработка перед HUD защитила бы HUD, но распространилась бы на эти материалы. Нет доказанного opaque-only color attachment и надёжной per-pixel exclusion mask. Наличие PS 1.4 на локальном D3D8 HAL не решает изоляцию проходов.

Для продолжения нужен отдельный opaque color/mask capture с корректным порядком composition и восстановлением depth/RT при MSAA/Reset. Условный бюджет двух quarter-resolution X8R8G8B8 buffers при 1920×1080 — 1,036,800 байт без дополнительных resolve/mask targets. Сейчас они НЕ выделяются. CPU reference время не является GPU-временем или прогнозом FPS.

Фиктивный включаемый параметр Bloom не добавлен. Работающий SunFX не переписан, прозрачные проходы сохранены. Это конкретный технический блокер этапа, а не заявленная завершённая реализация bloom.
