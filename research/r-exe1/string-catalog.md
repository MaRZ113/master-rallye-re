# Cross-build executable string catalog

Ghidra Bridge defined strings are indexed by build, address, direct function xrefs, subsystem and confidence. The JSON retains all matching records; the Markdown is a curated route map, capped per category so generic engine/library text does not swamp the architectural evidence.

## Coverage

| Build | Defined strings | Classified game/engine strings | Generic library matches |
|---|---:|---:|---:|
| 8.4.1 | 3,017 | 958 | 31 |
| 9.3.1 | 4,177 | 1,378 | 31 |
| 9.10.0 | 4,882 | 1,729 | 31 |
| retail | 7,447 | 2,240 | 32 |

## Category coverage

| Category | 8.4.1 | 9.3.1 | 9.10.0 | retail |
|---|---:|---:|---:|---:|
| filesystem_resource | 41 | 42 | 43 | 48 |
| xml_parameter_brokers | 31 | 34 | 35 | 38 |
| graphics_renderer | 53 | 55 | 70 | 70 |
| model_scene_loading | 76 | 78 | 81 | 85 |
| frontend_menu | 164 | 307 | 509 | 623 |
| course_race_route | 130 | 153 | 166 | 178 |
| vehicle_physics_damage | 128 | 205 | 346 | 385 |
| ai_opponent | 227 | 287 | 324 | 381 |
| input_controller | 34 | 66 | 72 | 85 |
| audio_music | 52 | 59 | 62 | 71 |
| save_progress_unlocks | 112 | 267 | 345 | 621 |
| networking | 44 | 66 | 66 | 88 |
| developer_debug_cooker | 31 | 36 | 36 | 43 |
| timing_profiling | 19 | 20 | 22 | 24 |
| replay_ghost | 20 | 35 | 35 | 45 |
| source_build_metadata | 2 | 15 | 10 | 32 |

## Representative strings with xrefs

### filesystem_resource

| Build | Address | Text | Referencing functions | Confidence |
|---|---:|---|---|---|
| 8.4.1 | `005eca70` | `DataScene/` | FUN_004b9810, FUN_004b98d0, FUN_004b99f0, FUN_004b9b50, FUN_004ed470, FUN_004ed690, FUN_004ed830 | HIGH |
| 8.4.1 | `005eca7c` | `DataGame/` | FUN_004b9d40, FUN_004b9ee0, FUN_004ba080, FUN_004ec6e0, FUN_004ec8d0, FUN_004ecab0, FUN_004ece20 | HIGH |
| 8.4.1 | `005f23d4` | `DataGame/Test.txt` | FUN_004ef920 | HIGH |
| 8.4.1 | `005f23e8` | `DataGame/Test.xml` | FUN_004ef920 | HIGH |
| 8.4.1 | `005f47a8` | `Saved cached image bank: [%s] ` | FUN_0051db40 | HIGH |
| 8.4.1 | `005f482c` | `Cached image bank out of date or missing. ` | FUN_0051db40 | HIGH |
| 8.4.1 | `005f4874` | `Cannot load cached image bank: [%s] ` | FUN_0051e720 | HIGH |
| 8.4.1 | `005f489c` | `Loaded cached image bank: [%s] ` | FUN_0051e720 | HIGH |
| 8.4.1 | `005f48c8` | `Saved cached model: [%s] ` | FUN_00520bb0 | HIGH |
| 8.4.1 | `005f4928` | `Reading GXM: [%s] ` | FUN_00520bb0 | HIGH |
| 8.4.1 | `005f493c` | `Cached model out of date, missing or invalid format. ` | FUN_00520bb0 | HIGH |
| 8.4.1 | `005f4978` | `Cannot load cached model: [%s] ` | FUN_00520e60 | HIGH |
| 8.4.1 | `005f4998` | `Loaded cached model: [%s] ` | FUN_00520e60 | HIGH |
| 8.4.1 | `005f4a20` | `Saved cached texture: [%s] ` | FUN_00521d20, FUN_005220c0 | HIGH |
| 8.4.1 | `005f4a54` | `Reading GXI: [%s] ` | FUN_00521d20 | HIGH |
| 8.4.1 | `005f4a68` | `Cached texture out of date or missing. ` | FUN_00521d20 | HIGH |
| 8.4.1 | `005f4ab8` | `Cannot load cached texture: [%s] ` | FUN_00521fd0 | HIGH |
| 9.3.1 | `006725e4` | `DataScene/` | FUN_004fa800, FUN_004fa8c0, FUN_004faa30, FUN_004fab90, FUN_006014b0, FUN_006016d0, FUN_00601870 | HIGH |
| 9.3.1 | `006725f0` | `DataGame/` | FUN_004fad80, FUN_004faf20, FUN_004fb0c0, FUN_00600720, FUN_00600910, FUN_00600af0, FUN_00600e60 | HIGH |
| 9.3.1 | `006735c4` | `Saved cached image bank: [%s] ` | FUN_0051be80 | HIGH |
| 9.3.1 | `00673658` | `Cached image bank out of date or missing. ` | FUN_0051be80 | HIGH |
| 9.3.1 | `006736a8` | `Cannot load cached image bank: [%s] ` | FUN_0051cc70 | HIGH |
| 9.3.1 | `006736d0` | `Loaded cached image bank: [%s] ` | FUN_0051cc70 | HIGH |
| 9.3.1 | `006736fc` | `Saved cached model: [%s] ` | FUN_0051f140 | HIGH |
| 9.3.1 | `0067375c` | `Reading GXM: [%s] ` | FUN_0051f140 | HIGH |
| 9.3.1 | `00673770` | `Cached model out of date, missing or invalid format. ` | FUN_0051f140 | HIGH |
| 9.3.1 | `006737b4` | `Cannot load cached model: [%s] ` | FUN_0051f3f0 | HIGH |
| 9.3.1 | `006737d4` | `Loaded cached model: [%s] ` | FUN_0051f3f0 | HIGH |
| 9.3.1 | `0067385c` | `Saved cached texture: [%s] ` | FUN_005202b0, FUN_00520650 | HIGH |
| 9.3.1 | `00673890` | `Reading GXI: [%s] ` | FUN_005202b0 | HIGH |
| 9.3.1 | `006738a4` | `Cached texture out of date or missing. ` | FUN_005202b0 | HIGH |
| 9.3.1 | `006738ec` | `Cannot load cached texture: [%s] ` | FUN_00520560 | HIGH |
| 9.3.1 | `0067d04c` | `DataGame/Test.txt` | FUN_00603fc0 | HIGH |
| 9.3.1 | `0067d060` | `DataGame/Test.xml` | FUN_00603fc0 | HIGH |
| 9.10.0 | `006adafc` | `DataGame/` | FUN_0050fd10, FUN_0050fed0, FUN_00510080, FUN_00632170, FUN_00632360, FUN_00632540, FUN_006328b0 | HIGH |
| 9.10.0 | `006adb08` | `DataScene/` | FUN_005103e0, FUN_00510490, FUN_00510610, FUN_00510770, FUN_00632f00, FUN_00633120, FUN_006332c0 | HIGH |
| 9.10.0 | `006af69c` | `Saved cached image bank: [%s] ` | FUN_0054f240 | HIGH |
| 9.10.0 | `006af728` | `Cached image bank out of date or missing. ` | FUN_0054f240 | HIGH |
| 9.10.0 | `006af778` | `Cannot load cached image bank: [%s] ` | FUN_00550000 | HIGH |
| 9.10.0 | `006af7a0` | `Loaded cached image bank: [%s] ` | FUN_00550000 | HIGH |
| 9.10.0 | `006af7cc` | `Saved cached model: [%s] ` | FUN_00552700 | HIGH |
| 9.10.0 | `006af82c` | `Reading GXM: [%s] ` | FUN_00552700 | HIGH |
| 9.10.0 | `006af840` | `Cached model out of date, missing or invalid format. ` | FUN_00552700 | HIGH |
| 9.10.0 | `006af884` | `Cannot load cached model: [%s] ` | FUN_005529b0 | HIGH |
| 9.10.0 | `006af8a4` | `Loaded cached model: [%s] ` | FUN_005529b0 | HIGH |
| 9.10.0 | `006af92c` | `Saved cached texture: [%s] ` | FUN_00553ab0, FUN_00553e50 | HIGH |
| 9.10.0 | `006af960` | `Reading GXI: [%s] ` | FUN_00553ab0 | HIGH |
| 9.10.0 | `006af974` | `Cached texture out of date or missing. ` | FUN_00553ab0 | HIGH |
| 9.10.0 | `006af9bc` | `Cannot load cached texture: [%s] ` | FUN_00553d60 | HIGH |
| 9.10.0 | `006b8f5c` | `DataGame/Test.txt` | FUN_00635350 | HIGH |
| 9.10.0 | `006b8f70` | `DataGame/Test.xml` | FUN_00635350 | HIGH |
| retail | `006e7c6c` | `DataScene/` | FUN_00522330, FUN_00522550, FUN_005b2260, FUN_005b2480, FUN_005b2620 | HIGH |
| retail | `006e7c84` | `DataGame/` | FUN_00522810, FUN_005229b0, FUN_00522b60, FUN_005b14d0, FUN_005b16c0, FUN_005b18a0, FUN_005b1c10 | HIGH |
| retail | `006e8c18` | `Saved cached model: [%s] ` | FUN_0053c3f0 | HIGH |
| retail | `006e8c78` | `Reading GXM: [%s] ` | FUN_0053c3f0 | HIGH |
| retail | `006e8ca0` | `Cached model out of date, missing or invalid format. ` | FUN_0053c3f0 | HIGH |
| retail | `006e8ce4` | `Cannot load cached model: [%s] ` | FUN_0053c6b0 | HIGH |
| retail | `006e8d04` | `Loaded cached model: [%s] ` | FUN_0053c6b0 | HIGH |
| retail | `006e8d9c` | `Saved cached texture: [%s] ` | FUN_0053dcc0 | HIGH |
| retail | `006e8dd0` | `Reading GXI: [%s] ` | FUN_0053dcc0 | HIGH |

