# R-GRID8 candidate

| Property | Value |
|---|---|
| Profile | `retail-r-grid8-audit` |
| Source | `retail-pristine`, `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` |
| Output | `75942c0b65147b96b8b2254ee536f6aefc7f3a501c23d12be640f85a562680ac` |
| Size | 3,121,214 bytes |
| Generated file | `.research-output/general-re/grid8/MRallye.exe` |
| State | `READY_FOR_HUMAN_AUDIT`; not runtime-tested on this candidate |

The stock menu remains One/Two/Three. With visible `Opponents=Three`, the
guarded research hook publishes seven AI (eight total). It is reached through
the normal one-human Quick Race chooser when frontend mode is 2, visible
opponents is Three, split screen is off, Ghost is off, player ID is 0, and the
registered scene ID is `0..38`. The split-screen chooser and other game-mode
call sites are untouched; multiplayer and other modes are not supported or
claimed. The active-race capture oracle separately requires `Race/Type=2`,
`Race/NumNetworkPlayers=0`, and `Race/NetworkSyncActive=False`, and rejects an
explicit `Race/Networked=True`; these are runtime state checks. No randomizer
DLL, UI extension, registry expansion, or course asset is included.

The deterministic roster is copied from the closed R-AI2.1 eight-car manifest:

| Slot | CarID | Class | DriverID | Runtime family |
|---:|---:|---:|---:|---|
| Car0 | 0 | T1 | 30 | Landcruiser / human |
| Car1 | 1 | T1 | 0 | Pajero |
| Car2 | 7 | T2 | 1 | Navara |
| Car3 | 14 | T3 | 2 | Wildcat |
| Car4 | 2 | T1 | 3 | Tata |
| Car5 | 8 | T2 | 4 | Forester |
| Car6 | 15 | T3 | 5 | Simmbugghini |
| Car7 | 17 | T3 | 6 | Kangoo |

The exact source hash, target original-byte checks, declared ranges, and
deterministic output are enforced by `tools/r_grid8_candidate.py`. The
reproducible build command, from the checkout root, is:

```powershell
python tools/r_grid8_candidate.py build "D:\Game\Master Rallye\corpora\retail\MRallye.exe" --output .research-output\general-re\grid8\MRallye.exe
```

Verify the generated file with:

```powershell
python tools/r_grid8_candidate.py verify .research-output\general-re\grid8\MRallye.exe
```

The candidate contains the narrow legacy Loading→false-Attract neutralization.
Its native Dump formatter is **stock**: active-race Dump is supported, while
post-Results Dump is unsafe. It retains the R-AI2.1 code-cave layout and
`.text` VirtualSize extension; no participant storage, global grid formula,
UI list or course data is changed. The compact, payload-free range summary is
in [patch-manifest.json](patch-manifest.json).
