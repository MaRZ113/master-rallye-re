# PS2-REVALIDATION1

Independent evidence audit for TREEBLEND1 and the France1 `bush01` PILOT1.3
four-mode experiment. The audit rechecks the supported retail PC executable
with REA, repeats compact source/geometry/texture checks from the canonical
corpora, and reviews earlier phase outputs without silently treating those
outputs as newly captured runtime evidence.

**Status: `REVALIDATION_PARTIAL_PROVIDER_LIMITED`.** REA provided useful PE
analysis of the original PC executable, but its configured Windows/Ghidra
provider does not support this PS2 R5900 ELF. The earlier PS2 executable
analysis remains useful evidence; its instruction bodies were not freshly
reanalyzed by REA here. The PILOT1.3 raw logs and screenshots are also absent
from this checkout, so the four-mode observations remain user-reported.

No corrections were applied to the renderer, PS2 port implementation, source
assets, or previous research claims. This directory records evidence
provenance refinements and explicit limits. The renderer source tree remains
unchanged, and existing uncommitted `ps2-research/pc-port/` work was preserved.

Read [the final report](final-report.md), then the
[claim ledger](claim-ledger.md), [validation record](validation.md), and
[next experiment](next.md). The deterministic documentation-only handoff is
created under ignored `ps2-research/data/revalidation1/`.