### xml_parameter_brokers

| Build | Address | Text | Referencing functions | Confidence |
|---|---:|---|---|---|
| 8.4.1 | `005f23e8` | `DataGame/Test.xml` | FUN_004ef920 | HIGH |
| 9.3.1 | `0067d060` | `DataGame/Test.xml` | FUN_00603fc0 | HIGH |
| 9.10.0 | `006b8f70` | `DataGame/Test.xml` | FUN_00635350 | HIGH |
| retail | `006f259c` | `DataGame/Test.xml` | FUN_005fda00 | HIGH |

### graphics_renderer

| Build | Address | Text | Referencing functions | Confidence |
|---|---:|---|---|---|
| 8.4.1 | `005f3374` | `shader/particle_blend` | FUN_004f8c30, FUN_005098f0, FUN_00512800 | HIGH |
| 8.4.1 | `005f338c` | `shader/particle_densityabsorb` | FUN_004f8c30, FUN_00512800 | HIGH |
| 8.4.1 | `005f33ac` | `shader/particle_colorabsorb` | FUN_004f8c30, FUN_00512800 | HIGH |
| 8.4.1 | `005f33c8` | `shader/particle_add` | FUN_004f8c30, FUN_00512800 | HIGH |
| 8.4.1 | `005f33dc` | `shader/particle_solid` | FUN_004f8c30, FUN_00512800 | HIGH |
| 8.4.1 | `005f422c` | `shader/base_noise_alpha` | FUN_00512800 | HIGH |
| 8.4.1 | `005f4244` | `shader/base_noise` | FUN_00512800 | HIGH |
| 8.4.1 | `005f4258` | `shader/base_env_alpha` | FUN_00512800 | HIGH |
| 8.4.1 | `005f4270` | `shader/base_env` | FUN_00512800 | HIGH |
| 8.4.1 | `005f4280` | `shader/base_alpha` | FUN_00512800 | HIGH |
| 8.4.1 | `005f4294` | `shader/base` | FUN_00512800 | HIGH |
| 8.4.1 | `005f42a0` | `shader/default` | FUN_00512800, FUN_00533930 | HIGH |
| 8.4.1 | `005f4928` | `Reading GXM: [%s] ` | FUN_00520bb0 | HIGH |
| 8.4.1 | `005f4a54` | `Reading GXI: [%s] ` | FUN_00521d20 | HIGH |
| 8.4.1 | `005f5264` | `shader/` | FUN_005395e0 | HIGH |
| 9.3.1 | `00673588` | `shader/particle_blend` | FUN_0051a980, FUN_0052af30, FUN_00534b50, FUN_005503b0 | HIGH |
| 9.3.1 | `0067375c` | `Reading GXM: [%s] ` | FUN_0051f140 | HIGH |
| 9.3.1 | `00673890` | `Reading GXI: [%s] ` | FUN_005202b0 | HIGH |
| 9.3.1 | `00673fd0` | `shader/particle_densityabsorb` | FUN_0052af30, FUN_00534b50 | HIGH |
| 9.3.1 | `00673ff0` | `shader/particle_colorabsorb` | FUN_0052af30, FUN_00534b50 | HIGH |
| 9.3.1 | `0067400c` | `shader/particle_add` | FUN_0052af30, FUN_00534b50 | HIGH |
| 9.3.1 | `00674020` | `shader/particle_solid` | FUN_0052af30, FUN_00534b50 | HIGH |
| 9.3.1 | `00674168` | `shader/base_noise_alpha` | FUN_00534b50 | HIGH |
| 9.3.1 | `00674180` | `shader/base_noise` | FUN_00534b50 | HIGH |
| 9.3.1 | `00674194` | `shader/base_env_alpha` | FUN_00534b50 | HIGH |
| 9.3.1 | `006741ac` | `shader/base_env` | FUN_00534b50 | HIGH |
| 9.3.1 | `006741bc` | `shader/base_alpha` | FUN_00534b50 | HIGH |
| 9.3.1 | `006741d0` | `shader/base` | FUN_00534b50 | HIGH |
| 9.3.1 | `006741dc` | `shader/default` | FUN_00534b50, FUN_0055d530 | HIGH |
| 9.3.1 | `00675184` | `shader/` | FUN_005644b0 | HIGH |
| 9.10.0 | `0069c7bc` | `DirectX/Options/Reflections` | FUN_0045e060, FUN_0045e400 | HIGH |
| 9.10.0 | `0069c858` | `DirectX/Options/DetailPasses` | FUN_0045e060, FUN_0045e400 | HIGH |
| 9.10.0 | `006af3a0` | `shader/particle_blend` | FUN_005426f0, FUN_00544270, FUN_0054db50, FUN_00560000 | HIGH |
| 9.10.0 | `006af3b8` | `shader/particle_densityabsorb` | FUN_005426f0, FUN_00544270 | HIGH |
| 9.10.0 | `006af3d8` | `shader/particle_colorabsorb` | FUN_005426f0, FUN_00544270 | HIGH |
| 9.10.0 | `006af3f4` | `shader/particle_add` | FUN_005426f0, FUN_00544270 | HIGH |
| 9.10.0 | `006af408` | `shader/particle_solid` | FUN_005426f0, FUN_00544270 | HIGH |
| 9.10.0 | `006af420` | `shader/base_water_alpha` | FUN_00544270 | HIGH |
| 9.10.0 | `006af438` | `shader/base_water` | FUN_00544270 | HIGH |
| 9.10.0 | `006af44c` | `shader/base_noise_alphatest` | FUN_00544270 | HIGH |
| 9.10.0 | `006af468` | `shader/base_noise_alpha` | FUN_00544270 | HIGH |
| 9.10.0 | `006af480` | `shader/base_noise` | FUN_00544270 | HIGH |
| 9.10.0 | `006af494` | `shader/base_env_alphatest` | FUN_00544270 | HIGH |
| 9.10.0 | `006af4b0` | `shader/base_env_alpha` | FUN_00544270 | HIGH |
| 9.10.0 | `006af4c8` | `shader/base_env` | FUN_00544270 | HIGH |
| 9.10.0 | `006af4d8` | `shader/base_alphatest` | FUN_00544270 | HIGH |
| 9.10.0 | `006af4f0` | `shader/base_alpha` | FUN_00544270 | HIGH |
| 9.10.0 | `006af504` | `shader/base` | FUN_00544270 | HIGH |
| 9.10.0 | `006af510` | `shader/default` | FUN_00544270, FUN_00549740, FUN_005801e0 | HIGH |
| 9.10.0 | `006af82c` | `Reading GXM: [%s] ` | FUN_00552700 | HIGH |
| 9.10.0 | `006af960` | `Reading GXI: [%s] ` | FUN_00553ab0 | HIGH |
| 9.10.0 | `006b0c20` | `shader/` | FUN_005885d0 | HIGH |
| retail | `006b4c4c` | `DirectX/Options/Reflections` | FUN_00463a10, FUN_00464050, FUN_00577620, FUN_00580360 | HIGH |
| retail | `006b4ce8` | `DirectX/Options/DetailPasses` | FUN_00463a10, FUN_00464050, FUN_00577620, FUN_00580360 | HIGH |
| retail | `006e8c78` | `Reading GXM: [%s] ` | FUN_0053c3f0 | HIGH |
| retail | `006e8dd0` | `Reading GXI: [%s] ` | FUN_0053dcc0 | HIGH |
| retail | `006e9a7c` | `shader/particle_densityabsorb` | FUN_005639d0, FUN_00565da0 | HIGH |
| retail | `006e9aac` | `shader/particle_colorabsorb` | FUN_005639d0, FUN_00565da0 | HIGH |
| retail | `006e9ad8` | `shader/particle_add` | FUN_005639d0, FUN_00565da0 | HIGH |
| retail | `006e9af0` | `shader/particle_blend` | FUN_005639d0, FUN_00565da0, FUN_00571770, FUN_00587bb0 | HIGH |

