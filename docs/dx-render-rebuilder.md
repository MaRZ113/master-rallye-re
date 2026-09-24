# R4F vehicle DX render-core rebuilder

This experimental writer targets the observed 78 vehicle DX resources and retains the existing draw/material/hierarchy set. It is not a from-scratch DX generator. The old R3/R4E same-topology patch path remains the production path for unchanged topology.

## Binary boundary

The first 12 header bytes are copied. The rebuilt region begins at header vertex count offset `0x0c` and ends after the stored global-index array. The complete collision/footer suffix is copied as bytes, although its file offset shifts when the render core grows or shrinks. The parser's collision grammar uses internal counted references; no parsed field is a file-absolute pointer into the render core. A 44-byte marker-1339 footer occurs after collision in 78/78 vehicle DX resources. Its min/max matches the union of render and collision vertices, and its center matches their midpoint. R4G later identified the fourth scalar as a covering radius on 77/78 corpus resources within 1e-5, with a documented WildCat exception; see vehicle-bounds.md. Unknown suffix shapes are rejected.

The core rebuild writes: vertex count; position/normal/color arrays; existing UV-set count and arrays; local index count and uint16 indices; the original draw-table envelope and original draw record bytes with `vertex_base`, inclusive `local_vertex_max`, `index_start`, `index_count` updated; and global table preamble/count/uint32 indices. All other draw bytes are compared after masking only those four fields. For each display-order triangle `(a,b,c)`, wire local indices are `(b,a,c)` and stored global indices are `(a+base,b+base,c+base)`.

## Supported source grammar

All 78 original vehicle resources have contiguous, disjoint vertex and local-index ranges in draw order. Every declared vertex is referenced in all 1,478 source draws; orphan output vertices are rejected. Later bases and starts must shift after an earlier draw changes. Source top-level count warnings in some files and one original degenerate triangle are preserved; they are not newly generated constraints. New draw records, strings, tag families, hierarchy changes, collision topology and UV-set creation are unsupported in the original R4F path. R4G adds an explicit conservative expanded-bounds mode. The writer retains unchanged source float bytes, including exceptional source values, while new/edited attributes must be finite float32.

The writer fails closed on source hash mismatch, malformed footer, noncontiguous draw pools, index/count overflow, empty draw, unexpected material record bytes, changed collision/suffix/prefix, reparse errors or new diagnostics. Its `external_diff_count` is zero only after these comparisons pass. The source and output render-core ranges are reported separately because insertion shifts later bytes.

## Evidence

- `research/r4f/topology-dependency-map.md` classifies every topology-relevant field.
- `research/r4f/draw-layout-corpus.json` records 1,478 draws across 78 resources.
- `research/r4f/rebuild-corpus.json` records 78/78 byte-identical zero-edit rebuilds and reparses.
- Synthetic tests cover vertex/triangle addition and removal, corner splits, index/base updates, capacity rejection, collision and suffix preservation.
- Blender 5.2.2 duplicated an Astero body triangle and exported the same candidate bytes as the direct writer.

Later R4F F1 human testing confirmed new car.dx topology with preserved collision, external/internal damage, breakable glass and wheels. R4G B1/P1/W1 then confirmed expanded bounds and complete.dx/wheel.dx topology, including four instantiated wheels. See ../research/r4f/runtime-results.md and ../research/r4g/runtime-results.md.
