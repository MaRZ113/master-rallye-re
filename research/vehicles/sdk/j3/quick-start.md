# Quick Start — donor-based addon project

This procedure creates an author project without distributing or modifying
game files. Use a legitimate retail source whose exact `Data.sma` matches the
capability profile. Runtime launch is not available for arbitrary addon
identities yet; this guide ends at a verified offline build.

## 1. Create a project

From the repository root:

```powershell
py -3 tools/mrtool.py addon init `
  --name "My Rally Car" `
  --class T2 `
  --donor Navara `
  --family MyRallyCar `
  --donor-source "D:\Games\Master Rallye\DataGx\Vehicles\Navara" `
  --output "D:\Mods\MyRallyCar"
```

`--donor-source` is referenced locally and never copied by `addon init`. The
project's `README.md` explains how to copy your own source resources into
`assets/source/Navara` if you want a portable working folder. Do not publish
stock/demo assets unless you have redistribution rights.

## 2. Author the donor resources

Open the project `vehicle-project.json` with the existing Vehicle Authoring
SDK workflow. Keep donor draw/material identities and use the supported DX,
DXT, bounds and collision operations. See [authoring.md](authoring.md).

## 3. Edit addon identity

Edit `addon.json`: keep `physical_id` on `auto`, assign your own family name,
enter manufacturer/model/combined labels, choose a supported stock frame,
and review the default audio, unlock and AI settings. See [manifest.md](manifest.md).

## 4. Validate

```powershell
py -3 tools/mrtool.py addon project-validate "D:\Mods\MyRallyCar" `
  --retail-data-sma "D:\Games\Master Rallye\Data.sma" `
  --retail-data-root "D:\Games\Master Rallye\Data.sma_unpacked"
```

The paired retail arguments verify the exact pinned archive and compare the
two unpacked DataGame XML inputs byte-for-byte with their archive members.
They are required to generate physics-family overlays.

## 5. Build to a new directory and verify

```powershell
py -3 tools/mrtool.py addon project-build "D:\Mods\MyRallyCar" `
  --retail-data-sma "D:\Games\Master Rallye\Data.sma" `
  --retail-data-root "D:\Games\Master Rallye\Data.sma_unpacked" `
  --output "D:\Mods\Builds\MyRallyCar-build-001"

py -3 tools/mrtool.py addon verify "D:\Mods\Builds\MyRallyCar-build-001"
```

The build contains an offline addon plan, semantic frontend plan, hashed
resource inventory, the independent `DataGx/Vehicles/<family>` dependency
closure, and generated `DataGame/vehicles.xml` / `Modifications.xml` donor
family overlays. `verify` checks the generated files and all artifact hashes.
It deliberately reports `runtime_installable: false`. Do not copy it over the
game installation or launch it with the fixed J.1/J.2 reference launcher.

## Supported target limits

This profile has one additional T1 slot (ID26/local7) and one additional T2
slot (ID27/local7). Only the exact Mercedes and R5VQualifier identities have
runtime qualification. A Glacier Sprint plan may resolve to ID27/T2/local7,
but that identity is not runtime-qualified. A T2-only native runtime profile
is also not yet qualified; the current reference native layer contains a
Mercedes ID26 dependency. The compiler must not hide that dependency.
