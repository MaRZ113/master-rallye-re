# R5V-I sparse class mapping

The retail mapping helpers are `FUN_00481E20` (class/local to physical ID)
and `FUN_00481E50` (physical ID to class/local). The T2 arm of the first
helper uses a seven-ID dense range beginning at physical 7; I.0 intercepts
only T2/local7 and returns physical 27. The reverse helper intercepts only
physical ID27 and fills class 1/local7 before returning to the native helper.

| Class code | Local index | Physical ID |
|---:|---:|---:|
| 0 / T1 | 0–6 | 0–6 |
| 0 / T1 | 7 | 26 |
| 1 / T2 | 0–6 | 7–13 |
| 1 / T2 | 7 | 27 |
| 2 / T3 | 0–11 | 14–25 |

ID25 remains the pre-existing T3 local11 Trooper. Physical ID14 remains T3
local0; no T2 operation uses contiguous `range(0, 8)` arithmetic. The
synthetic tests enumerate every physical ID 0–27 through both mapping
directions, assert ID25/26/27 identities, and assert ID14 is impossible as
T2/local7. The candidate capacities are T1=8, T2=8 and T3=12.

The Ghidra bridge export in the current vehicle checkout records the stock
helper fields: class at record offset +0x10, T1 local index +0x14, T2 local
index +0x18 and T3 local index +0x1C. The mapping claim is static; no
human-runtime confirmation is implied for ID27.
