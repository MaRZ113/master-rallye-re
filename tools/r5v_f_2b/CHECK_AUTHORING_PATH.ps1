$ErrorActionPreference = 'Stop'

$phaseRoot = Split-Path -Parent $PSScriptRoot
$sourcePath = Join-Path $phaseRoot 'authoring-root\Mercedes'
$linkPath = 'D:\projects\MRallyeTNG\DataGx\Vehicles\Mercedes'
$markerPath = Join-Path $phaseRoot 'junction-created.json'
$manifestPath = Join-Path $phaseRoot 'source-manifest.json'

function Normalize-Path([string] $Path) {
    return [IO.Path]::GetFullPath($Path).TrimEnd([char[]]@('\', '/'))
}

function Get-ItemIfPresent([string] $Path) {
    try { return Get-Item -Force -LiteralPath $Path -ErrorAction Stop }
    catch [System.Management.Automation.ItemNotFoundException] { return $null }
    catch [System.Management.Automation.DriveNotFoundException] { return $null }
}

function Assert-AuthoringCopy {
    $sourceItem = Get-ItemIfPresent $sourcePath
    if ($null -eq $sourceItem -or -not $sourceItem.PSIsContainer) {
        throw "Authoring source directory is absent: $sourcePath"
    }
    if (($sourceItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Authoring source must be an ordinary directory: $sourcePath"
    }
    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    $expected = @($manifest.source.files | Where-Object { $_.name -like '*.gxi' })
    $actual = @(Get-ChildItem -LiteralPath $sourcePath -File -Force)
    if ($expected.Count -ne 25 -or $actual.Count -ne $expected.Count) {
        throw "Expected exactly 25 copied GXI files; found $($actual.Count)."
    }
    foreach ($entry in $expected) {
        $filePath = Join-Path $sourcePath $entry.name
        if (-not (Test-Path -LiteralPath $filePath -PathType Leaf)) {
            throw "Copied authoring file is missing: $filePath"
        }
        $actualHash = (Get-FileHash -LiteralPath $filePath -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actualHash -ne $entry.sha256.ToLowerInvariant()) {
            throw "Copied authoring file hash mismatch: $($entry.name)"
        }
    }
}

function Assert-ExpectedJunction($Item, [string] $ExpectedTarget) {
    if (($Item.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) {
        throw "Existing authoring path is not a reparse point: $linkPath"
    }
    if ($Item.LinkType -ne 'Junction') {
        throw "Existing authoring path is not a Junction (LinkType=$($Item.LinkType)): $linkPath"
    }
    $targets = @($Item.Target)
    if ($targets.Count -ne 1 -or [string]::IsNullOrWhiteSpace([string]$targets[0])) {
        throw "Cannot read Junction target: $linkPath"
    }
    $actualTarget = [string]$targets[0]
    if ((Normalize-Path $actualTarget) -ine (Normalize-Path $ExpectedTarget)) {
        throw "Existing authoring junction target mismatch: actual '$actualTarget', expected '$ExpectedTarget'"
    }
}

Write-Output "Authoring link path: $linkPath"
Write-Output "Expected isolated target: $sourcePath"
Assert-AuthoringCopy
$sourcePath = (Resolve-Path -LiteralPath $sourcePath).ProviderPath
$linkItem = Get-ItemIfPresent $linkPath
$marker = $null
if (Test-Path -LiteralPath $markerPath -PathType Leaf) {
    $marker = Get-Content -LiteralPath $markerPath -Raw | ConvertFrom-Json
}

if ($null -eq $linkItem) {
    if ($null -ne $marker) { throw "Authoring path is absent but a phase marker exists; inspect manually: $markerPath" }
    Write-Output 'SAFE STATE: exact authoring path is absent; setup helper may create the junction.'
    exit 0
}

if ($null -eq $marker -or $marker.phase -ne 'R5V-F.2b' -or
    $marker.state -notin @('creating', 'created')) {
    throw "Authoring path exists without a completed R5V-F.2b ownership marker. Nothing was changed."
}
if ((Normalize-Path $marker.link_path) -ine (Normalize-Path $linkPath) -or
    (Normalize-Path $marker.target) -ine (Normalize-Path $sourcePath)) {
    throw 'R5V-F.2b ownership marker path/target mismatch. Nothing was changed.'
}
Assert-ExpectedJunction $linkItem $sourcePath
if ($marker.state -eq 'creating') {
    Write-Output 'RECOVERABLE STATE: exact R5V-F.2b Junction verified; run the setup helper to mark it created.'
    exit 0
}
Write-Output 'SAFE STATE: exact R5V-F.2b Junction and target verified; existing link may be reused.'
