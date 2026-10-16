# PS2-REVALIDATION1 handoff

This bundle contains the revalidation report, claim ledger, compact source
identities, test/command record, and deterministic packaging script.

It excludes original game executables, archives, extracted PSM/DX/GXI/DXT
assets, original image pixels, raw runtime captures, and generated full
geometry data. The ignored local file
`ps2-research/data/treeblend1/revalidation1-cases.json` is not included.

The bundle is for evidence review and report inspection. Re-running the
corpus-backed tests requires the canonical PS2 input root, protected PC retail
course corpus, and the read-only Course SDK path listed in
`command-log.md`. REA queries require a configured REA connection and the
hash-verified original PC PE. No PCSX2 capture is included.

Create or verify the archive with:

```powershell
python ps2-research/revalidation1/package_handoff.py
```

The script sorts inputs, fixes ZIP timestamps, hashes every included file,
writes a manifest inside the archive, reopens it to verify every hash, and
prints/writes the final archive SHA-256. The archive stays under ignored
`ps2-research/data/revalidation1/`.
