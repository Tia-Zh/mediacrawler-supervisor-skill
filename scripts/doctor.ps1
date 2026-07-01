param(
    [string]$MediaCrawlerHome = $env:MEDIACRAWLER_HOME,
    [switch]$Json
)

$ErrorActionPreference = "SilentlyContinue"

function Test-Command($Name) {
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    return [bool]$cmd
}

function Get-VersionLine($Command, $Arguments) {
    try {
        $output = & $Command @Arguments 2>&1 | Select-Object -First 1
        return [string]$output
    } catch {
        return ""
    }
}

function Find-MediaCrawler($Provided) {
    $candidates = @()
    if ($Provided) { $candidates += $Provided }
    $candidates += Join-Path $HOME ".data_assistant\engines\MediaCrawler"
    $candidates += Join-Path (Get-Location) "MediaCrawler"
    $candidates += Join-Path (Get-Location) "engines\MediaCrawler"

    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path (Join-Path $candidate "main.py")) -and (Test-Path (Join-Path $candidate "pyproject.toml"))) {
            return (Resolve-Path $candidate).Path
        }
    }
    return ""
}

$foundHome = Find-MediaCrawler $MediaCrawlerHome
$checks = [ordered]@{
    mediaCrawlerHome = $foundHome
    mediaCrawlerFound = [bool]$foundHome
    git = [ordered]@{ found = Test-Command "git"; version = "" }
    uv = [ordered]@{ found = Test-Command "uv"; version = "" }
    python = [ordered]@{ found = Test-Command "python"; version = "" }
    node = [ordered]@{ found = Test-Command "node"; version = "" }
    chromeLikely = $false
    warnings = @()
}

if ($checks.git.found) { $checks.git.version = Get-VersionLine "git" @("--version") }
if ($checks.uv.found) { $checks.uv.version = Get-VersionLine "uv" @("--version") }
if ($checks.python.found) { $checks.python.version = Get-VersionLine "python" @("--version") }
if ($checks.node.found) { $checks.node.version = Get-VersionLine "node" @("--version") }

$chromePaths = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "$env:LocalAppData\Google\Chrome\Application\chrome.exe",
    "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
    "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"
)
$checks.chromeLikely = [bool]($chromePaths | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1)

if (-not $checks.mediaCrawlerFound) { $checks.warnings += "MediaCrawler not found. Set MEDIACRAWLER_HOME or run bootstrap.ps1." }
if (-not $checks.git.found) { $checks.warnings += "git is missing; bootstrap cannot clone MediaCrawler." }
if (-not $checks.uv.found) { $checks.warnings += "uv is missing; install uv before dependency sync." }
if (-not $checks.node.found) { $checks.warnings += "node is missing; some MediaCrawler platforms require Node.js." }
if (-not $checks.chromeLikely) { $checks.warnings += "Chrome/Edge was not found in common locations; CDP login may fail." }

if ($Json) {
    $checks | ConvertTo-Json -Depth 5
} else {
    "MediaCrawler doctor"
    "MediaCrawler found: $($checks.mediaCrawlerFound)"
    "MediaCrawler home : $($checks.mediaCrawlerHome)"
    "git              : $($checks.git.found) $($checks.git.version)"
    "uv               : $($checks.uv.found) $($checks.uv.version)"
    "python           : $($checks.python.found) $($checks.python.version)"
    "node             : $($checks.node.found) $($checks.node.version)"
    "Chrome/Edge       : $($checks.chromeLikely)"
    if ($checks.warnings.Count) {
        ""
        "Warnings:"
        $checks.warnings | ForEach-Object { "- $_" }
    }
}
