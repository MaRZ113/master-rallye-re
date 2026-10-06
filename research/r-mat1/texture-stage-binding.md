# Fixed texture positions, environment states, and NULL

## Complete binding chain — CONFIRMED_BY_EXE

1. `005528B0` resolves the ordered texture strings into material+38/+3C/+40.
2. `00577620` appends exactly four positions to compiled+2C/+30. Position0 is
   material+38 if mask01, otherwise zero. Position1 is +3C if mask04 and
   Reflections>0, otherwise zero. Later positions concern unobserved vehicle
   detail/water features and are outside this closeout.
3. Base pass constructor `00586560` calls `005A29F0(1,1,1)` and sets pass+18
   mapping0=0. Env constructor `005860A0`, reached by `00585EB0`, calls
   `005A29F0(2,1,3)` and sets mapping0=0, mapping1=1. Both source UV mappings
   at pass+10 select UV0. Env virtual table 0069270C has method 00586150;
   base table 00692714 has method 005867A0.
4. `00576970` indexes the compiled vector through those mapping bytes, resolves
   a texture resource pointer, and substitutes zero for an empty handle/pointer.
   It passes the loop's stage index and that pointer to `00564EE0`.
5. `00564EE0` calls device vtable+F4 with `(device, stage, texture)`.

There is no compression of empty positions and no first-non-NULL fallback.

Focused assembly from `00576970`:

```asm
00576AAC MOV EAX,[EBX+2C]             ; compiled binding vector
00576AAF XOR EDX,EDX
00576AB1 MOV DL,[ECX+EDI+18]          ; pass binding map[stage]
00576AB5 MOV EAX,[EAX+EDX*4]          ; mapped handle
; the NULL branch:
00576AFF PUSH 0                      ; NULL texture pointer
00576B01 MOV ECX,[ESI+1C]             ; texture-binding wrapper object
00576B04 PUSH EDI                    ; stage index is retained
00576B05 CALL 00564EE0                ; SetTexture(stage,NULL)
```

The executable object/compiled binding/pass mapping are separate structures:
material+38 is the first raw handle, while compiled+38 is the shader pointer.
Conflating these offsets would break the proof. Full instruction addresses and
p-code are in the hash-indexed local exports for the five steps above.

## Texture-stage state — CONFIRMED_BY_EXE

Stage0, both methods: COLOROP4 MODULATE(TEXTURE2,DIFFUSE0), ALPHAOP4
MODULATE(TEXTURE2,DIFFUSE0), TEXCOORDINDEX0, texture transform disabled.
Environment stage1: COLOROP18 MODULATEALPHA_ADDCOLOR(CURRENT1,TEXTURE2),
ALPHAOP4 MODULATE(CURRENT1,TEXTURE2), TEXCOORDINDEX0x10000
CAMERASPACENORMAL, TEXTURETRANSFORMFLAGS2 COUNT2. These are camera-space
normals, not a reflection-vector mode.

Env constructor `005860A0` writes a matrix at pass+24, with M11=M22=0.5,
M41=M42=0.5, M33=M44=1 and remaining terms zero. Thus the projected XY
coordinates are cameraNormal.xy*0.5+0.5. With saturating fixed-function stage
results, the relevant equations before framebuffer blending are:

```text
C0 = texture0.rgb * diffuse.rgb; A0 = texture0.a * diffuse.a
C1 = C0 + A0 * texture1.rgb;     A1 = A0 * texture1.a
```

The operation expression follows the official
[MODULATEALPHA_ADDCOLOR definition](https://learn.microsoft.com/en-us/windows/win32/direct3d9/d3dtextureop).
The actual integer IDs and arguments come from the traced executable.

Reflections OFF suppresses both env family selection and compiled binding1;
it does not rewrite serialized slots or mask. The typed model accepts an OFF
projection and the preview cache accepts `reflections=False`.

## Verified NULL-base records

| Resource | Draw | Slots 0 / 1 / 2 | Flags | Mask | ON family |
|---|---:|---|---|---:|---|
| KiaSportage/car.dx | 11 | Null / perspex-tga / Null | 00000101 | 6 | base_env |
| KiaSportage/complete.dx | 6 | Null / perspex-tga / Null | 00000101 | 6 | base_env |
| Pajero/complete.dx | 22 | Null / glass-tga / Null | 00000101 | 6 | base_env |
| IceCream/car.dx | 3 | Null / Null / Null | 00000100 | 2 | base |
| IceCream/complete.dx | 3 | Null / Null / Null | 00000100 | 2 | base |

For the first three, stage0 is explicitly NULL and stage1 is still bound to
its helper with ON family base_env. With OFF, family base is selected and
binding1 is zero. **No promotion is CONFIRMED_BY_EXE.**

The official fixed-function
[NULL texture cascade rule](https://learn.microsoft.com/en-us/windows/win32/direct3d9/texture-blending)
says a NULL texture with COLORARG1=TEXTURE terminates that stage and higher
stages. Applied to this D3D8 shader, diffuse-only output and suppression of the
env contribution are **HIGH_CONFIDENCE_INFERENCE**, not a newly observed
Master Rallye pixel result. Blender implements that conservative approximation
and records this exact distinction in `null_slot_behavior`. Textureless draws
preview vertex diffuse; none use a helper as their base image. This is not proof
of authorial intent or a universal engine-wide slot2 rule.
