# PS2-REFL1 findings

The principal vehicle path is **mixed static image plus framebuffer feedback**,
sampled using transformed source normals. It is executable-backed, not inferred
from texture filenames. The body and glass paths differ in source and GS blending.
See [final report](final-report.md), [render contract](render-contract.json) and
[function inventory](elf-functions.json). Runtime validation is NOT_PERFORMED.

## Principal evidence

| Finding | Evidence |
|---|---|
| Tata and Kia visual tag2 meshes actually carry carshiny/carglass/carflat | CONFIRMED_BY_BOTH; vehicle-evidence.json, 391d38/390d98 |
| carshiny writes mode3 and replaces the secondary map, except the resolved name containing `rubber` | CONFIRMED_BY_EXE; 3ade58 |
| carglass/carsglass write mode20 and WINDSCREEN-REFLECT | CONFIRMED_BY_EXE; 3ae040/3ae0c8 |
| Actual render target writer combines ENVSOURCE and framebuffer | CONFIRMED_BY_EXE; 330780 ->31a518 twice |
| Shared update guard reset, first eligible object, split-screen exclusion | CONFIRMED_BY_EXE; 32f988/330780, globals42dd34/38 |
| Secondary UVs use local normal and object/view orientation; no reflection vector in selector1 | CONFIRMED_BY_EXE; VU408,2cf,30e,41c,430 |
| Body RGB is prepared from local normal Y, not a view/light specular equation | CONFIRMED_BY_EXE; 322220; empty frame auxiliary3223f8 |
| Body environment color is added with FIX128; glass highlight with FIX96 | CONFIRMED_BY_EXE; 312610 modes3/20 and decoded ALPHA selectors |
| GS templates and CPU VIF1 DMA chain are connected to the vehicle mesh cache | CONFIRMED_BY_BOTH; tag2 ->3714e0 ->3bca80 ->31d250/31cd98 |
| Live target contents, VU residency and visible pixel parity | UNKNOWN; no trusted running PCSX2/debugger session |

## Five required causal chains

Every parenthesized transition below identifies supporting executable/data evidence.
These are static execution contracts, not captured live frames.

**A — Vehicle material**

```text
Canonical TATA/CAR.PSM root.3, material offset170849
 -> owning tag2 mesh and eight authored strips (original bytes,391d38)
 -> $shader(carshiny) (390d98 extraction,391690/3a6c58 registry)
 -> mesh+28=3 and secondary target (3ade58, verified vtable487ee8+14)
```

**B — Resource**

```text
CommonTextures\rendertarget64x64 (canonical GXI; resource-evidence.json)
 -> 2fd7d0 name/root GXI lookup and cache (shared verified loader)
 -> mesh+e4 handle (3714e0 binds mesh+38)
 -> 3bca80/31d250 queued second texture
 -> 312130 secondary TEX0;312610 mode3 combination
 -> VIF/GIF state and strip queue (31e6a8/31d7c8)
 -> live TEX0 contents at a selected frame: UNKNOWN LINK
```

**C — Environment source**

```text
ENVSOURCE64X64 GXI ->2fd7d0 handle49b388 (330780)
 -> cached GS descriptor42ea88 (2fa058)
 ->31a518 first textured-sprite pass, target49b380, FIX80,D=zero
Current framebuffer42d298 ->31a518 second sprite pass, flipY,FIX48,D=destination
 -> target FRAME writes and texture flush (31a518)
 -> same cached target name used by carshiny (3ade58/3714e0)
 -> live source-frame identity / actual VRAM allocation: UNKNOWN LINK
```

**D — Coordinates**

```text
PSM normal+0 -> runtime48+0 -> cached64 qword0 (3900f0/31f4e0)
Object matrix inputs -> cache+70/+30 (3628c0) ->42e230/270 (3432b8)
Camera position/basis -> view matrices (3387c8,36fc18/36fb28)
 ->42e2b0/2f0 (343458)
 ->317770/317470 VIF matrix packets -> VU2cf/30e
 -> interpolated matrices and product (41c/430)
 -> normal dot, scale(+.5,-.5),bias(.5,.5) (408)
 -> source UV qword xy retained, environment zw replaced
 -> actual live interpolation state319.w: UNKNOWN LINK
```

**E — Rendering**

```text
Vehicle tag2/strip -> mesh cache31f4e0
 -> queued handles/mode3 or20 (3bca80/31d250)
 -> GS templates and selector1 (31cd98/312610)
 -> selector packet31af50 MSCAL36a, state MSCAL37c/377,
    cached strip REF/UNPACK/MSCAL00f (31d7c8/31e010)
 -> matching uploaded program, normal UV helper408 and GIF/XGKICK
    (initialization callsite311370 ->317208 ->DMA CALL442170; original MPG hashes)
 -> frame ring316b88 ->30ea80 ->VIF1 QWC/TADR/CHCR
 -> live VU program residency / visible frame: UNKNOWN LINK
```

## Scope of negative evidence

No separate reflection-camera scene capture or cube-map construction is present
in the traced feedback producer. This does not rule out unrelated effects.
STATICRENDERTARGET64X64 has no consumer in the selected path or 29-CAR name survey;
its purpose elsewhere remains UNKNOWN. Chrome-named Kia secondary data is replaced
by the same body target, rather than proving a dedicated chrome shader. The
survey also retains the original `crashiny` spelling as an untraced token.

The PC comparison separates original native CAMERASPACENORMAL from proxy
REFLECTIONVECTOR experiments. Neither platform's screenshot supplies an algorithm.
