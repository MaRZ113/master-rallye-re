# Debug/developer anchor map

| Anchor | Static path | Supported meaning |
|---|---|---|
| Menues/Enabled | 006E7888 → 005AFB20 | startup gate used for app/menu and second capability-checked Debug path; owner runtime confirms true opens Debug |
| DebugWindow/Enabled | 006E78F0 → default registration only | no consumer found; toggling had no observable effect in owner test; orphaned/redundant remains a hypothesis |
| DataEditors help paths | editor constructors → generic reader | intended help lookup, files absent from supplied views |
| BuildData MODEL/TEXTURE/IMAGE BANK | 005B29C0/2AD0/2C40 | ordinary loaders and counters |
| GXM model stage messages | xrefs in 0054D6E0 | conditional stages in a real model build path |
| Shader selection | 00586B70 | shader-selection diagnostic |

See debug-anchor-map.json and debug-message-producers.json for addresses and build presence. The owner-reported flag-isolation result is recorded in corrections.md; the tested build was not specified.
