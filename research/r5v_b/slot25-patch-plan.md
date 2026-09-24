# Slot-25 decision and conditional patch plan

**Decision: MORE RESEARCH NEEDED. No candidate or executable patch.** Record 25 is allocated but uninitialized in critical fields. It is not proved to be a sentinel, and it is not usable as constructed. The frontend has a separate 11-car class-2 limit. The resource/physics and quick-race paths are still incomplete.

The smallest *conditional* retail proof would:

1. Complete the record 25 initialization after all 26 default constructors, using an owned `Astero` string and Astero's known fields, with `ID=25` and `class=2`. Do not memcpy an owned string pointer or change IDs 0–24.
2. Change the screen constructor at `0x480A62` from class-2 limit 11 to 12 **only after** proving the corresponding UI marker and unlock behavior. The immediate byte is at file offset `0x80A65` (`0B`), but this address is a research anchor, not an approved patch point.
3. Confirm any other `<=24` gate on preview, quick race, race load, AI, model and physics lookup before adding further edits.

No new string, model folder, physics XML or localization data is needed in the intended first proof if all paths can reuse Astero. The full initializer's four float words and owned string mean a one-byte capacity change alone cannot work. A code-cave/hook or relocation is **not designed or authorized** without the missing xref/path audit. A data-only path has not been found.

The retail binary SHA-256 is `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. No exact replacement byte sequence, patcher, patched executable or manifest is offered while the path remains unproved. The future patcher must verify this hash and every old byte, write a different path, document every range, and test rejection/determinism/source preservation. No proprietary binaries enter Git.

`demo-8.4.1` and `demo-9.3.1` are unpacked installs without `Data.sma`. Their registry strides and frontend objects differ from retail. They provide architecture history only; IDs, names, folders and hashes stay version-specific. In particular, similarly named/positioned Forester/NewRav and LandCruiser/WildCat variants are not merged across builds. An equivalent demo case switch was not established, so no case-25 behavior is inferred from demos.
