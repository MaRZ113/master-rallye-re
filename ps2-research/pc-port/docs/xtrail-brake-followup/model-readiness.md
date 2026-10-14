# Separate race, frontend and wheel gates

Race: existing safe body partitions are preserved. Full CAR replacement remains
blocked on current model ownership and damage/wheel/driver transformations, exact
native suppression and restart/resource lifetime. X-Trail remains the first
candidate. A selected vehicle ID or historical draw ordinal is insufficient.

Frontend: the original X-Trail COMPLETE contains 4,636 faces in 24 meshes. The
new F10 observer covers its 24 PC source records, including the normal-only
32-byte layout, but does not replace geometry. The missing chain is:

current CarMover AI / Egg -> en3d -> name/cache -> compiled model -> current VB/IB

The byte-verified observation point is 0x44c4f6: EDI is the CarMover AI (vtable
0x69020c), EBP the current Egg, [EBP+0x50] the en3d state, ESI the requested
vehicle. The model name is en3d+0xc and owned cache en3d+0x74. This point executes
with stable selection; setter 0x4f5b70 only observes changes. A capped x32dbg
observation and targeted cache-consumer trace are the next steps. No persistent
owner hook or speculative structure walk was installed.

Wheels: X-Trail frame 4233 contains four source material ranges under four current,
nonambiguous world matrices, FVF 0x112/stride 32. All 252 PC source faces match PS2.
The rubber groups (72/36/54 faces) must retain their rubber maps. The 90-face rim
matches shape, but PS2 jumpwheel64 texture/UV differs (UV residual 0.17088175).
A model port therefore does not automatically guarantee the correct wheel material.

Current wheel upload/attribute identity and wheel owner/pose lifetime still require
validation. F10 did not contain uploaded vertex/index bytes. No wheel changes or
full frontend/race model replacement are included in this release.
