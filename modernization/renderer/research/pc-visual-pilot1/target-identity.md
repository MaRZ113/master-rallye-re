# Source versus live identity

Source record:France1 draw54,course.batch.1.21,tag2/core3261170,vertex base4299,index start9792,index count144. Material:bush $alphatest() $clamp(uv) $shader(tree); texture bush01-tga.28 referenced vertices;48 records;24 distinct unsigned triangles,each present twice with both windings. The source draw ordinal is never a runtime predicate.

[source-signatures.json](source-signatures.json) preserves canonical DX/TXT hashes, the exact source group,48 face hashes, whole multiset hash,25 same-texture controls and a Turkey3 control. The same-texture controls differ geometrically; this does not prove their live buffer/range mapping.

Hash contract:finite XYZ float32; normalize signed zero; order each point by its three uint32 words; sort three points; hash36 little-endian bytes. Sort lowercase face hashes and hash their ASCII concatenation, preserving multiplicity. Winding is intentionally ignored for correspondence; culling remains a separately captured attribute. No epsilon is used for PC native content hashes. Native GetIndices base and minIndex determine the sampled VB byte range; raw indices are checked against the declared range.16/32-bit index formats are supported.

A matching full digest or subset in F10 produces content evidence only. The auditor always emits UNPROVEN/override_allowed=false. Mixed target+other calls cannot safely be altered as one draw. Missing/unsupported/truncated/over-budget or transformed data cannot prove absence. User-supplied course names are USER_RUNTIME_OBSERVATION, not engine-derived identity.

Missing links before any activation:actual France1 resource/course ownership; actual API partitioning; original state at the selected draw; mutable upload/revision ownership; reset/recreation validation; same-texture/other-course/vehicle/UI live negative controls. Existing registry serials observe creation and pool Reset survival, but do not intercept buffer Unlock writes or all raw COM escapes. A cached activation predicate must not rely on creation serial alone.

```text
PS2 node3509209 -> 24 source faces [CONFIRMED_BY_BYTES]
  -> PC compiled draw54,24 unique/48 records [CONFIRMED_BY_BYTES,0.001]
  -> UNKNOWN LINK: native course/resource/upload identity
  -> opt-in F10 content/state evidence [IMPLEMENTED; USER CAPTURE PENDING]
  -> UNKNOWN LINK: persistent safe draw predicate
  -> material override [BLOCKED]
```
