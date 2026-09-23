# R4D review of texFinder material heuristics

The recovered classifier remains LEGACY_HEURISTIC evidence. This table evaluates only its structural search value; no class has a validated complete runtime render equation.

| Legacy class | R4D status | Evidence and limit |
|---|---|---|
| paint | PARTIALLY_SUPPORTED | whitepaint-tga is slot 1 in 222 bindings across 26 families; tint/combine equation UNKNOWN. |
| decal_on_base | PARTIALLY_SUPPORTED | Ordered two-texture body/sticker tuples recur; no stage or blend proof. |
| glass | PARTIALLY_SUPPORTED | Glass-named slot pairs, alpha-bearing pixels, alpha-like draw flags, and executable alpha shader variants correlate; exact draw-state binding UNKNOWN. |
| perspex | UNVERIFIED | perspex-tga occurs in 221 slot-1 bindings; its role varies with first-slot texture. |
| chrome | PARTIALLY_SUPPORTED | chrome-tga occurs in 145 slot-1 bindings and executable env variants exist; direct binding UNKNOWN. |
| rubber | UNVERIFIED | rubber-tga occurs in 220 slot-1 bindings, mostly wheels/treads; operation UNKNOWN. |
| plastic | UNVERIFIED | Names alone; no distinctive proven shader path. |
| glow | PARTIALLY_SUPPORTED | Brake-glow family has a distinctive alpha/control signature, but additive/emissive behavior is UNKNOWN. |
| light | UNVERIFIED | Light-named textures occupy several distinct signatures; no one renderer class is established. |
| generic | UNVERIFIED | Fallback label without material semantics. |

No old heuristic is marked CORRECTLY_SUPPORTED for exact runtime behavior. The old tool was useful in naming candidate families; its distinctions between glass and glow roughly match corpus flag families but require runtime or executable confirmation.
