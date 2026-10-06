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

**Historical R-OBS1 workflow:** `audit-build --audit-only` reports hash, size,
PE identity/sections and bounded fingerprints, but matching anchors alone did
not admit an unknown executable. R-OBS2 supersedes exact-SHA-only admission for
the internal `retail-broker-v1` family. Use
`python tools/research_build_profiles.py audit-build <exe>` to resolve an exact
profile or, after every family/layout/anchor gate passes, create/reuse a local
SHA-bound profile under ignored `.research-output/observatory/build-profiles/`.
`--audit-only` remains diagnostic and does not create a profile. The family
path does not edit the EXE, registry, or external Observatory implementation.
It uses no `--allow-any`/force or filename/size-only trust. See the current
[R-OBS2 structural audit](../r-obs2/structural-audit.md) and
[profile schema](../r-obs2/build-profile-schema.md).

Capabilities: active-race Broker capture supported, post-Results native Dump
safe=false, legacy_loading_attract_present=true, registry=merc-id26. Broker
format itself is unchanged. Audit report is [merc-build-audit.json](merc-build-audit.json).
