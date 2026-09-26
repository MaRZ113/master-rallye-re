# R-BRIDGE1 — Demo 9.3.1 DX ↔ retail DX compatibility

## Result

**No Jump bridge candidate is justified yet.** The retail cache path requires the first two DX DWORDs to be `0xD00D` and `135`; demo 9.3.1 uses `0xD00D` and `131`. After those gates, the retail executable enters its DX record reader. The local retail parser accepts all inspected retail Jump roles and rejects all inspected demo Jump roles at the draw region. Changing only the revision DWORD in memory does not fix that parser failure.

The evidence supports a shared early DX envelope and render-array order, but it does not establish that demo 9.3.1 and retail use the same complete serialized format. The safest eventual direction is a retail-targeted semantic rebuild, but the current writer cannot emit a new arbitrary retail draw/material tree. **The narrow blocker is the demo draw/material region decoder plus a retail draw-tree writer that can preserve demo-derived geometry and material grouping.** No raw demo model or proprietary asset was modified; no game was launched.

## Scope, corpora, and evidence rules

Jump is the same-vehicle control across DEMO 8.4.1, DEMO 9.3.1, and retail. Trooper is the DEMO 9.3.1 transfer target; Navara is the possible retail replacement slot. This report does not add a vehicle slot, change physics, prepare a Trooper candidate, or infer that the earlier empty-path Debug log belonged to Trooper.

Inputs are the external `DataGx/Vehicles` trees and the three matching executables. All file paths below are corpus-relative. Per-file absolute paths, hashes, parser findings, GXM references, and texture inventory are in the ignored machine report:

`.research-output/r-bridge1/asset-inventory-and-jump-comparison.json`

Retail executable SHA256: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. Demo 9.3.1 executable SHA256: `931cfc4e0c520c26581b0c1173d1beb586facd17176b885666f455090f646680`. Demo 8.4.1 executable SHA256: `bbdfdb709ed41b10461b233b2f5c55403f1b6640f57d9e440476211e51ce75be`.

The retail structural parser is the project parser in `src/master_rallye/dx.py`; `src/master_rallye/demo_dx.py` parses common leading arrays and collision while keeping the demo draw area raw. A parser pass is not runtime acceptance proof. Ghidra static exports for the retail loader are kept under ignored `.research-output/r-bridge1/retail-static/`.

## Exact model inventory

`GXM` is absent from the retail extracted vehicle directories. Retail has precompiled DX and DXT resources; the demos include GXM, DX, DXT, and GXI. Retail TXT sidecars exist for the inspected roles. Hashes below are SHA256. `D-parser` means the demo structural parser; `R-parser` means the retail typed DX parser.

| Build | Role | DX size / SHA256 | GXM size / SHA256 | Parser status |
|---|---|---|---|---|
| DEMO 8.4.1 | Jump/car | 124,147 / `90a599ceb6fe8c5bddbe6bd0c354a5be3fcc7bba2087d97f1b729aa8f3d61964` | 217,595 / `b0471acb4ff095e67bba4cd1729c8a1baa71608aee37321f6cfc91c4a48be73d` | D pass; R rejects draw region |
| DEMO 8.4.1 | Jump/complete | 134,246 / `f6ca7636638441f159bb34738e0ecf15850d666cd84fb2cb2c5030da82223a2b` | 255,283 / `7cb3c04bc6dc9f05aebaeecb3ed800824735101800730e0906bdd34533e9a0fe` | D pass; R rejects draw region |
| DEMO 8.4.1 | Jump/wheel | 12,932 / `016b4bc698836671bc003e1b04f76b7be12fc657de8b621cd2721dceb1fffeb5` | 27,227 / `68c084024eb7df133e133b47739991a0f25440452c6e9259facc51250d963245` | D pass; R rejects draw region |
| DEMO 9.3.1 | Jump/car | 124,150 / `e92b9b093cfd62cb1dc2a9401b300e86b372ec5ea2df15a1d760c2faed5a771b` | 217,594 / `55bd09e1f8c9c647c82381dba463bb555dfcc51c6b2d63b9e8e39c55231da17e` | D pass; R rejects draw region |
| DEMO 9.3.1 | Jump/complete | 134,249 / `1ed72a856abdbc18bd2faa5964ec22816baef28aff3883b49f6bc84549e80724` | 255,282 / `71979cfb0217e8cbc7edaed5e8dd69d88f4b6482bee79029701c9075f11e5bb1` | D pass; R rejects draw region |
| DEMO 9.3.1 | Jump/wheel | 12,932 / `c366f0430b77efbdc9e3395fb0965b2fcef8fc4a4b45c1a90c6984cf5ff72fea` | 27,227 / `68c084024eb7df133e133b47739991a0f25440452c6e9259facc51250d963245` | D pass; R rejects draw region |
| RETAIL | Jump/car | 127,341 / `a6ad8bcb7c71e572f065a5c3710308730c2c4f0cc8b32f25af279adc923a7baa` | absent | R pass; 30 physical draws, 25 roots |
| RETAIL | Jump/complete | 134,496 / `bf7dc94e437fd66b90f9ca54fc150651a834b75147c894bf7804c98f1aa9a65a` | absent | R pass; 19 physical draws, 19 roots |
| RETAIL | Jump/wheel | 12,997 / `81c6a980df7c32ae16702afda6a42dfb6f9b5917c9cd6d7ddb4e3a84c0bf0ab0` | absent | R pass; 5 physical draws, 5 roots |