### model_scene_loading

| Build | Address | Text | Referencing functions | Confidence |
|---|---:|---|---|---|
| 8.4.1 | `005eca70` | `DataScene/` | FUN_004b9810, FUN_004b98d0, FUN_004b99f0, FUN_004b9b50, FUN_004ed470, FUN_004ed690, FUN_004ed830 | HIGH |
| 8.4.1 | `005f47a8` | `Saved cached image bank: [%s] ` | FUN_0051db40 | HIGH |
| 8.4.1 | `005f482c` | `Cached image bank out of date or missing. ` | FUN_0051db40 | HIGH |
| 8.4.1 | `005f4874` | `Cannot load cached image bank: [%s] ` | FUN_0051e720 | HIGH |
| 8.4.1 | `005f489c` | `Loaded cached image bank: [%s] ` | FUN_0051e720 | HIGH |
| 8.4.1 | `005f48c8` | `Saved cached model: [%s] ` | FUN_00520bb0 | HIGH |
| 8.4.1 | `005f4928` | `Reading GXM: [%s] ` | FUN_00520bb0 | HIGH |
| 8.4.1 | `005f493c` | `Cached model out of date, missing or invalid format. ` | FUN_00520bb0 | HIGH |
| 8.4.1 | `005f4978` | `Cannot load cached model: [%s] ` | FUN_00520e60 | HIGH |
| 8.4.1 | `005f4998` | `Loaded cached model: [%s] ` | FUN_00520e60 | HIGH |
| 8.4.1 | `005f4a54` | `Reading GXI: [%s] ` | FUN_00521d20 | HIGH |
| 9.3.1 | `006725e4` | `DataScene/` | FUN_004fa800, FUN_004fa8c0, FUN_004faa30, FUN_004fab90, FUN_006014b0, FUN_006016d0, FUN_00601870 | HIGH |
| 9.3.1 | `006735c4` | `Saved cached image bank: [%s] ` | FUN_0051be80 | HIGH |
| 9.3.1 | `00673658` | `Cached image bank out of date or missing. ` | FUN_0051be80 | HIGH |
| 9.3.1 | `006736a8` | `Cannot load cached image bank: [%s] ` | FUN_0051cc70 | HIGH |
| 9.3.1 | `006736d0` | `Loaded cached image bank: [%s] ` | FUN_0051cc70 | HIGH |
| 9.3.1 | `006736fc` | `Saved cached model: [%s] ` | FUN_0051f140 | HIGH |
| 9.3.1 | `0067375c` | `Reading GXM: [%s] ` | FUN_0051f140 | HIGH |
| 9.3.1 | `00673770` | `Cached model out of date, missing or invalid format. ` | FUN_0051f140 | HIGH |
| 9.3.1 | `006737b4` | `Cannot load cached model: [%s] ` | FUN_0051f3f0 | HIGH |
| 9.3.1 | `006737d4` | `Loaded cached model: [%s] ` | FUN_0051f3f0 | HIGH |
| 9.3.1 | `00673890` | `Reading GXI: [%s] ` | FUN_005202b0 | HIGH |
| 9.10.0 | `006adb08` | `DataScene/` | FUN_005103e0, FUN_00510490, FUN_00510610, FUN_00510770, FUN_00632f00, FUN_00633120, FUN_006332c0 | HIGH |
| 9.10.0 | `006af69c` | `Saved cached image bank: [%s] ` | FUN_0054f240 | HIGH |
| 9.10.0 | `006af728` | `Cached image bank out of date or missing. ` | FUN_0054f240 | HIGH |
| 9.10.0 | `006af778` | `Cannot load cached image bank: [%s] ` | FUN_00550000 | HIGH |
| 9.10.0 | `006af7a0` | `Loaded cached image bank: [%s] ` | FUN_00550000 | HIGH |
| 9.10.0 | `006af7cc` | `Saved cached model: [%s] ` | FUN_00552700 | HIGH |
| 9.10.0 | `006af82c` | `Reading GXM: [%s] ` | FUN_00552700 | HIGH |
| 9.10.0 | `006af840` | `Cached model out of date, missing or invalid format. ` | FUN_00552700 | HIGH |
| 9.10.0 | `006af884` | `Cannot load cached model: [%s] ` | FUN_005529b0 | HIGH |
| 9.10.0 | `006af8a4` | `Loaded cached model: [%s] ` | FUN_005529b0 | HIGH |
| 9.10.0 | `006af960` | `Reading GXI: [%s] ` | FUN_00553ab0 | HIGH |
| retail | `006e7c6c` | `DataScene/` | FUN_00522330, FUN_00522550, FUN_005b2260, FUN_005b2480, FUN_005b2620 | HIGH |
| retail | `006e8c18` | `Saved cached model: [%s] ` | FUN_0053c3f0 | HIGH |
| retail | `006e8c78` | `Reading GXM: [%s] ` | FUN_0053c3f0 | HIGH |
| retail | `006e8ca0` | `Cached model out of date, missing or invalid format. ` | FUN_0053c3f0 | HIGH |
| retail | `006e8ce4` | `Cannot load cached model: [%s] ` | FUN_0053c6b0 | HIGH |
| retail | `006e8d04` | `Loaded cached model: [%s] ` | FUN_0053c6b0 | HIGH |
| retail | `006e8dd0` | `Reading GXI: [%s] ` | FUN_0053dcc0 | HIGH |
| retail | `006e9ddc` | `Saved cached image bank: [%s] ` | FUN_00572fb0 | HIGH |
| retail | `006e9e4c` | `Cached image bank out of date or missing. ` | FUN_00572fb0 | HIGH |
| retail | `006e9e9c` | `Cannot load cached image bank: [%s] ` | FUN_00573d80 | HIGH |
| retail | `006e9ec4` | `Loaded cached image bank: [%s] ` | FUN_00573d80 | HIGH |
| retail | `006ebe84` | `BuildData : MODEL : %s ` | FUN_005b29c0 | HIGH |
| retail | `006ebeb8` | `BuildData : IMAGE BANK : %s ` | FUN_005b2c40 | HIGH |
| retail | `006f4364` | `datascene/` | FUN_0064d530 | HIGH |

