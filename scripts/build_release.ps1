[CmdletBinding()]
param(
    [string]$ReleaseTag,
    [switch]$SkipInstall,
    [switch]$SkipTests,
    [switch]$SkipAudit,
    [switch]$SkipFirmware,
    [switch]$AllowDirty
)

$ErrorActionPreference = "Stop"
$root = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [string[]]$ArgumentList = @()
    )

    & $FilePath @ArgumentList
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $FilePath $($ArgumentList -join ' ')"
    }
}

function Remove-GeneratedDirectory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RelativePath
    )

    $target = [IO.Path]::GetFullPath((Join-Path $root $RelativePath))
    $rootPrefix = $root.TrimEnd([IO.Path]::DirectorySeparatorChar) +
        [IO.Path]::DirectorySeparatorChar
    if (-not $target.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove a path outside the repository: $target"
    }
    if (Test-Path -LiteralPath $target) {
        Remove-Item -LiteralPath $target -Recurse -Force
    }
}

Push-Location $root
try {
    if (-not $AllowDirty) {
        $status = & git status --porcelain
        if ($LASTEXITCODE -ne 0) {
            throw "Unable to inspect repository status."
        }
        if ($status) {
            throw "Release builds require a clean worktree. Commit or stash changes, or pass -AllowDirty for a local diagnostic build."
        }
    }

    if (-not $SkipInstall) {
        Invoke-Checked "python" @("-m", "pip", "install", "--upgrade", "pip")
        $extras = if ($SkipFirmware) { ".[dev]" } else { ".[dev,firmware]" }
        Invoke-Checked "python" @("-m", "pip", "install", "-e", $extras)
        Invoke-Checked "python" @("-m", "pip", "check")
    }

    $versionArguments = @("scripts/check_release.py")
    if (-not [string]::IsNullOrWhiteSpace($ReleaseTag)) {
        $versionArguments += $ReleaseTag
    }
    Invoke-Checked "python" $versionArguments
    Invoke-Checked "python" @("scripts/scan_secrets.py")
    Invoke-Checked "python" @("-m", "ruff", "check", ".")
    Invoke-Checked "python" @("-m", "ruff", "format", "--check", ".")
    Invoke-Checked "python" @("-m", "mypy")

    if (-not $SkipTests) {
        Invoke-Checked "python" @(
            "-m", "pytest",
            "--cov=src",
            "--cov-report=term-missing",
            "--cov-report=xml"
        )
    }
    if (-not $SkipAudit) {
        Invoke-Checked "python" @(
            "-m", "pip_audit", "--strict", "--requirement", "requirements.txt"
        )
    }

    Remove-GeneratedDirectory "build"
    Remove-GeneratedDirectory "dist"
    Invoke-Checked "python" @("-m", "build", "--no-isolation")
    Invoke-Checked "python" @("-m", "twine", "check", "dist/*")
    Invoke-Checked "python" @(
        "-m", "PyInstaller", "--clean", "--noconfirm", "streamdeck_control.spec"
    )
    Invoke-Checked "python" @("scripts/check_pyinstaller.py")

    if (-not $SkipFirmware) {
        Invoke-Checked "pio" @("run", "-d", "firmware", "-e", "uno_active_high")
        Invoke-Checked "pio" @(
            "run", "-d", "firmware", "-e", "uno_internal_pullup"
        )
    }

    Write-Host "Release candidates are available under dist/."
}
finally {
    Pop-Location
}
