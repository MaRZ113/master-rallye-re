# Four separate state contracts

| Field | Original PC static prediction | Selected live PC | PS2 executable mode2 | Pilot implementation |
|---|---|---|---|---|
| Alpha test | On,GREATER128 | UNKNOWN | Disabled | No change |
| Alpha blend | Off | UNKNOWN | Enabled,(Cs−Cd)*As/128+Cd | No change |
| Depth writes | On | UNKNOWN | ZMSK1 masked | No change |
| Depth comparison | Native PC | UNKNOWN | GEQUAL with inheritedZTE | No change |
| Culling/stages | Native PC | UNKNOWN | Remaining inherited fields bounded | No change |
| Texture | Stock PC bush01 | Binding pending | PS2 course bush01 | Stock PC |

Original PC flags1/1/1/1 and feature mask3 predict generic_alphatest. This is STATIC_PC_INFERENCE supported by original engine research, not LIVE_PC_PROXY_OBSERVATION. TREEBLEND1 callback003ae618,mode2,state producer00312610/mode branch00313270 and queue bucket1 are PS2_EXECUTABLE_CONTRACT.

After the identity gate, the proposed **not implemented** D3D8 approximation is alpha test FALSE,blend TRUE,SRCALPHA/INVSRCALPHA,ZWRITEFALSE. Preserve ZENABLE,ZFUNC,CULLMODE and other states. As/255 versus PS2As/128, texture/vertex-alpha conversion and queue ordering preclude pixel-exact claims. Do not amplify alpha or force GEQUAL in this checkpoint.

The new probe obtains12 native render states and8 stage states for each of stages0/1, native WORLD and material diffuse alpha, bound resources and referenced vertex diffuse-alpha range when supported. Null values remain unknown. Sampling is before the existing reflection scope, which remains responsible for its own native TCI override. Probe getter state must not be represented as an active foliage override or as the state of unrelated later reflection writes.
