# Third-party reference — separate historical layout

Read/disassembled, never executed: MasterRallyeWidescreenFix.exe SHA256 `e0de5489b3b512d174024397eac0d54dc2afd8f3f2c13933a0c3881f75860814`,1,404,483 bytes, PE32/I386 GCC, ImageBase0x400000,entryRVA0x14E0,COFF/DWARF main **VA0x00401500/RVA0x1500**. Historical MRallye_patched.exe SHA256 `bcf310a79133b03aa89ce51197a37516ee27c1b0e9da19788519e849e7a2f2f6`,3,117,118 bytes. Archive hash remains user-provided: archive unavailable for rehash; extracted inputs independently verified.

Latest installed Ghidra12.1.4 onD: and local ghidra-bridge exporter used. Pristine queries: read-only domain objects, transaction rollback/no save. Patcher: new ignored scratch project, main export pcode_errors=[]; no existing project mutation. Raw outputs/provenance remain ignored. Deterministic quality_research.py hashes four inputs before code/cave interpretation.

Actual main file-write branches corroborate embedded assembler references:

| Option | Old-layout behavior |
|---|---|
| 1 FOV only | Branch old file0xF2325, FOV cave0x28DF7C; UI width640; restore FSUB/FLD at0x109711. |
| 2 centered UI | Same FOV; orthographic bounds via0x161B2C/0x161B34; stock FSUB/FLD restored. |
| 3 preserve margins | Same widened projection, jump0x109711 -> coordinate cave0x2AC444; half-extra shifts for selected points/text bands. |

Old VAs0x004F2325,0x00509711,0x00561B2C/34,0x0068DF7C/A9,0x006AC444 belong to reference PE. None are installed on pristine. Section mapping, not arithmetic on arbitrary file offsets, determines VA/RVA.

Main computes aspect=width/height, virtual_width=480*aspect, extra=virtual_width-640. Directly read constants at patcher VA0x0048D62C/RVA0x0008D62C float480;0x0048D630/RVA0x0008D630 float640;0x0048D648/RVA0x0008D648 float2;0x0048D64C/RVA0x0008D64C float-2. Options2/3 bounds left=-extra/2,right=640+extra/2; source coordinates remain640x480, not globally scaled.

FOV cave writes67.5*aspect*user_multiplier and33.75*aspect*user_multiplier. Verified doubles at VA0x0048D638/RVA0x0008D638 and0x0048D640/RVA0x0008D640. Equivalent to original90/45*aspect*0.75*multiplier; **reference only, no reuse**. Existing modern VFOV+CPU culling remains owner, preview45 unchanged.

Historical coordinate cave VA0x006AC444/RVA0x002AC444 has162 reviewed CMP/branch instructions. Bounded Capstone interpreter recovers51 exact points and left text bands x[25,106],y[19,100) or[259,340),z=0. Right points add half-extra,left subtract,others centered. [Rules](margin-rules.json) agree with native header. Apparent border/text anchoring is STATIC_INFERENCE; exact UI element names unproved. This is compatibility behavior, not universal layout metadata.

Current general UI projection seam is cleaner for Centered4x3. No proved left/right anchor metadata covers every packet, so PreserveMargins retains **documented compatibility exceptions** only in a strongly identified 2D packet branch. Old mode3 menu alignment risk remains human work. [Pristine mapping](widescreen-integration.md).
