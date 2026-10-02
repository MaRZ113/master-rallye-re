# Mercedes evidence gate

R5V-F.1 did not audit Mercedes. R5V-F.2 has now completed the static source,
physics, collision, localization and frontend-art audit. The owner-reported F.1
cleanup P0 result remains authoritative for its tested candidate; the separate
ID0 colour comparison was not reported and remains non-blocking.

**Current gate: BLOCKED before Mercedes candidate generation.** The distinct
demo-8.4.1 `Copy of Mercedes` model has three revision127 DX files. The current
proven release converter accepts revision131 to 135, and the original 9.10
cooker route has no exact reproducible Mercedes source/output record. Retail
physics is schema-compatible, and source collision passes a bounded structural
check, but no retail-compatible full model is available. No Mercedes profile,
overlay or executable candidate was created.

Keep the target invariant `ID26 / T1 local7`; IDs0–25 and all other class
mappings remain unchanged. Close the exact revision127-to-retail model build
and strict SDK validation gate before a controlled Mercedes P0. See
`research/r5v_f_2/findings.md` and
`research/r5v_f_2/mercedes-model-conversion.md`.