DEMO 9.3.1 Trooper and RETAIL Navara inventory:

| Corpus / role | DX size / SHA256 | GXM size / SHA256 | Parser status |
|---|---|---|---|
| DEMO 9.3.1 Trooper/car | 124,568 / `bf644c0530b3908789676564b4761cd670cc2bb187b084983d414bba458fa041` | 222,754 / `5caed6da1213f17e2638d0ee47860cf521d4715475418e028bfd13f7c0e87642` | D pass; R rejects draw region |
| DEMO 9.3.1 Trooper/complete | 134,349 / `fe4dfa6639c0ac2c9baf4e07428abe4ea3a528bb86b411a3034d74d4ce83a3a9` | 260,220 / `122d84a45a6b2f81989e645c18ecfd7a32392bf029c7503698fb5fc900eb5c34` | D pass; R rejects draw region |
| DEMO 9.3.1 Trooper/wheel | 12,924 / `4611a14326b0413cab8bffc7a61e0c6ee710f69bb986f0cab83921193bf8505f` | 27,234 / `ade8e42e4e1c4c946b2bf726c722494b31854ee0ebd2e16384db675a7595aa65` | D pass; R rejects draw region |
| RETAIL Navara/car | 166,309 / `2d3727f5bcd889ba38891276111c53f9c4d67cee1f5ece13de374a8235690655` | absent | R pass; one declared-root-count warning |
| RETAIL Navara/complete | 174,352 / `0edab556302273db41736993cdd041e73b1894419a623526c91f458b5fcfdc2e` | absent | R pass |
| RETAIL Navara/wheel | 12,904 / `2ae0c70a1912edfa8c628038541305132bf6843a00d33ce8761f351f17b72e08` | absent | R pass |

Texture/material inventory is included in the JSON report, with size/hash rows for every DXT and GXI and partial GXM material references. Jump has 25 DXT in DEMO 8.4.1, 25 DXT plus 26 GXI in DEMO 9.3.1, and 29 DXT in retail. Trooper has 25 DXT plus 26 GXI; Navara has 95 DXT. No texture conversion was needed to answer the DX-acceptance question, and this report makes no claim that Trooper's referenced textures are all present under Navara names.

## Jump: content differences versus format evidence

All inspected files have magic `0xD00D`; the next words are 127 (8.4.1), 131 (9.3.1), and 135 (retail). Word `0x08` is 1337 in all three generations. DEMO 9.3.1 Jump/car has header `(0xD00D, 131, 1337, 2361)`; RETAIL Jump/car has `(0xD00D, 135, 1337, 2401)`.

| Role | Render geometry / indices | Draw region | Collision tags and observations |
|---|---|---|---|
| car | 2,361 vs 2,401 vertices; 5,424 vs 5,514 local and global indices. Position/normal/color/UV content differs. | 1,622 vs 2,833 bytes. Retail parser reconstructs tags `[2,7,8]`. | Both have tag 101. Rep A is 8 vertices / 12 triangles and Rep B is 26 / 48 in both files. |
| complete | 2,551 vertices and 6,816 indices in both, but positions, normals, colors, UVs, and index order differ. | 1,429 vs 1,676 bytes. Retail has 19 tag-2 draws. | Both have tag 102; no tag 101 in this pair. |
| wheel | 220 vertices / 756 indices in both; indices, normals, colors, and UV bytes are equal. Only three position components differ, with maximum absolute delta `3.552713678800501e-15`. | 388 vs 453 bytes. Retail has five tag-2 draws. | Both have tag 102; parsed tag 102 and marker-1339 bytes match exactly. |

The retail parser succeeds on all three retail Jump files. It rejects all three demo Jump files while interpreting the first draw record (`unreasonable texture slot count`: `1752392036` for car/complete; `1818584424` for wheel). The demo parser can inspect retail DX because it keeps the draw region opaque; that does **not** prove the retail parser accepts demo DX. Thus the shared prefix/array order is real, but draw/material serialization is not yet normalized.

The Jump/car tag-101 comparison is especially useful and is kept separate from render compatibility:

