# Vehicle draw and VU submission contract

The vehicle path is linked to shared WATER1 infrastructure through actual mesh
fields and callers. It is not attributed to water merely because its textures
also use two passes.

`391d38` owns vehicle tag2 strips. `390d98 ->391690/3a6c58` applies carshiny or
carglass, writing mode3/20 and secondary name. `3714e0` binds primary/secondary
handles at mesh+dc/+e4. `31f4e0` prepares64-byte cached vertices:

| Qword | Data |
|---|---|
|0|Source normal.xyz and original primitive-control data|
|1|RGBA float32, source byte components multiplied by0.5|
|2|Primary UVxy; selector1 replaces secondary zw|
|3|Position XYZW|

`3bca80` resolves cache/texture handles and calls queue31d250. `31cd98` consumes
the queued mesh, establishes mode through312610 and primary/secondary textures
through311c50/312130. State producers31e478/31e6a8 use MSCAL37c/377. The mode3/20
selector is1 at42de60;31af50 supplies MSCAL36a. Strip producer31d7c8/31e010
builds REF/UNPACK commands (four qwords per cached vertex), then MSCAL00f.

Transform revision helper31c228 invokes317470/317770 for view/object matrix
packets (MSCAL30e/2cf). Original embedded entry00f dispatches selector1 to408;
the normal formula modifies qword2 before projected STQ/color/XYZ output. GIF
streams include primary then secondary context state/geometry for this material.
This proves local packet ordering, not that every body/glass draws after every
opaque scene object.

## Program provenance

Renderer initialization contains the original JAL at311370 targeting317208;
the containing function entry is not claimed here. That producer emits a DMA CALL to
442170, whose original five MPG commands upload the embedded VU1 program at
micro-PC0,100,200,300,400. Original instruction hashes were freshly recomputed
and equal WATER1's proven chunks; the addresses/hashes are included independently
in elf-functions.json. This study separately connects vehicle selector1 and
matrix packets to408/2cf/30e. The normal helper is in the final400 chunk.

The embedded strip output has XGKICK at00fa; source word mapping is from the MPG
chunks, not a guessed CPU address. The sprite copy path uses373 then the copy /
buffer-flush helper with XGKICK3d7. These compatible embedded operations and
their upload producer are proved statically. The live micro-RAM entry/residency
and real frame packet contents are not captured.

## Final CPU submission

`316b88` seals/flips the frame-chain ring associated with42da10; `30ea80` consumes
the corresponding descriptor via42da12. Original stores set VIF1 QWC10009020=0,
TADR10009030=current chain and CHCR10009000=145. Target-generation and vehicle
producers append to the same42d690/e0 descriptor family. This is a concrete
CPU-to-VIF1 chain, not only a standalone compatible VU file.

Report the boundary as EMBEDDED_PROGRAM_CONFIRMED, UPLOAD_PRODUCER_CONFIRMED,
CPU_PACKET_CONTRACT_CONFIRMED, LIVE_RESIDENCY_UNKNOWN, LIVE_FRAME_NOT_CAPTURED.
The last two are never upgraded by an offline decoder or synthetic normal test.
A global renderer or complete unrelated VU/GS reverse was not attempted.
