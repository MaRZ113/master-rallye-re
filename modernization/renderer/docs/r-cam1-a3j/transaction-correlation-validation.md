# Transaction correlation — validation

Status: **TRANSACTION_CORRELATION_PROBE_READY**, build/static/synthetic evidence. No new live game run, deployment, physical teleport or native-hook runtime restoration is claimed.

- Win32 x86 Release: `python modernization/renderer/tools/build.py`, native CTest **19/19 PASS**. Existing 18 suites remain; the added suite exercises the literal production assembly for all seven inline bridges, 128 repetitions each (**896 invocations**), both flag values, observed before/after operands, ESP/register/FLAGS preservation and the restore-path original stack argument/`ret 4`.
- The same production inline exchange function is tested for 6/7/8-byte install/remove, write/flush/protection failure rollback and refusal to overwrite foreign code. The same production capture model tests 522 routine zeros before publication, duplicate active consumers, distinct publication IDs, pointer/race reuse, diagnostic partition isolation, important overflow and matrix digest mutation.
- Full renderer Python: **188/188 PASS**, 149.010 s. This includes **14** transaction analyzer regressions; the affected 14/6/3 analyzer/retail/disassembly tests were rerun after final capture diagnostics changed.
- Root synthetic: **630/630 PASS**, 20.014 s; external TEMP/TMP `D:/Temp/MRR-transaction-root`. Renderer TEMP/TMP is ignored `.analysis/transaction-python-temp`.
- Exact retail `.text`: **6/6 PASS**, SHA/size/base, existing three native callsites/contexts, accepted getter plus new production context arrays, full matrix copier and restore native call target/ret4.
- Built-DLL bridge disassembly: **3/3 PASS**, retaining getter forwarding assertions and strengthening the store test to check all seven production bridges, both observer calls, exact replayed native instructions and relocated callee slot.
- Proxy verification: valid **PE32/I386**, exports Direct3DCreate8=5, ValidateVertexShader=3, ValidatePixelShader=2; no recursive d3d8 import. Compileall and diff check PASS. These checks do not execute game physics or prove destination clearance.

DLL: `D:/Game/Master Rallye/master-rallye-re-general/modernization/renderer/.build-msvc/Release/d3d8.dll`
SHA256: `33303bb4a9bab7b1654f81db3fdacac6aeee54e338e3412dd3ecb5fe40af3a55`
Size: **2,193,408 bytes**. Build identifier: `ROAD-TRANSACTION-CORRELATION-1`.

The accepted session remains uncorrelated: clear -3466.7379 ms relative to the active consumer, later zero +34.6236 ms. New observer state is needed; old captures are not silently upgraded. Installation prerequisites and one-session instructions are in [transaction-correlation.md](transaction-correlation.md).

Starting/ending HEAD `676ed24b2d32543c3b9356ed359e280f2b36a309`, branch master. Existing dirty work remains, no staging/commit/new branch/worktree/push. Phase changes are listed in [transaction-correlation.json](transaction-correlation.json). Source-only handoff/changed-file archives live in ignored `.analysis`; proprietary EXEs, DLL/PDB/OBJ/LIB, logs and reverse databases are excluded.
