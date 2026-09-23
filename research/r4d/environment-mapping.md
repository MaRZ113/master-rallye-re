# R4D environment mapping

**CONFIRMED_BY_EXECUTABLE:** the shader registry at 00565DA0 has base_env, base_env_alpha, and base_env_alphatest variants. The selector at 00580360 includes an env suffix only if material-object bit 2 at +0x34 is set and DirectX/Options/Reflections is enabled. The damage config constructor at 00589110 registers RemoveEnvMap and EnvMapFadeStrength.

**CONFIRMED_BY_CORPUS:** chrome-tga is present in slot 1 of 145 draw bindings and across all 26 vehicle folders. Other second-slot helper families coexist, so the name alone cannot establish its stage operation.

**UNKNOWN:** whether chrome-tga is bound as stage 1 in these draws; whether coordinates are generated from normals/reflection vectors or source UVs; blend operation; damage fade implementation; exact relation between DX unknown_0x24 and the selector mask. A controlled chrome-tga replacement and a narrow loader-to-shader xref are the next discriminators.
