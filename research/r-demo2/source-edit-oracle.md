# Safe GXM position edit → original 9.3.1 cooker DX

## Source and human runtime result

Scratch source candidate: `.research-output/r-demo2/source-edit/DataGx/Vehicles/Trooper/car.gxm`, SHA256 `4f6dce6a90c1824955fbd9bfa9259166e96bca07bb046a95635aae994b7c8f2d`. It changes only Vector C index 646 component 2 by `+0.15`, from `1.4849326610565186` to `1.6349326372146606`; this record belongs to visible body geometry, not `$chull`. The user reports that the generated DX loads with GXM absent and that the visual edit appears (**CONFIRMED_BY_RUNTIME**).

The exact source candidate hash above is recorded in this workspace. The earlier same-build baseline GXM SHA256 is `5caed6da1213f17e2638d0ee47860cf521d4715475418e028bfd13f7c0e87642`. The output association is supported by folder provenance and the byte differential; retain this provenance caveat for the user-created scratch run.

## Compiled differential

Baseline: unchanged-source rebuild-A/B `car.dx`, 124,568 bytes, SHA256 `8238078c40f7b419b2f3cc3a14f4511f1cdb6a8bce00f3589a39fbfcde32d5b1`. Modified: `input/gxm_custom_rebuild/car.dx`, 124,568 bytes, SHA256 `9d3e8d4181ddd4929d777709d37dc4a1177a4b4a5ae4f2a3bf4b9042a6ebe655`.

Exactly one render position changes: DX vertex 1224 Y is `1.4849326610565186 → 1.6349326372146606`. The source-to-DX coordinate mapping is `(x,y,z) → (x,z,-y)`. Marker-1339 recomputes Y center, radius, and Y maximum. All normals, tag101 bytes, render topology, vertex colors, UV, local/global indices, and raw draw/material bytes remain identical. The total diff is 11 changed bytes in four ranges. Machine report: ignored `.research-output/r-demo2/baseline-vs-gxm-custom.json`.

Classification: the source edit→compiled geometry and bounds mapping is **CONFIRMED_BY_BYTES**; successful DX-only load and visible edit are **CONFIRMED_BY_RUNTIME**. This is one safe Vector-C position example, not a rule for `$chull` source data. The separate `$chull` candidate crashes inside hull construction; no second mutation was attempted.
