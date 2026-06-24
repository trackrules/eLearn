param(
    [string]$SourceDirectory = "D:\image",
    [string]$DestinationDirectory = (Join-Path $PSScriptRoot "..\data\disc-assets")
)

$ErrorActionPreference = "Stop"
$source = (Resolve-Path -LiteralPath $SourceDirectory).Path
New-Item -ItemType Directory -Force -Path $DestinationDirectory | Out-Null
$destination = (Resolve-Path -LiteralPath $DestinationDirectory).Path

function Get-Sha256([string]$Path) {
    $stream = [System.IO.File]::OpenRead($Path)
    try {
        $sha = [System.Security.Cryptography.SHA256]::Create()
        try { return ([System.BitConverter]::ToString($sha.ComputeHash($stream))).Replace("-", "") }
        finally { $sha.Dispose() }
    } finally { $stream.Dispose() }
}

$sourceFiles = Get-ChildItem -LiteralPath $source -Filter "*.image" -File
$verified = 0
foreach ($file in $sourceFiles) {
    $target = Join-Path $destination $file.Name
    $sourceHash = Get-Sha256 $file.FullName
    $targetHash = if (Test-Path -LiteralPath $target) { Get-Sha256 $target } else { $null }
    if ($sourceHash -ne $targetHash) {
        Copy-Item -LiteralPath $file.FullName -Destination $target -Force
    }
    if ((Get-Sha256 $target) -ne $sourceHash) { throw "Disc asset hash mismatch: $($file.Name)" }
    $verified++
}

$destinationFiles = Get-ChildItem -LiteralPath $destination -Filter "*.image" -File
if ($destinationFiles.Count -ne $sourceFiles.Count) {
    throw "Disc asset cache count mismatch: source=$($sourceFiles.Count), destination=$($destinationFiles.Count)"
}

[ordered]@{
    source = $source
    destination = $destination
    file_count = $destinationFiles.Count
    byte_count = ($destinationFiles | Measure-Object Length -Sum).Sum
    sha256_verified_files = $verified
    source_untouched = $true
} | ConvertTo-Json
