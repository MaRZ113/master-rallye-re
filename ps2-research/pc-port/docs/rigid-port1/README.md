# PS2-RIGID-PORT1 preliminary feasibility

Current checkpoint: [native resource/lifecycle follow-up](final-report.md).
The new evidence explicitly qualifies the older stale-cache hypothesis and
adds byte-exact source wire conversion plus a bounded read-only control. The
physical pilot remains disabled until native resource/admission/lifetime gates
pass. Earlier findings below are preserved with their original evidence scope.

Status: **NATIVE_PROP_PATH_FOUND; IMPLEMENTATION_NOT_STARTED**.

The bounded follow-up after Grass2 is closed in `static-followup.md`: native Egg creation, installed collision backend, convex clone/body binding and cleanup conditions are now concrete. The physical port remains **BLOCKED_ON_NATIVE_COLLISION_RESOURCE_AND_OWNERSHIP**; no spawn implementation is supplied.

This is a read-only preparation for the phase after the second grass layer. It does not claim a working physical PC tumbleweed or checkpoint barrel. The PC EXE was opened by REA/Ghidra 12.1.4 and independently decoded with installed GNU objdump 2.46. The original image remains SHA-256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`, 3,121,214 bytes, PE32/i386 at `0x00400000`. No game was launched or process memory changed in this preparation. No baseline, game assets, Course SDK, existing port source or research finding was edited.

## Strongest new finding

The retail PC executable contains a real **gaAiHayBale** native prop path. The absence of `gaAiRigidBody` from the PC XML scan does not mean the PC executable has no rigid-prop capability.

`0x004C9C30` constructs its 0x14-byte owner; factory `0x004C9C60` allocates it. The constructor installs vtable `0x00691470`. The vtable's +0x14 entry is `0x004C9CF0`. Its selected initializer resolves `gaPhysicsManager`, renames the supplied Egg to `HayBale%d`, selects `Misc/Haybale/haybaletest`, adds `AISimulateeTransform` in AI slot 1, and calls `0x0043E2A0` with the same Egg.

The call at `0x004C9E0B -> 0x0043E2A0` is independently verified in original bytes. The latter allocates a 0x1DC-byte physical body, constructs it with the Egg name at +0x5C, appends it to manager +0x28/+0x2C/+0x30, initializes it, calls `0x004FEE10(1)` to construct its integration wrapper, and registers it through collision manager `0x0043A9B0`. `0x0043AC80` resolves the body's entity and calls the currently installed collision service's +0x0C method with entity, body and category. The concrete live service and the successfully attached convex instance have **not** been captured.

Manager `0x0043F960` integrates the nonvehicle body vector using `0x004FDBA0`; `0x0043FA00` includes that vector in contact-accumulator setup and solver helper calls. Manager destructor `0x0043E020` owns destruction of its physical bodies. These observations establish a native candidate path; they do not establish that arbitrary external calls or mid-race object removal are safe.

## First suitable source case

Turkey3 has six authored PS2 tumbleweed Eggs. Fresh PackFS extraction reproduced its XML SHA `7c1c274cd8403bc7fcc2b5e2e8a13e57dccc44dade53a1be57d631ea073e51ce` and source model SHA `eb959250d0bdb6fa051fb69f4a852c4789be200613eb8e90678d36a48ab54bf4` (9,819 bytes). The first exact source identity is `\TNG\DATASCENE\RACETEST\TURKEY3.XML:list:11:egg:13:ai:0`, authored translation `(3213.659912, 43.099998, -155.139999)`, matrix SHA `dbb65381027ae9e1c0d3f76271b1a7bd5eca952dfc03e2094ac290686e99f7dc`.

This initial translation is not guaranteed to remain unchanged: original collision placement can adjust height before later body updates. The selected PSM has 96 visual vertices / 48 emitted visual faces and `bigshrub $shader(treeblend)`, with source texture `shrubtrig2`. Its tag101 convex A has 8 vertices / 12 triangles; B has 26 / 48. The authored mass is 5 and diagonal MOI is (2,2,2). Counts refer to source records and representations, not measured live population.

## Exact implementation boundary

Calling the PC hay initializer verbatim is unsuitable: it **replaces the model with a haybale**, hardcodes mass 350 and MOI (800,2200,2200), and creates the corresponding native shape indirectly through resource ownership. That would not implement the researched tumbleweed.

The smallest defensible architecture is a private, opt-in PS2 prop descriptor plus original visual mesh and tag101 convex data, joined to one native PC Egg/body through the established native prop-registration path. The existing port can supply the visual draw and native-state restoration; it supplies no physical body or vehicle-contact registration. A render-thread sprite collision approximation must not be described as native or original PS2 physics.

Before any spawn, the missing interfaces are:

- an owned PC runtime convex-resource instance made from the verified PS2 tag101 data, with the installed service's attachment and destruction contracts;
- safe Egg creation, name/Broker publication, insertion and selective retirement, without replacing a stock Egg's AI slot;
- a validated physics-thread course-load boundary and body/scene lifetime across restart, race exit and teardown;
- a controlled observation that the original PC solver responds to car contact and publishes the same body's pose to the private visual mesh.

The PC standalone hay collision provides a useful existing-format control (A8/12 and B16/28); its hull does not prove the distinct tumbleweed B26/48 is already loaded or safely writable. Do not insert a new body by writing manager vector pointers directly.

## Recommended bounded next experiment

Trace one native prop registration from entity -> body -> installed collision service -> manager teardown, first using original PC `gaAiHayBale` as the factory/lifetime control. Then validate a private source-convex registration for **one** Turkey3 source identity. Keep original files unchanged, reject unsupported build/course/owner, retire through proved native APIs, and measure one controlled car strike. The exact capture checklist is in `targeted-capture.md`.

Yellow barrels are separate; see `checkpoint-boundary.md`. No barrel physics is inferred from the tumbleweed path.

## Evidence and tool limitations

`pc-native-probes.json` contains original function addresses, complete Ghidra-reported bounds where available, REA Evidence IDs, source hashes and pending links. Ghidra's default analysis did not define `0x004C9CF0`; the entry comes from exact vtable bytes and the selected instructions were independently decoded from the original PE with GNU objdump. No guessed Ghidra function was created. Its 736-byte source window maps independently to file offset 826608 and hashes to `996f359dc25022231ed71820abd09558d525692c9e61445e7248c65993314eab`.

Decompiler pseudocode is generated analysis, not original source. Fields above were checked against relevant original instructions. All new native results are **CONFIRMED_BY_EXE**; the PS2 source facts are **CONFIRMED_BY_BYTES** or reused bounded RIGID1 **CONFIRMED_BY_BOTH**. Runtime validation of the port is **NOT_PERFORMED**.
