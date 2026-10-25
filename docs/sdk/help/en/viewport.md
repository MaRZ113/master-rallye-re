# 3D viewport and diagnostics

The D3D9 fixed-function Previewer is a diagnostic approximation of native D3D8,
not gameplay proof. Runtime lighting, sorting and inherited states can differ.

| Control | Action |
| --- | --- |
| Left mouse / middle mouse / wheel | Orbit and geometric pick / pan / zoom |
| F / Home | Focus selected draw / reset view |
| 1..6 | Camera presets |
| Ctrl+1..6 / Shift+1..6 | Save / recall view bookmarks |
| S / V | Save / recall bookmark 1 |
| F3 / F1 | Current diagnostic states / complete help |
| K | Cycle Cull CW / CCW / NONE |
| W / E / B | Wireframe / reflections / brake-light test |
| D | Composed / base / vertex colors / reflection-weight mask |
| Z | Instance-enabled depth-write / shader-only diagnostic |
| C | Case 1/2 for all generic source switch groups; NOT an impact simulation |
| L / 0 | Next isolated layer / restore all layers |
| A | Raw / assembled race wheels |
| Tab / I | Race/frontend/wheel / resource accounting |
| R / O | Reload resources / open converted DX |

An F1 hint remains visible with F3 hidden. F3 shows K/W/E/B/D/Z/C/A states and
layer/model/diagnostic shortcuts. **Cull NONE is preview-only and may hide real
missing backfaces.** Stock-calibrated CW remains the default. Compare opposite
views under CW, CCW and NONE before editing winding.

Reflection-mask mode shows texture-alpha × vertex-alpha for environment-capable
surfaces; other draws are dark. It intentionally overrides blend/test for mask
inspection and is not a native beauty render or a semantic paint mask.

Wheel fitting is a rest-pose preview, not settled suspension. Use named
`glass_states` profiles for individual native zones. C does not simulate impacts.
Native damage, brake triggers and draw ordering require actual gameplay tests.
