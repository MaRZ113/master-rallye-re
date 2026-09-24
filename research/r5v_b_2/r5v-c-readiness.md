# R5V-C readiness decision

**R5V-C BLOCKED.** R5V-B.2 is read-only evidence closure; no executable, game asset, runtime candidate or patch manifest was produced.

| Required gate | Finding |
|---|---|
| class2/local11 reaches race ID25 | Proven through `0x481E20`, `0x481340`, `0x47B780`, subject to frontend unlock/selection |
| 26-record storage and normal record25 initialization | B.1 proved original `0x45A0B0` ABI and owned-string copy; existing capacity includes ID25 |
| preview `Astero/complete` | Proven conditional on initialized record25 and unlocked `CarModel=25` |
| race `Astero/car` and `/wheel` | Dynamic `CarType` path proven **only when `Frontend/Active` is true** at actor creation; that state was not proved for intended Quick Race P1 |
| Astero named physics to `Car0` | Proven from `Race/Car0/CarID` through record name and `0x493E30`/`0x4938C0`; `Car%d` is race instance index |
| class2 capacity 12 has no unknown frontend dependency | Unproven: missing `Button11XPos` widget/focus behavior and ID25 unlock flag 15 state |
| all P0/P1 hard gates classified | Unproven due to conditional render branch and frontend gates |

Exact next research targets: (1) establish `Frontend/Active` value when the Quick Race car actor executes `0x4B6A00`, or find the alternative live race render loader; (2) demonstrate how local 11 is displayed/focused without a `Button11XPos` scene widget; (3) establish the ID25 unlock flag 15 result or a narrow legitimate test path. A P0 frontend test and P1 race test must not be conflated. The prompt's `PlayerT3Car0=11` premise is false: that key holds absolute ID25 on the observed path, while Quick Race stores absolute IDs directly.

If these gates are closed in a future phase, the minimal *design* remains: use the original full initializer for record25 with ID25/class2 and semantic Astero donor values (including a deep-copied `Astero` name); change class2 capacity 11→12; then stage human P0 preview verification before P1 race verification. This is not an approved patch specification or runtime result.
