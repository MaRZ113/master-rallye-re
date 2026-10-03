# R-COOKER3 capability matrix

| Source class | V1 behavior | Evidence/status |
|---|---|---|
| Demo 8.4.1 Mercedes supported GXM roles | Prepare isolated native cook job; collect retail DX | **CONFIRMED_BY_RUNTIME** for the exact Mercedes source/build/harness only |
| Demo 9.3.1 Forester supported GXM roles | Prepare isolated native cook job | Static preflight passes; native cook and runtime **PENDING** |
| Supported vehicle DX revision 131 | Use canonical R-COOKER2 conversion to rev135 | Corpus validated within R-COOKER2's documented grammar; runtime tested for Trooper and Forester |
| Supported vehicle DX revision 135 | Validate and copy bytes unchanged into package | Existing-rev135 input policy; no triangle normalization |
| Revision-127 DX with usable GXM | Prefer supported retail-native GXM source strategy | Native result still depends on a supported source/build/harness and successful operator cook |
| Revision-127 DX only, no usable GXM | Reject; do not guess-convert | Explicitly unsupported |
| Valid historical DXT | Parse, hash, and reuse | Used for Mercedes and Forester preflight |
| GXI without a usable DXT | Reuse existing offline GXI-to-DXT encoder, then validate | Mercedes T1 offline encoding matched the historical DXT exactly for the tested texture |
| Ordinary retail DXT miss | Do not depend on automatic GXI regeneration | T1 found no GXI read or cached DXT write in the tested path |
| Arbitrary GXM layout/hierarchy | Do not claim support | Prefix checked; opaque tail/hierarchy is not fully reconstructed |
| Retail-native tag101 secondary descriptor producer | Delegate to retail for the tested native source path | Offline exact semantics remain unresolved |
| Game cooker automation/headless loading | Not implemented | V1 uses an operator-assisted isolated runtime job |
| Vehicle IDs, menu/roster, AI, physics config | Out of scope | Package contains model resources and dependencies only |

Current native GXM runtime coverage is one family: Mercedes. Forester's
prepared job is a static candidate, not an additional runtime confirmation.