### frontend_menu

| Build | Address | Text | Referencing functions | Confidence |
|---|---:|---|---|---|
| 8.4.1 | `005e6920` | `FrontEnd/Network/selectedGameType` | FUN_00430a00, FUN_0046cf30 | HIGH |
| 8.4.1 | `005eb71c` | `FrontEnd/Network/Browse` | FUN_0046ce30, FUN_0046cfc0 | HIGH |
| 8.4.1 | `005eb734` | `FrontEnd/Network/selectedCar` | FUN_0046ced0, FUN_0046d050 | HIGH |
| 8.4.1 | `005eb754` | `FrontEnd/Network/selectedCourse` | FUN_0046cf00, FUN_0046d080 | HIGH |
| 9.3.1 | `00665e3c` | `Frontend/Network/Checkpoint` | FUN_0045a2c0 | HIGH |
| 9.3.1 | `00670298` | `FrontEnd/Network/Browse` | FUN_0048b1e0, FUN_0048b370 | HIGH |
| 9.3.1 | `006702b0` | `FrontEnd/Network/selectedCar` | FUN_0048b280, FUN_0048b400 | HIGH |
| 9.3.1 | `006702d0` | `FrontEnd/Network/selectedCourse` | FUN_0048b2b0, FUN_0048b430 | HIGH |
| 9.3.1 | `006702f0` | `FrontEnd/Network/selectedGameType` | FUN_0048b2e0 | HIGH |
| 9.3.1 | `0067048c` | `Frontend/Network/CheckpointMode` | FUN_0048bc80, FUN_0048bcb0 | HIGH |
| 9.10.0 | `0069d314` | `Frontend/Network/Checkpoint` | FUN_004657d0 | HIGH |
| 9.10.0 | `006ab858` | `FrontEnd/Network/Browse` | FUN_004a1230, FUN_004a13c0 | HIGH |
| 9.10.0 | `006ab870` | `FrontEnd/Network/selectedCar` | FUN_004a12d0, FUN_004a1450 | HIGH |
| 9.10.0 | `006ab890` | `FrontEnd/Network/selectedCourse` | FUN_004a1300, FUN_004a1480 | HIGH |
| 9.10.0 | `006ab8b0` | `FrontEnd/Network/selectedGameType` | FUN_004a1330 | HIGH |
| 9.10.0 | `006aba24` | `Frontend/Network/CheckpointMode` | FUN_004a1cd0, FUN_004a1d00 | HIGH |
| retail | `006b5660` | `Frontend/Network/Track` | FUN_0046ab50, FUN_0047e2d0 | HIGH |
| retail | `006b5678` | `Frontend/Network/Car0` | FUN_0046ab50, FUN_00480b60 | HIGH |
| retail | `006b5ba0` | `Frontend/Network/Checkpoint` | FUN_0046ceb0 | HIGH |
| retail | `006e5744` | `FrontEnd/Network/Browse` | FUN_004ad7a0, FUN_004ad930 | HIGH |
| retail | `006e575c` | `FrontEnd/Network/selectedCar` | FUN_004ad840, FUN_004ad9c0 | HIGH |
| retail | `006e577c` | `FrontEnd/Network/selectedCourse` | FUN_004ad870, FUN_004ad9f0 | HIGH |
| retail | `006e579c` | `FrontEnd/Network/selectedGameType` | FUN_004ad8a0 | HIGH |
| retail | `006e5910` | `Frontend/Network/CheckpointMode` | FUN_004ae240, FUN_004ae270 | HIGH |

### course_race_route

