# Research bridge and modular implementation

The new DLL source includes the frozen R-AI1.2 runtime and unchanged policy.
MRChooseV1 is unchanged; MRChallengeV1 becomes a lifecycle dispatcher. The legacy
Challenge body is not exported or called. Small header Roster owns process-local
cache semantics. No general randomizer redesign, driver override, save or sidecar.

| New retail site | Purpose |
|---|---|
| 45EC35, seven bytes | Original authored EDI load followed by prepare/cache result; only saved EDI is replaced |
| 45E511, five bytes | Clear at Challenge screen initialization; tail-jump to original4E3DD0 with original stack |
| 45EA9A, five bytes | Clear on Challenge Back; tail-jump to original45D910 preserving screen2 argument |
| 68EF00 | Preview bridge in verified zero padding |
| 68EF60 /68EF90 | Entry/Back reset bridges in verified zero padding |

Existing R-AI1.2 selectors/loader, hardening and optional five-car shim retain
their exact bytes. Header VirtualSize grows to cover the new bounded padding;
no .rdata/IAT write, physical storage expansion or loop-bound change. Full
manifest inverse restores the exact pristine hash, then reproduction matches
the candidate byte-for-byte. Original/replacement payload bytes are only in
ignored generated manifests; [safe build summary](build-summary.json) stores
range hashes, offsets, lengths and purposes.

DLL verifies exact on-disk supported EXE hash/size and live immutable bridge
bytes before game calls. Only the two exact new research profiles are supported;
unknown builds fail closed. Existing adjacent-DLL loader, failure fallback and
four audited Observatory implementation pins remain unchanged.

Diagnostic log retains one original Challenge generation group and adds
PreviewV1 Begin/Use records: serial,event,policy,ID,class,config hash,PID.
Begin appears once; redraw has no generation log; Use consumes the same record
without RNG/config reload. These are external diagnostics, not native Broker
state, and cannot prove actors or UI visibility.

Reproduce from pristine: `python tools/r_ai1_2_build_native.py --source
<exact-pristine-MRallye.exe> --output .research-output/r-ai1-2a/package
--challenge-preview`. Verify with `tools/r_ai1_2a_preview.py verify` and
`verify-module`. Restore the isolated game copy from its preserved original EXE
and remove the research DLL/INI; do not distribute proprietary research EXEs.
