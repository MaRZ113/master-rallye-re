# Painted-body computation

Tata and Kia carshiny meshes select mode3 through3ade58, retain the primary paint
texture and generally replace the authored secondary with the mutable target.
The exception is a resolved secondary name containing `rubber`. This is
CONFIRMED_BY_BOTH for the selected meshes, independently of their live visibility.

There are two contributing computations besides source paint pixels.

First, auxiliary327f30/vtable485350 prepares the original runtime vertex color
via322220. For every selected strip vertex:

```text
s = ((0*nx) + (1*ny)) + (0*nz)
gray_float = ((s * float32(.225)) + float32(.4)) * 255
gray = clamp(CVT.W.S(gray_float), 2, 254)
source RGBA8 = (gray,gray,gray,254)
cached float RGBA = source RGBA8 * .5       31f4e0
```

The color writes are runtime vertex+2c..2f, normal source+0. This is a local
normal-Y grayscale gradient, not a recovered directional-light/view specular
equation. Source vertex colors are overwritten by this auxiliary for carshiny
and carflat. Its per-frame auxiliary callback3223f8 is empty; this does not rule
out mesh reload/preparation or other lighting outside the traced path.
CVT.W.S depends on the live FCSR rounding mode, which is not captured. Tests
explicitly supply nearest-even/toward-zero instead of presenting either as a
captured PS2 state.

Second, the normal coordinate helper supplies environment UVzw. GS context1's
primary uses TCC0/TFX0 MODULATE with the prepared RGB; mode3 clears ABE and allows
depth writes. Context2's secondary uses TCC0/TFX1 DECAL and ABE, then ALPHA
0000008000000029:

```text
(Cd - 0) * FIX128 / 128 + Cs = Cd + Cs
```

The environment image adds to the existing base result. It is not multiplied
by the stored GXI alpha or by the primary texture alpha. Color saturation,
PSM conversion, fog and depth acceptance still affect final pixels. The primary
ALPHA44 template is present but does not blend while ABE=0.

Thus the most concrete PS2-versus-PC differences are the framebuffer/static
image mixture, prepared body gradient and the body addition contract. Their
contribution to a particular brighter-looking screenshot is STATIC_INFERENCE
until a controlled draw/frame correlation; no image was tuned as an oracle.
