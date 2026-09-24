# retail record 25: constructor audit

Binary: retail `MRallye.exe`, SHA-256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. VAs below are image addresses, with `VA - 0x400000` as file offset in this PE. Static analysis only.

At `0x458CD0`, the singleton constructs 26 records of stride `0x34`, beginning at singleton `+0x04`; record 25 begins at `+0x518`, ends at `+0x54B`, and the second array begins at `+0x54C`. `0x458E70` calls the full initializer `0x45A0B0` for IDs 0–24 only. The default record constructor at `0x45A080` writes `+0x00=0x006903A4` (vtable), `+0x20=0` (empty string pointer), and `+0x24/+0x28/+0x2C/+0x30=0x3F800000` (four float32 1.0 values). It **does not write** `+0x04..+0x1C`. The allocation at `0x45A3C0` goes through MSVC 2003 `operator new` / `__nh_malloc`; no zero-fill contract was established. Thus the constructor cannot establish an ID, class, statistics or the integer at `+0x1C` for record 25. These are indeterminate, not zero.

The full initializer `0x45A0B0` writes ID at `+0x04`, class at `+0x08`, four frontend stat fields at `+0x0C..+0x18` (speed, acceleration, handling and endurance, verified at `0x4819B0`), the further integer at `+0x1C`, constructs a *new owned string* at `+0x20` using `0x4D1990`, and writes four float words at `+0x24..+0x30`. The record destructor `0x458D60` frees `+0x20`. A raw 0x34-byte copy from Astero would alias an owned pointer and risks double-free; a valid clone must construct/copy the string with its ownership rules.

Verified initializer examples from the retail call sites in `0x458E70` (last seven small integer pushes, reversed into field order):

| ID | Build-specific name | Class | +0x0C | +0x10 | +0x14 | +0x18 | +0x1C |
|---:|---|---:|---:|---:|---:|---:|
| 0 | Landcruiser | 0 | 4 | 2 | 4 | 6 | 9 |
| 7 | Navara | 1 | 7 | 6 | 6 | 5 | 13 |
| 14 | Wildcat | 2 | 7 | 6 | 8 | 8 | 3 |
| 16 | Astero | 2 | 6 | 6 | 8 | 8 | 0 |

For Astero, `+0x20` is an owned copy of the `Astero` string passed from literal `0x006B3CB4`; the four float words are `0x3D8B1C04`, `0x3F092D67`, `0x3EF74E40`, `0x3F800000` at the `0x459572` initializer. Their meanings are not established. This gives a concrete normal-vehicle template but not a safe insertion mechanism. A cloned record 25 would need ID **25**, class 2 and otherwise Astero-equivalent contents.

The default state alone does not prove intentional sentinel semantics. It does prove record 25 is **unusable as constructed**. No retail data-only write reaches this compiled initializer.
