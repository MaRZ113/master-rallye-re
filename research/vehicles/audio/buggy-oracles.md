# Buggy audio oracles

Retail registry and audio constructor mapping:

| Vehicle | ID | Class/local | Sample | Sample-object `+0x1C` | Tuning-object `+0x14` | Curves |
|---|---:|---|---|---|---|:---:|
| Simmbugghini | 15 | T3 / 1 | `vehicles/engine9` | `3fbae148` | `3f87ae14` | A |
| Mattserati | 19 | T3 / 5 | `vehicles/engine9` | `3fc7ae14` | `3f8147ae` | A |

Earlier listening notes describe both as bass-heavy. The G.2 A/B now directly
confirms that ID19/Mattserati sounds clearly bass-heavy on physical Mercedes
ID26. Static evidence explains a shared sample family and curve-table pair,
but the raw scalar settings differ, so they are **not one byte-identical tuned
profile**. The separate audible contributions of the shared `engine9` sample
and differing scalars have not been isolated.

Candidate B used ID19/Mattserati; canonical Candidate A uses ordinary ID0.
Their exact executable outputs differ at only the byte encoding the selected
profile immediate. The generalized builder verifies this relation. No sound
asset is added or modified.

ID19's bass-heavy character is `HUMAN_RUNTIME_CONFIRMED`; it does not establish
that ID15 has an identical complete profile or sound.
