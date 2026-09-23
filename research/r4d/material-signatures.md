# R4D neutral material signatures

CONFIRMED_BY_CORPUS: all 1,478 draws store three texture slots; slot 2 is always Null.
Signatures use slot count, Null mask, draw tag, and raw flags_0x20 bytes. Cluster IDs assert no runtime semantic type.

| Cluster | Draws | Structural signature |
|---|---:|---|
| CLUSTER_A | 708 | slots=3;null=001;tag=2;f20=00000101 |
| CLUSTER_B | 356 | slots=3;null=011;tag=2;f20=00000101 |
| CLUSTER_C | 121 | slots=3;null=001;tag=2;f20=00000001 |
| CLUSTER_D | 71 | slots=3;null=001;tag=7;f20=01000101 |
| CLUSTER_E | 71 | slots=3;null=001;tag=8;f20=01000101 |
| CLUSTER_F | 64 | slots=3;null=001;tag=2;f20=01000101 |
| CLUSTER_G | 14 | slots=3;null=001;tag=2;f20=01000001 |
| CLUSTER_H | 14 | slots=3;null=001;tag=7;f20=00000001 |
| CLUSTER_I | 13 | slots=3;null=001;tag=8;f20=00000101 |
| CLUSTER_J | 11 | slots=3;null=001;tag=7;f20=00000101 |
| CLUSTER_K | 11 | slots=3;null=011;tag=2;f20=01000001 |
| CLUSTER_L | 9 | slots=3;null=011;tag=8;f20=00000001 |
| CLUSTER_M | 6 | slots=3;null=011;tag=2;f20=01000101 |
| CLUSTER_N | 3 | slots=3;null=101;tag=2;f20=00000101 |
| CLUSTER_O | 2 | slots=3;null=001;tag=8;f20=00000001 |
| CLUSTER_P | 2 | slots=3;null=111;tag=2;f20=00000100 |
| CLUSTER_Q | 1 | slots=3;null=011;tag=2;f20=00000001 |
| CLUSTER_R | 1 | slots=3;null=011;tag=8;f20=00000101 |

## Slot 1 recurrence

| Texture | Bindings |
|---|---:|
| Null | 386 |
| whitepaint-tga | 222 |
| perspex-tga | 221 |
| rubber-tga | 220 |
| glass-tga | 220 |
| chrome-tga | 145 |
| silverpaint-tga | 60 |
| lightshine-tga | 2 |
| lights-tga | 2 |

The first non-Null slot is a preview choice. Runtime stage mapping and combination remain UNKNOWN.
