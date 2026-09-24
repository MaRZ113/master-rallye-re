# Demo versus retail resource comparison

The retail corpus has `Data.sma_unpacked/` around its `DataGx` tree; comparison below removes that prefix only to form a logical key. Manifests retain original `relative_path` and `corpus_id`.

| Same logical path and type | demo-8.4.1 overlap | Byte-identical to retail | demo-9.3.1 overlap | Byte-identical to retail |
|---|---:|---:|---:|---:|
| DX | 27 | 0 | 27 | 0 |
| DXT | 811 | 289 | 1,297 | 523 |
| GXI/GXM/GXB/GXP | 0 | 0 | 0 | 0 |

No source-format GXI/GXM/GXB/GXP files were found in the supplied retail corpus. This does not prove retail EXE lacks their loaders: static extension strings still occur in the retail executable. All shared-path DX files differ by hash; their format and model semantics may also differ. The current retail DX parser rejects the demo Trooper draw-table grammar, although the leading geometry header is readable; see `gxm-to-dx.md`.

No cross-corpus fallback or file mutation was used. A same-name vehicle folder is only a candidate counterpart; no trademark or legal identity inference is made.
