# Physics commit probe — validation

**`PHYSICS_COMMIT_PROBE_READY`, build/static verification only.** The accepted earlier runtime is reused; no new game session or write-enabled teleport test was run.

- `python modernization/renderer/tools/build.py`: Win32/x86 Release built successfully; its native CTest target passed **18/18** suites, including physics capture, RaceLine, getter ABI, camera/bookmarks/Clean View, race lifecycle, UI/quality, reflections, COM identity and compatibility contracts.
- Full renderer Python after the final test changes: **173/173 PASS**, 118.715 s.
- Root synthetic: **630/630 PASS**, 20.590 s. External `TEMP/TMP=D:\Temp\MRR-physics-commit-root` preserves the extraction-boundary contracts. Renderer test scratch remains ignored under `.analysis/physics-commit-python-temp`.
- Exact retail PE integration: **5/5 PASS**; seven existing complete hook contexts, four call targets, complete getter body and the newly pinned stock publication/timer branch sequences match pristine `.text`.
- Built-DLL disassembly: **3/3 PASS**; getter argument forwarding/`ret 4` and all three unchanged clear bridges' callback/replayed-store contracts match the production PE/linker map. The accepted native getter ABI harness also passed in CTest.
- Offline analyzer: five regression tests passed in the renderer suite. Applying it to the accepted saturated session yields `NEEDS_CLEAR_ATTRIBUTION_CAPTURE`, `legacy_capture=true`, `capture_loss_or_overlap=true`, no clear candidate and no teleport authorization.
- `python -m compileall -q modernization/renderer`: PASS.
- Proxy verifier: valid PE32/I386, required exports `Direct3DCreate8`, `ValidatePixelShader`, `ValidateVertexShader`; imports bcrypt, USER32, KERNEL32, no recursive `d3d8` import.
- `git diff --check`: PASS; only existing CRLF conversion warnings. New source/docs are restricted to `modernization/renderer/`; the changed-file list is in `physics-commit-probe.json`.

DLL: `D:\Game\Master Rallye\master-rallye-re-general\modernization\renderer\.build-msvc\Release\d3d8.dll`.

SHA256: `479a82b8a0c59ed7cf4f93b2fde011fd5f9b36781ae4f3b63ae0118155300cc9`.

Size: **2,133,504 bytes**. DLL remains ignored and was not deployed into the game directory. The pristine EXE hash was checked again after analysis and is unchanged.

The handoff ZIP contains the current renderer source, native/Python tests, build/tools/vendor headers, configuration example and selected current A3j documents. It excludes generated binaries, runtime JSONL, old handoff archives and reverse scratch/databases. It includes the current production baseline rather than restoring an old archive. Root synthetic tests remain in the main repository. Package integrity is checked separately; package integrity is not runtime evidence.

Starting/ending HEAD: `676ed24b2d32543c3b9356ed359e280f2b36a309`, branch `master`. Existing dirty work is retained; no staging, commit, new branch/worktree or push was performed. Human handoff and the precise remaining commit invariant are in [physics-commit-probe.md](physics-commit-probe.md).
