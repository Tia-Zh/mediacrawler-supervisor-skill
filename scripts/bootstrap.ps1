param(
    [string]$InstallRoot = (Join-Path $HOME ".data_assistant\engines"),
    [string]$RepoUrl = "https://github.com/NanmiCoder/MediaCrawler.git",
    [switch]$SkipPlaywrightInstall
)

$ErrorActionPreference = "Stop"

function Require-Command($Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Missing command '$Name'. Install it first, then rerun bootstrap.ps1."
    }
}

Require-Command "git"
Require-Command "uv"

$target = Join-Path $InstallRoot "MediaCrawler"
New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null

if (Test-Path (Join-Path $target "main.py")) {
    Write-Host "MediaCrawler already exists at $target"
} else {
    Write-Host "Cloning MediaCrawler into $target"
    git clone $RepoUrl $target
}

Push-Location $target
try {
    Write-Host "Syncing Python dependencies with uv"
    uv sync

    if (-not $SkipPlaywrightInstall) {
        Write-Host "Installing Playwright browser drivers"
        uv run playwright install
    }

    Write-Host ""
    Write-Host "Bootstrap complete."
    Write-Host "Set MEDIACRAWLER_HOME to: $target"
    Write-Host "Review MediaCrawler LICENSE and platform terms before running collection tasks."
} finally {
    Pop-Location
}
