# Lighting input decision

| Family | Existing normal | Diffuse as unlit albedo/tint | New-light status | Reason |
|---|---|---|---|---|
|0x142 BASE_PRELIT risk|no|not established|NO_NORMAL + DOUBLE_LIGHT_RISK|source-color variation already contributes to stock appearance; generated normals would be a later feature|
|0x152 opaque env|yes|unsafe to assume pure albedo|DOUBLE_LIGHT_RISK|normal-correlated variable source color; separate tint/illumination not recovered|
|0x112 env wheels|yes|FVF omits diffuse|SAFE_CANDIDATE for normal input; NEEDS_MORE_EVIDENCE for texture albedo|vertex-color double lighting avoided, but diffuse texture shading and material identity are unresolved|
|0x152 alpha env|yes|not established|NEEDS_MORE_EVIDENCE / DOUBLE_LIGHT_RISK|blend and texture-alpha/reflection coupling; excluded from prototype|
|0x242 shared world|no|not established|NO_NORMAL|vehicle ownership unproved|
|0x252 shared world|yes|not established|NEEDS_MORE_EVIDENCE|vehicle ownership/material combine unproved|

The unchanged src/master_rallye/dx.py bounds-checks source arrays and validates draw index reconstruction. Analyze tool deduplicates referenced vertices per physical draw and decodes little-endian D3DCOLOR BGRA. It measures RGB uniqueness, normalized numerical Rec709 luma min/max/mean/stddev, alpha histogram, normal lengths, per-axis normal/luma Pearson, height/luma Pearson and intercept+normal best-fit vector/R-squared. The luma calculation is a numerical heuristic, not verified linear-light source encoding. Rank-deficient/constant fits return null rather than invented directions.

Representative inputs: twelve hashed car/wheel DX files from the protected retail corpus.187 diffuse-enabled draws;174 variable RGB. Strongest-axis median absolute correlation0.95354;171 finite full-rank fits have median R-squared0.92565. Alpha255 in every sampled diffuse-enabled referenced source color. This strongly motivates a double-light risk, but does not prove sun orientation, cooker light parameters, ambient magnitude or source-color provenance. Material tint, ambient/AO, directional prelight and artist-authored color remain alternatives. A linear fit on a small submesh can look convincing by construction; it is not a recovered lighting algorithm.

Stage0 multiplies diffuse by texture with LIGHTING=0 in the mapped families (R-MAT1 runtime map). Serialized colors are copied into compiled geometry by VA0x00577DD0 /RVA0x00177DD0. Damage configuration includes RemoveEnvMap/EnvMapFadeStrength, but post-damage color mutations are not measured here. Arrays contain normals even for layouts that omit NORMAL; source normal presence alone is not a runtime input claim. Alpha/glass behavior can still come from textures/material flags even when vertex alpha=255.

Decision: preserve colors, normals and textures; no new directional term, LIGHTING, SetLight, SetMaterial, vertex/pixel shaders or normal generation. Child VB/IB wrappers are DEFERRED: existing assets answer the source-color questions without COM identity changes. R-GFX5 lighting must first resolve or bound the prelight/tint split and post-damage behavior. Reflection research is a cleaner candidate than multiplying a new sun term into stock diffuse.
