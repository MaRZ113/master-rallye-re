# Persistence unknowns and limits

1. Actual native round-trip behavior: not yet human-tested in this phase.
2. Archive-only target: read-based existence can succeed but loose CopyFileA can
   fail. Test only with a disposable target in an explicitly authorized follow-up.
3. All IO-failure interleavings: immediate successful startup order is proven;
   the pump exits on failure and pending work may remain.
4. Complete Matrix/vector/StringList/class serialization fidelity and encoding.
5. Mode 4's intended PS2-labelled workflow beyond its recovered filter.
6. __NO_CHANGE UI intention: applying it changes SaveFile in the recovered branch
   path; no universal preserve-old guard exists there.
7. Multi-editor __IGNORE owner callback and application-local reused storage:
   do not extrapolate the mapped dummy mode-0 argument to all consumers.
8. All normal progress/profile writers and fixed identity/capacity constraints.
9. Backend root variations under custom developer configurations.

There is a one-generation overwriteable `#` backup, not transactional durability.
Open-only safety does not cover edit, Commit, SaveAs or any whole Game operation.
The observational helper deliberately exposes none of those writer commands.
