# R-COOKER3 capability matrix

| Source class | Current behavior | Evidence and limits |
|---|---|---|
| Demo 8.4.1 Mercedes supported GXM roles | Prepare isolated native cook job; validate and collect retail DX | **CONFIRMED_BY_RUNTIME** for the exact source and cook harness; deterministic outputs, cache-only use, collision, and damage were checked |
| Demo 9.3.1 Forester supported GXM roles | Prepare isolated native cook job; validate native DX/DXT outputs | **CONFIRMED_BY_RUNTIME** for model/race loading and collision/damage under a temporary Mercedes runtime namespace; does not prove Forester physics |
| Forester cache-only package named `DataGx/Vehicles/Forester` | Static validation passes: 3 rev135 DX plus 23 required DXT; no GXM/GXI | Forester-named runtime/cache-only test is pending |
| Supported vehicle DX revision 131 | Convert through the canonical R-COOKER2 adapter | Corpus-tested within its documented grammar; Trooper and Forester conversions passed runtime |
| Supported vehicle DX revision 135 | Validate and copy bytes unchanged | Existing-rev135 policy accepts known legitimate local/global index ordering divergence without normalizing it |
| Revision-127 DX with usable GXM | Prefer the supported native GXM source strategy | Requires a supported source layout and exact isolated harness |
| Revision-127 DX only, with no usable GXM | Reject | No revision-127-only conversion is implemented |
| Valid DXT | Parse and reuse unchanged | Used in Mercedes and Forester packages |
| GXI without a valid DXT | Use the existing offline GXI-to-DXT encoder where supported | Mercedes T1 matched the historical DXT for the tested texture; ordinary retail cache misses are not relied upon |
| Arbitrary GXM hierarchy/tail | Do not claim support | Supported material/geometry/triangle prefixes are checked; hierarchy/tail remains opaque |
| Native tag101 secondary descriptors | Delegate generation to the retail cook for tested GXM cases | Offline exact semantics remain unresolved |
| Headless cooker / menu automation | Not implemented | Operator loads preview and race in the isolated runtime |
| Vehicle IDs, menu roster, AI, physics config | Out of scope | Output package contains model resources and texture dependencies only |

Native GXM runtime coverage currently consists of Mercedes and Forester source
families for the exact reported runs. Forester's cook harness used the
temporary `Mercedes` namespace; the pending cache-only test checks Forester
namespace portability separately. Broader source support is not inferred from
those cases.
