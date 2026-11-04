# VEHICLE-UNIFY1 — уборка Kia / X-Trail-специфики в общий fleet-путь

Kia Sportage и X-Trail были пилотами до fleet-порта: под них написаны свои модули, классы, ресурсы и ключи.
Сейчас обе машины есть во всех общих реестрах (race/frontend fleet, колёса port3, damage, ON/OFF-фонари, glow),
но рантайм местами явно отправляет их в старые пути. Этот документ — инвентаризация и порядок уборки.

## Шаг 1 (сделан): переименования и владение без изменения картинки

| Было | Стало | Почему |
|---|---|---|
| `PS2KiaBrakeOn.gxi`, ключ `KiaBrakeOnAsset` | `PS2BrakeOn.gxi`, ключ `BrakeOnAsset` (по умолчанию `PS2Vehicles\PS2BrakeOn.gxi`); старые ключ и файл читаются вторыми | BREAKLIGHTSON на PS2 один и тот же у всех 25 машин (SHA-256 fd4c121f…, `vehicle-fleet-port3/lamps/findings.md`); fleet ON_CORE уже накладывал «Kia»-текстуру на все машины |
| `BrakeGlow::kia_on_texture()`, `initialize_kia_on`, `GlassTransaction::kia_lamp_on_pass` | `brake_on_texture()`, `initialize_brake_on`, `LampTransaction::brake_on_pass` | то же |
| `GlassTransaction`, `kGlassOps` в `xtrail_glass.hpp/.cpp` | `LampTransaction`, `kLampOps` в `lamp_transaction.hpp` | транзакция общая для фонарей всех машин и стекла X-Trail |
| `xtrail_fidelity_opt_in` | `feature_opt_in` (`lamp_transaction.hpp`) | общий двухключевой opt-in (BrakeGlow, XtrailGlass, XtrailFidelity) |
| `BrakeGlow` — член `XtrailFidelity` (`e->xtrail()->brake()`) | член расширения: `PS2PortExtension::brake_glow()` | стоп-сигналы всего флота не зависят от X-Trail-пилота |
| откат транзакции фонарей внутри `xtrailintegration::repair` | `lampintegration::repair` (`lamp_integration.hpp`), отдельные хуки в патче 0001 (repair_reflection, reset_begin, reset) | то же; catch-ветки `brake_glow_native` / `fleet_lamp_native` теперь откатывают именно фонари |
| `xtrailintegration::Result` / `notify` (64 места в 13 файлах: вода, GroundDetail, HUD, колёса, кузов, меню) | `dipintegration::Result` / `notify` (`dip_integration.hpp`); в `xtrailintegration` оставлены `using` | это общие утилиты цепочки DIP, а не X-Trail |

Установленная игра продолжает работать без переименования файла: `PS2Vehicles\PS2KiaBrakeOn.gxi` подхватывается
как запасной источник. Новые комплекты могут класть `PS2BrakeOn.gxi` (те же байты).

## Шаг 2 (нужен A/B в игре): удаление дублей

Рантайм-исключения, из-за которых живут старые пути:

| Где | Исключение | Чем заменяется | Что удаляется |
|---|---|---|---|
| `fleet_lamp_native.hpp:18` | `KiaSportage` → «runtime-proven Kia route» | общий ON/glow/OFF fleet (профили Kia есть в `fleet_on/off/brake_glow` реестрах) | Kia-ветка `brake_glow_native.hpp` (`kia_gate`, `kia_candidate`, `kia_context`), `KiaLampContinuity`, `kia_lamp_continuity.hpp` (общий `NativeLampContinuity` остаётся) |
| `fleet_wheel_native.hpp:15` | `KIASPORTAGE`, `XTRAIL`, `UFO` | `kPort3KiaSportageWheelProfile`, `kPort3XtrailWheelProfile` (ресурсы `port3-*-WHEEL-FLEET.ps2model` уже установлены) | `kia_wheel_native/loader/registry/warmup.hpp`, `KIASPORTAGE-WHEEL-FLEET.ps2model`; X-Trail-ветка `wheel_model_native.hpp` + `XTRAIL-WHEEL-DRAW.ps2model` |
| `race_car_fleet_native.hpp:41/47/88/100` | `KIASPORTAGE` → `kia_damage` | `fleet_damage` (профиль KIASPORTAGE в `fleet_damage_registry.hpp` полный: 26 draw, candidates/mapping/static) | `kia_damage.hpp`, `kia_damage_registry.hpp` (122 КБ) |
| `race_car_fleet_native.hpp:11/74/81` | `XTRAIL` исключён из fleet-кузова | `XTRAIL-CAR-FLEET.ps2model` есть, **но профиль damage X-Trail пустой** (`fleet_damage_registry.hpp:131`) — сначала сгенерировать | X-Trail-ветка `race_model`, `race_damage_registry.hpp`, `vehicle_partition_registry.hpp` (только Xtrail), `XTRAIL-CAR.ps2model` |
| `frontend_model_native.hpp` (профиль `nullptr` = Xtrail) | меню по умолчанию — X-Trail-пилот | `XTRAIL-COMPLETE-FLEET.ps2model` | `xtrail_frontend_registry.hpp`, `XTRAIL-COMPLETE.ps2model` |
| `xtrailintegration::draw` (decal) | только при Reflection=4 | — | `xtrail_fidelity.*`, `xtrail_decal_registry.hpp` вместе с режимом 4 или перенос декали в fleet |
| `xtrail_glass*` | `XtrailGlassMode` по умолчанию 0, ни в одном конфиге не включён | — | 5 файлов + `XtrailHeadlight.ps2glass` в архив |

Порядок: Kia фонари → Kia колёса → Kia damage (каждое — свой A/B и коммит), затем X-Trail колёса,
X-Trail меню, генерация damage-профиля X-Trail и только потом X-Trail кузов. Glass/decal — в конце, вместе с решением по Reflection=4.

### Прогон A/B для каждого Kia-шага
Курс с прямой и торможением (например FranceS1), Kia Sportage игроком и одна Kia среди AI, `Diagnostics=1`
в RendererDiag.ini. A = DLL до шага, B = после. Сравнить: целая машина, после удара (private tree), меню/шоурум.
По логам — `ps2_brake_glow` / `kia_brake_continuity` / `fleet_lamp` и `fleet_wheel` / `fleet_car` без новых `fallback`.

## Ресурсы не на своих местах (отдельно, низкий приоритет)
`PS2BrakeGlow.gxi`, `PS2EnvSource64x64.gxi`, `PS2GroundNoise.gxi` лежат в `PS2Grass`, хотя к траве не относятся.
Перенос — так же через новый путь по умолчанию + старый запасной.
