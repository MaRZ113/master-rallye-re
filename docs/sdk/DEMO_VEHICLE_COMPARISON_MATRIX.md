# Complete Demo vehicle comparison matrix

Exact paths, resource hashes, decoded fingerprints, texture dimensions/alpha and comparison evidence are in private catalog.json. Native completeness does not imply playable integration. Source/GXM-only normalized comparisons are positional diagnostics; material/UV/hierarchy limitations remain explicit.

| Source / family | Source distinction | Input completeness | Native roles | Missing texture refs | Closest retail car (overlap / sampled RMS) | Accepted reference |
|---|---|---|---|---:|---|---|
| pcg-rebaked/Forester | NO_EXACT_RETAIL_SURFACE_MATCH | COMPLETE_NATIVE_INPUTS | car,complete,wheel | 0 | retail/ChevyBlazer / 0.0 / 0.134648 | accepted/Mercedes / 0.0 / 0.118751 |
| pcg-rebaked/Jump | PARTIAL_RETAIL_SURFACE_VARIANT | COMPLETE_NATIVE_INPUTS | car,complete,wheel | 0 | retail/Jump / 0.976605 / 0.005331 | accepted/PDSilver / 0.0 / 0.191215 |
| pcg-rebaked/LandCruiser | NO_EXACT_RETAIL_SURFACE_MATCH | COMPLETE_NATIVE_INPUTS | car,complete,wheel | 0 | retail/LandCruiser / 0.391304 / 0.054221 | accepted/HeritageTrooper / 0.0 / 0.122527 |
| pcg-rebaked/megane | PARTIAL_RETAIL_SURFACE_VARIANT | COMPLETE_NATIVE_INPUTS | car,complete,wheel | 0 | retail/megane / 0.504344 / 0.026493 | accepted/PDSilver / 0.0 / 0.178396 |
| pcg-rebaked/Mercedes | NO_EXACT_RETAIL_SURFACE_MATCH | COMPLETE_NATIVE_INPUTS | car,complete,wheel | 0 | retail/ChevyBlazer / 0.0 / 0.113184 | accepted/Mercedes / 1.0 / 0 |
| pcg-rebaked/Original/Forester | NO_EXACT_RETAIL_SURFACE_MATCH | COMPLETE_NATIVE_INPUTS | car,complete,wheel | 0 | retail/ChevyBlazer / 0.0 / 0.130188 | accepted/Mercedes / 0.0 / 0.121572 |
| pcg-rebaked/Original/Jump | PARTIAL_RETAIL_SURFACE_VARIANT | PARTIAL_OR_SOURCE_ONLY | car,wheel | 0 | retail/Jump / 0.976605 / 0.005331 | accepted/PDSilver / 0.0 / 0.191215 |
| pcg-rebaked/Original/KiaSportage | PARTIAL_RETAIL_SURFACE_VARIANT | COMPLETE_NATIVE_INPUTS | car,complete,wheel | 0 | retail/KiaSportage / 0.880758 / 3.2e-05 | accepted/Mercedes / 0.0 / 0.161751 |
| pcg-rebaked/Original/megane | PARTIAL_RETAIL_SURFACE_VARIANT | COMPLETE_NATIVE_INPUTS | car,complete,wheel | 0 | retail/megane / 0.504344 / 0.026493 | accepted/PDSilver / 0.0 / 0.178396 |
| pcg-rebaked/Original/Navara | NO_EXACT_RETAIL_SURFACE_MATCH | COMPLETE_NATIVE_INPUTS | car,complete,wheel | 0 | retail/Navara / 0.0 / 0.101387 | accepted/HeritageTrooper / 0.0 / 0.159022 |
| pcg-rebaked/Original/Simmbugghini | PARTIAL_RETAIL_SURFACE_VARIANT | NATIVE_TEXTURE_GAPS | car,complete,wheel | 1 | retail/Simmbugghini / 0.858782 / 0.016113 | accepted/PDSilver / 0.0 / 0.186251 |
| pcg-rebaked/Original/Trooper | NO_EXACT_RETAIL_SURFACE_MATCH | COMPLETE_NATIVE_INPUTS | car,complete,wheel | 0 | retail/LandCruiser / 0.0 / 0.113334 | accepted/HeritageTrooper / 0.954382 / 0.0 |
| pcg-rebaked/Original/Wildcat | PARTIAL_RETAIL_SURFACE_VARIANT | COMPLETE_NATIVE_INPUTS | car,complete,wheel | 0 | retail/WildCat / 0.96046 / 0.0 | accepted/PDSilver / 0.0 / 0.139301 |
| pcg-rebaked/Rav4 | NO_EXACT_RETAIL_SURFACE_MATCH | COMPLETE_NATIVE_INPUTS | car,complete,wheel | 0 | retail/Kangoo / 0.0 / 0.119896 | accepted/Mercedes / 0.0 / 0.133083 |
| pcg-rebaked/Trooper | NO_EXACT_RETAIL_SURFACE_MATCH | COMPLETE_NATIVE_INPUTS | car,complete,wheel | 0 | retail/LandCruiser / 0.0 / 0.113334 | accepted/HeritageTrooper / 0.954382 / 0.0 |
| pcg-rebaked/WildCat | NO_EXACT_RETAIL_SURFACE_MATCH | COMPLETE_NATIVE_INPUTS | car,complete,wheel | 0 | retail/WildCat / 0.0 / 0.106535 | accepted/Mercedes / 0.0 / 0.164798 |
| nov-local/Forester | NO_EXACT_RETAIL_SURFACE_MATCH | COMPLETE_NATIVE_INPUTS | car,complete,wheel | 0 | retail/ChevyBlazer / 0.0 / 0.134648 | accepted/Mercedes / 0.0 / 0.118751 |
| nov-local/ForesterAlpha | NO_EXACT_RETAIL_SURFACE_MATCH | PARTIAL_OR_SOURCE_ONLY |  | 0 | retail/Forester / 0.0 / 0.130775 | accepted/Mercedes / 0.0 / 0.121347 |
| nov-local/Jump | PARTIAL_RETAIL_SURFACE_VARIANT | COMPLETE_NATIVE_INPUTS | car,complete,wheel | 0 | retail/Jump / 0.976605 / 0.005331 | accepted/PDSilver / 0.0 / 0.191215 |
| nov-local/JumpAlpha | PARTIAL_RETAIL_SURFACE_VARIANT | PARTIAL_OR_SOURCE_ONLY | wheel | 0 | retail/Jump / 0.917301 / 0.005335 | accepted/MichelinRAV4 / 0.0 / 0.178778 |
| nov-local/NewRav | NO_EXACT_RETAIL_SURFACE_MATCH | PARTIAL_OR_SOURCE_ONLY | car,wheel | 0 | retail/NewRav / 0.0 / 0.080853 | accepted/Lancer / 0.0 / 0.151663 |
| nov-local/newRavAlpha | NO_EXACT_RETAIL_SURFACE_MATCH | PARTIAL_OR_SOURCE_ONLY |  | 0 | retail/NewRav / 0.0 / 0.078883 | accepted/Lancer / 0.0 / 0.165428 |
| nov-local/Rav4 | NO_EXACT_RETAIL_SURFACE_MATCH | PARTIAL_OR_SOURCE_ONLY |  | 0 | retail/Terrano / 0.0 / 0.110365 | accepted/Mercedes / 0.0 / 0.126 |
| nov-local/rav4Alpha | NO_EXACT_RETAIL_SURFACE_MATCH | PARTIAL_OR_SOURCE_ONLY |  | 0 | retail/Kangoo / 0.0 / 0.125107 | accepted/Mercedes / 0.0 / 0.142836 |
| nov-local/Tata | PARTIAL_RETAIL_SURFACE_VARIANT | PARTIAL_OR_SOURCE_ONLY |  | 0 | retail/Tata / 0.511869 / 0.049757 | accepted/HeritageTrooper / 0.0 / 0.153036 |
| nov-local/Trooper | NO_EXACT_RETAIL_SURFACE_MATCH | COMPLETE_NATIVE_INPUTS | car,complete,wheel | 0 | retail/LandCruiser / 0.0 / 0.113334 | accepted/HeritageTrooper / 0.954382 / 0.0 |
| nov-local/TrooperAlpha | NO_EXACT_RETAIL_SURFACE_MATCH | PARTIAL_OR_SOURCE_ONLY |  | 0 | retail/LandCruiser / 0.0 / 0.104153 | accepted/HeritageTrooper / 0.937981 / 0.0 |
| nov-local/Wildcat | PARTIAL_RETAIL_SURFACE_VARIANT | NATIVE_TEXTURE_GAPS | car,complete,wheel | 1 | retail/Simmbugghini / 0.889222 / 0.016113 | accepted/PDSilver / 0.0 / 0.186251 |
| nov-local/WildcatAlpha | PARTIAL_RETAIL_SURFACE_VARIANT | PARTIAL_OR_SOURCE_ONLY |  | 0 | retail/WildCat / 0.941675 / 0.011084 | accepted/PDSilver / 0.0 / 0.142543 |
| nov-local@Forester.zip/Forester | NO_EXACT_RETAIL_SURFACE_MATCH | PARTIAL_OR_SOURCE_ONLY | car,wheel | 0 | retail/ChevyBlazer / 0.0 / 0.134648 | accepted/Mercedes / 0.0 / 0.118751 |
| nov-local@Forester.zip/ForesterAlpha | NO_COMPARABLE_RETAIL_SURFACE | PARTIAL_OR_SOURCE_ONLY |  | 0 | UNRESOLVED | UNRESOLVED |
| shipped841/Copy of Mercedes | NO_EXACT_RETAIL_SURFACE_MATCH | PARTIAL_OR_SOURCE_ONLY |  | 0 | retail/ChevyBlazer / 0.0 / 0.113184 | accepted/Mercedes / 1.0 / 0 |
| shipped841/Copy of Mercedes/lpha | NO_EXACT_RETAIL_SURFACE_MATCH | PARTIAL_OR_SOURCE_ONLY |  | 0 | retail/Terrano / 0.0 / 0.12052 | accepted/Mercedes / 0.9375 / 0.000791 |
| shipped841/Copy of MercedesAlpha | NO_EXACT_RETAIL_SURFACE_MATCH | PARTIAL_OR_SOURCE_ONLY |  | 0 | retail/Terrano / 0.0 / 0.12052 | accepted/Mercedes / 0.9375 / 0.000791 |
| shipped841/Jump | PARTIAL_RETAIL_SURFACE_VARIANT | PARTIAL_OR_SOURCE_ONLY |  | 0 | retail/Jump / 0.976605 / 0.005331 | accepted/PDSilver / 0.0 / 0.191215 |
| shipped841/JumpAlpha | PARTIAL_RETAIL_SURFACE_VARIANT | PARTIAL_OR_SOURCE_ONLY |  | 0 | retail/Jump / 0.917301 / 0.005335 | accepted/MichelinRAV4 / 0.0 / 0.178778 |
| shipped841/LandCruiser | NO_EXACT_RETAIL_SURFACE_MATCH | PARTIAL_OR_SOURCE_ONLY |  | 0 | retail/LandCruiser / 0.391304 / 0.054221 | accepted/HeritageTrooper / 0.0 / 0.122527 |
| shipped841/LandCruiserAlpha | NO_EXACT_RETAIL_SURFACE_MATCH | PARTIAL_OR_SOURCE_ONLY |  | 0 | retail/LandCruiser / 0.389582 / 0.054479 | accepted/HeritageTrooper / 0.0 / 0.12544 |
| shipped841/megane | PARTIAL_RETAIL_SURFACE_VARIANT | PARTIAL_OR_SOURCE_ONLY |  | 0 | retail/megane / 0.504344 / 0.026493 | accepted/PDSilver / 0.0 / 0.178396 |
| shipped841/MeganeAlpha | NO_EXACT_RETAIL_SURFACE_MATCH | PARTIAL_OR_SOURCE_ONLY |  | 0 | retail/megane / 0.494208 / 0.02411 | accepted/PDSilver / 0.0 / 0.176263 |
| shipped841/Mercedes | NO_EXACT_RETAIL_SURFACE_MATCH | PARTIAL_OR_SOURCE_ONLY |  | 0 | retail/LandCruiser / 0.391304 / 0.054221 | accepted/HeritageTrooper / 0.0 / 0.122527 |
| shipped841/Mercedes/lpha | NO_EXACT_RETAIL_SURFACE_MATCH | PARTIAL_OR_SOURCE_ONLY |  | 0 | retail/LandCruiser / 0.389582 / 0.054479 | accepted/HeritageTrooper / 0.0 / 0.12544 |
| shipped841/MercedesAlpha | NO_EXACT_RETAIL_SURFACE_MATCH | PARTIAL_OR_SOURCE_ONLY |  | 0 | retail/LandCruiser / 0.389582 / 0.054479 | accepted/HeritageTrooper / 0.0 / 0.12544 |
| shipped841/Trooper | NO_EXACT_RETAIL_SURFACE_MATCH | PARTIAL_OR_SOURCE_ONLY |  | 0 | retail/LandCruiser / 0.0 / 0.113334 | accepted/HeritageTrooper / 0.954382 / 0.0 |
| shipped841/TrooperAlpha | NO_EXACT_RETAIL_SURFACE_MATCH | PARTIAL_OR_SOURCE_ONLY |  | 0 | retail/LandCruiser / 0.0 / 0.104153 | accepted/HeritageTrooper / 0.937981 / 0.0 |
| shipped841/WildCat | NO_EXACT_RETAIL_SURFACE_MATCH | PARTIAL_OR_SOURCE_ONLY |  | 0 | retail/WildCat / 0.0 / 0.106535 | accepted/Mercedes / 0.0 / 0.164798 |
| shipped841/WildcatAlpha | NO_EXACT_RETAIL_SURFACE_MATCH | PARTIAL_OR_SOURCE_ONLY |  | 0 | retail/WildCat / 0.0 / 0.10338 | accepted/PDSilver / 0.0 / 0.156599 |
| shipped931/Forester | NO_EXACT_RETAIL_SURFACE_MATCH | PARTIAL_OR_SOURCE_ONLY | car,wheel | 0 | retail/ChevyBlazer / 0.0 / 0.134648 | accepted/Mercedes / 0.0 / 0.118751 |
| shipped931/ForesterAlpha | NO_EXACT_RETAIL_SURFACE_MATCH | PARTIAL_OR_SOURCE_ONLY |  | 0 | retail/Forester / 0.0 / 0.130775 | accepted/Mercedes / 0.0 / 0.121347 |
| shipped931/Jump | PARTIAL_RETAIL_SURFACE_VARIANT | COMPLETE_NATIVE_INPUTS | car,complete,wheel | 0 | retail/Jump / 0.976605 / 0.005331 | accepted/PDSilver / 0.0 / 0.191215 |
| shipped931/JumpAlpha | PARTIAL_RETAIL_SURFACE_VARIANT | PARTIAL_OR_SOURCE_ONLY |  | 0 | retail/Jump / 0.917301 / 0.005335 | accepted/MichelinRAV4 / 0.0 / 0.178778 |
| shipped931/NewRav | NO_EXACT_RETAIL_SURFACE_MATCH | COMPLETE_NATIVE_INPUTS | car,complete,wheel | 0 | retail/NewRav / 0.0 / 0.080853 | accepted/Lancer / 0.0 / 0.151663 |
| shipped931/newRavAlpha | NO_EXACT_RETAIL_SURFACE_MATCH | PARTIAL_OR_SOURCE_ONLY |  | 0 | retail/NewRav / 0.0 / 0.078883 | accepted/Lancer / 0.0 / 0.165428 |
| shipped931/Rav4 | NO_EXACT_RETAIL_SURFACE_MATCH | PARTIAL_OR_SOURCE_ONLY |  | 0 | retail/Terrano / 0.0 / 0.110365 | accepted/Mercedes / 0.0 / 0.126 |
| shipped931/rav4Alpha | NO_EXACT_RETAIL_SURFACE_MATCH | PARTIAL_OR_SOURCE_ONLY |  | 0 | retail/Kangoo / 0.0 / 0.125107 | accepted/Mercedes / 0.0 / 0.142836 |
| shipped931/Tata | PARTIAL_RETAIL_SURFACE_VARIANT | COMPLETE_NATIVE_INPUTS | car,complete,wheel | 0 | retail/Tata / 0.5455 / 0.043523 | accepted/HeritageTrooper / 0.0 / 0.144358 |
| shipped931/Trooper | NO_EXACT_RETAIL_SURFACE_MATCH | COMPLETE_NATIVE_INPUTS | car,complete,wheel | 0 | retail/LandCruiser / 0.0 / 0.113334 | accepted/HeritageTrooper / 0.979498 / 0.0 |
| shipped931/TrooperAlpha | NO_EXACT_RETAIL_SURFACE_MATCH | PARTIAL_OR_SOURCE_ONLY |  | 0 | retail/LandCruiser / 0.0 / 0.104153 | accepted/HeritageTrooper / 0.937981 / 0.0 |
| shipped931/Wildcat | PARTIAL_RETAIL_SURFACE_VARIANT | COMPLETE_NATIVE_INPUTS | car,complete,wheel | 0 | retail/WildCat / 0.96046 / 0.0 | accepted/PDSilver / 0.0 / 0.139301 |
| shipped931/WildcatAlpha | PARTIAL_RETAIL_SURFACE_VARIANT | PARTIAL_OR_SOURCE_ONLY |  | 0 | retail/WildCat / 0.941675 / 0.011084 | accepted/PDSilver / 0.0 / 0.142543 |
| shipped910/Jump | PARTIAL_RETAIL_SURFACE_VARIANT | COMPLETE_NATIVE_INPUTS | car,complete,wheel | 0 | retail/Jump / 0.949946 / 0.005331 | accepted/PDSilver / 0.0 / 0.191215 |
| shipped910/KiaSportage | PARTIAL_RETAIL_SURFACE_VARIANT | COMPLETE_NATIVE_INPUTS | car,complete,wheel | 0 | retail/KiaSportage / 0.880758 / 3.2e-05 | accepted/Mercedes / 0.0 / 0.161751 |
| shipped910/megane | PARTIAL_RETAIL_SURFACE_VARIANT | COMPLETE_NATIVE_INPUTS | car,complete,wheel | 0 | retail/megane / 0.504344 / 0.026493 | accepted/PDSilver / 0.0 / 0.178396 |
| shipped910/Navara | NO_EXACT_RETAIL_SURFACE_MATCH | COMPLETE_NATIVE_INPUTS | car,complete,wheel | 0 | retail/Navara / 0.0 / 0.101387 | accepted/HeritageTrooper / 0.0 / 0.159022 |
| shipped910/Simmbugghini | PARTIAL_RETAIL_SURFACE_VARIANT | NATIVE_TEXTURE_GAPS | car,complete,wheel | 1 | retail/Simmbugghini / 0.858782 / 0.016113 | accepted/PDSilver / 0.0 / 0.186251 |
| shipped910/Wildcat | PARTIAL_RETAIL_SURFACE_VARIANT | COMPLETE_NATIVE_INPUTS | car,complete,wheel | 0 | retail/WildCat / 0.96046 / 0.0 | accepted/PDSilver / 0.0 / 0.139301 |


