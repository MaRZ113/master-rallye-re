# V-MESH4.6 validation and follow-up

Final private candidate: **v46-exp-002**. `v46-exp-001` is retained as a superseded development build; do not use it for the game test.

## Confirmed offline

- 95 focused tests pass. Coverage includes native alpha gates, alpha-test depth/discard behavior, opaque nonreflective trim versus true glazing, donor-wheel topology, outward mirrored frontend wheels, existing geometry/atlas/arch cases and material writer constraints.
- Project validate/build, author bundle verify, runtime prepare/verify and both launcher verification modes pass. No game launch was performed.
- Final candidate ZIP: 355,042,551 bytes, 202 members, CRC PASS; SHA256 `95da414f29c26bd4e27fcfd34af900587d037269b4f728e98d51c73f21f1f848`.
- 3,770 source-face records compared across both frames; maximum before/after position delta is **0**. The 277 cabin records per frame use the existing inset policy; no new inset or vertex repair is introduced.
- In each frame, **126 trim faces switch blend -> opaque**: 22 cowl details, 12 lower-windshield support faces, 92 window-frame faces. All 44 actual pane faces remain blend; 24 masked cabin faces retain blend. Opaque paint/cutout selection stays as in V4.5.
- Role-specific reflection controls are authored in final texture alpha independently of opaque coverage: paint 0.58, trim/interior 0, tail lamps 0.14, wheel disc/sidewalls 0.10. A diagnostic shows these encoded controls, not simulated reflections. Existing helper normalization has shared consumers, as reported by the builder.
- `wheel.dx`: 455 vertices / 684 triangles, 36-segment rebuilt disc. Four embedded frontend wheel copies match the final race mesh within **5.96e-8 m** after hub placement and side mirroring. Maximum radial envelope remains **0.37620 m**, half-width **0.12852 m**. Adding intermediate radial vertices fills the former tyre facets; Y-axis extent rises from 0.37049 to 0.37620 m without increasing the radial envelope.
- Texture-aware fitment: 270,490 visible grid samples, 11,336 masked samples skipped, zero detected tyre/body penetrations at the four H1 hubs. This is a finite grid check with fixed hypothesized hubs, not a proof for moving suspension.
- 1,482 texture footprints checked: mean RGB error **1.46/255**, 16 outliers (V4.5 had 16). The validator now measures opaque RGB independently of reflection alpha; zero-reflection surfaces are not counted as transparent black. Atlas/mask sampling remains approximate.
- Retail EXE SHA256 remains `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. No installed EXE/proxy, Randomizer, Git staging, commit or remote publication was changed by this work.

## Fixed policy versus unconfirmed visual effects

The serialized trim pass, opacity/reflection separation, repeated frontend/race wheel geometry and source-position preservation are verified. Reduction of the photographed windshield/window gaps and bumper/lamp glare is the intended effect and still needs the user's V4.6 game test. Actual geometric holes, transparent sorting and reflection interpolation are not declared fixed. The gold disc is a GT3 texture on reconstructed donor geometry, not a recovered GT3 wheel mesh. Its spoke openings are opaque dark imagery; there is no brake/hub interior through those openings.

## Further possible improvements recorded from the captures

1. If hard patches survive on painted bumper regions, inspect per-surface reflection interpolation/normals and original reflection-shell semantics. Do not reduce the entire body again solely to hide local artifacts.
2. If real edge gaps survive opaque trim, measure source boundary distances and identify missing surfaces before introducing bounded seal geometry. No speculative gap-filling geometry is part of V4.6.
3. Source wheel geometry recovery remains useful: the current private OBJ has zero vertex/face lines. Future complete source wheel inputs could replace the reconstructed disc and allow actual spoke openings.
4. Small logos, decals and seals still expose fixed donor atlas resolution and aliasing. A denser packing or an independently validated expanded texture path would be needed for sharper detail.
5. The visible crew/cabin remain donor-derived. Helmet placement, cockpit detail and windscreen sorting need separate targeted captures if they become the next priority.

## Reproduce the final audit

```powershell
$env:PYTHONPATH = 'src;tools;.'
python tools/validate_vmesh46_candidate.py --stage .research-output/vehicles/vmesh46/v46-exp-002 --before .research-output/vehicles/vmesh45/v45-exp-002 --previews
```

Open `preview/index.html` for labelled body, wheel, window/cowl and reflection-control comparisons. Software output does not reproduce game lighting, environment mapping, mipmaps or complete sorting.
