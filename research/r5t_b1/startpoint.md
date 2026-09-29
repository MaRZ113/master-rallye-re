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

The edit is bounded to the observed first-eight candidate, checks the exact
float preimage, and leaves all original source files unchanged. The association
of this point with the startpoint node is still an inference. No compiled
effect or runtime movement result is available until the required three plus
three independent cooks are captured and compared.