## Reading the matrix

All66 source snapshots include originals, nested aliases and archival copies;
they are not66 different cars. The closest retail/accepted reference is **not
asserted identity or a recommended donor**. Zero-overlap nearest matches are
usually unrelated. Overlap is quantized triangle correspondence, RMS a bounded
unscaled vertex sample, not a full surface metric. Cross-format GXM comparison
is position-only. See results and shortlist for reviewed edition corrections.

## Per-family source feature ownership

Glass/lamp counts are candidate names in original sidecars, not qualified damage
zones or brake states. Native tags describe the primary car only. UNKNOWN means
GXM-only, unsupported or legacy draw grammar. Physics counts are named local XML
rows, not tuned/qualified parameters. Collision tags do not prove damage playback.

| Source / family | Glass/lamp candidates | Car native tags | Collision tags | Named physics rows |
|---|---:|---|---|---:|
| pcg-rebaked/Forester | 6/21 | 2:15 | [101] | 147 |
| pcg-rebaked/Jump | 4/6 | 2:22 | [101] | 147 |
| pcg-rebaked/LandCruiser | 4/8 | 2:24 | [101] | 147 |
| pcg-rebaked/megane | 4/10 | 2:21 | [101] | 147 |
| pcg-rebaked/Mercedes | 4/6 | 2:17 | [101] | 144 |
| pcg-rebaked/Original/Forester | 6/21 | 2:15 | [101] | 147 |
| pcg-rebaked/Original/Jump | 4/6 | 2:22 | [101] | 147 |
| pcg-rebaked/Original/KiaSportage | 4/6 | 2:26 | [101] | 147 |
| pcg-rebaked/Original/megane | 4/10 | 2:21 | [101] | 147 |
| pcg-rebaked/Original/Navara | 20/26 | 2:27 | [101] | 147 |
| pcg-rebaked/Original/Simmbugghini | 2/7 | 2:22 | [101] | 147 |
| pcg-rebaked/Original/Trooper | 6/18 | 2:22 | [101] | 147 |
| pcg-rebaked/Original/Wildcat | 4/8 | 2:21 | [101] | 147 |
| pcg-rebaked/Rav4 | 4/8 | 2:25 | [101] | 0 |
| pcg-rebaked/Trooper | 6/18 | 2:22 | [101] | 147 |
| pcg-rebaked/WildCat | 4/8 | 2:17 | [101] | 147 |
| nov-local/Forester | 6/21 | 2:15 | [101] | 150 |
| nov-local/ForesterAlpha | 2/7 | UNKNOWN | UNKNOWN | 0 |
| nov-local/Jump | 4/6 | 2:22 | [101] | 150 |
| nov-local/JumpAlpha | 2/3 | UNKNOWN | UNKNOWN | 0 |
| nov-local/NewRav | 8/6 | 2:23 | [101] | 150 |
| nov-local/newRavAlpha | 4/3 | UNKNOWN | UNKNOWN | 0 |
| nov-local/Rav4 | 4/8 | UNKNOWN | UNKNOWN | 0 |
| nov-local/rav4Alpha | 2/4 | UNKNOWN | UNKNOWN | 0 |
| nov-local/Tata | 2/5 | UNKNOWN | UNKNOWN | 150 |
| nov-local/Trooper | 6/18 | 2:22 | [101] | 150 |
| nov-local/TrooperAlpha | 2/6 | UNKNOWN | UNKNOWN | 0 |
| nov-local/Wildcat | 2/7 | 2:22 | [101] | 150 |
| nov-local/WildcatAlpha | 2/4 | UNKNOWN | UNKNOWN | 0 |
| nov-local@Forester.zip/Forester | 6/21 | 2:15 | [101] | 0 |
| nov-local@Forester.zip/ForesterAlpha | 2/7 | UNKNOWN | UNKNOWN | 0 |
| shipped841/Copy of Mercedes | 4/6 | UNKNOWN | [101] | 0 |
| shipped841/Copy of Mercedes/lpha | 2/3 | UNKNOWN | UNKNOWN | 0 |
| shipped841/Copy of MercedesAlpha | 2/3 | UNKNOWN | UNKNOWN | 0 |
| shipped841/Jump | 4/6 | UNKNOWN | [101] | 121 |
| shipped841/JumpAlpha | 2/3 | UNKNOWN | UNKNOWN | 0 |
| shipped841/LandCruiser | 4/8 | UNKNOWN | [101] | 121 |
| shipped841/LandCruiserAlpha | 2/4 | UNKNOWN | UNKNOWN | 0 |
| shipped841/megane | 4/10 | UNKNOWN | [101] | 121 |
| shipped841/MeganeAlpha | 2/5 | UNKNOWN | UNKNOWN | 0 |
| shipped841/Mercedes | 4/8 | UNKNOWN | [101] | 121 |
| shipped841/Mercedes/lpha | 2/4 | UNKNOWN | UNKNOWN | 0 |
| shipped841/MercedesAlpha | 2/4 | UNKNOWN | UNKNOWN | 0 |
| shipped841/Trooper | 6/18 | UNKNOWN | [101] | 121 |
| shipped841/TrooperAlpha | 2/6 | UNKNOWN | UNKNOWN | 0 |
| shipped841/WildCat | 4/8 | UNKNOWN | [101] | 121 |
| shipped841/WildcatAlpha | 2/4 | UNKNOWN | UNKNOWN | 0 |
| shipped931/Forester | 6/21 | 2:15 | [101] | 150 |
| shipped931/ForesterAlpha | 2/7 | UNKNOWN | UNKNOWN | 0 |
| shipped931/Jump | 4/6 | 2:22 | [101] | 150 |
| shipped931/JumpAlpha | 2/3 | UNKNOWN | UNKNOWN | 0 |
| shipped931/NewRav | 8/6 | 2:23 | [101] | 150 |
| shipped931/newRavAlpha | 4/3 | UNKNOWN | UNKNOWN | 0 |
| shipped931/Rav4 | 4/8 | UNKNOWN | UNKNOWN | 0 |
| shipped931/rav4Alpha | 2/4 | UNKNOWN | UNKNOWN | 0 |
| shipped931/Tata | 2/5 | 2:31 | [101] | 150 |
| shipped931/Trooper | 6/18 | 2:22 | [101] | 150 |
| shipped931/TrooperAlpha | 2/6 | UNKNOWN | UNKNOWN | 0 |
| shipped931/Wildcat | 4/8 | 2:21 | [101] | 150 |
| shipped931/WildcatAlpha | 2/4 | UNKNOWN | UNKNOWN | 0 |
| shipped910/Jump | 4/6 | 2:22 | [101] | 147 |
| shipped910/KiaSportage | 4/6 | 2:26 | [101] | 147 |
| shipped910/megane | 4/10 | 2:21 | [101] | 147 |
| shipped910/Navara | 20/26 | 2:27 | [101] | 147 |
| shipped910/Simmbugghini | 2/7 | 2:22 | [101] | 147 |
| shipped910/Wildcat | 4/8 | 2:21 | [101] | 147 |
