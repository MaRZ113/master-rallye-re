# Master Rallye Observatory v0.2.3-beta

## What's new

- Fixed live native Dump anchor matching for the exact retail reference: the canonical anchor VA is converted to an RVA using the audited PE image base before it is compared with the resolved runtime profile.
- The comparison continues to require the exact walker length, SHA256, and PE section. The stock walker and the separately audited J.1 NULL-safe walker remain the only accepted in-memory variants.
- J.1 hardened Results Dump classification still requires the pristine retail executable identity, the audited mapped image, the complete exact walker, both exact trampoline targets and instruction bytes, valid null/continuation paths, and unchanged required Broker anchors. Unknown or altered state fails closed.

## Compatibility and safety

The supported on-disk retail executable remains SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` at 3,121,214 bytes. Live process memory is verified independently; the pristine file identity does not by itself grant hardened Results Dump safety. Observatory remains read-only and does not inject code or write process memory.

## Verification

The release was built from the explicit standalone allowlist and checked for archive-member integrity, import closure, forbidden/proprietary files, and clean-extraction command behavior. Archive and member hashes are recorded in the generated release manifest.

## Limitations

- Windows live-process capture remains a runtime validation step.
- Compatible build recognition does not imply compatibility with arbitrary modified executables.
- No game executable, assets, saves, raw captures, screenshots, or profile cache is included.
