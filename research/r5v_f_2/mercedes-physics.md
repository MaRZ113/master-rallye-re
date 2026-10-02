# Retail Mercedes physics audit

The actual retail `Data.sma_unpacked/DataGame/vehicles.xml` was re-read and validated against the current reader-aware vehicle schema. Its SHA-256 is `a6762bb20999c7224c71b9f5d1d7edca55bcea147ff9f973300a8cf8d350aee0` (757,388 bytes).

| Property | Result |
|---|---|
| Family | `Vehicles/Mercedes` |
| Parsed values | 144 |
| Schema class | `COMPATIBLE` |
| Required/missing fields | 120/120 fixed fields present; no missing paths |
| Unexpected paths / type mismatches / count errors | None |
| Group counts | Chassis 16; DamageParams 25; Dimensions 8; Engine 42; Steering 5; Suspension 48 |
| Gear count / torque entries | 6 / 6 |

The September demo's Mercedes physics section has 121 values; November has 147, including a later/different schema shape. The ID26 target must use the retail `Mercedes` family, not copy a demo config or infer settings from its model. The semantic validator establishes static schema compatibility only. It does not establish runtime loading or correct instance-to-family binding; that remains part of a future P1 test after P0 and conversion pass.