- Base geometry, base scalar, Rep A and Rep B geometry coordinates, triangles, referenced indices, edges, primary descriptors, edge/face adjacency, and face loops match exactly.
- Rep A and Rep B core topology classify as `CORE_TOPOLOGY_EQUAL`.
- Secondary descriptor tuples differ (4 Rep A faces and 7 Rep B faces); their semantics remain unresolved. They are reported separately and are not counted as a proven topology change.
- Marker-1339 center/minimum/maximum match exactly. Radius differs by `2.384185791015625e-7`.

This supports geometric equivalence of Jump's recognized collision core across these controls; it does not authorize copying unrelated retail sections or resolving the auxiliary descriptor order.

## Retail cache and DX loader xrefs

Ghidra was run read-only on the retail executable identified above. The raw focused export is `.research-output/r-bridge1/retail-static/retail-dx-loader.txt`; helper and native cache-reader disassembly are in `.research-output/r-bridge1/retail-loader-followup.txt` and `.research-output/r-bridge1/retail-cache-reader.txt`.

The message is assembled from separate literals, not one combined string:

| Literal | Retail VA | Xref | Function |
|---|---:|---:|---|
| `Cached model out of date, missing or invalid format.` | `0x006E8CA0` | `0x0053C51C` | `FUN_0053C3F0` |
| `Reading GXM: [%s]` | `0x006E8C78` | `0x0053C535` | `FUN_0053C3F0` |
| `Can't load GXM [%s]` | `0x006E8C34` | `0x0053C579` | `FUN_0053C3F0` |

In `FUN_0053C3F0`, the same resource-path parameter is passed to the cache/source helpers and to the `Reading GXM` / `Can't load GXM` format calls. The cache decision is a composite condition:

```text
source_metric <= cache_metric + 0x14
AND cache-enabled byte at object + 8 is nonzero
AND FUN_00551970(cache-DX-path) succeeds
```

`FUN_0064D1C0` supplies the two compared values. Its exact return meaning is unresolved here; this report does not call them timestamps or file sizes. A false composite condition selects the cache-miss diagnostic and calls the GXM loader. If `FUN_00609190(param_2)` returns null, the function logs `Can't load GXM [%s]` and returns null.

The parent `FUN_0053BE70` calls `FUN_0053C3F0` at `0x0053BFB1`; on a null result it calls `FUN_0053C6B0` at `0x0053BFC6`. `FUN_0053C6B0` invokes the cached-DX reader `FUN_00551430` at `0x0053C719` and logs `Loaded cached model` or `Cannot load cached model`. This recovers the source/cache fallback chain beyond the first log line.

Both `FUN_00551970` (cache preflight) and `FUN_00551430` (cached-DX reader) open the cached path and read two DWORDs. Retail machine instructions compare:

| Gate | Retail check | Demo Jump value | Retail Jump value | Result |
|---|---|---:|---:|---|
| first DWORD, file offset `0x00` | `0xD00D` (`FUN_00551970` at `0x00551B6E`; `FUN_00551430` at `0x0055157C`) | `0xD00D`, pass | `0xD00D`, pass | same |
| second DWORD, file offset `0x04` | `0x87` = 135 (`0x00551BA1`; `0x005515A8`) | 131, fail | 135, pass | build gate differs |
| next DWORD / marker, offset `0x08` | `FUN_00551430` dispatches `0x539` (1337) specially after the first two checks | 1337 in bytes; not reached after revision failure | 1337 | byte value matches |
| following typed records | native reader dispatches recognized record values and structure handlers after the header gates | not reached for unmodified demo files; record conversion not proven | parsed by retail reader | unresolved demo conversion |
| cache freshness/config | opaque helper comparison and cache-enabled byte described above | asset-only pass/fail not established | asset-only pass/fail not established | unresolved environment gate |

The preflight checks only the opening header; it is not a complete DX parse. The full cached reader then handles later records. The 9.3.1 demo has an independently documented probe for `0xD00D` + 131 at VA `0x005466C9` / `0x005466F4`; that agrees with its own header and confirms the retail 135 expectation is build-specific.

### What the earlier Trooper log proves

If the earlier Trooper DX was passed through this retail cache path, its DEMO 9.3.1 second DWORD of 131 would fail the retail version gate. That is a concrete candidate cause for a cache miss, not proof that the specific observed log line belonged to `vehicles/navara/car`. The earlier Debug capture contained an empty `.gxm`/`.dx` resource path. Static code shows the resource path is an argument at the log site, but cannot recover the runtime argument from that capture. Therefore the old failure remains **unattributed to a specific resource invocation**.

## Transcode and semantic-rebuild feasibility

