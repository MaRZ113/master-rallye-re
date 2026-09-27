# R-COOKER1 Input Manifest

Evidence: **CONFIRMED_BY_BYTES** for all listed sizes, SHA256 values, revisions, and byte comparisons. The proprietary files remain under ignored `inputs/` and are not tracked.

## Supplied files

| Path | Role | Cooker generation | Size | SHA256 | Revision / dimensions |
|---|---|---:|---:|---|---|
| `9.10.0_dxTrooper/black-tga.dxt` | COOKED_DXT | 9.10.0 | 1,044 | `c8af53e3c1ea06c42178b3e1988dff0b3c64f150b722cba6bdd0450dc1357f82` | 16×16 |
| `9.10.0_dxTrooper/Black-tga.gxi` | SOURCE_GXI | 9.10.0 | 1,032 | `f1e8c064908150ef3a0b354bfa2ae6de8493d2b43b895fb803987dc23cdac8a8` |  |
| `9.10.0_dxTrooper/car.dx` | COOKED_DX | 9.10.0 | 124,854 | `c2f44f09e116dad7d9ad16d026b13109c1631360151e4aa2be5b62a333ebcc40` | rev 135 |
| `9.10.0_dxTrooper/car.gxm` | SOURCE_GXM | 9.10.0 | 222,754 | `5caed6da1213f17e2638d0ee47860cf521d4715475418e028bfd13f7c0e87642` |  |
| `9.10.0_dxTrooper/complete.dx` | COOKED_DX | 9.10.0 | 134,609 | `85c3f74ca062acb994bd23722dfe1c774845d3db33a85cc5aadd7ab3f3fa242e` | rev 135 |
| `9.10.0_dxTrooper/complete.gxm` | SOURCE_GXM | 9.10.0 | 260,220 | `122d84a45a6b2f81989e645c18ecfd7a32392bf029c7503698fb5fc900eb5c34` |  |
| `9.10.0_dxTrooper/wheel.dx` | COOKED_DX | 9.10.0 | 12,989 | `236853cb1d8f1cf068f3639b90e8b372fdab1b9c3b40b3d8793bc959931e7b5c` | rev 135 |
| `9.10.0_dxTrooper/wheel.gxm` | SOURCE_GXM | 9.10.0 | 27,234 | `ade8e42e4e1c4c946b2bf726c722494b31854ee0ebd2e16384db675a7595aa65` |  |
| `9.3.1_dxTrooper/black-tga.dxt` | COOKED_DXT | 9.3.1 | 1,044 | `c8af53e3c1ea06c42178b3e1988dff0b3c64f150b722cba6bdd0450dc1357f82` | 16×16 |
| `9.3.1_dxTrooper/Black-tga.gxi` | SOURCE_GXI | 9.3.1 | 1,032 | `f1e8c064908150ef3a0b354bfa2ae6de8493d2b43b895fb803987dc23cdac8a8` |  |
| `9.3.1_dxTrooper/car.dx` | COOKED_DX | 9.3.1 | 124,568 | `8238078c40f7b419b2f3cc3a14f4511f1cdb6a8bce00f3589a39fbfcde32d5b1` | rev 131 |
| `9.3.1_dxTrooper/car.gxm` | SOURCE_GXM | 9.3.1 | 222,754 | `5caed6da1213f17e2638d0ee47860cf521d4715475418e028bfd13f7c0e87642` |  |
| `9.3.1_dxTrooper/complete.dx` | COOKED_DX | 9.3.1 | 134,349 | `27b429e271fc7afb3b71f45bf14c197c779473b087227dbf468fd48ad97a911f` | rev 131 |
| `9.3.1_dxTrooper/complete.gxm` | SOURCE_GXM | 9.3.1 | 260,220 | `122d84a45a6b2f81989e645c18ecfd7a32392bf029c7503698fb5fc900eb5c34` |  |
| `9.3.1_dxTrooper/wheel.dx` | COOKED_DX | 9.3.1 | 12,924 | `9e7da7b3ea525fb5f29b61be763894ae98cd54fd0430c1b46b9f64d76e48d0ed` | rev 131 |
| `9.3.1_dxTrooper/wheel.gxm` | SOURCE_GXM | 9.3.1 | 27,234 | `ade8e42e4e1c4c946b2bf726c722494b31854ee0ebd2e16384db675a7595aa65` |  |

