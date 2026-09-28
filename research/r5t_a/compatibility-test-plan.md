# R5T-A component compatibility test plan

## Evidence boundary

`CONFIRMED_BY_RUNTIME` (project owner): retail course resources load in Demo 9.10.0 when required files are supplied/selected; the same retail packages fail in Demo 9.3.1 and 8.4.1 with an empty/void world. No cause is assigned by this report.

Static comparisons make three first-tier Italy1 candidates discriminate meaningfully:

1. DX: revision 131 → 135 and a different first draw-record body; reading the 9.3.1 record with the later 40-byte tag-2 core yields impossible slot counts from texture-name bytes. The revision-135 parser succeeds on 9.10.0 and retail.
2. SFL: 9.3.1 and 9.10.0 headers/dimensions match, but payload hashes change; 9.10.0 and retail payload hashes match.
3. RaceTest XML: full files differ, and Italy1's literal root child changes from `EggLists_Version3` to `EggLists_Version4` between 9.3.1 and 9.10.0.

At the first France1/Italy1 root tag-4 record, raw control words change from `(49, 1, 106)` to `(49, 1, 23)` and `(77, 1, 66)` to `(77, 1, 28)` respectively. The words are recorded as bytes here; only the revision-135 parser assigns the third word a child-count role.

The 9.3.1 course HNT is absent and the 9.10.0 Italy1 HNT is empty, so an HNT-only swap is not a useful isolated first test. If the three file swaps do not discriminate, the next test should use the retail Italy1 HNT plus its exact resolved dependency closure as a bundle. That tests the resource graph as a unit; it must not be described as an HNT-only result.

## Minimal 9.3.1 matrix

Keep a pristine copy of the native Demo 9.3.1 Italy1 package and install one overlay at a time at the exact path shown. Record whether the scene loads, which resources are requested, and whether the world contains the expected track. Revert to the pristine copy between rows.

| Order | Overlay replacement | Tests primarily | Interpretation if the course loads |
|---:|---|---|---|
| 0 | Native Demo 9.3.1 Italy1, no overlay | Baseline/control | Confirms the local demo install and course selection work |
| 1 | Retail `DataGx/Course/Italy1/track01.dx` only | Compiled DX compatibility | DX replacement is sufficient in the native 9.3.1 package |
| 2 | Retail `DataScene/ICont/Italy1.sfl` only | SFL payload dependency | SFL replacement is sufficient |
| 3 | Retail `DataScene/RaceTest/Italy1.xml` only | Scene/registry/resource declarations | XML replacement is sufficient |
| 4 (conditional) | Retail `Italy1.hnt` plus only its exact resolved dependencies | Manifest/resource closure | Dependency bundle is sufficient; individual dependency cause remains unresolved |

Do not combine overlays 1–3 in the first pass. If a row fails, that is not evidence the swapped resource is irrelevant when another required resource is still native.

## 9.10.0 control

Use the already reported retail-in-9.10 success as the compatibility reference. If the install has a known-good native Demo 9.10 Italy1 baseline, one optional retail-DX-only overlay can confirm the DX component independently. Run the SFL/XML rows on 9.10 only if the 9.3.1 results leave those hypotheses unresolved. No executable modification is part of this plan.

## Prepared candidate overlays

Machine-generated isolated replacement files and their hashes are placed under the ignored `.research-output/r5t_a/compatibility/` folder. Each overlay contains only one retail file at its runtime-relative path; it is intended to be copied into a separate Demo 9.3.1 test installation, not into the supplied corpus. The generated manifest records the source and SHA-256. No runtime candidate was launched in R5T-A.
