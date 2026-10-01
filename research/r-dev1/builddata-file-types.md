# BuildData formats and write risk

| Input | Consumer | Potential output | Evidence/risk |
|---|---|---|---|
| .gxm | 005B29C0 → 0054B320 | .dx model cache | ordinary model path; CREATE_ALWAYS writer when cache generation occurs |
| .gxi | 005B2AD0 → 0054A9B0 → 0054ACD0 | .dxt texture cache | ordinary texture path; CREATE_ALWAYS writer when cache generation occurs |
| .gxb | 005B2C40 → 0054B430 | unknown | downstream write behavior UNKNOWN |
| .gxp | 005B2C40 → 0054B430 | unknown | downstream write behavior UNKNOWN |
| other file under a DataGx path | callbacks reject | none shown | file failure counter incremented |

The recursive walker filters file paths for the DataGx\\ segment rather than restricting the recursive root to that one directory. It skips directories whose names begin with a dot; handling of the Win32 hidden attribute is UNKNOWN.

ModelCaching/CachingDisabled=false permits cache lookup and output. A valid cache may avoid source parsing, so BuildData does not prove a forced cook.
