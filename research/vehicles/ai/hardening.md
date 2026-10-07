# R5V-H.0.1 neutral research hardening

This file records two quality-of-life fixes composed for safe research runs,
plus the independent ID26 Results-name presentation fix. None changes vehicle
physics, resource identity, the stock AI pool, or participant capacity.

## Legacy Loading -> Attract false trigger

At VA `0x00464F69` / file offset `0x064F69`, retail bytes
`68 84 1F 6B 00` are replaced with `E9 D8 FF FF FF`, a relative jump to the
existing path at `0x00464F46`. This bypasses the obsolete loading media-check
false-trigger path. The idle-main-menu Attract owner is not patched. The
exact false-trigger was not isolated by the later H.0.1 human test and remains
`UNKNOWN` at runtime.

## Native Debug->Dump null guards

The stock native formatter dereferences nullable values:

| Site | Retail bytes | Guard/helper | Null continuation |
|---|---|---|---|
| StringList, VA `0x0060201E`, offset `0x20201E` | `8B 7B 04 3B 7B 08` | Hook to `0x0068E6D0`; `TEST EBX,EBX` before replaying stock begin/end loads | formatter cleanup at `0x00602040` |
| XmlData, VA `0x00602153`, offset `0x202153` | `8B 10 8B C8 FF 52 0C` | Hook to `0x0068E6F0`; `TEST EAX,EAX` before replaying the stock vtable call | formatter cleanup at `0x0060218E` |

Non-null paths replay the displaced instructions and resume at `0x00602024`
and `0x0060215A` respectively. These guards make the native textual dump a
safety representation; an emitted empty `{}` cannot distinguish a NULL list
payload from an allocated empty list. Human runtime confirmed native Dump
survival and continuation after the NULL StringList. The separate XmlData
guard remains unisolated at runtime.

## ID26 Results name selector

The group-`0x39` Results-name policies are documented in
[race-results-identity.md](race-results-identity.md). H.0.1 maps only AI
display selector CarID 26 to the participant's already-selected DriverID and
is runtime-confirmed for its tested rows. H.1 uses a fixed
`JEAN-PIERRE STRUGO` Results display for physical ID26 after the exact demo
selector audit; native DriverID selection remains untouched. The H.1 fixed
display still awaits its own natural-pool runtime test.

## Composition and code layout

All changes are built from pristine retail `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`, then the committed G.1 ID26 vehicle and G.2 audio-profile-0 compositions. The ordinary profile contains no forced CarID hook and no randomizer. The forced profile adds only the existing bounded H.0 proof hook at `0x00458428` and its 50-byte stub at `0x0068E690..0x0068E6C2`; that hook is deterministic proof scaffolding, not a randomizer.

The new helpers occupy these disjoint ranges:

| VA range | Purpose |
|---|---|
| `0x0068E6D0..0x0068E6E3` | StringList null guard (19 bytes) |
| `0x0068E6F0..0x0068E704` | XmlData null guard (20 bytes) |
| `0x0068E720..0x0068E73B` | ID26 Results-name selector (27 bytes) |

The G.1 registry/display payload ends at `0x0068E679`, G.2's audio wrapper
ends at `0x0068E68F`, and the forced proof stub ends at `0x0068E6C2`. The new
ranges do not overlap those payloads or one another. Final `.text`
VirtualSize is `0x28D73B`; `.rdata` begins at RVA `0x28F000`.

## Current candidate profiles

| Profile | SHA256 | Size | Forced H hook | Randomizer |
|---|---|---:|---:|---:|
| `ordinary-hardened` | `391d5d864699b6e945eed43fd8e7bc28b28639b24b222428ab79231e7cc3a819` | 3,121,214 | no | no |
| `forced-id26-ai-hardened` | `9255c9d7cb27336d0a5324bd193719c768f09f5bb7d37e30bab384031b0de0e7` | 3,121,214 | yes, Car1 only | no |
| `natural-t1-id26` | `e59895776dd53acb3ac4a25e1973c8de341da815b90407ec372b696be06d363a` | 3,121,214 | no; natural T1 pool | no |

The `ordinary-hardened` EXE is a separate stock-path research base for tests
that must not include either forced AI selection or an opponent randomizer.
Both EXEs are generated only under ignored `.research-output`; source,
candidate, manifest, resource package, and runtime root are hash-verified by
the builder and package verifier.

The H.0.1 native StringList Dump guard is **CONFIRMED_BY_RUNTIME**. The XmlData
guard and exact Loading->Attract trigger remain **STATICALLY VERIFIED / runtime
not isolated**. The H.1 natural T1 package composes the hardened base, but its
natural selection and fixed Results identity remain pending human validation.
