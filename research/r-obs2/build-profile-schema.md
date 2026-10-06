# Exact build and local profile schema

## Committed exact profile

`build-profiles.json` records exact SHA-256, file size, display/profile name, family, registry profile, PE identity/layout, provenance, and capability flags. The current exact profiles are `retail-pristine` and `retail-merc-id26`. Exact profile checks still rerun the family anchors and compare the full exact PE record.

## Locally audited exact profile

An unknown SHA is not committed into source. After a successful `retail-broker-v1` audit, the developer-local cache writes:

```json
{
  "schema_version": 1,
  "sha256": "<exact file SHA-256>",
  "size": 3121214,
  "profile_id": "local-audited-<12 hex digits>",
  "profile_origin": "locally_audited",
  "compatibility_family": "retail-broker-v1",
  "audit_version": "retail-broker-v1.0",
  "audit_fingerprint": "<canonical audit digest>",
  "vehicle_registry_profile": "merc-id26 | pristine | unknown",
  "capabilities": {"broker_read": true, "native_dump": true}
}
```

The actual JSON also records registry fingerprint provenance and the full capability map. Cache filenames are `<sha256>.json` under `.research-output/observatory/build-profiles/`; no executable bytes are stored or committed.

Every lookup reads the current executable, recomputes SHA-256 and size, reruns the bounded structural audit, checks schema/family/audit fingerprint/capabilities, then reuses the local record only if the complete derived profile matches. A stale, malformed, cross-SHA, or cross-family record is not accepted; the current file is re-audited and a fresh record is written only on success.

## Independent registry profile

`vehicle_registry_profile` is metadata on a build profile, not a Broker-family property. The `merc-id26` detector requires all four exact mapping fingerprints in `registry-profile.json`; strings or filename are insufficient. Unknown registry support still allows generic raw Broker checks but disables ID-to-class/family validation.
