# Контакт и направленные тени

BLOCKED для нового runtime shadow path. Штатные тени сохранены. Проверены существующие `rigid_props.hpp::rigid_shadow_triangles`, Terrain/Pose/AABB и course-alive3 source evidence: PS2 drop-shadow 332628 / model 330780 / tag1400 receiver. Эти данные относятся к ограниченному props пути; прежнее предположение о тенях hay/tumbleweed было отозвано после наблюдения владельца.

Нет подтверждённого общего native car-caster ownership + существующей тени, которую можно безопасно заменить, и единого receiver contract для PC и PS2 loose/custom layouts. Terrain loader привязан к RigidProps, поэтому сделать его обязательным для освещения автомобиля нарушило бы независимость модулей. Подмена земной плоскостью проецировала бы тень поверх стен/разрывов/воды; это не улучшенный контакт.

Для реализации нужны: доказанный caster pose/hull в обоих race model путях, bounded receiver triangles/generation API вне RigidProps, согласованный Z-bias/alpha order, запрет water/vertical receiver и исключение двойной штатной тени. Для полноценных shadow maps дополнительно нужны переигрывание casters и depth sampling; они не подтверждены.

Новый фальшивый shadow overlay, источник независимый от SunDir и переключатель без реализации не добавлены. Existing native shadows/physics и кадр не меняются. Продолжение требует узкого receiver/caster capture, не обхода всех декоративных объектов.
