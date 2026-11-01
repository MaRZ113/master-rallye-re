# Historical Demo frontend ratings

Field order is **Speed / Acceleration / Handling / Endurance**. These four
registration/display values are not a physics profile or measured performance.
Rerun `tools/audit_demo_frontend_stats.py` with the existing
`research/vehicles/sdk/restorations/demo-identity-corpus.json`. The tool reuses
`audit_demo_identity.pc_records`, original bounded x86 instructions and catalog
localization. Exact source hashes, call addresses, record IDs and localized
table offsets/pointers are in `restorations/frontend-stats.json`.

| Shortlist target | 8.4.1 | 9.3.1 | Attribution / active policy |
|---|---|---|---|
| Forester |6/7/5/4 PROVEN catalog |6/7/5/4 PROVEN named family |8.4.1 unresolved family string, exact SUBARU FORESTER localization;9.3.1 named Forester ID8. Updated future restoration manifest; accepted build unchanged. |
| Canonical retired RAV4 |UNKNOWN |UNKNOWN |No own named record. Existing5/5/5/5 explicitly SDK placeholder; do not take Newrav13 or Nissan Patrol12 values. |
| Early WildCat / TOMCAT |7/6/8/8 PROVEN |7/6/8/8 PROVEN |Wildcat ID15 in each version.8.4.1 TOMCAT/PRIVATEER TOMCAT evidence selected for this restoration; later geometry is distinct. |
| Newrav |7/7/6/4 PROVEN catalog |7/7/6/4 PROVEN named family |13, with explicit RAV4 PICKUP model label.8.4.1 family string unresolved. Not evidence for the retired enclosed RAV4. |
| Landcruiser |4/2/4/6 PROVEN |4/2/4/6 PROVEN |Named family0; body/livery identity differs across versions. Preserve version scope. |
| Megane |9/9/8/7 PROVEN |9/9/8/7 PROVEN |Named family19. Source identity does not authorize renaming another Mégane donor. |
| Tata |7/4/4/7 PROVEN catalog |7/4/4/7 PROVEN named family |8.4.1 family string unresolved, exact TATA SAFARI localization;9.3.1 family10. No reuse of retail physical ID2 without remapping. |
| Rav4Alpha |UNKNOWN |UNKNOWN |No independent qualified registration. Never infer full-RAV4 or Newrav ratings from the folder/Alpha suffix. |

The parser retains ratings even when a restricted Demo registration initializes
an unresolved model-family string. Such a value is attributed only through a unique
exact catalog label, explicitly marked as catalog evidence rather than proof
that the vehicle loaded in that Demo. Raw slot12/13 values alone are insufficient.
Original table/class indices are never assumed identical to retail runtime IDs.

Manifest `identity.frontend_stats` keeps source evidence separate from current
`identity.frontend.stats`. PROVEN values must match the original record and
source SHA. UNKNOWN entries remain explicit, with labelled SDK placeholders.
Native initialization tests assert all four selected values. No physics file,
coefficient or performance curve is derived from these ratings.

Workshop Vehicle Details exposes four integers0–10, history and baseline Restore.
The inspector distinguishes ORIGINAL_CATALOG, CUSTOM and SDK_PLACEHOLDER; original
evidence is retained when the user edits display ratings. Existing frozen
Forester/RAV4 candidate resources and native records are not overwritten by
updating source manifest defaults.

V-DEF3 ordering is owner accepted; this audit does not qualify the new TOMCAT's
gameplay. See [V-DEF4 results](V_DEF4_TOMCAT_RESULTS.md).

An unresolved `family: null` in this audit is the reader result, not proof that
the native pointer is null or the vehicle is disabled. For example8.4.1 ID8
pushes nonzero VA0x5f9114 before constructor0x447f10 at0x4479dd; that string
address is not uniquely file-backed. The original6/7/5/4 arguments and unique
FORESTER catalog entry are verified independently. No speculative runtime
initialization meaning is assigned to that address.
