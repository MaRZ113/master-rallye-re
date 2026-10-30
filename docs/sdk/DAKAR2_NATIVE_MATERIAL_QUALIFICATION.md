# Dakar 2 Xbox native material qualification

30 October 2026. Cross-game material milestone, baseline `e7353076512431b5ec71456bde9c2d203eb77336`. This extends the accepted renderer investigation; it does not repeat disc discovery, alter an original scene, install a native vehicle or allocate a CarID.

## Outcome

**Material-level L3 remains BLOCKED for Pajero, Nissan Pickup and Hino.** The blocker is now a decoded, reproducible source-material requirement rather than a generic statement that the engine uses several textures. The original three-map shader adds a secondary color contribution through a separate texture's **alpha mask**. It cannot be replaced with diffuse-only MR paint, even though all 132 present UV1 arrays equal UV0. Original shader coordinate outputs, lighting inputs, runtime constant state and conditional coverage remain unresolved. No native fixture is presented as qualified by discarding those inputs.

Actual implementation is `src/master_rallye/source_adapters/dakar2_materials.py`: a bounded 60-DWORD record decoder, typed stage/input/output/constant inspection, independently written arithmetic evaluator, exact per-draw resource qualification and a non-omittable native-requirements contract. `tools/qualify_dakar2_materials.py` checks all three scenes independently and writes private original-binding diagnostics. Existing source semantics and shared native bridge remain the integration boundary. No second compiler or GPU emulator was introduced.

## Original executable evidence

The exact Xbox `default.xbe` SHA256 remains `715db4e407b38c0a6d14ea0ee9d08ebc524b9ece92ceeaa70b5fb81a5ec32378`. Existing Ghidra `Dakar2Xbox` / `mapped-xbe.bin` was opened **read-only**, without analysis or project changes. New exports are in ignored `scratch/cross-game-materials/`. Existing isolated Capstone 5.0.9 independently decoded original x86 bytes. Four sampled ranges (pixel upload, shader dispatch, texture binding and draw binding) match the existing Ghidra mapped input byte-for-byte; original section file offsets and hashes are retained privately.

| Original path | Newly qualified interpretation |
|---|---|
| `0x8b590` | Original submesh texture fields `+0x10/+0x14/+0x18/+0x1c` bind slots 0/1/2/3 independently. Binding four fields does not make all stages active |
| `0x8b360` → `0x8d930` → `0x8cba0` → `0xe6210` | Declaration-selected original pixel definition reaches the original shader upload, alongside declaration-specific blend mode and vertex-program composition |
| `0xe6250` | Copies definition words 0–7 to NV097 combiner alpha inputs; 10–41 to constant/alpha-output/RGB-input registers; word42 to compare mode; words45–53 to RGB output/count registers. Words8/9 determine whether the final combiner is emitted. Both selected source definitions have no final combiner |
| `0x8aed0` | Texture flags' low two bits select original per-stage U/V address modes (native values 1 or 3). Parameter2 in the vehicle draw enforces this path. This does not qualify complete filtering, mip bias or shader coordinate generation |

