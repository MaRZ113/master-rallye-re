# Course development-format reconnaissance

This is a path and file-type survey only. Full track reverse engineering belongs to a later phase.

- `demo-8.4.1` contains source-format GXM under `DataGx/Course/France1/France1.gxm` and `DataGx/Course/Italy1/track01.gxm`, plus GXM in multiplayer/test track folders. It also contains many course GXI textures; `DataGx/Course/France1/` alone includes an explicit GXM source.
- `demo-9.3.1` contains no GXM/GXB/GXP paths under course, track, stage, terrain, or road names in this corpus. Its 38 GXP files are frontend resources. This is a path survey; a course asset under an unrelated name could be missed.
- The supplied retail corpus has no GXM/GXI/GXB/GXP files. It retains compiled DX/DXT course assets.

The 29 GXM variants whose post-header section remains opaque include the 8.4.1 course/test resources. Their full structure is deferred; no course parser or writer was started.

Future R5T should use the France1/Italy1 source-era GXM and related test/multiplayer resources as comparison oracles against compiled course assets. This R-DEMO continuation does not parse their opaque post-header sections or begin full track RE.
