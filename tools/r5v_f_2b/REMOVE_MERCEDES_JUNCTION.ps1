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
    if ($null -eq $Item -or ($Item.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) {
        throw "Junction removal refused: exact path is not a reparse point: $linkPath"
    }
    if ($Item.LinkType -ne 'Junction') {
        throw "Junction removal refused: exact path is not a Junction (LinkType=$($Item.LinkType))."
    }
    $targets = @($Item.Target)
    if ($targets.Count -ne 1 -or [string]::IsNullOrWhiteSpace([string]$targets[0])) {
        throw "Junction removal refused: cannot read the actual target of $linkPath."
    }
    $actualTarget = [string]$targets[0]
    if ((Normalize-Path $actualTarget) -ine (Normalize-Path $ExpectedTarget)) {
        throw "Junction removal refused: target '$actualTarget' does not match '$ExpectedTarget'."
    }
}

Write-Output "Exact path considered for removal: $linkPath"
Write-Output "Expected phase target: $sourcePath"
if (-not (Test-Path -LiteralPath $markerPath -PathType Leaf)) {
    throw "Junction removal refused: R5V-F.2b ownership marker is missing: $markerPath"
}
$marker = Get-Content -LiteralPath $markerPath -Raw | ConvertFrom-Json
if ($marker.phase -ne 'R5V-F.2b' -or $marker.state -ne 'created') {
    throw 'Junction removal refused: marker does not record a completed R5V-F.2b setup.'
}
$sourcePath = (Resolve-Path -LiteralPath $sourcePath).ProviderPath
if ((Normalize-Path $marker.link_path) -ine (Normalize-Path $linkPath) -or
    (Normalize-Path $marker.target) -ine (Normalize-Path $sourcePath)) {
    throw 'Junction removal refused: marker path/target differs from this helper.'
}
Assert-AuthoringCopy
$linkItem = Get-ItemIfPresent $linkPath
Assert-ExpectedJunction $linkItem $sourcePath

# Directory.Delete with recursive=false removes only the Junction node.
[IO.Directory]::Delete($linkPath, $false)
if ($null -ne (Get-ItemIfPresent $linkPath)) {
    throw 'Junction removal did not remove the exact link node.'
}
if (-not (Test-Path -LiteralPath $sourcePath -PathType Container)) {
    throw 'The isolated authoring target is unexpectedly absent after link removal.'
}
Assert-AuthoringCopy
Remove-Item -LiteralPath $markerPath -Force

Write-Output 'SAFE REMOVAL: removed only the marked Junction node; target files remain in the isolated workspace.'
Write-Output "Unchanged authoring target: $sourcePath"
