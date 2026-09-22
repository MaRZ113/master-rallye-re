# Legacy material hypotheses

These names describe legacy Blender preview heuristics, not proven DirectX
runtime semantics. None is promoted into binary-format truth.

| Legacy preset | Inputs used by legacy code | Modern support | Status |
|---|---|---|---|
| `paint` | texmode 6/7, helper names `whitepaint`/`silverpaint`, body/shell names | ordered helper slots and TXT names are preserved | **LEGACY_HEURISTIC**, runtime semantics unverified |
| `decal_on_base` | decal-like primary name, paint-like helper slot, texture white/background ratio | multi-slot tuple is real; blend equation is unknown | **SUPPORTED_BY_TEXTURE_DATA**, **UNVERIFIED_RUNTIME_SEMANTICS** |
| `glass` | TXT `UsesAlpha`, glass/windscreen names, glass helper slot | alpha bytes and `UsesAlpha` are preserved | **SUPPORTED_BY_SIDECAR**, blend/test mode unknown |
| `perspex` | perspex material/helper names, sometimes alpha | naming and slots are preserved | **LEGACY_HEURISTIC**, runtime semantics unverified |
| `chrome` | chrome/rim names or helper texture | chrome-named resources exist | **LEGACY_HEURISTIC**, reflection/environment behavior unknown |
| `rubber` | rubber/tread/tyre/black names | wheel/tread naming supports preview classification | **LEGACY_HEURISTIC** |
| `plastic` | bumper/mirror/grille/interior/character names | name evidence only | **LEGACY_HEURISTIC** |
| `glow` | `UsesAlpha` plus glow/brake-light naming | alpha and names support a luminous preview guess | **SUPPORTED_BY_SIDECAR**, exact emission/blend unknown |
| `light` | perspex/light naming without the legacy alpha condition | name/slot evidence only | **LEGACY_HEURISTIC** |
| `generic` | fallback | no semantic claim | **HISTORICAL_ONLY** |

R2.5 preserves TXT `HasAlpha`, `UsesAlpha`, and `IsNoise` independently.
Across vehicle TXT sidecars, 3,536 texture entries were parsed: 3,155
`No/No/No`, 8 `No/Yes/No`, 96 `Yes/No/No`, and 277 `Yes/Yes/No`.
The eight `HasAlpha=No, UsesAlpha=Yes` entries independently prove that the
two flags must not be collapsed. No vehicle entry sets `IsNoise=Yes`, but the
field remains representable and is not defaulted to false when absent.
