# R-DEMO2.8 — demo 9.3.1 `$chull` cooker oracle

## Scope and status

Prepare one controlled source edit for the original demo 9.3.1 cooker:

```text
GXM $chull(Trooper) -> generated DX tag101
```

The original corpus asset is read-only. The candidate, byte audit, and runtime DX outputs live below ignored `.research-output/r-demo2/931-chull-oracle/`. The game was not launched during preparation. The +0.10 candidate is **CANDIDATE_PREPARED_RUNTIME_UNTESTED**.

## Why +0.10 X

The prior demo 8.4.1 +0.4 X hull edit crossed the native plane-equivalence decision under the stock `PlaneThickness` (`0.0005000000237487257`) and crashed during convex-hull construction. The user then confirmed that the same +0.4 X hull with `PlaneThickness = 0.00052` reached “Building convex hull - done”, continued loading, and visibly changed collision. That resolves the earlier NULL-crash pursuit for now.

Offline replay of that analyzed 8.4.1 hull kept the complete baseline decision sequence at +0.10 X; divergence began around +0.1065/+0.107. This motivates a smaller, controlled cooker probe. Those thresholds are **not transferred to 9.3.1**. The 9.3.1 run below is an oracle experiment, not a prediction that its native plane decisions will match 8.4.1.

## Exact 9.3.1 source and derived target

| Evidence | Value |
|---|---|
| Original `car.gxm` | `D:\Game\Master Rallye\corpora\demo-9.3.1\DataGx\Vehicles\Trooper\car.gxm` |
| Original GXM SHA256 / size | `5caed6da1213f17e2638d0ee47860cf521d4715475418e028bfd13f7c0e87642` / 222,754 bytes |
| Sibling `Trooper.txt` SHA256 | `66bbce78328eb224ab7170bb2df978116f4f38ade24d689d336a05c23b576779` |
| Header words | `[132866, 0, 0, 22, 5937, 2376, 1979, 1353]` |
| Parsed counts | 22 materials; 5,937 Vector A; 2,376 Vector B; 1,979 triangle records; 1,353 Vector C |
| Directive | `$chull(Trooper)`; records `[1911, 1979)`; 68 records |
| Referenced unique Vector C positions | `[1317, 1318, 1319, 1320, 1321, 1322, 1323, 1324, 1325, 1326, 1327, 1328, 1329, 1330, 1331, 1332, 1333, 1334, 1335, 1336, 1337, 1338, 1339, 1340, 1341, 1342, 1343, 1344, 1345, 1346, 1347, 1348, 1349, 1350, 1351, 1352]` |
| Shared references to other mesh records | 0 |

The index set above was derived by parsing this 9.3.1 GXM and its sibling sidecar, then reading the C-index triples from the associated triangle records. It was not copied from the 8.4.1 result.

## Candidate and byte audit

The generated candidate is `trooper-931-chull-xplus010.gxm`, SHA256 `b7a4da48f32ce0e4e9802e0656f79905b23af373d0dc0a397e8f2f64c973c5b3` (222,754 bytes). It changes only `C[i].x` float32 for those 36 derived indices by source-coordinate `(+0.10, 0, 0)`. C.y/z remain unchanged. Vector A/B, material records, triangle records/order/indices/winding, hierarchy/tail, and file size remain byte-identical.

Exactly 117 bytes differ. The audit enumerates all changed byte offsets and 36 coalesced ranges; every range lies inside the approved four-byte X field for one selected Vector C index. Some bytes inside those float32 words retain the same bit value. Masking only the approved X fields produces equal source/candidate SHA256 values, proving all non-target bytes match.

Artifacts:

- Candidate: `.research-output/r-demo2/931-chull-oracle/trooper-931-chull-xplus010.gxm`
- Full byte and parse audit: `.research-output/r-demo2/931-chull-oracle/trooper-931-chull-xplus010-audit.json`
- Human-readable audit: `.research-output/r-demo2/931-chull-oracle/trooper-931-chull-xplus010-report.md`
- Builder: `tools/scanner/r_demo2_931_chull_candidate.py`

