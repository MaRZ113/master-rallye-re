# R5V-B — dormant retail vehicle record 25 audit

## Result

**MORE RESEARCH NEEDED; runtime candidate BLOCKED.** Ghidra Bridge plus exact retail disassembly shows record25 is default constructed with an empty string and **seven unwritten integer fields**, including stored ID and class. The class-2 frontend is fixed at 11 cars. The prior R5V-A dynamic `VehicleList` observation applies to *class labels*, not vehicles. Retail `0x45A150` has a case 25 unlock check, and `0x4819B0` has a localization selector for absolute ID25, so the slot is not proved to be an intentional sentinel. These facts do not establish a safe playable path.

## Evidence and corrections

- Retail EXE hash and constructors are recorded in `retail-record25.md/json`; default bytes that are not written are explicitly indeterminate.
- `retail-case25.md` documents the 26-case switch and case25's flag index 15.
- `class2-vehiclelist.md` corrects the R5V-A frontend interpretation and identifies the 7/7/11 screen counters and car navigation bound.
- `resource-physics-path.md` states the observed chain and the missing model/physics/save/AI edges.
- `slot25-patch-plan.md` refuses a speculative patch; `runtime-test-plan.md` defines the later human gate.

The local installed Ghidra Bridge project was used for targeted functions. No retail/demo EXE, `Data.sma`, game asset or Ghidra project was modified. No Forklift activation, track research, or runtime test occurred. The first eventual payload remains duplicate Astero only.

## Build discipline

Use `demo-8.4.1`, `demo-9.3.1`, `retail`. The demos contain unpacked data and no `Data.sma`. Their `0x24` registry records and frontend object layouts are not retail-compatible. Version-specific vehicle identities were not merged.