| Build | Address | Text | Referencing functions | Confidence |
|---|---:|---|---|---|
| 8.4.1 | `005e6fb8` | `Race/GhostPlayback` | FUN_00442220, FUN_00443410, FUN_004559c0, FUN_00469210 | HIGH |
| 8.4.1 | `005ea3c8` | `gaRaceFinishAI` | FUN_004527f0 | HIGH |
| 8.4.1 | `005ea438` | `gaRaceFinishAreaAI` | FUN_00452f90 | HIGH |
| 8.4.1 | `005ea4a0` | `gaRaceLineAI` | FUN_00453320 | HIGH |
| 8.4.1 | `005ea4fc` | `gaRaceNetworkStarterAI` | FUN_004538b0 | HIGH |
| 8.4.1 | `005ea52c` | `gaRacePaceNoteAI` | FUN_00453c10, FUN_00453ff0 | HIGH |
| 8.4.1 | `005ea5c0` | `gaRacePostFirstSplitTimeAI` | FUN_00454180, FUN_004542b0 | HIGH |
| 8.4.1 | `005ea620` | `gaRaceSplitTimeAI` | FUN_004543f0, FUN_00454900 | HIGH |
| 8.4.1 | `005ea698` | `Race/SplitTime%d/Car%d` | FUN_004544f0 | HIGH |
| 8.4.1 | `005ea6b0` | `Race/Car%d/SplitPoint` | FUN_004544f0 | HIGH |
| 8.4.1 | `005ea770` | `gaRaceStartCountdownAI` | FUN_00454a90 | HIGH |
| 8.4.1 | `005ea7f8` | `gaRaceStarterAI` | FUN_004555b0 | HIGH |
| 8.4.1 | `005ea854` | `Race/Car%d/RecordSpline` | FUN_004559c0 | HIGH |
| 8.4.1 | `005ea8e4` | `gaRaceTimerAI` | FUN_00455ff0 | HIGH |
| 9.3.1 | `006625b4` | `gaRaceSplitTimeAI` | FUN_00407220, FUN_00469f80, FUN_0046c390, FUN_0046e8e0, FUN_0046ee90 | HIGH |
| 9.3.1 | `006645e4` | `Race/GhostPlayback` | FUN_004464b0, FUN_00447ad0, FUN_004703e0, FUN_004874a0 | HIGH |
| 9.3.1 | `0066e990` | `EditControllergaRacePaceNoteAI` | FUN_00468f70, FUN_00469be0 | HIGH |
| 9.3.1 | `0066eaa8` | `EditControllergaRacePostFirstSplitTimeAI` | FUN_00469e70 | HIGH |
| 9.3.1 | `0066ebec` | `gaRacePostFirstSplitTimeAI` | FUN_00469f80, FUN_0046b160, FUN_0046e670, FUN_0046e7a0 | HIGH |
| 9.3.1 | `0066ec54` | `EditControllergaRaceSplitTimeAI` | FUN_0046b320 | HIGH |
| 9.3.1 | `0066ecc4` | `gaRaceFinishAI` | FUN_0046c970 | HIGH |
| 9.3.1 | `0066ed50` | `gaRaceFinishAreaAI` | FUN_0046d390 | HIGH |
| 9.3.1 | `0066eda4` | `gaRaceLineAI` | FUN_0046d760 | HIGH |
| 9.3.1 | `0066ee18` | `gaRaceNetworkStarterAI` | FUN_0046dd70 | HIGH |
| 9.3.1 | `0066ee48` | `gaRacePaceNoteAI` | FUN_0046e100, FUN_0046e4e0 | HIGH |
| 9.3.1 | `0066ef00` | `Race/SplitTime%d/Car%d` | FUN_0046eac0, FUN_00498d70 | HIGH |
| 9.3.1 | `0066ef18` | `Race/Car%d/SplitPoint` | FUN_0046eac0 | HIGH |
| 9.3.1 | `0066efb4` | `gaRaceStartCountdownAI` | FUN_0046f020 | HIGH |
| 9.3.1 | `0066f048` | `gaRaceStarterAI` | FUN_0046fe20 | HIGH |
| 9.3.1 | `0066f0f0` | `Race/Car%d/RecordSpline` | FUN_00470560 | HIGH |
| 9.3.1 | `0066f188` | `gaRaceTimerAI` | FUN_00470c20 | HIGH |
| 9.10.0 | `00698750` | `gaRaceSplitTimeAI` | FUN_004073c0, FUN_0047cca0, FUN_0047f2c0, FUN_00482740, FUN_00482e30 | HIGH |
| 9.10.0 | `0069a998` | `Race/GhostPlayback` | FUN_00448dd0, FUN_004845b0, FUN_0049cfb0 | HIGH |
| 9.10.0 | `006a9d74` | `EditControllergaRacePaceNoteAI` | FUN_0047bc90, FUN_0047c900 | HIGH |
| 9.10.0 | `006a9e8c` | `EditControllergaRacePostFirstSplitTimeAI` | FUN_0047cb90 | HIGH |
| 9.10.0 | `006a9fd0` | `gaRacePostFirstSplitTimeAI` | FUN_0047cca0, FUN_0047e030, FUN_004823e0, FUN_00482590 | HIGH |
| 9.10.0 | `006aa08c` | `EditControllergaRaceSplitTimeAI` | FUN_0047e250 | HIGH |
| 9.10.0 | `006aa0fc` | `gaRaceFinishAI` | FUN_0047f8a0 | HIGH |
| 9.10.0 | `006aa174` | `gaRaceFinishAreaAI` | FUN_004802e0 | HIGH |
| 9.10.0 | `006aa1d8` | `gaRaceLineAI` | FUN_00480730 | HIGH |
| 9.10.0 | `006aa270` | `gaRaceNetworkStarterAI` | FUN_00481af0 | HIGH |
| 9.10.0 | `006aa2a0` | `gaRacePaceNoteAI` | FUN_00481e80, FUN_00482250 | HIGH |
| 9.10.0 | `006aa380` | `Race/SplitTime%d/Car%d` | FUN_00482910, FUN_004af7f0 | HIGH |
| 9.10.0 | `006aa398` | `Race/Car%d/SplitPoint` | FUN_00482910 | HIGH |
| 9.10.0 | `006aa434` | `gaRaceStartCountdownAI` | FUN_00482fe0 | HIGH |
| 9.10.0 | `006aa4c8` | `gaRaceStarterAI` | FUN_00483e60 | HIGH |
| 9.10.0 | `006aa5a4` | `Race/Car%d/RecordSpline` | FUN_00484730 | HIGH |
| 9.10.0 | `006aa63c` | `gaRaceTimerAI` | FUN_00484df0 | HIGH |
| retail | `006af8a8` | `gaRaceSplitTimeAI` | FUN_00407880, FUN_00486dc0, FUN_004893e0, FUN_0048cb50, FUN_0048d260 | HIGH |
| retail | `006b1dd4` | `Race/GhostPlayback` | FUN_00449100, FUN_0048e9c0, FUN_004a74a0 | HIGH |
| retail | `006e3b2c` | `EditControllergaRacePaceNoteAI` | FUN_00485da0, FUN_00486a20 | HIGH |
| retail | `006e3c44` | `EditControllergaRacePostFirstSplitTimeAI` | FUN_00486cb0 | HIGH |
| retail | `006e3d88` | `gaRacePostFirstSplitTimeAI` | FUN_00486dc0, FUN_00488150, FUN_0048c780, FUN_0048c9a0 | HIGH |
| retail | `006e3e44` | `EditControllergaRaceSplitTimeAI` | FUN_00488370 | HIGH |
| retail | `006e3eb4` | `gaRaceFinishAI` | FUN_004899c0 | HIGH |
| retail | `006e3f68` | `gaRaceFinishAreaAI` | FUN_0048a750 | HIGH |
| retail | `006e3fbc` | `gaRaceLineAI` | FUN_0048acb0 | HIGH |
| retail | `006e402c` | `gaRaceNetworkStarterAI` | FUN_0048be90 | HIGH |
| retail | `006e4044` | `gaRacePaceNoteAI` | FUN_0048c230, FUN_0048c5f0 | HIGH |
| retail | `006e4124` | `Race/SplitTime%d/Car%d` | FUN_0048cd20, FUN_004bc2b0 | HIGH |

