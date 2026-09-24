# Full initializer ABI — retail `0x45A0B0`

`RAW_GHIDRA_SUPPORTED`. The callee takes `ECX = VehicleRecord*` and returns with `ret 0x30`, consuming twelve stack dwords. Callers create 16 bytes of float arguments, a temporary owned name string, then push seven integers right-to-left. The pointer to the temporary string is the eighth stack argument. This is a Microsoft x86 `thiscall`-shaped ABI with callee stack cleanup, not the short signature suggested by incomplete decompilation. There is no hidden result pointer observed.

Conceptual signature (semantic names after the first two fields are tentative):

```cpp
void VehicleRecord::initialize(
    int id, int vehicleClass, int stat0, int stat1, int stat2,
    int stat3, int extraInteger, OwnedTemporaryString name,
    float f0, float f1, float f2, float f3);
```

| Input | Caller source / callee use | Destination | Confidence |
|---|---|---|---|
| `ECX` | `lea ecx,[esi+offset]`; `mov esi,ecx` | base record | high |
| stack 1 | first integer after call frame | `+0x04`, stored ID | high |
| stack 2 | second integer | `+0x08`, class | high |
| stack 3–6 | four integer immediates | `+0x0c,+0x10,+0x14,+0x18`, displayed stats | high for offsets, medium for individual stat labels |
| stack 7 | seventh integer | `+0x1c`, purpose untyped | high for offset, low for meaning |
| stack 8 | temporary string pointer from `0x4D11D0` | deep-copied to `+0x20` by `0x4D1990` | high |
| stack 9–12 | caller's reserved 16-byte area | `+0x24,+0x28,+0x2c,+0x30` | high for offsets, low for meaning |

Raw call windows: ID0/class0 `0x458ED8` (`Landcruiser`, record `[esi+0x4]`); ID7/class1 `0x4591B8` (`Navara`, `[esi+0x170]`); ID16/class2 `0x459572` (`Astero`, `[esi+0x344]`). Integer push sequences respectively: `9,6,4,2,4,0,0`; `13,5,6,6,7,1,7`; `0,8,8,6,6,2,16`. The last push becomes stack argument 1. Astero float bit patterns: `3D8B1C04, 3F092D67, 3EF74E40, 3F800000`. Callee stores all seven ints and four floats; the call sites do not clean the 0x30 bytes.

The decompiler's apparent fewer parameters are a `CONFLICT` with raw stack setup and `ret 0x30`; raw ABI wins. ReAgent reconstruction was unavailable, so there is no ReAgent/Ghidra agreement claim.
