# XML parameter contract

Configuration `1a7dc8` wraps the owner node with `1e2460`. Typed readers walk
child Values in source order and return on the first correctly typed matching
name. They use interned literal IDs; `3fa760` compares original string bytes.
Successful typed parsing followed by name comparison can temporarily write
other Values, but an exhausted lookup explicitly writes zero. **Constructor
defaults do not survive a missing property when this config method runs.**

| Serialized name | Type / reader | Field | Constructor default | Missing after config | Consumer |
|---|---|---|---|---|---|
| MarkerList Name | String / `1e28f8` | +0c | `SplineList` | ID 0 | Named lookup in prep |
| Use Const Speed | Bool / `1e2470` | +1c | True | False | Chord-time vs equal-knot-time branch |
| Use Closed Loop | Bool / `1e2470` | +28 | True | False | Control wrapping, closing-time preparation, advancement |
| Use Trigger System | Bool / `1e2470` | +2c | True | False | Init inactive and per-tick hysteresis |
| Max Speed/Const Speed | Float / `1e2510` | +38 | 15 | 0 | Route clock and bank speed ratio |
| Trigger Dist On | Float / `1e2510` | +40 | 200 | 0 | Squared activation radius |
| Trigger Dist Off | Float / `1e2510` | +44 | 600 | 0 | Squared deactivation radius |
| Use Rest On NonLoop | Bool / `1e2470` | +30 | False | False | Only open endpoint branch |
| Rest Time (sec) | Int / `1e25b0` | +58 | 360 **invocations if config never runs** | 0 | After config, signed low32 product of supplied integer and 30 |
| Banking | Float / `1e2510` | +50 | 0 | 0 | Up-row rotation and moving average |
| Number Of Samples | Int / `1e25b0` | +120 | 30 | 0 | Bank buffer allocation, divisor and ring modulo |

Typed decoders are `1e0368` (Bool literal comparison), `1e04d8` (Float sscanf),
`1e0630` (Int sscanf), and the String reader's `1e0bf8`. Property and marker
metadata preserve type, lexical value, duplicates and order. All eleven
controls are present with expected types in the 24 canonical selected owners.

No config range clamp was found for speed, radii, bank amount or sample count.
Config applies abs to internal +48/+4c, which XML does **not** expose here.
Prep checks speed against 0.0001, but some divisions/reads precede that check;
it is not a safe general validation API. Samples=0 reaches a divide/modulo
trap in the active tick even with Banking=0. Negative counts and malformed
numeric conversions are not silently repaired by the diagnostic.

Diagnostic guards are deliberately stricter than the executable: finite
float32 inputs, speed >0.0001, samples 1..100000, nondegenerate four-point
routes. These guards are tool policy, not invented game clamps. Missing string
ID 0 is not guessed to mean an empty route or a named default list.

Evidence: parameter names/types and canonical values `CONFIRMED_BY_BYTES`;
reader/field/consumer mapping `CONFIRMED_BY_EXE`; their connection
`CONFIRMED_BY_BOTH`. Actual successful load/motion `UNKNOWN` without runtime.
