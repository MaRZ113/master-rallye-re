# Аудит фактической готовности

Проверка локальных данных, без архива и без запуска игры. Ветка `perf/ps2-fps1`, HEAD `2875eb854405f6707e6cfb368cd7a3eb2f63398c`. Накопленные исходники 2.6–2.9 не закоммичены. До начала ATMOSPHERE4 они совпадали с source SHA build-report 2.9. Комплекты 2.6–2.9 прошли повторную проверку всех manifest hashes, без расхождений. Это не новые принятые релизы.

Обозначения: IMPLEMENTED — код и runtime-вызов присутствуют; OFFLINE_VALIDATED — доступные автоматические проверки пройдены; RUNTIME_TESTED — есть соответствующий игровой сеанс; ACCEPTED — пользователь явно принял; BLOCKED — конкретная незакрытая зависимость. Эти состояния не взаимозаменяемы.

| Фаза / функция | Исходники и подключение | Проверки | Игровое состояние / ограничение |
|---|---|---|---|
| BL1 / первый sky cold start | IMPLEMENTED, нативный null→false, source guard | Сохранённые контракты и текущие CTest | Исторические прогоны владельца; новая DLL не проверена |
| 2.1 Universal Scene Resolver | IMPLEMENTED, provenance VB/IB, roles/render-state admission, generation cache | Текущие resolver/geometry/contracts | Принят как рабочая архитектура владельцем; это не подтверждение всех материалов |
| 2.2 seams/body | IMPLEMENTED, shared material contracts, normals/prelight, private copies | CTest/Python, метаданные | Исторические игровые проверки с известными остатками; не все старые кандидаты приняты |
| Natural Lighting / 2.3 | IMPLEMENTED, diffuse-only exposure, native highlights | Текущие body/exposure tests | candidate-007 принят владельцем как основа; новый rim ещё не проверен |
| 2.4 SunFX/PC water | IMPLEMENTED, depth mask, guarded water path | Source + contracts; вода не переписывалась в 4 | Владелец подтвердил солнце за горой на 001; не переносить это на новую DLL |
| 2.5 composite005 | IMPLEMENTED; DLL a52d755a… | Последний локальный сеанс 47920 соответствует DLL | ACCEPTED владельцем как исходная основа; не полный fleet acceptance |
| 2.6 factory/seams/fog | IMPLEMENTED | OFFLINE_VALIDATED; manifest цел | DLL 6209e7f9… установлена, но matching session не найден; RUNTIME_TESTED=false, ACCEPTED=false |
| 2.7 batch metadata / captures | IMPLEMENTED: 41 каталога → 59 SceneID packages; custom layout alias | OFFLINE_VALIDATED: SDK/export/install/native parsing | Нет соответствующего игрового сеанса; автопара world/native — не новый игровой результат |
| 2.8 regions | IMPLEMENTED: base→region→course, 4 региона/58 сцен | OFFLINE_VALIDATED: parser/catalog/profile checks | Нет соответствующего игрового сеанса; process-immutable catalog требует restart при смене каталога |
| 2.9 fleet materials | IMPLEMENTED: BLM3, car/wheel/texture pair roles | OFFLINE_VALIDATED: 1060 контрактов, 461 PS2 identity, 108 источников | Не полный игровой fleet acceptance; extras и 50 неqualified источников остаются вне допуска |
| 3.0 lamps/glow rollout | NOT_IMPLEMENTED как новая фаза | Нет комплекта/источников завершённой фазы | Существующий BrakeGlow не доказывает новый generic lamp-state rollout; BLOCKED missing phase delivery |
| 3.1 final art calibration | NOT_IMPLEMENTED как завершённая фаза | LiveTuning существует раньше и сохранён | Финальная игровая калибровка/приёмка BLOCKED: владелец не может запускать игру |
| 4 текущий кандидат | Частичная реализация семи направлений, см. семь отчётов | Сборка/CTest/Python + isolated D3D8 fixture | RUNTIME_TESTED=false; ACCEPTED=false. Bloom и новые тени BLOCKED, не скрыты за фиктивными переключателями |

## Сохранность и риски

Universal Resolver, правила ролей и resource-generation cache не переписаны. Все runtime-данные пакета 2.9 сохраняются побайтно; новых пообъектных SHA нет. SDK остаётся инструментом авторинга, не runtime-зависимостью штатных трасс. Региональный каталог и пакетная загрузка сохранены. Для чистых A/B новых настроек используются Global-профили: региональное переопределение FogStrength иначе затрудняет сравнение.

BrakeGlow, отражения/их UV-ориентация, PS2 Water, физические объекты, FreeCam, Collision Debug и ABI независимого D3D8 Proxy не изменялись этим этапом. Совпадение хешей соответствующих исходников с 2.9 включено в validation.json; совместимость новой DLL подтверждена тестами, не игрой. В текущем INI владельца Reflection=0 и Water=0: нельзя объявлять этот запуск проверкой Reflection=4/PS2 Water. Для будущего теста есть отдельный PS2 compatibility INI. В ConfigVersion=3 Reflection=1 означает исторический Reflection=4, VehicleLighting=1 сохранён.

SunTransaction восстанавливает затронутые states и COM references. Failed restore оставляет pending и блокирует forwarding до repair. Новые sky states используют тот же pending/repair контракт. Добавлены fault-injection тесты и исправлен реальный пропуск UnlockRect на невалидном pitch/null bits внешнего sun sprite. Reset освобождает default-pool ресурсы после repair. LiveTuning сбрасывает lighting/environment caches и отменяет незавершённую A/B-пару.

Тесты не доказывают отсутствие всех memory leaks или конфликтов на каждом драйвере. Изолированный D3D8 тест проверяет точное восстановление доступных states, render target и 200 повторений виньетки. Полный Reset/Restart/Re-entry, утечки за длительную игровую сессию, FPS/GPU cost, переключение PC/PS2 и художественный результат остаются игровыми пунктами. Чужие dirty build-policy документы не включены в source archive и не изменялись этим этапом. Рабочая DLL и оригинальные ресурсы не заменялись.
