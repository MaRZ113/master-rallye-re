# Retail BrokerEntry, partial layout

Size **0x1C**, 32-bit. `CONFIRMED_BY_EXE`: constructor `004DD980`, setter
families, `00601D00` Dump, `005FE460` filter and `005FE580` Value serializer.

| Offset | Conservative field | Representation |
|---|---|---|
| `+00` | path_id | pooled string ID; also vector index |
| `+04` | payload | owned typed allocation, or direct XmlData object pointer |
| `+08` | type_tag | uint32; `0x0C` empty |
| `+0C` | save_flags | uint32 storage; low bits 1 Game, 2 PlayerState, 4 Options |
| `+10` | revision | uint32, per entry |
| `+14` | scope | uint32; 0 GLOBAL, 1 SCENE, other values displayed USER |
| `+18` | save_file_id | pooled logical filename/category ID |

Constructor/reset initialize empty payload, type 0x0C, revision 0, scope 1,
clear the three save bits, and assign `__NO_SAVE`. Static initializer `004DD950`
interns that label into `006F9474`, used by the entry constructor. Unknown high
save_flags bits are not promoted to new semantics.

Use only as a **retail partial structure**. Pristine demo serializers stride
0x94 with save flags at +0x84. Their inline payload representation needs a
separate type, not this struct with a different base address.