### vehicle_physics_damage

| Build | Address | Text | Referencing functions | Confidence |
|---|---:|---|---|---|
| 8.4.1 | `005ea6b0` | `Race/Car%d/SplitPoint` | FUN_004544f0 | HIGH |
| 8.4.1 | `005ea854` | `Race/Car%d/RecordSpline` | FUN_004559c0 | HIGH |
| 9.3.1 | `0066ef18` | `Race/Car%d/SplitPoint` | FUN_0046eac0 | HIGH |
| 9.3.1 | `0066f0f0` | `Race/Car%d/RecordSpline` | FUN_00470560 | HIGH |
| 9.10.0 | `006aa398` | `Race/Car%d/SplitPoint` | FUN_00482910 | HIGH |
| 9.10.0 | `006aa5a4` | `Race/Car%d/RecordSpline` | FUN_00484730 | HIGH |
| retail | `006e413c` | `Race/Car%d/SplitPoint` | FUN_0048cd20 | HIGH |
| retail | `006e4358` | `Race/Car%d/RecordSpline` | FUN_0048eb40 | HIGH |

### ai_opponent

| Build | Address | Text | Referencing functions | Confidence |
|---|---:|---|---|---|
| 8.4.1 | `005e6860` | `gaNetworkManager: UDP listen port (%d) bind failed ` | FUN_0042fbf0 | HIGH |
| 8.4.1 | `005ea4a0` | `gaRaceLineAI` | FUN_00453320 | HIGH |
| 9.3.1 | `00664044` | `gaNetworkManager: UDP listen port (%d) bind failed ` | FUN_00430f20 | HIGH |
| 9.3.1 | `0066eda4` | `gaRaceLineAI` | FUN_0046d760 | HIGH |
| 9.10.0 | `0069a364` | `gaNetworkManager: UDP listen port (%d) bind failed ` | FUN_00431f50 | HIGH |
| 9.10.0 | `0069c858` | `DirectX/Options/DetailPasses` | FUN_0045e060, FUN_0045e400 | HIGH |
| 9.10.0 | `006aa1d8` | `gaRaceLineAI` | FUN_00480730 | HIGH |
| retail | `006b170c` | `gaNetworkManager: UDP listen port (%d) bind failed ` | FUN_00433240 | HIGH |
| retail | `006b4ce8` | `DirectX/Options/DetailPasses` | FUN_00463a10, FUN_00464050, FUN_00577620, FUN_00580360 | HIGH |
| retail | `006e3fbc` | `gaRaceLineAI` | FUN_0048acb0 | HIGH |

### input_controller

| Build | Address | Text | Referencing functions | Confidence |
|---|---:|---|---|---|
| 9.3.1 | `0066e990` | `EditControllergaRacePaceNoteAI` | FUN_00468f70, FUN_00469be0 | HIGH |
| 9.3.1 | `0066eaa8` | `EditControllergaRacePostFirstSplitTimeAI` | FUN_00469e70 | HIGH |
| 9.3.1 | `0066ec54` | `EditControllergaRaceSplitTimeAI` | FUN_0046b320 | HIGH |
| 9.10.0 | `006a9d74` | `EditControllergaRacePaceNoteAI` | FUN_0047bc90, FUN_0047c900 | HIGH |
| 9.10.0 | `006a9e8c` | `EditControllergaRacePostFirstSplitTimeAI` | FUN_0047cb90 | HIGH |
| 9.10.0 | `006aa08c` | `EditControllergaRaceSplitTimeAI` | FUN_0047e250 | HIGH |
| retail | `006e3b2c` | `EditControllergaRacePaceNoteAI` | FUN_00485da0, FUN_00486a20 | HIGH |
| retail | `006e3c44` | `EditControllergaRacePostFirstSplitTimeAI` | FUN_00486cb0 | HIGH |
| retail | `006e3e44` | `EditControllergaRaceSplitTimeAI` | FUN_00488370 | HIGH |

### save_progress_unlocks

| Build | Address | Text | Referencing functions | Confidence |
|---|---:|---|---|---|
| 8.4.1 | `005ea854` | `Race/Car%d/RecordSpline` | FUN_004559c0 | HIGH |
| 8.4.1 | `005f47a8` | `Saved cached image bank: [%s] ` | FUN_0051db40 | HIGH |
| 8.4.1 | `005f48c8` | `Saved cached model: [%s] ` | FUN_00520bb0 | HIGH |
| 8.4.1 | `005f4a20` | `Saved cached texture: [%s] ` | FUN_00521d20, FUN_005220c0 | HIGH |
| 9.3.1 | `0066f0f0` | `Race/Car%d/RecordSpline` | FUN_00470560 | HIGH |
| 9.3.1 | `006735c4` | `Saved cached image bank: [%s] ` | FUN_0051be80 | HIGH |
| 9.3.1 | `006736fc` | `Saved cached model: [%s] ` | FUN_0051f140 | HIGH |
| 9.3.1 | `0067385c` | `Saved cached texture: [%s] ` | FUN_005202b0, FUN_00520650 | HIGH |
| 9.10.0 | `006aa5a4` | `Race/Car%d/RecordSpline` | FUN_00484730 | HIGH |
| 9.10.0 | `006af69c` | `Saved cached image bank: [%s] ` | FUN_0054f240 | HIGH |
| 9.10.0 | `006af7cc` | `Saved cached model: [%s] ` | FUN_00552700 | HIGH |
| 9.10.0 | `006af92c` | `Saved cached texture: [%s] ` | FUN_00553ab0, FUN_00553e50 | HIGH |
| retail | `006e4358` | `Race/Car%d/RecordSpline` | FUN_0048eb40 | HIGH |
| retail | `006e8c18` | `Saved cached model: [%s] ` | FUN_0053c3f0 | HIGH |
| retail | `006e8d9c` | `Saved cached texture: [%s] ` | FUN_0053dcc0 | HIGH |
| retail | `006e9ddc` | `Saved cached image bank: [%s] ` | FUN_00572fb0 | HIGH |

### networking

