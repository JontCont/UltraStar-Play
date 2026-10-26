[CmdletBinding()]
param(
    [string] $MainGameBuildPath = "$PSScriptRoot\..\..\Build\UltraStarPlay-v1.7.1-beta1-Windows64",
    [string] $CompanionBuildPath = "$PSScriptRoot\..\..\Build\UltraStarPlayCompanion-v1.3.4-Windows64",
    [string] $OutputDirectory = "$PSScriptRoot\..\..\Build\Installers",
    [ValidatePattern('^[0-9A-Za-z][0-9A-Za-z.+-]*$')]
    [string] $Version = '1.7.1-beta1-lan-test',
    [string] $IsccPath
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repoRoot = (Resolve-Path -LiteralPath "$PSScriptRoot\..\..").Path

if (-not $IsccPath) {
    $compiler = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($compiler) {
        $IsccPath = $compiler.Source
    }
    else {
        $IsccPath = @(
            "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
            "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
        ) | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
    }
}
if (-not $IsccPath -or -not (Test-Path -LiteralPath $IsccPath -PathType Leaf)) {
    throw 'Inno Setup 6 is required. Install JRSoftware.InnoSetup or pass -IsccPath.'
}

$products = @(
    @{ Key = 'MainGame'; Name = 'UltraStar Play'; Source = $MainGameBuildPath },
    @{ Key = 'Companion'; Name = 'UltraStar Play Companion'; Source = $CompanionBuildPath }
)
foreach ($product in $products) {
    $product.Source = (Resolve-Path -LiteralPath $product.Source).Path
    foreach ($relativePath in @(
        "$($product.Name).exe",
        'UnityPlayer.dll',
        "$($product.Name)_Data\globalgamemanagers",
        "$($product.Name)_Data\Managed",
        'MonoBleedingEdge'
    )) {
        if (-not (Test-Path -LiteralPath (Join-Path $product.Source $relativePath))) {
            throw "Incomplete $($product.Key) Windows Mono player: missing $relativePath"
        }
    }
}

$null = New-Item -ItemType Directory -Path $OutputDirectory -Force
$OutputDirectory = (Resolve-Path -LiteralPath $OutputDirectory).Path
foreach ($product in $products) {
    Write-Host "Packaging $($product.Name) from $($product.Source)"
    & $IsccPath /Q "/DProduct=$($product.Key)" "/DSourceDir=$($product.Source)" `
        "/DRepoRoot=$repoRoot" "/DOutputDir=$OutputDirectory" "/DAppVersion=$Version" `
        "$PSScriptRoot\WindowsPlayer.iss"
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup failed for $($product.Key) with exit code $LASTEXITCODE."
    }
}

$installers = Get-Item -LiteralPath "$OutputDirectory\UltraStarPlay-Windows64-Setup.exe",
    "$OutputDirectory\UltraStarPlayCompanion-Windows64-Setup.exe"
$installers | Get-FileHash -Algorithm SHA256 |
    ForEach-Object { "$($_.Hash)  $([IO.Path]::GetFileName($_.Path))" } |
    Set-Content -LiteralPath "$OutputDirectory\SHA256SUMS.txt" -Encoding ascii
$installers | Select-Object FullName, Length
