# Exact profile and reusable audit

`retail-merc-id26` is pinned to SHA256
1fb0a1f1ba02cd05fa25f0c94558cf1b281fd12affcdc37bb3c1ca538e6c65af,
size3121214. Pristine bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4
has its own profile, registry and PE identity.

PE32/x86, ImageBase400000, timestamp3C02695D, entry RVA1C4602,
SizeOfImage311000. Section RVAs/raw extents/flags are unchanged.
.text VirtualSize: pristine28D294, Mercedes28D509. Added payload/literals span
VA68E2A0 through68E508 inclusive, declared end68E509. This overlaps older
Loading/Dump guards and mixed/capacity stubs near68E2A0/68E300. **Do not apply
legacy research manifests**. Future integration must relocate code or use an
external runtime module. No such work occurs here.

`python tools/research_build_profiles.py audit-build <exe> --output
.research-output/r-observatory-modded-builds/<report>.json` reports hash, size,
PE identity/sections and bounded fingerprints. It returns
ANCHOR_COMPATIBLE_ONLY or INCOMPATIBLE; `automatic_trust=false` in both cases.
It never writes a profile registry or changes the EXE. Matching anchors cannot
admit an unknown executable.

Workflow: audit -> review native owners/layout and registry -> deliberately commit
an exact profile + capability/registry metadata and explicit adapter verifier
selection -> test rejection/regression cases -> prepare human captures.
No --allow-any/force or filename/size-only trust. Current registration is in
[build-profiles.json](build-profiles.json); fingerprints store bounded hashes,
not copied proprietary code. `verify-build` adds exact hash/size and full
registered PE-layout checks to the audit.

Capabilities: active-race Broker capture supported, post-Results native Dump
safe=false, legacy_loading_attract_present=true, registry=merc-id26. Broker
format itself is unchanged. Audit report is [merc-build-audit.json](merc-build-audit.json).
