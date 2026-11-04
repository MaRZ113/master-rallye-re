# ATMOSPHERE2.2 — состояние кандидата

Реализованы исходные пространственные normal hints и ограниченная F10 диагностика,
чистое переключение WorldLighting при том же sky/fog, менее контрастный GoldenHour,
внешние material capabilities для кузовов Patrol и Tata. Статус нового runtime:
**PENDING**. Нельзя считать этот кандидат художественно принятым до парных кадров.

## RUNTIME_TESTED: предыдущая DLL ATMOSPHERE2.1

DLL `40e630dbee5163fbeea89de626cdee4e8b9b35a30d3d36b6961bd6c1cdd00885`:
повторно прочитаны реальные PID 50280/42324/29412, шесть полных F10.
Original и GoldenHour France1/Turkey2/Turkey3, длительная France1; подтверждены
Universal Resolver и видимый вечерний мир. Скриншоты показывают резкие световые
границы и яркий Patrol. Это не подтверждение конкретной причины каждого стыка.
Ревью оценивает CPU median .349/.405 мс, P95 .529/.743; это hook QPC, не FPS.
`previous-runtime-evidence.json` содержит исходные SHA и события этих сеансов.

## Изменения нового кандидата

- **LNH1 необязателен и не допускает геометрию.** Исходные нормали Course SDK
  индексируются по course/material texture/координатам с шагом 1 мм. Совпадающие
  границы разных draw получают авторские нормали. Различные исходные кластеры
  настоящих острых граней сохраняются: выбор по facing agreement > .5, близкая
  неоднозначность сохраняет геометрическую нормаль. Изменение UV/prelight/order
  не меняет ключ. Новые/перемещённые вершины продолжают освещаться по геометрии;
  отсутствие или повреждение LNH1 не становится запретом материала. Нет SHA мешей.
  65 916 записей, 10 085 224 байта для PC+PS2 трёх трасс. Поиск и bake — при
  изменении содержимого диапазона, не каждый кадр. SDK exporter поставляется отдельно.
- Ограничение геометрического cache прежнее: 2048 ranges / 48 MiB; учитываются
  добавленные normals/used. Race/Reset очищает cache. LNH1 неизменяем в процессе.
- **SeamDebug:** Ctrl+Alt+L при фокусе игры переключает только world RGB;
  fog/admission/sky сохраняются. F10 пишет отдельные atmosphere22-*.jsonl (даже при заполненном лимите session log): samples XYZ, geometry /
  effective normal, winding, source prelight, effective ARGB, texture/material,
  range и generation. Для исключённых материалов только диагностически читается
  текущая геометрия: native range не становится освещённым. Выборка не полная.
- **GoldenHour:** cold ambient (.67,.74,.90) × .95, warm sun (1.25,.86,.45) × .58,
  WorldBrightness .68, Exposure 1. У полностью открытого белого prelight red gain
  теперь .433–.926 вместо примерно .272–1.520. Направление солнца, исходная alpha,
  baked visibility и fog сохраняются. Это настройка кандидата, не новое доказательство
  финального художественного качества. GT3 sky assets побайтно прежние.
- **BLM1:** 12 source material capabilities для Patrol/Tata, обновляемых без DLL.
  PC route доказывает actual owner/tree/resource `vehicles/<family>/car`, material
  binding, texture/generation, VB/IB descriptor/current mirrors, opaque native
  normal-bearing pass и world transform. Освещение — private VB, восстановление
  до reflection cleanup. PS2 route встроен после existing complete fleet certificate,
  reflection capture, damage transfer и финальной проверки owner. Только mode3
  с подтверждённой primary texture capability. mode3 сам по себе не даёт допуска.
  Применяется к transient CPU copy для существующего DrawPrimitiveUP.
- PS2 VehicleLighting=1 сохраняется; его model-space normal-Y term заменяется
  в transient copy нейтральной базой .4 и world-normal GoldenHour один раз.
  Исходный prepared buffer не меняется. Reflection ADD/map/UV не модифицируются.
  PC сохраняет исходный prelight. Отдельные glass/wheel/rubber/light/glow/logo/
  sticker/driver passes исключены; текстуры и alpha не редактируются.
  Фактический PC/PS2 admission и damage после этих изменений пока PENDING.
- Body CPU учитывается отдельно от world/sky QPC; cache counters cumulative.

## Офлайн-доказательства и границы

`offline-seam-evidence.json`: на исходных PC France1/Turkey2/Turkey3 найдены
5104/3310/7360 пар совпадающих координат разных draw с одинаковыми авторскими
нормалями, но dot локальных normals < .95; на PS2 — 1472/1123/2942 таких пар.
Это пары вершин, не число видимых швов. Подтверждена возможность артефакта от
изолированного восстановления; конкретный скриншот не атрибутирован офлайн.
Настоящие source UV/prelight/material/LOD seams этим не исправляются автоматически.

Сборка/CTest/Python и file manifest — в `build-report.json` и `manifest.json`.
Они не подтверждают визуальное исправление, FPS, PS2-on, Reset или две машины в игре.
Реальные 65 916 LNH1 и 12 BLM1 записей также прочитаны отдельным x86
пробником через тот же C++ parser: PASS, около 95 мс на однократное холодное
чтение/построение обеих таблиц. Это не CPU/кадр и не игровой тест.
LNH1 base round-trip побайтно идентичен; максимум 10 кластеров на spatial key
при runtime лимите 16. Принятая DLL не перезаписывается; rollback ATM2.1 поставляется целиком.

## Sun FX: выключен

Пункт P2 отложен до runtime стабилизации мира и двух кузовов. В существующем
per-draw hook нет подтверждённой точки «world depth завершён, HUD ещё не нарисован»
для независимого sun draw; наличие depth surface не доказывает visibility.
Depth-tested disk потенциально возможен без CPU readback, однако его место в
кадре, прозрачные/alpha-tested препятствия, reflection capture и окклюзия
скала/дерево/тоннель здесь ещё не проверены. Именно это недоказанное сочетание
является блокером; не заявляется невозможность D3D8 occlusion вообще.
Disk/halo/flare не рисуются, даже если Sun-Debug запросил disk/halo.

## PENDING

Парные точки seams с тем же sky/fog; заметность/целостность минимум двух кузовов
в PC и PS2-on; France1/Turkey2/Turkey3 Baseline и PS2-on, edited layout;
Restart/Re-entry/Reset, HUD/FreeCam/water/physics/Collision Debug, standalone
без Extra Options; QPC обеих частей и отдельный FPS/frametime. Полная задача 2.2
не объявляется завершённой до этих наблюдений.
