# Demo group 0x39 and ID26 Results-name policy

## Exact demo selector map

The hash-pinned extractor [extract_demo_group39.py](../../../tools/extract_demo_group39.py)
reads the contiguous 12-byte group rows from both demo executables. The full
derived rows and raw offsets are in [demo-group-39.json](demo-group-39.json).

| Build | EXE SHA256 | Group 0x39 row table(s), raw offset | Rows | Selector 2 |
|---|---|---:|---:|---|
| demo-8.4.1 | `2d4a3b02d3cdb740dfdf3c11002c0026837dc19ba8e5211ad9763b35eb06e15a` | `0x1E8F30` | 12 | `JOSE MARIA SERCIA` |
| demo-9.3.1 | `611526d30be94879012efe54c56ceff428cb4d20a4bd49173370a4ebfe31a728` | `0x2677CC`, duplicate `0x269CBC` | 20 each | `JOSE MARIA SERCIA` |

The selector map is identical in both builds for selectors 0–11: 0 Jean Louis
Schlesser; 1 Henri Magne; 2 Jose Maria Sercia; 3 Jean Marie Lurquin; 4 Luc
Alphande; 5 Arnaud Debron; 6 Bruno Saby; 7 Tim Dvoskin; 8 Vladimir Strakhov;
9 Rene Metge; 10 Player 1; 11 Player 2. Demo 9.3.1 additionally carries
selectors 40–47 as `RESERVED1` through `RESERVED8`.

The current-branch Ghidra 12.1.4 cross-build registry evidence in
[cross-build.md](../../audio/cross-build.md) identifies physical demo vehicle
ID2 as Mercedes/T1 in both executables. The Results path uses the participant
physical vehicle selector for the ordinary vehicle-associated name lookup;
therefore demo Mercedes ID2 reaches group 0x39 selector 2, which resolves to
`JOSE MARIA SERCIA`.

## Historical comparison and classification

The archived 2001 Master Rallye Stage 5 table lists all three relevant
Mercedes T1 crews: car 208 Jean-Pierre Strugo / Pascal Larroque, car 216
Lansac / Jacquema, and car 234 Menguy / Menguy. That same Stage 5 table lists
car 202 Servia / Lurquin with Schlesser in T3. The Stage 7 overall table again
lists the three Mercedes crews in T1. See the [Stage 5 results](https://au.motorsport.com/ccr/news/master-rallye-auto-stage-five-results/1911176/)
and [Stage 7 overall results](https://au.motorsport.com/ccr/news/master-rallye-auto-leg-seven-overall/1911788/).

Thus the *demo Mercedes ID2 -> selector 2* association is classified
`DEVELOPER-PLACEHOLDER`, not an authentic Mercedes T1 driver pairing. The
string appears to refer to the real rally driver José María Servià, but the
demo spells it `SERCIA`; the historical result tables place Servià with
Schlesser T3, not a Mercedes T1. This does not establish that the name itself
was invented.

For the H.1 ID26 Race Results display only, the selected fixed identity is:

```text
JEAN-PIERRE STRUGO
classification: REAL_2001_MASTER_RALLYE_MERCEDES_DRIVER
exact ML-320 pairing: unproven
```

The historical tables substantiate Strugo as a 2001 Master Rallye Mercedes T1
driver. They do not prove he drove the specific addon ML-320 representation.
The H.1 helper changes only the ID26 Results display string. It does not alter
native DriverID selection, the participant's DriverID, physical CarID26,
vehicle family, or any other vehicle's Results lookup.
