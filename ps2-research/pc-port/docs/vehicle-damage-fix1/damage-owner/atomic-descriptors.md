# Atomic private-tree source certificate: descriptor contract

Bounded REA/Ghidra12.1.4 original retail x86 analysis, EXE bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4. Original PE-mapped byte windows accompany separate compact function/allocator evidence. No renderer/source integration or build by this reviewer.

## Paths from owned current mesh

Let G=[006f9cf0], M=[G+28] (native buffer manager).

* Leaf+38 points to material-vector object. Original00576910 reads begin at+4/end at+8; number=(end-begin)/4. Queue00562560 emits one24-byte record per material index i: [instance,mesh,i,...], so queue record+8 is the subindex, not always0.
* Index handle=[leaf+24]. Original568ab0 uses QI=[M+2c], tableBegin=[QI+8], indexDesc=[tableBegin+12*handle].
* Vertex handle array=[leaf+18]. Original576a1e..2b loads handle=handleArray[subindex]. Original568660 uses QV=[M+28], tableBegin=[QV+8], vertexDesc=[tableBegin+12*handle]. If returned pointer isnull, original emitter uses [instance+a4] as explicit fallback vertexdescriptor; ifbothnull it logs Could not draw compiled model and returns.
* Vertexdescriptor24bytes: +0 buffer-holder, +4allocation record, +8minvertex, +cvertexcount, +10FVF, +14stride. Actual native/proxy VB is [[vertexDesc]].
* Indexdescriptor20bytes: +0buffer-holder,+4allocation,+8startindex,+cindexcount,+10D3DFORMAT. Actual native/proxy IB is [[indexDesc]]. OriginalDIP is type4, min=vertexDesc+8,count=vertexDesc+c,start=indexDesc+8,triangles=indexDesc+c divided3.

These are direct original instruction consumers, not reconstructed guessed offsets. Both568420(VB) and568880(IB) allocator functions prove table objects use begin+8/end+c,12-byteentries, with capacity check handle<(end-begin)/12. Bounded read-only extraction must check pointer/overflow/alignment, end>=begin, divisibility12, handlewithinrange andnonzero descriptor. Table lookupfunctions themselves omitbounds; do notinheritunsafeomission.

## Per-material variation and conservative admission

Do not assume commonFVF/stride oronebufferforall13sources. Native descriptors are selected through each owned leaf andmaterialindex; minvertex arises from pooled byteoffset/stride. Match all13sources uniquely by exact sourcecertificate, notrootordinal alone. For simplest first atomic certificate, explicitly requirematerialCount==1 foreachselectedleaf beforeusingindex0; otherwise fallback orenumerateprovedsubindices withcompletecoverage. Alwayscrosscheck the trigger draw's looked-updescriptors againstalreadyvalidatedcurrentstackdescriptors.

Importantpreparation boundary: emitter576978..6987 calls optional [leaf+44] virtual+4(leaf) beforedescriptorlookup. No proof was collected that thisoptionalcallback neverchangesfutureleafVB/descriptors. Conservativelyrequirecallbacknullforall13atomic-readleaves, orproveitsconcretebehaviorbeforeclaimingpre-drawdataequalslaternativeDIP. Recheck selectedownerlist, descriptors andallmirrorgeneration/revisiontokens aftersnapshotandimmediatelybeforecommit. Noenginefunctioninvocationisrequired/authorized.

The descriptorcontract is sufficient totryboundedall13currentownedtreesnapshotbeforefirstreplacement, withfailclosedifanyfuturebufferuploadnotavailable. ItdoesnotjustifycarryinglastframepositionsorrelaxingUV/windingchecks tohideaone-frameblink. Runtimecomparisonmustmeasurewhetherthecorrectprivatecopiesalreadyhavecompleteuploadsatthefirsttrigger.
