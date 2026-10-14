# Executed bounded commands

From re-general. REA open_binary used original Pristine MRallye.exe; returned x86
PE and SHA bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4.
REA xrefs0x6e7350 ->0x4ca044; xrefs0x6e7370 includes0x4ca14a. analyze_function
queries0x4ca044/0x4ca14a/0x4d3be0/0x4d3c50 produced pc-rea-evidence.json.
analyze_function0x4ca1d0 explicitly returned invalid_request because no analyzed
function existed. The following bounded original-byte fallback succeeded.

```powershell
$ghidra='D:/Game/Master Rallye/_reverse-tools/ghidra-bridge-main/ghidra_12.1.4_PUBLIC/support/analyzeHeadless.bat'
$scratch='D:/Game/Master Rallye/master-rallye-re-general/ps2-research/data/xtrail-brake-next'
# Executed using identical probe source in ignored scratch; both probe sources included here.
& $ghidra 'D:/Game/Master Rallye/master-rallye-re-general/ps2-research/data/revalidation2/ghidra_ee' EERevalidation2 -process SLES_509.06 -readOnly -noanalysis -scriptPath $scratch -postScript BrakeModeProbe.java "$scratch/mode-probe.txt" -max-cpu 2
& $ghidra $scratch PCBrake -import 'D:/Game/Master Rallye Pristine/MRallye.exe' -noanalysis -scriptPath $scratch -postScript PcBrakeProbe.java "$scratch/pc-update.txt" -max-cpu 2
& ps2-research/data/revalidation1/tooling-venv/Scripts/python.exe ps2-research/pc-port/docs/xtrail-brake-followup/brake-contract/verify_mode14.py
python ps2-research/pc-port/docs/xtrail-brake-followup/brake-contract/verify_pc_brake.py
python -m unittest discover -s ps2-research/pc-port/docs/xtrail-brake-followup/brake-contract -p 'test_*.py' -v
git diff --check
```

Results: EER canonical language/hash verified;4623 original PS2 words checked by
Rabbitizer1.16.2 InstrCategory.R5900;41 original PC update byte windows checked by
original PE mappings;8/8 independent contract tests PASS;diff-check PASS (existing
unrelated LF/CRLF warnings). Native framebuffer/runtime brake captures NOT_PERFORMED.
No builds or renderer edits in this workstream. Scratch import modifies only an
ignored analysis database; original executable and renderer remain untouched.
