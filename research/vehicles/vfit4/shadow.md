# V-FIT4 shadow: native origin and source-bound footprint

Status: source, format and isolated x86 checks pass. Human live race comparison
is pending. No native visual parity or successful live admission of the model
key/bounds guard is claimed.

## Native evidence

Target: original retail `MRallye.exe`, SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
REA Ghidra 12.1.4 confirmed x86 and this digest. REA default analysis completed;
the original executable was never modified.

`00588200` gathers receiver terrain and generates shadow vertices. At
`0058848A` it calls `004F5BC0` with ECX equal to the model node. It reads min
XYZ at returned pointer `+14h` and max XYZ at `+20h`. Original x87 instructions
derive width `(maxX-minX)*1.75`, length `(maxZ-minZ)*1.5`, and the min/max
midpoint. UV is `(localX-centerX)/width+.5` and
`(localZ-centerZ)/length+.5`. Terrain vertices receive `+.1m` Y, and alpha
also depends on receiver height/vehicle orientation. This is a projected soft
blob; it is not the body silhouette cast by a directional light.

`00587DB0` binds shared resource `misc\shadow\shadow`, loaded as the original
`DataGx/Misc/Shadow/shadow.dxt`. The texture is 128x128, black RGB, varying
alpha. No vehicle-specific shadow DX or DXT is used by this route.

`004F5BC0` dispatches service vtable `+30h`. DirectX initialization
`0053F060` installs `0056B680`, vtable `006922C8`; its `+30h` entry is
`0056CFC0`. That implementation looks up the node's resource key at `+0Ch`
using `0054B320`, then returns model-resource `+8`. The key's readable string
is obtained by existing `004D0570`; its table accessor `004D4CD0` bounds-checks
the interned ID. No additional native object layout is guessed by the adapter.

REA evidence records:

- `ev_bc709dc3d781ba2e6f3d6f23e7316287297e8322ee089b6a4e0013c510f26690`: shadow generator pseudocode.
- `ev_dbb6210d6968ffd4110415fafaf19cd545159ab61a5df4af9b545549529701c3`: exact shadow generator assembly.
- `ev_83eda81498a17f3696277d11a28264687e8132dab46f18389a66deae8edb0a53`: shared shadow material/render function.
- `ev_efffa3ab77e5fa56ffeabd1c68faca7b4bccec07f57f75b8ce2f9f2d5493f78d`: DirectX service installation.
- `ev_1bad0f7775b0090283fa2527cf93afb64b34d3b4af5e58e9ca92c71277ef3c88`: resource-name accessor assembly.
- `ev_57281960fa9bf7a863cca5699084d32b9811ae9bcf5294f0f666b75b15a00bd7`: interned-name lookup assembly.

REA did not recognize the small vtable function `0056CFC0` as an existing
function. Complementary Ghidra `Scale1Gt4.java` created its function boundary
only in a read-only copy of the existing analysis project. Its original
instruction bytes and decompilation are retained in ignored
`scratch/vfit4/shadow-bound-provider.txt`. Private REA evidence bundle:
`.research-output/vehicles/vfit4/shadow/rea-evidence-final.json`.
Decompiler output is not original source.

## Measured baseline

These measurements use the requested
`vaudio1/candidate-combined-fitment/runtime/resource-root` Lancer `car.dx`.
They are local-space measurements, not settled race poses.

| Resource | Render X bounds, m | Render Z bounds, m | Marker1339 X bounds, m | Marker1339 Z bounds, m |
|---|---|---|---|---|
| Original Navara | -1.00930 .. 1.02825 | -2.79995 .. 2.34992 | -1.03259 .. 1.02955 | -2.86299 .. 2.37668 |
| Original Pajero | -1.01828 .. 1.01828 | -2.39494 .. 1.91831 | -1.01828 .. 1.01828 | -2.42972 .. 1.94713 |
| Lancer baseline | -.89087 .. .89087 | -2.29199 .. 2.20361 | -1.03259 .. 1.02955 | -2.86299 .. 2.37668 |

The baseline Lancer retains the Navara X/Z metadata exactly. Existing bounds
generation conservatively includes collision representation B, so donor hull
geometry can retain larger extrema even when the body mesh is narrower and
shorter. This is the evidenced origin of the source-space mismatch. Its visible
contribution in a particular race remains a runtime comparison.