The existing native-style plane replay is deliberately not run: `r_demo2_7_hull_divergence.py` pins demo 8.4.1 GXM and executable hashes. No validated 9.3.1 replay is available, so the 9.3.1 stock-tolerance decision signature remains **UNKNOWN**.

## DX comparison workflow

`tools/scanner/r_demo2_931_chull_dx_oracle.py` compares the three supplied DX files and writes JSON plus Markdown under ignored `.research-output/r-demo2/`:

1. `car_baseline_A.dx` vs `car_baseline_B.dx`: SHA256, size, exact byte identity, changed offsets/ranges, and structured parser comparison.
2. Each baseline vs `car_chull_xplus010.dx`: same raw and semantic comparison, including render positions/normals/colors/UVs; local/global index streams; raw draw/material region; recognized collision tags; tag101 base scalar, Rep A/B geometry/topology, face metadata and secondary lists; marker-1339 center/minimum/maximum/radius; and unparsed collision bytes.
3. If A/B are not byte-identical, the candidate is compared separately against both. The workflow does not invent a single baseline byte consensus.

The 9.3.1 same-build source-to-tag101 map supports `(x,y,z) -> (x,z,-y)`, so source +0.10 X predicts tag101 Representation A/B primary geometry (`geometry_a`) DX +0.10 X. The comparator measures that delta from the generated files. It labels byte difference, float noise within `1e-5`, topology changes, the predicted translation, and unexpected changes separately. Auxiliary parsed geometry, unknown DX draw bytes, and marker-1339 movement are reported without assigning unsupported meaning.

Baseline A is already staged at `.research-output/r-demo2/931-chull-oracle/input/car_baseline_A.dx`. It is a copy of the existing 9.3.1 runtime rebuild-A at `.research-output/r-demo2/input/rebuild-A/car.dx`, SHA256 `8238078c40f7b419b2f3cc3a14f4511f1cdb6a8bce00f3589a39fbfcde32d5b1` (124,568 bytes). The existing report records its byte-identical rebuild-B result. For this experiment, generate a fresh baseline B and the +0.10 output as described below.

When all inputs exist, run the comparator with the bundled Python runtime:

```powershell
$PythonExe = 'C:\Users\MaRZ\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $PythonExe tools/scanner/r_demo2_931_chull_dx_oracle.py `
  --baseline-a ".research-output/r-demo2/931-chull-oracle/input/car_baseline_A.dx" `
  --baseline-b ".research-output/r-demo2/931-chull-oracle/input/car_baseline_B.dx" `
  --candidate-dx ".research-output/r-demo2/931-chull-oracle/input/car_chull_xplus010.dx" `
  --candidate-audit ".research-output/r-demo2/931-chull-oracle/trooper-931-chull-xplus010-audit.json" `
  --output ".research-output/r-demo2/931-chull-oracle/dx-oracle-comparison.json"
```

The `python` command above means the workspace's bundled Python executable when the system Python launcher is unavailable.

## Human runtime procedure

Use a separate disposable demo 9.3.1 copy; leave the original corpus untouched.

1. Install the exact original 9.3.1 `car.gxm` in the scratch Trooper directory.
2. Remove that scratch copy's `car.dx`.
3. Run 9.3.1, load Trooper, and save the generated DX as `input/car_baseline_B.dx`.
4. Install `trooper-931-chull-xplus010.gxm` as scratch `car.gxm`.
5. Remove the scratch copy's generated `car.dx`.
6. Run 9.3.1 and load Trooper.
7. Save the generated DX as `input/car_chull_xplus010.dx`.
8. Return/provide `car_baseline_A.dx`, `car_baseline_B.dx`, `car_chull_xplus010.dx`, and the candidate audit/report. Baseline A is already staged in the repository output folder.

## Results placeholder

| Result | Status |
|---|---|
| Baseline A vs B bytes and semantics | Pending fresh baseline B |
| +0.10 candidate loaded by 9.3.1 | Pending human runtime result |
| Modified `car.dx` hash/size | Pending |
| Render geometry unchanged | Pending DX comparison |
| Tag101 Rep A/B and topology | Pending DX comparison |
| Marker-1339 and other collision blocks | Pending DX comparison |
| Candidate runtime confirmation | Not claimed |
