# Candidate-runtime-004 — проверка исправлений

Закрыть игру. Сохранить текущий DLL/Atmosphere.ini. Скопировать ВСЁ содержимое
runtime-overlay в Atmo-copy: новая DLL и три metadata обязательны.
SHA DLL — manifest.json. Проверить:

```powershell
.\Verify-Installation.ps1 -GameRoot 'D:\Game\Master Rallye Atmo-copy'
```

Не менять трассы или PS2Vehicles. Сохранить PS2Port.ini с Reflection=4,
VehicleLighting=1 и принятой ориентацией. Каталог loose PS2 трасс DataGx/Course.
Новая DLL не устанавливается автоматически. Откат полным rollback-runtime-003.

## Короткий контроль — PS2 трассы, PS2 renderer ON

profiles/Surfaces-Debug.ini скопировать как Atmosphere.ini. Новый процесс:

1. France1/Patrol: F10 + снимок стыка крыла/капота и баннеров/чекпоинта.
   Ctrl+Alt+L → F10 + снимок с той же камерой → вернуть Ctrl+Alt+L.
   Этот переключатель меняет ТОЛЬКО мир; кузов, sky и fog не переключаются.
2. Restart → F10. Меню → Tata/France1: F10 + снимок сверху (крыша tatalogo).
3. Меню → Turkey2: F10 + снимок basegrass и баннеров.
4. Меню → Turkey3: F10 + снимок тех же заметных полос/стыков →
   Ctrl+Alt+L/F10/снимок без движения → вернуть свет. Закрыть игру.

Написать «Сделал» с вердиктом по кузову/траве/стыкам. Указать, если отличается
каталог логов. Установку stage2 подтверждает atmosphere_body_exposure в логе;
запрос body lighting сам по себе её не подтверждает. Новые CPU окна сравню
отдельно от визуального результата. F10-кадры не использовать для FPS.

## Baseline и Original

Для PC трасс восстановить сохранённый PC Course штатным способом; не смешивать
исходники. PS2-off renderer профиль — из предыдущей согласованной конфигурации.
Повторить кратко 1/3/4 с Original.ini, затем Surfaces-Debug.ini в новых процессах.
Для FPS отдельно без F10 и debug: GoldenHour.ini, одинаковый маршрут/камера.
Не менять Reflection=4/VehicleLighting=1 для PS2-on сравнения.

Колёса/шины/стёкла/лампы намеренно native. Sun остаётся OFF. Исходные texture/UV
стыки могут быть видны и при WorldLighting off; их отдельно сравню с новыми.
