# Buggy audio oracles

Retail registry and audio constructor mapping:

| Vehicle | ID | Class/local | Sample | Sample-object `+0x1C` | Tuning-object `+0x14` | Curves |
|---|---:|---|---|---|---|:---:|
| Simmbugghini | 15 | T3 / 1 | `vehicles/engine9` | `3fbae148` | `3f87ae14` | A |
| Mattserati | 19 | T3 / 5 | `vehicles/engine9` | `3fc7ae14` | `3f8147ae` | A |

The human reports both are noticeably bass-heavy. Static evidence explains a
shared sample family and shared curve-table pair, but their raw scalar settings
differ. They are therefore **not one byte-identical tuned profile**. The
audible contribution of the shared `engine9` sample versus the differing
scalars has not been isolated by an A/B runtime test.

Candidate B uses ID19/Mattserati. Candidate A uses ordinary ID0. The two G.2
executables differ only in the one immediate byte encoding their donor IDs;
the candidate builder verifies this relation. No sound asset is added or
modified.
