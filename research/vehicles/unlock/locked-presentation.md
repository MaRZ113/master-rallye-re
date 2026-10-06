# ID26 locked-state presentation

## Native text writer

`FUN_004819B0` evaluates availability and writes the Vehicle Select lock state.
When unavailable, the first line uses group 6 selector 8 (`CAR LOCKED`). The
second line uses a table indexed by `physical Vehicle ID - 3`. The retail
jump-table at `0x00481D94` was checked entry-by-entry:

| Physical ID | Group 6 selector |
|---:|---:|
| 3 | 9 |
| 4 | 10 |
| 5 | 11 |
| 6 | 19 |
| 7–9 | 8 (stock default target) |
| 10 | 12 |
| 11 | 13 |
| 12 | 14 |
| 13 | 20 |
| 14–17 | 8 (stock default target) |
| 18 | 15 |
| 19 | 16 |
| 20 | 17 |
| 21 | 21 |
| 22 | 23 |
| 23 | 22 |
| 24 | 25 |
| 25 | 26 |

IDs 7–9 and 14–17 resolve to the existing default block at `0x00481B49`; the
list above does not claim additional authored requirement strings for them.
The group-6 resources are not modified.

For the current G.1 policy, ID26 mirrors ID3's availability and therefore must
also use selector 9. The candidate replaces the five-byte bound-check sequence
at `0x00481ACF` with a narrow trampoline. ID26 selects group 6/selector 9; all
other IDs reproduce the original compare, default, and jump-table dispatch.
The generic `CAR LOCKED` line is untouched.

## Slot art

Stock `T1_Car4` uses normal frame 27 and common locked frame 15, controlled by
its disabler AI. The ID26 slot uses its established Mercedes frame 3 while
unlocked and frame 15 while locked. The overlay also sets the base image-bank
index to 3. No image-bank payload or authored asset is changed.

The XML values are statically verified. Visible frame switching and the exact
localized requirement line are still part of the human runtime gate.
