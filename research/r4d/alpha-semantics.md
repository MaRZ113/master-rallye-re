# R4D alpha evidence

Counts are uniquely matched sidecar texture entries per draw, including repeated car/complete bindings.
Actual alpha means at least one DXT pixel with alpha below 255. This is CONFIRMED_BY_CORPUS, not a render-state claim.

| HasAlpha | UsesAlpha | DXT alpha below 255 | Bindings |
|---|---|---|---:|
| No | No | No | 2114 |
| Yes | Yes | Yes | 223 |
| Yes | No | Yes | 48 |
| Yes | No | No | 6 |
| No | Yes | No | 4 |

HasAlpha and UsesAlpha differ in real bindings. Opaque DXT can have UsesAlpha=Yes; alpha-bearing DXT can have UsesAlpha=No.
The executable has separate alpha and alpha-test shader names, but mapping either TXT flag to them remains UNKNOWN.
Alpha present, alpha test, and alpha blend must remain distinct.
