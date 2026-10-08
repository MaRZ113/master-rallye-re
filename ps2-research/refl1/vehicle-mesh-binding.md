# Vehicle PSM to visual mesh binding

REFL1 reuses WATER1's proven file vertex and tag2 mesh reader, with two explicitly
decoded additional vehicle wrappers. It does not decode a vehicle collision
trailer or assume all PSM hierarchies equal a landscape.

| Structure | File representation | Executable |
|---|---|---|
| Header |d00d/2/539; source vertex count+28, data begins+32|38fac0/3900f0|
| Source vertex |52bytes: normal xyz+0, control+12, color word+16, UVs+20, XYZW+36|3900f0 creates48-byte runtime vertex|
| Tag2 |Three map slots, material name, opaque fields, strip vector, child count|391d38 creates mesh and records strip ownership|
| Strip |u32first,u32count,u8flag,float32scale; contiguous vertex range|391d38; mesh+74 vector|
| Tag7 |u32 raw byte count; raw ASCII; u32 name index only if count>0; children|391d38 case7; not the general u32/u16 string grammar|
| Tag8 |u32 selector followed by children|391d38 case8|
| Vehicle visual terminal |101 at exact tree end|Observed both original CAR.PSMs; trailer remains unparsed|

General material strings use u32 length/u16 repeated length and ASCII, unlike
tag7's raw name. Tag7 names/indexed children register conditional model subsets;
they contain no new transform matrix in this grammar. The original loader places
named children in model-owned state (+40/+44 associations). Activation and LOD
are not reconstructed from a name count.

For each selected material, `vehicle-evidence.json` commits its node offset,
material offset, texture slots, original strip offsets, compact counts and model
bounds. Full proprietary vertices and mesh dumps stay ignored. Independent checks
verify the tag2 word, the literal original material bytes and frozen face counts,
rather than generating the expected stream with the new parser.

Tata root.3 at170755 owns material170849 `$shader(carshiny)`, eight strips and57
nonsuppressed, nondegenerate source triples. Kia root.4 at186053 owns
material186148 of the same shader,27strips and522 triples. Tata root.0 has
carflat and579 triples: a same-model negative control. These are actual visual
source strips, not spatial/collision triangles.

`mesh_triangles` reuses the original newest-vertex control-bit0 suppression.
The area cutoff1e-7 and shared-edge coordinate rounding1e-4 are declared host
diagnostic tolerances. Winding/back-face selection and simultaneous named-child
visibility are not reconstructed. The total2016 Tata /2289 Kia source triangles
includes conditional variants; it is not the number of live vehicle triangles.

Normals and positions are model-local. `3628c0` maintains current transform+30
and conditionally retained orientation+70 from scene-manager matrix+40.
`3432b8` copies those exact rows into the render globals. No source position is
promoted to course-world coordinates without the actual runtime matrix.
