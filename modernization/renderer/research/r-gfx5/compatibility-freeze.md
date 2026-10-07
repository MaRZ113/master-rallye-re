# Optional freeze fix — process memory only

Reference freeze-patch.py SHA256 `6719605fb97b59f6d11a480bf8b6e6f223c726cfff1b656862fd2a9640b02b1b`,2619bytes,read/not executed. Old file0x24A1BC `75 11 ->75 00`, old MD5 and permissive unknown attempt are not reused. Only independently correlated semantics.

Pristine **VA0x005B015C/RVA0x001B015C**, independently verified exact retail:

```text
Context VA0x005B015A/RVA0x001B015A:
85 ff 75 11 8b 44 24 10 8b 4e 18 50 e8 15 2f 0a 00 ff 44 24 14 84 db
005B015A TEST EDI,EDI
005B015C JNE 005B016F                  ;75 11
005B015E render-call arguments
005B0166 CALL 00653080                 ;RVA001B0166 ->ownerRVA00253080
005B016B increment counter
005B016F TEST BL,...
```

75 00 targets immediate fallthrough005B015E: either ZF outcome reaches original render call/counter rather than skipping them. Control flow CONFIRMED_BY_EXE; universal freeze efficacy HYPOTHESIS. Interior queries are not new function-boundary proof; stable branch/call VAs above are canonical.

MenuFreezeFix=false default. Install once at Root8::CreateDevice outside DllMain: exact pristine disk hash,ImageBase400000,full loaded context. Write only displacement byte **VA0x005B015D/RVA0x001B015D**. VirtualProtect/write/readback/FlushInstructionCache/protection restoration required; failure rolls back original and reports rollback. Unknown hash/context/opcode/placement skipped. Matching already75 00 recognized without rewrite/ownership.

No jump into DLL/disk write/candidate EXE. Byte persists until process exit even after device release; restart with false maps original again. No unload restoration needed because no DLL address is referenced. Log expected hash/RVA/context-valid/applied/already/ownership/rollback/reason. Tests inject protection/write/flush failures and demand original-byte rollback.

Render-skip branch fix is **SEPARATE** from media/no-CD,loading hardening and Attract. Healthy pristine A/B reproduction with restarts is required. If initial freeze cannot be reproduced, efficacy is untested rather than PASS.
