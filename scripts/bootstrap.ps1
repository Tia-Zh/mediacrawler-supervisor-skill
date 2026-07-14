param(
    [string]$InstallRoot = (Join-Path $HOME ".data_assistant\engines"),
    [string]$RepoUrl = "https://github.com/Tia-Zh/MediaSpider.git",
    [string]$RepoRef = "mediaspider-v0.2.2",
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

$target = Join-Path $InstallRoot "MediaSpider"
New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null

if (Test-Path (Join-Path $target "main.py")) {
    Write-Host "MediaSpider already exists at $target"
} else {
    Write-Host "Cloning MediaSpider into $target"
    Write-Host "Source: $RepoUrl"
    git clone $RepoUrl $target
}

Push-Location $target
try {
    if (Test-Path ".git") {
        $dirty = git status --porcelain
        if ($dirty) {
            Write-Warning "MediaSpider has local changes. Skipping automatic checkout of $RepoRef."
            Write-Warning "Review the changes, then update manually if this is not intentional."
        } else {
            Write-Host "Updating MediaSpider to $RepoRef"
            git fetch --tags origin
            git checkout $RepoRef
        }
    } else {
        Write-Warning "MediaSpider exists but is not a git checkout. Cannot automatically update to $RepoRef."
        Write-Warning "Install into a new directory or replace it with MediaSpider if the compatibility patch is missing."
    }

    Write-Host "Syncing Python dependencies with uv"
    uv sync

    if (-not $SkipPlaywrightInstall) {
        Write-Host "Installing Playwright browser drivers"
        uv run playwright install
    }

    Write-Host ""
    Write-Host "Bootstrap complete."
    Write-Host "Set MEDIASPIDER_HOME to: $target"
    Write-Host "Default source is MediaSpider, based on MediaCrawler."
    Write-Host "Default version is: $RepoRef"
    Write-Host "Review MediaCrawler LICENSE and platform terms before running collection tasks."
} finally {
    Pop-Location
}
