# Probe: PS2 outer limits on PC Turkey3 (data copy, channel B)

Question: if the PC outer limit lists take the PS2 `LeftOuterLimit2` / `RightOuterLimit2` positions, does the PC OFF COURSE border move out like on PS2?
Background: `T2-BEHAVIOR.md` (PS2 border sits farther out), `research/g1/limits-executable.md` (`gaLimitsAI` uses the four lists, outside the outer region for 8 samples gives LimitState 2).

## Candidate
`D:\Game\Master Rallye\research-output\limits-port\Turkey3.xml` (untracked output). Built by `limits_port.py` from the retail PC `Turkey3.xml` (SHA-256 `9f00ef08...4822`), candidate SHA-256 `75667e94...cd76`.
- Only the bodies of `LeftOuterLimit` (110 to 230 markers) and `RightOuterLimit` (126 to 209) change; everything outside those two lists is byte-identical (checked).
- Positions come from the PS2 lists, in PS2 order (progress along the RaceLine is monotonic apart from sparse sections, no reversals).
- Y forced to 0.00 like all PC Turkey3 limit markers (PS2 has -4.5 to 5.0 and the game's nearest-marker search is 3D). Marker Type and Dir keep the PC values (`markers\purple_marker`, `1 0 0`).
- Inner lists untouched.

## How to run
1. Baseline: in `MRRRenderer.ini` set `[ProbeTeleport]` points as below, teleport to Point1 and let the car sit. PC should show OFF COURSE and reset within a few seconds.
2. Install the candidate as a loose file: create `D:\Game\Master Rallye Pristine\DataScene\RaceTest\` and copy `Turkey3.xml` there (the G0/G1 probes used this loose location; whether the game prefers it over `Data.sma` is part of what is tested). Restart the game.
3. Teleport to the same points. Expected if it works: no OFF COURSE at the spots (they lie between the PC border and the PS2 border).
4. Remove the file to go back to stock.
Reading the outcome: baseline and candidate behave the same means the loose file was not read or the outer lists are not what raises OFF COURSE; no OFF COURSE with the candidate means the border moved (data channel B works for limits).

## Test spots (between the PC and PS2 borders, ground = PC ground + 1.5), script `limits_port_spots.py`
```
; spot 1: route idx 96, left side, PC border 203 from the road, PS2 border 294
Point1=2298.9,29.0,554.9,0
; spot 2: route idx 378, left side, PC border 186, PS2 border 253
Point2=3268.2,37.2,-620.7,0
; spot 3: route idx 294, right side, PC border 259, PS2 border 283
Point3=2822.1,59.6,-188.0,0
```
Near the road the two borders mostly agree (no spot with a gap of 15 or more within 150 units of the road), so the visible difference is far from the track.
Caveat: the PS2 solid wall is not ported (T2-BEHAVIOR.md), so the car is not blocked on PC even with the PS2 border.
