# Structural audit and commands

## Commands

Audit and create/reuse a local exact profile after a compatible family pass:

```powershell
python tools/research_build_profiles.py audit-build "<MRallye.exe>" --output .research-output/observatory/audits/build-audit.json
```

Report without creating a cache entry:

```powershell
python tools/research_build_profiles.py audit-build "<MRallye.exe>" --audit-only
```

The internal Observatory runner audits automatically and caches on first compatible use:

```powershell
python tools/r_ai1_observe.py --observatory "<audited Observatory directory>" --exe "<MRallye.exe>" -- --label mercv2-stock-race
```

## Audit procedure

1. Bound input to 64 MiB and parse DOS, PE, COFF, optional, and section headers.
2. Require machine `0x014C`, PE32 magic `0x010B`, sane section count, in-file raw extents, and audited family image/section layout.
3. Map each VA through its owning section and hash only its bounded bytes (or the proven zero-filled BSS slot).
4. Require every family anchor fingerprint exactly. No fuzzy, wildcard, nearest-build, filename, or file-size admission exists.
5. Independently attempt registry fingerprints. Failure leaves registry `unknown`; it does not invalidate generic family capture.
6. Derive capabilities from the family and matched behavior fingerprints; write only the local SHA-bound profile.

Machine-readable output includes PE facts, anchor expected/observed SHA values and per-anchor results, family decision, registry detection result, capabilities, exact profile, and cache provenance. Terminal output summarizes hash, exact identity, family, registry, Broker/native Dump capabilities, Results Dump safety, and cache use.

Family admission is still narrower than arbitrary build support: the external Observatory implementation remains SHA-pinned; the candidate is re-audited immediately before launch; only family-proven native addresses are used; the pinned byte reader limits capture data as before. A failure rejects capture rather than falling back to best-effort reads.

`native_dump_walker` matches the stock NULL-unsafe formatter, so Results Dump is marked unsafe. A nonmatching walker fails this family audit until a separately audited compatible family/capability is added. The legacy Loading-to-Attract anchor is informational; no EXE patch is applied.
