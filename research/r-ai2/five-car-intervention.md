# Guarded five-car research intervention

Exact output profile `retail-r-ai2-five-car-hardened`:

- Source SHA256: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
- Hardening base SHA256: `bbb9f0a8bb2523adf125582d16512c25f9b51db7a4104ee5edf8f7251865ae00`.
- Output SHA256: `806ebedcd6d174682fcc4619fb75eaabca2a1281eda4d4d784807b3583f5f2e2`.
- Size: **3,121,214 bytes**, unchanged.
- Generated path: `.research-output/r-ai2/five-car/MRallye.exe`; no EXE committed.

**Capacity seam:** native Quick Race setup47B780, original count getter4AE150.
Redirect CALLs47B88A and47B8DD to a131-byte shim at68E300. The shim always calls
the original getter first, then preserves all registers/flags and checks:
opponents3, mode2, SplitScreenFalse, Ghost0, Track10, player absolute ID0.
Only the saved return EAX becomes4; all rejection paths restore the original
return. The original INC publishes NumCars5; original chooser receives
firstAI1/count4/class0/playerID0/second exclusion-1.

The two reads happen before/after other ordinary setup writes. The guard uses
frontend state, not stale Race/NumPlayers. It doesn't independently patch
CarClass, DriverID, CarType, WheelType or controller state. Player Car0 is
unchanged. Car1..3 retain normal T1 draw paths; Car4 is a fourth unique ordinary
T1 draw, ID1..6. Native driver bookkeeping and both shuffles still execute.

| File offset | VA / length | Purpose |
|---|---|---|
| 218 | PE header /4 | text VirtualSize28D294 ->28D383 |
| 64F69 | 464F69 /5 | existing legacy Loading hardening |
| 7B88A | 47B88A /5 | guarded count read for NumCars publication |
| 7B8DD | 47B8DD /5 | guarded count read for four AI construction |
| 20201E | 60201E /6 | existing nullable StringList Dump guard |
| 202153 | 602153 /7 | existing nullable XmlData Dump guard |
| 28E2A0 | 68E2A0 /19 | existing StringList guard code |
| 28E2C0 | 68E2C0 /28 | existing XmlData guard code |
| 28E300 | 68E300 /131 | five-car effective-getter shim |

Exact original/replacement bytes and semantic purposes are in the
[manifest](patch-manifest.json). Header is the only explicitly merged range;
the other eight ranges are disjoint. Source hash, size, original bytes, PE
VA/file translation, output hash and inverse-to-pristine reproduction all fail
closed. The cave is zero pristine text padding after declared text end68E294,
inside existing raw padding ending68F000. Its declared extension occupies the
same aligned pages. No absolute image relocation, new section, arbitrary
storage or proprietary payload distribution is used.

Reproduce from the main checkout:

```powershell
python tools/r_ai2_capacity.py build ../corpora/retail/MRallye.exe .research-output/r-ai2/reproduced/MRallye.exe
python tools/r_ai2_capacity.py verify .research-output/r-ai2/reproduced/MRallye.exe
```

The builder refuses to overwrite files and accepts pristine only. It composes
hardening directly; it rejects the old randomized EXE as an input. Restoring
the isolated game's preserved stock EXE removes the research intervention.
No live WriteProcessMemory is used; Observatory remains read-only apart from
its already-audited native Dump UI commands.
