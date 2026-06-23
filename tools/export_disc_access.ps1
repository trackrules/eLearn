param(
    [Parameter(Mandatory = $true)][string]$SourceDatabase,
    [Parameter(Mandatory = $true)][string]$OutputDirectory
)

$ErrorActionPreference = "Stop"
$source = (Resolve-Path -LiteralPath $SourceDatabase).Path
$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "elearn-phase2a5"
New-Item -ItemType Directory -Force -Path $tempRoot, $OutputDirectory | Out-Null
$copy = Join-Path $tempRoot "elearn_2.dat"
Copy-Item -LiteralPath $source -Destination $copy -Force

function Get-Sha256([string]$Path) {
    $stream = [System.IO.File]::OpenRead($Path)
    try {
        $sha = [System.Security.Cryptography.SHA256]::Create()
        try { return ([System.BitConverter]::ToString($sha.ComputeHash($stream))).Replace("-", "") }
        finally { $sha.Dispose() }
    } finally { $stream.Dispose() }
}
$sourceHash = Get-Sha256 $source
$copyHash = Get-Sha256 $copy
if ($sourceHash -ne $copyHash) { throw "Temporary database copy hash mismatch" }

$connection = [System.Data.OleDb.OleDbConnection]::new(
    "Provider=Microsoft.ACE.OLEDB.16.0;Data Source=$copy;Mode=Read;"
)
$connection.Open()

function Export-QueryJsonLines([string]$Name, [string]$Query) {
    $path = Join-Path $OutputDirectory "$Name.jsonl"
    $writer = [System.IO.StreamWriter]::new($path, $false, [System.Text.UTF8Encoding]::new($false))
    try {
        $command = $connection.CreateCommand()
        $command.CommandText = $Query
        $reader = $command.ExecuteReader()
        try {
            while ($reader.Read()) {
                $row = [ordered]@{}
                for ($i = 0; $i -lt $reader.FieldCount; $i++) {
                    $value = $reader.GetValue($i)
                    $row[$reader.GetName($i).ToLowerInvariant()] = if ($value -is [DBNull]) { $null } else { $value }
                }
                $writer.WriteLine(($row | ConvertTo-Json -Compress -Depth 5))
            }
        } finally { $reader.Dispose() }
    } finally { $writer.Dispose() }
}

try {
    Export-QueryJsonLines "model" "SELECT * FROM [MODEL] WHERE LANGUAGE_ID=2"
    Export-QueryJsonLines "language" "SELECT * FROM [LANGUAGE] WHERE ID=2"
    Export-QueryJsonLines "section" "SELECT * FROM [SECTION] WHERE LANGUAGE_ID=2"
    Export-QueryJsonLines "element" "SELECT * FROM [ELEMENT] WHERE LANGUAGE_ID=2"
    Export-QueryJsonLines "xml" "SELECT * FROM [XML] WHERE LANGUAGE_ID=2"
    Export-QueryJsonLines "production" "SELECT * FROM [PRODUCTION] WHERE LANGUAGE_ID=2"
    Export-QueryJsonLines "validity" "SELECT * FROM [VALIDITY] WHERE LANGUAGE_ID=2"
    Export-QueryJsonLines "codep" "SELECT * FROM [CODEP] WHERE LANGUAGE_ID=2"
    foreach ($table in @(
        "ELEMENT_PRODUCTION", "ELEMENT_VALIDITY", "ELEMENT_CODEP",
        "XML_PRODUCTION", "XML_VALIDITY", "XML_CODEP"
    )) { Export-QueryJsonLines $table.ToLowerInvariant() "SELECT * FROM [$table]" }
} finally { $connection.Close() }

[ordered]@{
    source_path = $source
    source_sha256 = $sourceHash
    temporary_copy = $copy
    copy_sha256 = $copyHash
    hashes_match = $true
    provider = "Microsoft.ACE.OLEDB.16.0"
    mode = "Read"
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $OutputDirectory "extraction_metadata.json") -Encoding utf8