Original blob quad is 3.60875m wide, 7.85950m long, centered at
X=-.00152m, Z=-.24316m. The original texture alpha>=32 pixel cell support is
X `[18,111)/128`, V `[16,112)/128`. On flat ground before native height alpha,
that maps to X `[-1.29842,1.32357]`, Z `[-3.19047,2.70415]`.
Rear extent exceeds the render body by .89848m; front by .50054m.

## Controls and correction

Optional `shadow-profile.json` uses policy `body_alpha_support`. It pins source
car DX SHA256 and original shared shadow DXT SHA256. Generation derives a
desired alpha-threshold support from the render X/Z AABB, with explicit per-side
margin, scale and offset. Defaults: alpha32, X margin .05m, Z margin .10m,
unit scale and zero offset. These margins/threshold are author choices,
not recovered factory parameters or a claim of GT4 shadow behavior.

`vehicle_shadow.bind_profile(profile,model_bytes,texture_bytes)` verifies both
identities and returns the derived native binding. Texture support width/height
determines the quad size; native 1.75/1.5 factors are divided out to create the
private shadow-only bounds record. The alpha support's actual pixel center is
accounted for, including the original texture's half-pixel X asymmetry.

For the baseline defaults, alpha>=32 support becomes
X `[-.94087,.94087]`, Z `[-2.39199,2.30361]`; quad size
2.58992m by 6.26081m. Rear support shrinks .79848m, front .40054m.
Original body, wheel positions, physics, collision, damage, materials, UI,
audio and original texture are not rewritten by this correction.

`vehicle_shadow_native.append_shadow(source,image,blob,payload_va,bindings,allocation_size)`
appends code and literals within the existing sealed allocation, preserving the
entire previous payload prefix. It redirects only the shadow caller's getter at
`0058848A`, verified as original `8BCE E831D7F6FF`. Original native getter is
called once, with its original ECX. The wrapper admits only the complete
canonical `vehicles/<family>/car` key, normalized for ASCII case/slash, and all
40 serialized source bounds value bytes. The nonserialized object header is
excluded. The author/compiler must bind the profile to the final emitted DX
and seal its hash; a profile for a pre-edit source is intentionally rejected.

On admission the consumer receives an immutable private bounds record. Unknown
names, complete/wheel resources, changed bounds and null native results return
the original result. Original spatial metadata is never changed, so there is no
collision/culling policy weakening. Source files, global shadow constants and
the shared texture remain intact. Full original native integer registers and
flags are preserved, with only admitted EAX bounds return replaced; no x87
operations are added to the wrapper.

## Reproduce and validation

```powershell
python tools/diagnose_vehicle_shadow.py --model <final-car.dx> `
  --texture <retail-DataGx/Misc/Shadow/shadow.dxt> --family LancerEvo4 `
  --output .research-output/vehicles/vfit4/shadow

$env:PYTHONPATH='src;tools;.;.research-output/vehicles/scale1/python-tools'
python -m unittest tests.synthetic.test_vehicle_shadow -v
python tools/validate_vehicle_shadow_native.py --exe ../MRallye.exe `
  --model <final-car.dx> --texture <retail-shadow.dxt> `
  --profile <shadow-profile.json> --output <private-validation.json>
```

Five source-only synthetic tests pass. Isolated Unicorn x86 validation passes
54 cases: source admission, original passthrough, case/slash normalization,
stock/complete/suffix rejection, null result, every changed serialized bounds
byte, and multiple candidate records with earlier name/bounds mismatches.
The adapter preserves native call count, this pointer, registers, flags, stack
and original bounds memory. The unchanged original instructions
`0058848F..00588514` produce the generated quad/center within 2e-6m.

Forty-nine cases use explicit native resource/name stubs to check preservation
under caller-clobbered state. Five more execute the original `004F5BC0`,
service/vtable `0056CFC0`, `004D0570`, singleton and interned string-table lookup
instructions, with an explicitly initialized singleton/table and a stub only
for backing model-cache `0054B320`. These verify the selected key argument,
returned bounds pointer, string interpretation and passthrough paths. They do
not load a real car resource or establish real model-key resolution, terrain
selection, renderer execution, races, cameras or shadows
under jump/pitch/roll. The profile guard intentionally passes through if live
resource identity/bounds do not match. Verify admission and body/rear footprint
in a controlled live A/B before calling this visually qualified.

Private `shadow-topview.svg` shows the actual shared alpha texture mapped to
both quads, a cyan convex outline of render vertices, and the origin. It is an
offline top projection, not a game screenshot or exact body silhouette.
