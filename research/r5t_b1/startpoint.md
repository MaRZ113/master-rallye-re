# France1 GXM startpoint candidate

## Evidence

The Demo 8.4.1 France1 GXM/TXT pair has a literal `moMesh(Name [startpoint])`
node at ordinal 1, parent 0, with `Index 0`, `Size 12`. Its paired DX is
revision 127. Header word 7 is 49,278 and bounds a finite float3 bank ending
immediately before the TXT-validated object table.

The first eight float3 positions are unique and equal to the eight corners of
a 10-unit axis-aligned box. Their center in the best-matching DX frame is
`(-982.05554199, 53.53905106, 468.66671753)`. It lies 1.559 units from Demo
9.10 France1 RaceTest XML Marker 0. This is spatial evidence, not a direct
reference between the XML record and GXM node.

Across France1, Italy1, and developer Boinds, the strongest global source to
DX transform among all 48 signed axis permutations is `(x, z, -y)`.
Composed with the established DX-to-Blender `(x, -z, y)`, source-to-Blender
identity is a `HIGH_CONFIDENCE_INFERENCE` for this corpus. Per-node transforms,
the meaning of `Index`/`Size`, point/index membership, and box connectivity
remain `UNKNOWN`.

## Blender representation

The existing course panel's **Import GXM Startpoint Point Candidate** operator
adds eight Empty objects to `Course Helpers`. They are points only: it creates
no lines, faces, bounds volume, or gameplay marker. Each point and its
collection retain source hash, node ordinal/parent/span, point index, source
byte offset, and coordinates. The headless Blender 5.2.2 smoke test passed;
no manual viewport/runtime interpretation is claimed.

## Controlled edit prepared

An ignored copy of the paired source changes exactly point 0's X float at
GXM byte offset `10,838,403`:

```text
before: -987.0555419921875  (8e c3 76 c4)
after:  -986.0555419921875  (8e 83 76 c4)
delta:  +1.0 source unit
```

The edit was bounded to the observed first-eight candidate, checked the exact
float preimage, and left all original source files unchanged. The association
of the first eight points with the `startpoint` node is still an inference.

## Controlled 3+3 cook result (R5T-B.1 closeout)

The variance-aware report validates three identical-source baseline runs and
three identical-source modified runs. Across cohorts, the only changed source
input was `France1.gxm`; its recorded change is the single float32 at byte
offset `10,838,403`, source point 0 X from `-987.0555419921875` to
`-986.0555419921875` (+1.0).

All six cooked DX files parse as revision 135 and pass render/index validation.
Render prefix size, vertex count, triangle count, and draw count vary between
cold cooks. The extracted raw tag100 region is 10,118,248 bytes in each run.
All three baseline regions have SHA-256
`9a3ea51096fc24ab82689ac929951cf8ba3291f3dc9d688fb95365383ef5a7d7`; all three
modified regions have SHA-256
`c89654dbf502de96df366d05ecdd87051b0051e8308851550c0e0b6d37c23086`. This is
`CONFIRMED_BY_SOURCE_COMPILED_PAIR`: the isolated source edit reproducibly
changes course DX tag100 despite natural render variance.

The owner reports the course loaded in Demo 9.10 and no obvious starting-grid
or other gameplay difference. This is `CONFIRMED_BY_RUNTIME` for that
observation. Since only one corner moved, this does not establish whether a
whole startpoint volume controls spawning or another runtime behavior. The
startpoint-to-first-eight-point binding remains a `HIGH_CONFIDENCE_INFERENCE`.