| Build | Address | Text | Referencing functions | Confidence |
|---|---:|---|---|---|
| 8.4.1 | `005e6630` | `Network/active` | FUN_0042d850 | HIGH |
| 8.4.1 | `005e6708` | `Network/Car7/IpAddress` | FUN_0042f550 | HIGH |
| 8.4.1 | `005e6720` | `Network/Car6/IpAddress` | FUN_0042f550 | HIGH |
| 8.4.1 | `005e6738` | `Network/Car5/IpAddress` | FUN_0042f550 | HIGH |
| 8.4.1 | `005e6750` | `Network/Car4/IpAddress` | FUN_0042f550 | HIGH |
| 8.4.1 | `005e6768` | `Network/Car3/IpAddress` | FUN_0042f550 | HIGH |
| 8.4.1 | `005e6780` | `Network/Car2/IpAddress` | FUN_0042f550 | HIGH |
| 8.4.1 | `005e6798` | `Network/Car1/IpAddress` | FUN_0042f550 | HIGH |
| 8.4.1 | `005e67b0` | `Network/Car0/IpAddress` | FUN_0042f550 | HIGH |
| 8.4.1 | `005e67c8` | `Network/IpAddress` | FUN_0042f550, FUN_00443370, FUN_00443ff0, FUN_0046cff0 | HIGH |
| 8.4.1 | `005e67dc` | `Network/numPlayers` | FUN_0042f550, FUN_004305f0, FUN_00430a00, FUN_00443ff0 | HIGH |
| 8.4.1 | `005e67f0` | `Network/Transport` | FUN_0042f550, FUN_0042fdd0, FUN_00430180, FUN_0046ce00 | HIGH |
| 8.4.1 | `005e6804` | `Network/SyncState` | FUN_0042f550, FUN_0042fdd0, FUN_00430180, FUN_0046cf60 | HIGH |
| 8.4.1 | `005e6818` | `Network/GameToken` | FUN_0042f550, FUN_0042fdd0, FUN_00430180, FUN_0046cf90, FUN_0046cff0, FUN_0046d0b0 | HIGH |
| 8.4.1 | `005e682c` | `Network/Car%d/FinishTime` | FUN_0042fbf0 | HIGH |
| 8.4.1 | `005e6848` | `Network/Car%d/Finished` | FUN_0042fbf0, FUN_00430c80 | HIGH |
| 8.4.1 | `005e6860` | `gaNetworkManager: UDP listen port (%d) bind failed ` | FUN_0042fbf0 | HIGH |
| 8.4.1 | `005e6894` | `gaNetworkManager: UDP listen port (%d) established ` | FUN_0042fbf0 | HIGH |
| 8.4.1 | `005e68f8` | `Network/Car%d/IpAddress` | FUN_004305f0, FUN_00430a00, FUN_00443ff0 | HIGH |
| 8.4.1 | `005e6920` | `FrontEnd/Network/selectedGameType` | FUN_00430a00, FUN_0046cf30 | HIGH |
| 8.4.1 | `005e6958` | `gaNetworkConsole` | FUN_00432e90 | HIGH |
| 8.4.1 | `005e69c4` | `Network/ChatRequest` | FUN_00433380, FUN_00479970 | HIGH |
| 8.4.1 | `005e6a10` | `gaNetworkPositioning: Warning - no peer found for car %d ` | FUN_00434cb0 | HIGH |
| 8.4.1 | `005ea4fc` | `gaRaceNetworkStarterAI` | FUN_004538b0 | HIGH |
| 8.4.1 | `005eb71c` | `FrontEnd/Network/Browse` | FUN_0046ce30, FUN_0046cfc0 | HIGH |
| 8.4.1 | `005eb734` | `FrontEnd/Network/selectedCar` | FUN_0046ced0, FUN_0046d050 | HIGH |
| 8.4.1 | `005eb754` | `FrontEnd/Network/selectedCourse` | FUN_0046cf00, FUN_0046d080 | HIGH |
| 9.3.1 | `00663e48` | `Network/active` | FUN_0042eab0 | HIGH |
| 9.3.1 | `00663f20` | `Network/Car7/IpAddress` | FUN_00430880 | HIGH |
| 9.3.1 | `00663f38` | `Network/Car6/IpAddress` | FUN_00430880 | HIGH |
| 9.3.1 | `00663f50` | `Network/Car5/IpAddress` | FUN_00430880 | HIGH |
| 9.3.1 | `00663f68` | `Network/Car4/IpAddress` | FUN_00430880 | HIGH |
| 9.3.1 | `00663f80` | `Network/Car3/IpAddress` | FUN_00430880 | HIGH |
| 9.3.1 | `00663f98` | `Network/Car2/IpAddress` | FUN_00430880 | HIGH |
| 9.3.1 | `00663fb0` | `Network/Car1/IpAddress` | FUN_00430880 | HIGH |
| 9.3.1 | `00663fc8` | `Network/Car0/IpAddress` | FUN_00430880 | HIGH |
| 9.3.1 | `00663fe0` | `Network/IpAddress` | FUN_00430880, FUN_004479c0, FUN_00448810, FUN_0048b3a0 | HIGH |
| 9.3.1 | `00663ff4` | `Network/numPlayers` | FUN_00430880, FUN_00431a50, FUN_00431f10, FUN_00448810 | HIGH |
| 9.3.1 | `00664008` | `Network/Transport` | FUN_00430880, FUN_00431180, FUN_004315e0, FUN_0048b1b0 | HIGH |
| 9.3.1 | `0066401c` | `Network/SyncState` | FUN_00430880, FUN_00431180, FUN_004315e0, FUN_0048b310 | HIGH |
| 9.3.1 | `00664030` | `Network/GameToken` | FUN_00430880, FUN_00431180, FUN_004315e0, FUN_0048b340, FUN_0048b3a0, FUN_0048b460 | HIGH |
| 9.3.1 | `00664044` | `gaNetworkManager: UDP listen port (%d) bind failed ` | FUN_00430f20 | HIGH |
| 9.3.1 | `00664078` | `gaNetworkManager: UDP listen port (%d) established ` | FUN_00430f20 | HIGH |
| 9.3.1 | `006640ac` | `Network/LostHost` | FUN_004310b0, FUN_00431180, FUN_00465930 | HIGH |
| 9.3.1 | `006640c0` | `Network/Car%d/FinishTime` | FUN_004310b0 | HIGH |
| 9.3.1 | `006640dc` | `Network/Car%d/Finished` | FUN_004310b0, FUN_004321b0 | HIGH |
| 9.3.1 | `00664118` | `Network/Car%d/IpAddress` | FUN_00431a50, FUN_00431f10, FUN_00448810 | HIGH |
| 9.3.1 | `00664154` | `gaNetworkConsole` | FUN_00434630 | HIGH |
| 9.3.1 | `00664178` | `Network/ChatRequest` | FUN_00434bf0, FUN_0049e9b0 | HIGH |
| 9.3.1 | `006641f8` | `gaNetworkPositioning: Warning - no peer found for car %d ` | FUN_00436560 | HIGH |
| 9.3.1 | `00664850` | `Network/Car0/Name` | FUN_00448810 | HIGH |
| 9.3.1 | `00664864` | `Network/Car%d/Name` | FUN_00448810, FUN_00464e00 | HIGH |
| 9.3.1 | `00665e3c` | `Frontend/Network/Checkpoint` | FUN_0045a2c0 | HIGH |
| 9.3.1 | `0066ee18` | `gaRaceNetworkStarterAI` | FUN_0046dd70 | HIGH |
| 9.3.1 | `00670298` | `FrontEnd/Network/Browse` | FUN_0048b1e0, FUN_0048b370 | HIGH |
| 9.3.1 | `006702b0` | `FrontEnd/Network/selectedCar` | FUN_0048b280, FUN_0048b400 | HIGH |
| 9.3.1 | `006702d0` | `FrontEnd/Network/selectedCourse` | FUN_0048b2b0, FUN_0048b430 | HIGH |
| 9.3.1 | `006702f0` | `FrontEnd/Network/selectedGameType` | FUN_0048b2e0 | HIGH |
| 9.3.1 | `0067048c` | `Frontend/Network/CheckpointMode` | FUN_0048bc80, FUN_0048bcb0 | HIGH |
| 9.10.0 | `0069a168` | `Network/active` | FUN_0042faf0 | HIGH |

