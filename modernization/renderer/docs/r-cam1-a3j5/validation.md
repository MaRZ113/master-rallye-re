# R-CAM1-A3j.5 — Validation record

## Static target

- `D:\Game\Master Rallye Pristine\MRallye.exe`: 3,121,214 bytes, SHA-256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`, PE32/I386, ImageBase `0x00400000`.
- Native destination callsite: VA `0x004CCD34`, RVA `0x000CCD34`, call to VA `0x004CD200`; complete 31-byte caller context and native `ret 0x0C` are verified by the exact-retail tests.
- Route getter tests verify its retail `ret 4` contract. The built production bridge passes the returned route pointer and saved ESI manager identity to the observer, preserves native return registers/flags, and returns with `ret 4`.
- Hook installation retains exact-build/context gates, thread quiescence, batch rollback, ownership checks, restoration, and module pinning.

## Automated results

| Check | Result |
| --- | --- |
| Win32 x86 Release build and native CTest | **PASS — 21/21** |
| Renderer Python suite | **PASS — 189/189** |
| Root synthetic suite | **PASS — 630/630** |
| `python -m compileall -q modernization` | **PASS** |
| Exact retail identity and native-context tests | **PASS** in renderer suite; retail image hash independently checked |
| Built production bridge disassembly tests | **PASS** in renderer suite |
| D3D8 proxy verification | **PASS** — valid PE32/I386, expected exports, no recursive `d3d8.dll` import |
| `git diff --check` | **PASS**; Git reported CRLF normalization notices only |

The validated local DLL is `modernization/renderer/.build-msvc/Release/d3d8.dll`, **2,217,984 bytes**, SHA-256 `b45d713bbbc6d5a3a36fbfa836e773f7fc735e9093a5cc192495aa367bb38e70`. It is a local build artifact and is excluded from the source handoff archive and Git changes.

## Evidence boundary

- Native call bytes, targets, caller context, PE mapping, and exact executable identity: `CONFIRMED_BY_EXE`.
- Road selection state machine and production x86 bridge contract: `CONFIRMED_BY_SYNTHETIC_TESTS`.
- Prior ordinary stock recovery transaction and native RaceLine snapshot behavior: `CONFIRMED_BY_EXISTING_RUNTIME_RESEARCH`.
- A selected-marker transaction, physical clearance, continued driving, and no-request fallback on this candidate: **RUNTIME_PENDING**. No new in-game run was performed in this phase.

The source handoff archive contains code, tests, and documentation only. It excludes all DLL/OBJ/LIB/PDB outputs, proprietary executables/assets, runtime logs, and reverse-engineering databases.
