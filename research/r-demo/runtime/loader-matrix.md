# Demo 8.4.1 Trooper loader matrix

Evidence source: human in-game results supplied for the first R-DEMO pass on 2026-09-24. The observations below are **CONFIRMED_BY_RUNTIME** for the tested Trooper paths in `demo-8.4.1`. This report has no synchronized Debug log or file-access trace, so it does not establish whether an unchanged `.dx` was opened or read.

| Resource case | Observed result | Evidence boundary |
|---|---|---|
| `car.gxm` + `car.dx` | Race vehicle works. | Tested baseline. |
| `car.gxm` only | No visible difference from baseline. | `car.dx` not visually required in this case. |
| `car.dx` only | Race body and primary vehicle collision disappear; wheels remain. | `car.dx` alone does not supply the tested race body or its primary collision. |
| `complete.gxm` + `complete.dx` | Presentation/menu vehicle is available. | Tested baseline. |
| `complete.gxm` only | Presentation/menu model unchanged. | `complete.dx` not visually required in this case. |
| `complete.dx` only | Presentation/menu model disappears completely; race model remains available. | The tested presentation source is `complete.gxm`. |
| `wheel.gxm` + `wheel.dx` | Visual wheels are available. | Tested baseline. |
| `wheel.gxm` only | No visible/runtime effect from removing `wheel.dx`. | `wheel.dx` not visually required in this case. |
| `wheel.dx` only | Visual wheels disappear; the race vehicle remains and drives as though wheels physically exist. | The tested visual wheel template is `wheel.gxm`; wheel physics/placement remains separate. |

The case with neither file was not reported. No case above proves that any DX file is never opened, used as a cache, or used by another subsystem. The same behavior must not be assigned to `demo-9.3.1` or retail without testing.

A short traced repeat should record file opens/reads/writes and Debug messages for the three resources. See `file-access-correlation.md`.
