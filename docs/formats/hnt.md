# `.hnt` format notes (R0)

Status: **CONFIRMED** as a plain-text dependency manifest.

All 54 files are readable ASCII-like text:

- 36 begin with `Model\t[...]` and then `Texture\t[...]` entries;
- 18 begin with `FSTexture\t[...]` entries.

Example course manifest:

```text
Model   [course\france1\france1]
Texture [course\france1\grass-tga]
Texture [course\france1\road-tga]
```

Example frontend manifest entries:

```text
FSTexture [frontend\backgrounds\bg_cupselect_000_000]
FSTexture [frontend\buttons\longbutton_000_000]
```

There are 52 `.hnt` + `.xml` same-stem pairs and two pairs that also have an
`.xml#` file. The entries correspond to extensionless resource stems under
`DataGx`; model stems select `.dx` and texture stems select `.dxt`/2D resources.
The manifest role is **CONFIRMED**; exact loader fallback/search rules are
**UNKNOWN** because the executable was not inspected.
