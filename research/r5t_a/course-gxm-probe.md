# Course GXM probe (R5T-A)

The two demo 8.4.1 France1/Italy1 sources have a 32-byte header. At body offset 0x20 the observed first uint16 values are 40159 and 49007; those values exceed the existing generic parser's 4,096-byte length bound if read using its vehicle-side string-prefix assumption. That assumption is not established for course GXM. No geometry/hierarchy parser is claimed.

| Source | Bytes | Header word at 0x0C vs TXT materials | Word at 0x18 vs TXT mesh span | Word 0x10 = 3×0x18 | First u16 at 0x20 |
|---|---:|---|---|---|---:|
| `demo-8.4.1/DataGx/Course/France1/France1.gxm` | 11489135 | True | True | True | 40159 |
| `demo-8.4.1/DataGx/Course/Italy1/track01.gxm` | 8728347 | True | True | True | 49007 |

Header relations above were checked against same-build TXT and are `CONFIRMED_BY_SOURCE_COMPILED_PAIR` only for those count relations. They do not establish the body layout or directive runtime meaning.

The JSON retains same-build TXT material names, directive-bearing source lines, mesh names/counts and source spans alongside the raw GXM header probe. These TXT records are source-side oracle data, not proof of GXM body structure. The GXM reader boundary is the post-header body at 0x20; GXM hierarchy, geometry and source-to-DX mapping remain UNKNOWN.
