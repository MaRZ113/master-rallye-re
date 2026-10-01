# Debug/developer anchor map

| Anchor | Static path | Supported meaning |
|---|---|---|
| Menues/Enabled | 006E7888 → 005AFB20 | startup gate used for app/menu and second capability-checked Debug path |
| DebugWindow/Enabled | 006E78F0 → default registration only | no consumer found; stale/redundant/indirect is unresolved |
| DataEditors help paths | editor constructors → generic reader | intended help lookup, files absent from supplied views |
| BuildData MODEL/TEXTURE/IMAGE BANK | 005B29C0/2AD0/2C40 | ordinary loaders and counters |
| GXM model stage messages | xrefs in 0054D6E0 | conditional stages in a real model build path |
| Shader selection | 00586B70 | shader-selection diagnostic |

See debug-anchor-map.json and debug-message-producers.json for addresses and build presence. The older human observation shows the Debug window can display live logs with both flags true; it was not repeated here.
