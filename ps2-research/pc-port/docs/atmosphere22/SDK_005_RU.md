# SDK 005

LSM1 и LNH1 не изменены по сравнению с 004. Перестановка/дробление draw ranges
не требует object SHA. Стабильные CPU geometry caches привязаны к поколениям
VB/IB/texture, actual consumed range и revisions. Новая нормализация пар
работает при cache miss/rebuild; дорогостоящих проходов по всей трассе/кадру нет.

BLM2 использует новые роли 3=opaque_panel, 4=opaque_cover, наряду с 1=paint,
2=opaque_trim. Старый parser fail-closed отвергает новые роли, нужна DLL 005.
SDK body-selection.json и atmosphere_body_metadata.py авторят роли без
пересборки Proxy. Все выбранные PS2 source mesh bindings сверяются с binary.
Панель: whitepaint/silverpaint/perspex, только непрозрачный mode3; sticker token
может быть явной opaque_panel ролью. Cover: perspex + wheelcover/wheelcoverside,
не wheel/tread/rubber. Glass/lamp/driver/glow нельзя переквалифицировать ролью.
В runtime остаются owner/material/world/current descriptors и alpha guards.

GoldenHour 005 сохраняет original vertex RGB: PrelightContrast=1 и
PrelightVisibility=0. Они нужны для сохранения texture/prelight компенсации
между материалами. Не копировать .35 из 004 в рабочий sunset профиль.
Контролируемый ambient/sun и WorldBrightness=.68 сохранены.

Экспорт: python sdk/atmosphere_body_metadata.py --selection sdk/body-selection.json
--assets E:/PrivatePS2Vehicles --output E:/NewBodyLighting (новый output folder).
Новые материалы/семейства подключаются через metadata; BLM2 не заменяет
vehicle importer и не доказывает игровую квалификацию автомобиля.