The independently corroborated record layout matches the [Cxbx shader definition](https://github.com/Cxbx-Reloaded/Cxbx-Reloaded/blob/master/src/core/hle/D3D8/XbD3D8Types.h) and register encodings match [xemu's NV2A combiner definitions](https://github.com/xemu-project/xemu/blob/master/hw/xbox/nv2a/pgraph/psh_regs.h). These primary implementation references were inspected, not vendored. Cxbx is GPL and the inspected xemu file LGPL; no implementation from either project is copied into SDK sources. Decoder logic here is independently authored from the original data/consumer evidence and factual field encodings.

## Exact selected source rules

| Declaration keys | Pixel definition | SHA256 | Active texture modes | Algebraic result |
|---|---|---|---|---|
| `8`, `0x13` | `0x192148` | `94e33836ca5d7b6175ec1bc33333040eb542344050926f698eb24db1c2289327` | Stage0 PROJECT2D; 1–3 NONE | RGB = T0.rgb × V0.rgb; alpha = T0.a × V0.a |
| `0x51a08`, `0x51a13` | `0x192058` | `b4d026c37798c08c645d85af06cc7a21d4e2ce2dfd3fa7a321b74be2e6eab2ea` | Stages0/1/2 PROJECT2D; stage3 NONE | RGB = clamp(T0.rgb × V0.rgb + T1.a × clamp(T2.rgb × C0(stage1).a)); alpha = T0.a |

These are pointwise combiner relationships, subject to original stage saturation and precision; they do not reproduce complete Xbox rendering. T0–T2 mean **vertex-program-selected samples**, not an assertion that all are sampled at raw UV0. V0 means **vertex-program output**, not an unqualified alias for original BGRA stream3. Original source vertex colors and both UV arrays remain intact.

The four-combiner path proceeds:

1. RGB stage0 writes T0 × V0 to R1.
2. RGB stage1 writes T2 × C0(stage1).alpha to T2.
3. RGB stage2 writes T1.alpha × T2 + R1 to R0. In particular, T1 RGB is not the additive multiplier. Its alpha is a required mask.
4. Alpha stage3 replaces earlier scratch alpha with T0.alpha. Thus additive RGB must not leak into output alpha.

Embedded stage1 C0 is ARGB `0x59000000`, alpha 89/255. Its software constant mapping selects constant0. That establishes the embedded value and possible update mapping, **not proof that the running game modifies it or that every draw uses 89/255**. The arithmetic evaluator requires an explicit supplied value for mapped constants; it will not silently use this initial byte as an authoring bake coefficient.

The evaluator supports only the multiply/sum/identity output subset needed for these definitions, normalized supplied inputs and explicit constants. It rejects missing stage inputs, nonfinite values, active unknown operations, final combiners and dot/mux/bias/scale output flags. It is a floating-point diagnostic reference, not bit-exact NV2A precision, a texture sampler, vertex-program emulator or source runtime evidence.

## Three independent source cases

| Source | Original draws | Triangles | UV1 present / exact raw UV0 aliases | Simple / three-map draws | Native material result |
|---|---:|---:|---:|---:|---|
| Pajero `PAJERO_HI_0_0.LOD` | 56 | 4154 | 42 / 42 | 14 / 42 | BLOCKED |
| Nissan `NISSAN_HI_0_0.LOD` | 51 | 4065 | 43 / 43 | 8 / 43 | BLOCKED |
| Hino `HINO_HI_0_0.LOD` | 47 | 4676 | 47 / 47 | 0 / 47 | BLOCKED |

Every draw report records original node, mesh/material ID, member hash, submesh byte offset, triangle count, all four original resource IDs/bindings, decoded texture hashes, shader/vertex-program identity, exact UV-stream alias finding, blend, depth write, pass/order, cull inference and unknown alpha test. No named body, window, rim, tyre, cabin, lamp or equipment group is silently exempted. Original source labels remain evidence, not automatic semantic ownership. Pajero's three internal spare-wheel nodes remain original independent groups. Nissan's qualified nonidentity node transforms are retained. Hino's distinct body/cabin/wheel resources remain independent; dedicated truck physics/collision/suspension are unrelated additional native requirements.

Private evidence root: `.research-output/vehicles/cross-game-materials/dakar2/final/`. It contains `native-material-evidence.json`, each selected original member's `qualification.json` and `stage-bindings.png`, and deterministic `summary.json`. Shader words and donor pixels remain private. Public source-only deliverables contain decoder/tests/documentation, not these payloads. Stage atlases show original decoded alpha over grey; they are texture diagnostics, not Xbox runtime screenshots. The coordinated corpus's D3D9 views retain existing L2 WARN source-preview behavior until a qualified shader interpretation can replace it.

## Native translation boundary

No `omit_for_mr` permission is emitted for active stages. `native_requirements()` exposes each material's exact shader hash, required stage indices and blockers, and explicitly forbids treating UV data aliasing as shader equivalence. A shared bridge must reject a required source shader even if a caller tries to waive its stage bindings individually.

Before an MR-native material fixture can be qualified, evidence must establish:

1. The selected/composed vertex program's V0 lighting and output texture coordinates for each active stage, including any normal/view-dependent T2 generation.
2. Whether constant0 is updated by the game and its effective per-draw value; the original embedded 89/255 alone does not answer that question.
3. Exact alpha-test activation/equipment branches and verified glass/lamp/opaque ownership. Original GREATER100 mechanism remains known, activation is not globally asserted.
4. A supported translation that retains the required additive mask/map effect, or a narrowly justified approximation that is visibly identified and does not lose required coverage or lamp semantics.

Source texel alpha is not interpreted as generic window opacity, paint alpha or a brake switch. No global no-cull repair, polygon reversal, two-sided native override, native damaged-glass invention, universal diffuse-only policy or fragmented reflection selection is authorized by this report. Paint/decals, tyres/rims/interiors, glass/lamps, cabin and equipment remain BLOCKED where their required source shader behavior is unresolved. Source material readiness does not imply physics, collision, suspension, native assembly or gameplay readiness.

## Reproduction and validation

```powershell
$env:PYTHONPATH='src'
python -m unittest tests.synthetic.test_dakar2_materials -v
python tools/qualify_dakar2_materials.py --xbox "E:/RallyWorkshop_Sources/sources/Dakar 2 Xbox/Dakar 2 - The World's Ultimate Rally (USA).iso" --scene .research-output/vehicles/dakar2-fidelity/final/PAJERO/scene/scene.json --scene .research-output/vehicles/dakar2-fidelity/final/NISSAN/scene/scene.json --scene .research-output/vehicles/dakar2-fidelity/final/HINO/scene/scene.json --output .research-output/vehicles/cross-game-materials/dakar2/fresh-run
```

Fresh output is mandatory and must be disjoint from all original source scenes/disc roots. Eleven source-free tests pass: additive secondary inputs survive UV aliasing, T1 alpha is distinguished from T1 RGB, output alpha remains independent of additive RGB, mapped constants cannot silently become embedded defaults, missing inputs/reserved operations/allocation errors are rejected, provenance/binding mismatches fail, and no automatic native or L4 promotion occurs. Original source scenes and all accepted native builds remain unchanged. Full coordinated Windows and corpus/preservation results are recorded in the milestone delivery ledger.
