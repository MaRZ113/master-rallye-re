# Course source-to-compiled evidence (R5T-A)

## Same-build pairs

Demo 8.4.1 is the only supplied build with course GXM source-like inputs for France1 and Italy1. Same-build DX, TXT, DXT, RaceTest XML, and France1/Italy1 FL/SF files are inventoried. GXM bodies are treated as source oracle bytes; this phase does not feed them to a guessed vehicle grammar.

Both GXM files have a 32-byte header. For France1 and Italy1 separately, the word at `0x0C` equals the TXT declared material count; the word at `0x18` equals the TXT mesh span; and the word at `0x10` equals three times the `0x18` word. These equalities are `CONFIRMED_BY_SOURCE_COMPILED_PAIR`. At `0x20`, the first `uint16` values are 40,159 for France1 and 49,007 for Italy1, outside the shared parser's bounded 4,096-byte string limit. This marks the current body boundary; it does not explain the body.

The current sidecar parser reads all 42 available course TXT files unchanged. Exact material names, mesh names/spans, and directive-bearing source strings are preserved. France1 and Italy1 8.4.1 source TXT includes `$bsp`, `$draw`, `$nodraw`, `$landdb`, and `$grnd*` families. Later TXT versions introduce `$surfacetype` strings in addition to changing material counts and mesh spans.

## Correlations not yet established

No source GXM hierarchy or source render vertices are parsed, so the following remain unproven:

- whether source `$bsp` objects compile to the observed DX tag100 payload;
- whether `$startline`, `$finishline`, or `$splittime*` objects disappear from render geometry or feed another resource;
- whether `$nodraw` objects are removed, retained, or redirected;
- whether `$grnd*` and `$landdb` data compile into tag100, SFL, another DX section, or multiple resources;
- how the cooker welds/splits vertices or groups materials into DX draw records.

The exact Demo 9.10.0 cooker bridge is **NOT TESTED**. No separate course cooker executable/tool was identified in the supplied Demo 8.4.1 resources; the game executable is not treated as a cooker oracle.

## Small developer oracles inventoried

The Demo 8.4.1 inventory includes `gordonTrack/flatTrack.gxm`, `gordonTrack/track.gxm`, `RussiaTurkey1`, `boinds/track01.gxm`, `collisiontests/crack*.gxm`, RaceLineExample, BSPTopologyTester, and the named BSP intersection/no-draw/boundary testers. R5T-A records their paths, sizes, and hashes without reverse engineering each test. They are prioritized as R5T-B source-correspondence inputs.
