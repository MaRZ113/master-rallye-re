# R5V-H.1 natural T1 ID26 pool candidate

## Scope and static result

H.0 proved forced ID26 materialization. H.1 removes that force and changes the
native T1 candidate source so ordinary selection can choose physical ID26.
The candidate stays at one human plus three AI; it does not change the
participant count or selection probability policy.

The fail-closed build composes the exact pristine retail executable through
the ordinary G.1/G.2 neutral hardened profile, verifies that the ordinary base
reproduces SHA256
`391d5d864699b6e945eed43fd8e7bc28b28639b24b222428ab79231e7cc3a819`, then
adds only the T1 append seam and the H.1 ID26 Results display policy. The exact
builder is [build_vehicle_natural_t1_candidate.py](../../../tools/build_vehicle_natural_t1_candidate.py).

Retail's native `FUN_00458090` T1 source loop emits absolute physical IDs
0–6. Its exit at VA `0x00458167` skips the T1 loop body to the common class
exit. H.1 redirects that exit to a 25-byte stub at `0x0068E780`. On the first
visit, the stub sets ESI to 26 and re-enters the existing exclusion/appending
body at `0x00458137`. The native body applies the same two physical-ID human
exclusions to ID26 before it appends anything. After the body advances to 27,
the stub restores ESI to the original loop end value 7 and jumps to the
original common exit at `0x004582D5`.

The resulting source pool is exactly:

```text
[0, 1, 2, 3, 4, 5, 6, 26]
```

ID7 is never treated as T1; it remains the first T2 vehicle. Examples after
native human exclusions are `Car0=0 -> [1,2,3,4,5,6,26]`, `Car0=26 ->
[0,1,2,3,4,5,6]`, and split-screen exclusions `0,26 -> [1,2,3,4,5,6]`.
The existing shuffle, working-vector selection, removal, driver chooser,
publication, and registry-derived CarClass paths remain native. The player
unlock predicate is not consulted by this chooser.

## Patch bounds and preserved systems

| Site | Retail range | H.1 purpose |
|---|---|---|
| `0x00458167` / file `0x58167` | `E9 69 01 00 00` | Branch through the one-time ID26 append shim |
| `0x0068E780` / file `0x28E780` | 25 zero bytes | Re-enter native T1 exclusion/body once; restore index 7 |
| `.text` VirtualSize | retail/base manifest operation | Extend mapped code through `0x0068E799`, still before `.rdata` |

No operation overlaps T2 construction (`0x0045816C..0x004581B4`) or T3
construction (`0x004581B9..0x004582D5`). T2 stays 7–13; T3 keeps 14–20 and
the stock progress-gated 21–24. The original selected-ID publication bytes at
`0x00458428` remain `8B 44 24 14 50`: H.0 forced publication logic is absent,
its cave is zero, and there is no mixed-class randomizer.

## ID26 Results-name display choice

The group-0x39 audit found demo physical Mercedes ID2 uses selector 2 ->
`JOSE MARIA SERCIA` in both demo-8.4.1 and demo-9.3.1. Historical results put
Servia/Lurquin in the Schlesser T3 entry, while the Mercedes T1 crews include
Strugo/Larroque, Lansac/Jacquema, and Menguy/Menguy. The demo mapping is
therefore a developer placeholder for a Mercedes-associated Results name, not
a supported historical Mercedes T1 crew. Details, hashes, and sources are in
[historical-driver-selector.md](historical-driver-selector.md).

H.1 changes only the display returned for physical ID26 to `JEAN-PIERRE
STRUGO` (`REAL_2001_MASTER_RALLYE_MERCEDES_DRIVER`). Exact ML-320 pairing is
unproven. The ID26 Results helper supplies the literal to the existing string
consumer; all other AI retain the original group-0x39 physical-CarID lookup.
Human name branches remain unchanged. Native `FUN_00458980` DriverID
selection and participant DriverID publication are unchanged. H.0.1's
runtime-driver display behavior remains a historical, already-tested profile;
H.1's fixed display still requires human runtime confirmation.

## Candidate and package

| Artifact | Value |
|---|---|
| Profile | `natural-t1-id26` |
| Source retail SHA256 | `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` |
| Neutral hardened base SHA256 | `391d5d864699b6e945eed43fd8e7bc28b28639b24b222428ab79231e7cc3a819` |
| Candidate SHA256 | `e59895776dd53acb3ac4a25e1973c8de341da815b90407ec372b696be06d363a` |
| Size | 3,121,214 bytes |
| Candidate manifest SHA256 | `77ff35b1e49025e5b1d29f57d12339a117adb79bc427096cdcfc8685c22c412e` |
| Runtime package | `.research-output/vehicles/ai/natural-t1-id26/runtime-package/` |
| VehicleSelect.xml SHA256 | `6cdf398b892dbe01d2a1258030d2785e568cd993e4cf01d9dc4378ae9207341` |

The verified package has 145 files, includes the G.1 Mercedes assets and G.2
audio profile 0 resources, excludes PlayerState, and reports no forced proof
or randomizer. This is package verification, not race-runtime proof.

## Evidence boundary

* Exact stock pool, raw bytes, two-hits-only caller scope, and candidate
  control-flow composition: `CONFIRMED_BY_EXE`.
* Demo group-0x39 selector mapping and demo ID2 Mercedes registry identity:
  `CONFIRMED_BY_EXE` for the exact hashed demo builds.
* Historical 2001 Mercedes T1 crews: external historical result tables, not
  game-executable evidence.
* Natural ID26 selection, actor behavior, and fixed Results string:
  `READY_FOR_HUMAN_RUNTIME`.
* ID26 in other modes, further participant counts, and any probability claim:
  `UNKNOWN` / out of scope.
