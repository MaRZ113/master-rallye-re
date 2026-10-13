# Executed commands and dependencies

Preflight master HEAD3f837f4ddcb27ee1034a4b0753634c92009360ec, Git status and frozen
renderer tree7f9f5a7d9464b7b86ff09a9bf6c34b7ce341682d recorded. Unrelated prior
uncommitted work preserved. Source/camera/PS2 grass docs and supplied images
inspected; original PC log course certificate and config read-only. No broad
REA/Ghidra pass needed for the already recovered placement contract.

prepare_grass_pilot.py executed twice with canonical PS2 corpus, protected PC
DX/TXT and read-only Course SDK; equal artifact bytes/hash. Actual source roots
remain external; the compact source-contract identifies every input by hash/path.
12synthetic artifact cases ran separately and again in the64-case port suite.
Example regeneration (external inputs required; placeholders are not executed):

```powershell
python ps2-research/pc-port/tools/prepare_grass_pilot.py --ps2-input-root <canonical-disc-root> --pc-input-root <protected-PC-root> --sdk-root <course-SDK> --asset-out ps2-research/pc-port/.assets/grass/Turkey3Grass.ps2grass --report-out ps2-research/pc-port/docs/grass-port1/source-contract.json
```

Actual build setup:
MRR_PS2PORT_BUILD_ROOT=<port>/.build-overlay-grass1-final;
MRR_PS2PORT_REPORT_PATH=<build-root>/build-report.json;
MRR_GRASS_TEST_ASSET=<port>/.assets/grass/Turkey3Grass.ps2grass;
MRR_COURSE_OBJECT_TEST_ASSET=<port>/.assets/course-objects/Turkey3Puddles.ps2obj;
MRR_REFLECTION_TEST_GXI=<port>/.assets/reflection/PS2EnvSource64x64.gxi.
Executed python overlay/build_overlay.py: immutable Git staging, exact patches,
twice-run interface generators, separate Win32 Release builds --parallel1,
24baseline/30PS2CTest, both verify_proxy.py,64Python tests and compileall.

Final log-field clarification rebuilt PS2 in the same verified staging; both
generator checks, all30CTest,64Python, exports and compileall reran. Source/test
hashes matched before/after; the independent baseline DLL/source stayed unchanged.
This final_rebuild is explicit in build-report.json.

git diff --check and frozen/reference status checks executed. Packaging verifies
current/staged sources, exact patch lock, DLL SHA and deterministic ZIP manifest.
Native builds and included tests do not need original source files except the
declared optional original-asset integration cases. Full Python integration needs
verified external staging (MRR_PC_PORT_RENDERER_ROOT). No Blender requirement.

Manual installation, in-game GrassMode0/1 comparison, PCSX2 parity and shader
appearance are pending human steps, not executed commands. Raw meshes, original
images, private point packs, screenshots and capture logs are not in the handoff.