### developer_debug_cooker

| Build | Address | Text | Referencing functions | Confidence |
|---|---:|---|---|---|
| 8.4.1 | `005e72b8` | `Editing/EditorsOpen` | FUN_004484a0, FUN_004b9560, FUN_004bde70, FUN_004be370, FUN_004bef40, FUN_004c0090, FUN_004c06e0, FUN_004cb1f0, FUN_004cb8a0, FUN_004cbb70, FUN_004cbe40, FUN_004cc1b0, FUN_00507430, FUN_00550a90, FUN_00550c90 | HIGH |
| 8.4.1 | `005ec668` | `DebugWindow/Enabled` | FUN_00484ef0 | HIGH |
| 8.4.1 | `005f23d4` | `DataGame/Test.txt` | FUN_004ef920 | HIGH |
| 8.4.1 | `005f23e8` | `DataGame/Test.xml` | FUN_004ef920 | HIGH |
| 9.3.1 | `00664a90` | `Editing/EditorsOpen` | FUN_0044ed50, FUN_004fa550, FUN_00500940, FUN_00500d40, FUN_00501240, FUN_00502e60, FUN_00503fd0, FUN_00504cf0, FUN_00505370, FUN_00506d80, FUN_0050fa00, FUN_005100b0, FUN_00531740, FUN_00626ca0, FUN_00626ea0 | HIGH |
| 9.3.1 | `00672174` | `DebugWindow/Enabled` | FUN_004aee40 | HIGH |
| 9.3.1 | `0067d04c` | `DataGame/Test.txt` | FUN_00603fc0 | HIGH |
| 9.3.1 | `0067d060` | `DataGame/Test.xml` | FUN_00603fc0 | HIGH |
| 9.10.0 | `0069ae78` | `Editing/EditorsOpen` | FUN_004511a0, FUN_004526d0, FUN_004572a0, FUN_0050fa50, FUN_005160d0, FUN_005166c0, FUN_00516ac0, FUN_00516fc0, FUN_00518e30, FUN_00519250, FUN_00519530, FUN_00519880, FUN_0051a630, FUN_0051ad10, FUN_00525fc0, FUN_00548bd0, FUN_00658880, FUN_00658a80 | HIGH |
| 9.10.0 | `006ad75c` | `DebugWindow/Enabled` | FUN_004c3a00 | HIGH |
| 9.10.0 | `006b8f5c` | `DataGame/Test.txt` | FUN_00635350 | HIGH |
| 9.10.0 | `006b8f70` | `DataGame/Test.xml` | FUN_00635350 | HIGH |
| retail | `006b3090` | `Editing/EditorsOpen` | FUN_00454e00, FUN_004565a0, FUN_0045c420, FUN_00522060, FUN_005274a0, FUN_00527a90, FUN_00527e90, FUN_00528510, FUN_0052a420, FUN_0052a840, FUN_0052ab20, FUN_0052ae70, FUN_0052bc30, FUN_0052c310, FUN_00538a30, FUN_0056b680, FUN_0066c180, FUN_0066c380 | HIGH |
| retail | `006e78f0` | `DebugWindow/Enabled` | FUN_004d7bd0 | HIGH |
| retail | `006ebe84` | `BuildData : MODEL : %s ` | FUN_005b29c0 | HIGH |
| retail | `006ebe9c` | `BuildData : TEXTURE : %s ` | FUN_005b2ad0 | HIGH |
| retail | `006ebeb8` | `BuildData : IMAGE BANK : %s ` | FUN_005b2c40 | HIGH |
| retail | `006ebedc` | `BuildData : DIR : %s ` | FUN_005b2da0 | HIGH |
| retail | `006f2588` | `DataGame/Test.txt` | FUN_005fda00 | HIGH |
| retail | `006f259c` | `DataGame/Test.xml` | FUN_005fda00 | HIGH |

### timing_profiling

| Build | Address | Text | Referencing functions | Confidence |
|---|---:|---|---|---|
| 8.4.1 | `005ea8e4` | `gaRaceTimerAI` | FUN_00455ff0 | HIGH |
| 9.3.1 | `0066f188` | `gaRaceTimerAI` | FUN_00470c20 | HIGH |
| 9.10.0 | `006aa63c` | `gaRaceTimerAI` | FUN_00484df0 | HIGH |
| retail | `006e43f0` | `gaRaceTimerAI` | FUN_0048f200 | HIGH |

### replay_ghost

| Build | Address | Text | Referencing functions | Confidence |
|---|---:|---|---|---|
| 8.4.1 | `005e6fb8` | `Race/GhostPlayback` | FUN_00442220, FUN_00443410, FUN_004559c0, FUN_00469210 | HIGH |
| 8.4.1 | `005ea854` | `Race/Car%d/RecordSpline` | FUN_004559c0 | HIGH |
| 9.3.1 | `006645e4` | `Race/GhostPlayback` | FUN_004464b0, FUN_00447ad0, FUN_004703e0, FUN_004874a0 | HIGH |
| 9.3.1 | `0066f0f0` | `Race/Car%d/RecordSpline` | FUN_00470560 | HIGH |
| 9.10.0 | `0069a998` | `Race/GhostPlayback` | FUN_00448dd0, FUN_004845b0, FUN_0049cfb0 | HIGH |
| 9.10.0 | `006aa5a4` | `Race/Car%d/RecordSpline` | FUN_00484730 | HIGH |
| retail | `006b1dd4` | `Race/GhostPlayback` | FUN_00449100, FUN_0048e9c0, FUN_004a74a0 | HIGH |
| retail | `006e4358` | `Race/Car%d/RecordSpline` | FUN_0048eb40 | HIGH |

## Evidence limits

- A direct string xref proves that code references the literal, not what the surrounding operation does.
- Strings without direct xrefs may be reached through tables, generated keys, or may be retained but unused.
- Library signatures are separately counted and sampled; they are not presented as Master Rallye-specific behavior.
