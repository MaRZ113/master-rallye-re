# Executed bounded format and lamp commands

Read-only canonical R5900 export, using the existing project:

```powershell
& 'D:/Game/Master Rallye/_reverse-tools/ghidra-bridge-main/ghidra_12.1.4_PUBLIC/support/analyzeHeadless.bat' `
  'D:/Game/Master Rallye/master-rallye-re-general/ps2-research/data/revalidation2/ghidra_ee' `
  EERevalidation2 -process SLES_509.06 -readOnly -noanalysis `
  -scriptPath 'D:/Game/Master Rallye/master-rallye-re-general/ps2-research/pc-port/docs/vehicle-model-port1/ps2-format-lights' `
  -postScript VehicleFormatProbe.java `
  'D:/Game/Master Rallye/master-rallye-re-general/ps2-research/data/vehicle-model-port1/vehicle-format-probe.txt' `
  -max-cpu 2
```

The probe verified exact language and SHA256. The canonical ELF was not imported
again or patched. Raw decompilation remains ignored. One exploratory probe
attempt used an unavailable `FunctionManager.getFunctionAfter`; Java compilation
failed before execution. It was replaced with the supported `getFunctions`
iterator and the final read-only export completed successfully. Final independent
R5900 byte verification checks2032 original words and51 prior lamp probes.

```powershell
python ps2-research/pc-port/docs/vehicle-model-port1/ps2-format-lights/audit_complete.py
python ps2-research/pc-port/docs/vehicle-model-port1/ps2-format-lights/lights_contract.py
& ps2-research/data/revalidation1/tooling-venv/Scripts/python.exe ps2-research/pc-port/docs/vehicle-model-port1/ps2-format-lights/verify_bytes.py
python -m unittest discover -s ps2-research/pc-port/docs/vehicle-model-port1/ps2-format-lights -p 'test_*.py' -v
python -m compileall -q ps2-research/pc-port/docs/vehicle-model-port1/ps2-format-lights
git diff --check
```

Results:29/29 source grammar support;18/18 testsPASS. No build, integration,
runtime mutation or automatic deployment occurs in this workstream. The main
agent owns the common serial builds and release artifacts.

The source inventory and lamp report were regenerated a second time and compared
by SHA256. Both JSON reports and the source coverage Markdown were byte-identical:

| Output | SHA256 |
|---|---|
|complete-inventory.json|983f23ef1c01fa890e5161cbffc8a5d8d6b5042cacc5e32bda0bfce0354139ad|
|complete-coverage.md|eb6ffd19a038f09b30307caef034e4e24b1a6e73a32aaa21d7b2efde7f6f0763|
|lights-contract.json|e0443807631b0dc72cc1396143f6abf04b0eb578e3f020fa3f1ff6798656534c|