| Subsystem | Path A — minimal transcode | Path B — retail semantic rebuild |
|---|---|---|
| Header/cache revision | Proven field is `0x04 = 135`; a one-byte patch changes 131 to 135. It is necessary for the retail cache gate but not sufficient. | Retail template/writer can emit the retail marker, but that does not convert demo records. |
| Render arrays | Demo parser exposes positions, normals, colors, UVs, and local/global indices. The demo Jump car counts/content differ from retail, so raw copy cannot satisfy retail draw ranges. | Semantic arrays are readable. Existing topology writer only retains an existing retail draw/material hierarchy; it cannot create arbitrary groups. |
| Draws and materials | **Blocked:** the demo draw bytes are raw/opaque to the current parser; no evidence-backed record translation exists. | Retail draw tree is typed and parsed. Existing writers preserve its groups and strings; they do not emit a new arbitrary tree. |
| Indices and grouping | Available as byte streams, but car/complete streams differ and the demo partition-to-retail draw mapping is unknown. | Can rebuild index spans only after per-draw geometry/material assignment is known. |
| Collision | Jump car core is geometrically/topologically equal in the recognized parser; auxiliary descriptors differ. Trooper-specific retail compatibility remains untested. | R-DEMO2.10 supplies source-hull geometry evidence; a general retail tag-101 serializer is not established. |
| Bounds | Existing marker-1339 behavior is researched; no general transcode rule follows from header patching. | Recompute logic is corpus-supported, but does not solve unknown draw/material structures. |
| Hierarchy, damage, unknown blocks | Preserving opaque demo blocks is not a proven retail conversion. | Existing retail template can preserve retail blocks; creating/rebinding demo hierarchy and damage metadata is unsupported. |
| complete/wheel | Same revision mismatch and demo draw-parser rejection occur; not first-candidate requirements unless loader proves them mandatory. | Same draw-tree generation blocker; revisit after car policy. |

**Recommendation:** use Path B as the design target because it writes the known retail grammar and avoids carrying demo-only opaque records into retail. Do not generate a candidate until the demo draw/material semantics can be read and represented by an extensible retail serializer. Path A remains a possible implementation if the future reader reveals a compact record-level translation, but the header-only patch has been disproved as sufficient at parser level.

## Candidate validator and stopping decision

Reusable logic is in `src/master_rallye/bridge_analysis.py`:

- `compare_dx_generations(...)` runs demo and retail parsers independently, compares shared render/collision fields, and keeps content differences distinct from parser/layout evidence.
- `validate_bridge_candidate(...)` fails closed when the local retail parser, known cached header gates, index checks, or collision parser fails. A structural pass is reported as `STRUCTURALLY_VALIDATED_RUNTIME_UNCONFIRMED`; it never claims retail runtime acceptance.
- `audit_bridge_provenance(...)` verifies every changed byte against exact old/new bytes and a reason/evidence ledger.

The retail Jump controls pass local structural validation but remain `runtime_acceptance: NOT_TESTED` in this phase. Demo Jump/car fails both the revision gate and retail draw grammar. An in-memory revision-only probe changes only byte offset 4 (`0x83` to `0x87`) and still fails the retail parser at the first draw record. No output candidate or provenance ledger was created because a justification for changing only the header, or for rewriting the demo draw region, is absent.

Decision: **D — evidence is insufficient to claim the full 9.3.1 DX is retail-accepted or that a minimal bridge exists.** The exact first known gate and the next structural blocker are identified. No human runtime test is ready, so no game procedure is requested.

## Tests and files

Focused tests are in `tests/synthetic/test_r_bridge1.py`. They cover corpus/build IDs, both parser families, normalized content-vs-format differences, retail header gates, revision-only failure, Jump collision core versus unresolved auxiliary descriptors, provenance-ledger accounting, generic Trooper validation, and malformed-candidate rejection.

The reusable inventory/comparator entry point is `tools/scanner/r_bridge1.py`. Example invocation (read-only inputs; output under ignored research data):

```powershell
$env:PYTHONPATH = 'src'
python tools/scanner/r_bridge1.py `
  --demo-841-vehicles '...\DEMO-8.4.1\DataGx\Vehicles' `
  --demo-931-vehicles '...\DEMO-9.3.1\DataGx\Vehicles' `
  --retail-vehicles '...\RETAIL\DataGx\Vehicles' `
  --output '.research-output\r-bridge1\asset-inventory-and-jump-comparison.json'
```

Tracked R-BRIDGE1 files:

- `research/r-bridge/r-bridge1-demo-retail-dx-compatibility.md`
- `src/master_rallye/bridge_analysis.py`
- `tools/scanner/r_bridge1.py`
- `tests/synthetic/test_r_bridge1.py`

The next phase should focus only on decoding DEMO 9.3.1 Jump/car draw/material records and mapping them into the retail draw-tree writer. After that has a candidate that passes the local retail validator with a complete provenance ledger, return to the human for the smallest test: replace RETAIL Jump/car DX only and verify that retail accepts the demo-derived model file. Trooper→Navara comes after that policy is demonstrated.