## Source identity

The source snapshots under `inputs/9.3.1_dxTrooper/` and `inputs/9.10.0_dxTrooper/` have matching SHA256 values for all three GXM files and the supplied GXI. The GXM values also match the read-only Demo 9.3.1 Trooper corpus at `../corpora/demo-9.3.1/DataGx/Vehicles/Trooper/`. Demo 9.10.0 does not contain a Trooper source directory; the 9.10.0-generation input snapshot is the recorded source for those outputs.

| Source | SHA256 | 9.3.1 corpus match | Copies across input folders | 9.10.0 corpus path |
|---|---|---|---|---|
| `car.gxm` | `5caed6da1213f17e2638d0ee47860cf521d4715475418e028bfd13f7c0e87642` | yes | byte-identical | absent |
| `complete.gxm` | `122d84a45a6b2f81989e645c18ecfd7a32392bf029c7503698fb5fc900eb5c34` | yes | byte-identical | absent |
| `wheel.gxm` | `ade8e42e4e1c4c946b2bf726c722494b31854ee0ebd2e16384db675a7595aa65` | yes | byte-identical | absent |
| `Black-tga.gxi` | `f1e8c064908150ef3a0b354bfa2ae6de8493d2b43b895fb803987dc23cdac8a8` | yes | byte-identical | absent |

## Paired DX outputs

| Resource | Source GXM SHA256 | Rev 131 size / SHA256 | Rev 135 size / SHA256 |
|---|---|---|---|
| `car` | `5caed6da1213f17e2638d0ee47860cf521d4715475418e028bfd13f7c0e87642` | 124,568 / `8238078c40f7b419b2f3cc3a14f4511f1cdb6a8bce00f3589a39fbfcde32d5b1` | 124,854 / `c2f44f09e116dad7d9ad16d026b13109c1631360151e4aa2be5b62a333ebcc40` |
| `complete` | `122d84a45a6b2f81989e645c18ecfd7a32392bf029c7503698fb5fc900eb5c34` | 134,349 / `27b429e271fc7afb3b71f45bf14c197c779473b087227dbf468fd48ad97a911f` | 134,609 / `85c3f74ca062acb994bd23722dfe1c774845d3db33a85cc5aadd7ab3f3fa242e` |
| `wheel` | `ade8e42e4e1c4c946b2bf726c722494b31854ee0ebd2e16384db675a7595aa65` | 12,924 / `9e7da7b3ea525fb5f29b61be763894ae98cd54fd0430c1b46b9f64d76e48d0ed` | 12,989 / `236853cb1d8f1cf068f3639b90e8b372fdab1b9c3b40b3d8793bc959931e7b5c` |

## Paired texture and cooker builds

Only `black-tga.dxt` is supplied as a paired DXT. Both copies are byte-identical at SHA256 `c8af53e3c1ea06c42178b3e1988dff0b3c64f150b722cba6bdd0450dc1357f82`; their source `Black-tga.gxi` snapshots are also byte-identical.

| Cooker | Executable | Size | SHA256 |
|---|---|---:|---|
| Demo 9.3.1 | `../corpora/demo-9.3.1/MRallye.exe` | 2,637,886 | `931cfc4e0c520c26581b0c1173d1beb586facd17176b885666f455090f646680` |
| Demo 9.10.0 | `../corpora/demo-9.10.0/MRallye.exe` | 2,883,646 | `13eaa642d0aabdfc47911a8606b02d9fc8d57d74328b36a0d3d618aadf1e0b78` |

## Provenance limits

The input directory grouping and co-located source snapshots associate each output with its generation and source. No per-run ProcMon capture or cooker invocation log was supplied, so process-level source-read provenance was not independently traced. The source bytes themselves are confirmed identical.
