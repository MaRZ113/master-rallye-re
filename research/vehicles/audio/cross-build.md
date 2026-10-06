# Vehicle-audio cross-build comparison

All executables were independently fingerprinted and analyzed with Ghidra
12.1.4 via Ghidra Bridge. Demo evidence is not copied into retail.

| Build | SHA256 | Audio constructor / observation | Mercedes / higher-slot result |
|---|---|---|---|
| Demo 8.4.1 | `2d4a3b02d3cdb740dfdf3c11002c0026837dc19ba8e5211ad9763b35eb06e15a` | `FUN_00406BB0`; tuned switch cases 0 and 2 share `vehicles/rev9` and default curve A | Native registry `FUN_00447870` has Mercedes at ID2/T1; no unique Mercedes sample branch |
| Demo 9.3.1 | `611526d30be94879012efe54c56ceff428cb4d20a4bd49173370a4ebfe31a728` | `FUN_004088B0`; cases 0 and 2 share `vehicles/rev9`; ID26 takes default audio branch | Mercedes ID2/T1; the 27th registry record, ID26, is Citroen, not a 27th tuned audio entry |
| Demo 9.10.0 | `13eaa642d0aabdfc47911a8606b02d9fc8d57d74328b36a0d3d618aadf1e0b78` | `FUN_00408A50`; later constructor/tuning switch layout, default `rev9` | Ghidra string export found no `Mercedes` identity; no historical Mercedes mapping claimed |
| Retail | `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` | `FUN_00408F20`; explicit tuned IDs 0–24; 25+ default | No stock Mercedes record; project physical ID26 currently uses fallback |

## Byte comparisons

The two 60-word curve arrays for group A were extracted from the read-only
`.rdata` ranges identified in each constructor. Their concatenated SHA256 is
`c948e26ed1b204204a62aa06e4a6f5f7f57d2c5bf23fe02971fc3923406defd6` in all
four executables. The retail `vehicles/rev9.wav` hash is likewise
`3599c1a9cc9cc02e1475bc8bb7e6855b42f5b18b0421f2295b3496b30ec5c435` in the
four extracted audio corpora. This supports using retail ID0 as a compatible
semantic match for the historical demo Mercedes selector.

It does not prove every old-build object field has identical semantics or
binary layout. The candidate is built by reproducing the current retail G.1
profile and selecting current retail ID0; no pointer, object, handle, or
structure bytes are imported from demos.

The 9.3.1 ID26/Citroen record is not a tuned 27th sound profile: its audio
constructor has no ID26 tuned arm, so it reaches the normal default/warning
path. A 27-record registry does not imply 27 tuned audio entries.
