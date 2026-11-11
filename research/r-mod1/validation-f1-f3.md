# R-MOD1-F1/F2/F3 validation record

Date: 2026-10-10  
Branch: `research/r-mod1`  
Source HEAD: `ea3012a1481cf1d2f8ed3401eedc995c96dbcfb9`  
Retail input SHA256: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`  
Retail input size: 3,121,214 bytes

## Test commands and results

| Command/check | Result |
|---|---|
| `PYTHONPATH=src;tools python -m unittest` on R-MOD1 core, composition, native plan, runtime log, diagnostics and suspended preflight modules | 25 run, 24 passed, 0 failed, 1 skipped (opt-in real suspended child) |
| `tools/r_mod1_core_tests.ps1` | x86 native harness: 257 checks, 0 failures |
| `PYTHONPATH=src python -m unittest discover -s tests/synthetic -v` | 632 run, 631 passed, 0 failed, 0 errors, 1 skipped |
| Skip | `test_exact_retail_mapping_is_verified_before_resume_or_native_writes`; requires `RMOD1_RUN_WINDOWS_PREFLIGHT=1`. Each built candidate separately passed real launcher `--preflight` before native writes and terminated its suspended child. |
| `python -m compileall src tools tests` | Passed |
| `git diff --check` | Passed; only configured LF-to-CRLF notices |
| Candidate package verifier for F1/F2/F3 | All passed: package hashes, plan regeneration, feature ownership, overlap checks, wrong/missing executable and altered DLL/config negative paths |
| Launcher `--verify` and real suspended `--preflight` for each candidate | All passed for exact retail SHA; `WINDOWS_PASS_BEFORE_NATIVE_WRITES` |
| Deterministic rebuild comparison | F1 17/17, F2 17/17, F3 17/17 package file SHA/size rows identical; all plan template SHA256s and operation counts matched |

Focused command:

```powershell
$env:PYTHONPATH = 'src;tools'
python -m unittest `
  tests.synthetic.test_r_mod1_core `
  tests.synthetic.test_r_mod1_composition `
  tests.synthetic.test_r_mod1_native_plan `
  tests.synthetic.test_r_mod1_runtime_log `
  tests.synthetic.test_r_mod1_diagnostics `
  tests.synthetic.test_r_mod1_suspended_preflight -v
```

Full command:

```powershell
$env:PYTHONPATH = 'src'
python -m unittest discover -s tests/synthetic -v
```

Native shared-core harness:

```powershell
.\tools\r_mod1_core_tests.ps1
```

Candidate verifier (run once for each listed directory):

```powershell
python tools/test_r_mod1_candidate.py `
  '.research-output\r-mod1\first-integrated-candidate-v14-f1-r3' `
  --retail-exe 'D:\Game\Master Rallye\corpora\retail\MRallye.exe'
```

Use the analogous v15-f2 and v16-f3 package paths for the remaining checks.

## Candidate outputs

| Checkpoint | Launcher SHA256 | Runtime DLL SHA256 | INI SHA256 | Native patch plan SHA256 | Template SHA256 | Operations |
|---|---|---|---|---|---|---:|
| F1 `first-integrated-candidate-v14-f1-r3` | `51dfacee84f03344c4ff1f302e4a3bdd10e9af5d9c0a9b5e4b1c1ab39def5b33` | `cf743e356e3198cadd68ce750ff9f8c2cce5cb7caa965a4ee64d40c75f442da3` | `b47affdffa4748f337c405169d46b3b3763e1946931c0fdbd87bb5dc5b6eaacd` | `1d609a0f989ebb350a42a0c264c04756ad358d10f81d97496d2f80f43a117989` | `06597e1ea451df7427482fde97fbc707b5b7f48e12ad4ffc87acb5f421dac049` | 7 |
| F2 `first-integrated-candidate-v15-f2` | `5da905fe5fd03b88fe819625356063e021359d0feea6f3a8c0ca7f493d5d96a6` | `cf743e356e3198cadd68ce750ff9f8c2cce5cb7caa965a4ee64d40c75f442da3` | `b47affdffa4748f337c405169d46b3b3763e1946931c0fdbd87bb5dc5b6eaacd` | `2b9c0aa9eee34b9436a342879ed104978b12faec8114382905954599863e84f6` | `c972078639f9b76c7e3eb9aa4d6729aa85709248fed232df0389b2c73d3e0d98` | 13 |
| F3 `first-integrated-candidate-v16-f3` | `3849d57dcf57532b8ac9ca74c214f8643fec2bbe24d31ae9e77531dc4eab978a` | `cf743e356e3198cadd68ce750ff9f8c2cce5cb7caa965a4ee64d40c75f442da3` | `b47affdffa4748f337c405169d46b3b3763e1946931c0fdbd87bb5dc5b6eaacd` | `8d03c12e1f50779da43b185865f95acb0ddd2c6a67961fe3e402297ad1a3ddf4` | `3c760a475b854fd1435584f04450eada4dd90647ed7bbb7144fbf101e375d89d` | 17 |

All candidates are `STATIC_CANDIDATE_NOT_HUMAN_RUNTIME_QUALIFIED`. The DLL is
shared; launcher and native plan differ by checkpoint. On-disk retail EXE
SHA256 remained the exact pinned identity. No runtime gameplay claim is made
for F1, F2 or F3 by these build and test results.
