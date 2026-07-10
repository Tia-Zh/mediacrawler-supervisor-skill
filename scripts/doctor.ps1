param(
    [string]$CollectorHome = $(if ($env:MEDIASPIDER_HOME) { $env:MEDIASPIDER_HOME } elseif ($env:PUBLICSCOPE_HOME) { $env:PUBLICSCOPE_HOME } else { $env:MEDIACRAWLER_HOME }),
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

function Find-MediaSpider($Provided) {
    $candidates = @()
    if ($Provided) { $candidates += $Provided }
    $candidates += Join-Path $HOME ".data_assistant\engines\MediaSpider"
    $candidates += Join-Path $HOME ".data_assistant\engines\PublicScopeCollector"
    $candidates += Join-Path $HOME ".data_assistant\engines\MediaCrawler"
    $candidates += Join-Path (Get-Location) "MediaSpider"
    $candidates += Join-Path (Get-Location) "PublicScopeCollector"
    $candidates += Join-Path (Get-Location) "MediaCrawler"
    $candidates += Join-Path (Get-Location) "engines\MediaCrawler"

    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path (Join-Path $candidate "main.py")) -and (Test-Path (Join-Path $candidate "pyproject.toml"))) {
            return (Resolve-Path $candidate).Path
        }
    }
    return ""
}

$foundHome = Find-MediaSpider $CollectorHome
$checks = [ordered]@{
    mediaCrawlerHome = $foundHome
    mediaCrawlerFound = [bool]$foundHome
    dataAssistantCleanupPatch = $false
    dataAssistantCleanupPlatforms = @()
    dataAssistantCleanupMissing = @()
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

if ($foundHome) {
    $platforms = @("douyin", "kuaishou", "xhs", "bilibili", "weibo", "tieba", "zhihu")
    foreach ($platform in $platforms) {
        $corePath = Join-Path $foundHome "media_platform\$platform\core.py"
        if (Test-Path $corePath) {
            $text = Get-Content -LiteralPath $corePath -Encoding UTF8 -Raw
            if ($text.Contains("async def data_assistant_cleanup_pages") -and $text.Contains("await self.data_assistant_cleanup_pages()")) {
                $checks.dataAssistantCleanupPlatforms += $platform
            } else {
                $checks.dataAssistantCleanupMissing += $platform
            }
        } else {
            $checks.dataAssistantCleanupMissing += $platform
        }
    }
    $checks.dataAssistantCleanupPatch = ($checks.dataAssistantCleanupMissing.Count -eq 0)
}

if (-not $checks.mediaCrawlerFound) { $checks.warnings += "MediaSpider not found. Set MEDIASPIDER_HOME or run bootstrap.ps1." }
if (-not $checks.git.found) { $checks.warnings += "git is missing; bootstrap cannot clone MediaCrawler." }
if (-not $checks.uv.found) { $checks.warnings += "uv is missing; install uv before dependency sync." }
if (-not $checks.node.found) { $checks.warnings += "node is missing; some MediaCrawler platforms require Node.js." }
if (-not $checks.chromeLikely) { $checks.warnings += "Chrome/Edge was not found in common locations; CDP login may fail." }
if ($checks.mediaCrawlerFound -and -not $checks.dataAssistantCleanupPatch) {
    $checks.warnings += "MediaCrawler is missing the Data Assistant stale-tab cleanup patch for: $($checks.dataAssistantCleanupMissing -join ', '). Run bootstrap.ps1 to update to the adapted version."
}

if ($Json) {
    $checks | ConvertTo-Json -Depth 5
} else {
    "MediaSpider doctor"
    "Collector found: $($checks.mediaCrawlerFound)"
    "Collector home : $($checks.mediaCrawlerHome)"
    "Cleanup patch    : $($checks.dataAssistantCleanupPatch)"
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
