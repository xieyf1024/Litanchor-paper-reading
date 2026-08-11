[CmdletBinding()]
param(
    [Parameter(Position = 0, Mandatory = $true)]
    [ValidateSet("doctor", "setup", "discover-vaults", "run-plan")]
    [string]$Command,
    [string]$InstallRoot,
    [string]$ConfigPath,
    [string]$Vault,
    [string]$VaultPath,
    [string]$Inbox = "LitAnchor\00_Inbox",
    [ValidateSet("always_for_eligible_files", "ask_each_time", "never")]
    [string]$MinerUConsent,
    [switch]$CreateInbox,
    [string]$RegistryPath,
    [string]$Paper,
    [string]$PdfPath,
    [string]$OutputNote,
    [ValidateSet("title", "doi", "citekey", "item_key")]
    [string]$Selector = "title",
    [ValidateSet("skim", "deep", "internalize")]
    [string]$ReadingMode = "deep",
    [ValidateSet("json", "human")]
    [string]$Format = "json",
    [switch]$CheckMinerUNetwork,
    [switch]$SupportBundle,
    [string]$SupportBundlePath
)

$ErrorActionPreference = "Stop"
if (-not $InstallRoot) {
    if ($env:LOCALAPPDATA) {
        $InstallRoot = Join-Path $env:LOCALAPPDATA "LitAnchor"
    } else {
        $InstallRoot = Join-Path $HOME ".litanchor"
    }
}
if (-not $ConfigPath) {
    $ConfigPath = Join-Path $InstallRoot "config.json"
}

$statePath = Join-Path $InstallRoot "install-state.json"
$python = $null
$skillPath = $null
if (Test-Path -LiteralPath $statePath -PathType Leaf) {
    $state = Get-Content -LiteralPath $statePath -Encoding UTF8 | ConvertFrom-Json
    $python = $state.venv_python
    $skillPath = $state.active_skill_path
}
if (-not $python -or -not (Test-Path -LiteralPath $python -PathType Leaf)) {
    $python = "python"
}
if (-not $skillPath) {
    $skillPath = Join-Path $PSScriptRoot "skills\litanchor-paper-reading"
}
$setupScript = Join-Path $skillPath "scripts\litanchor_setup.py"
if (-not (Test-Path -LiteralPath $setupScript -PathType Leaf)) {
    throw "LitAnchor setup entry point is missing: $setupScript"
}

$arguments = @($setupScript, $Command)
if ($Command -ne "discover-vaults") {
    $arguments += @("--config-path", $ConfigPath)
}
if ($Command -eq "discover-vaults") {
    if ($RegistryPath) { $arguments += @("--registry-path", $RegistryPath) }
} elseif ($Command -eq "setup") {
    if ($VaultPath) {
        $arguments += @("--vault-path", $VaultPath)
    } elseif ($Vault) {
        $arguments += @("--vault", $Vault)
    } else {
        throw "Setup requires -Vault or -VaultPath."
    }
    if (-not $MinerUConsent) {
        throw "Setup requires -MinerUConsent."
    }
    $arguments += @("--inbox", $Inbox, "--mineru-consent", $MinerUConsent)
    if ($RegistryPath) { $arguments += @("--registry-path", $RegistryPath) }
    if ($CreateInbox) { $arguments += "--create-inbox" }
} elseif ($Command -eq "doctor") {
    $arguments += @("--format", $Format)
    if ($Paper) { $arguments += @("--paper-title", $Paper) }
    if ($CheckMinerUNetwork) { $arguments += "--check-mineru-network" }
    if ($SupportBundlePath) {
        $arguments += @("--support-bundle", $SupportBundlePath)
    } elseif ($SupportBundle) {
        $arguments += "--support-bundle"
    }
} else {
    if ([bool]$Paper -eq [bool]$PdfPath) {
        throw "Run-plan requires exactly one of -Paper or -PdfPath."
    }
    if ($PdfPath) {
        $arguments += @("--pdf-path", $PdfPath, "--reading-mode", $ReadingMode)
        if ($OutputNote) { $arguments += @("--output-note", $OutputNote) }
    } else {
        $arguments += @("--paper", $Paper, "--selector", $Selector, "--reading-mode", $ReadingMode)
        if ($Vault) { $arguments += @("--vault", $Vault) }
    }
}
& $python @arguments
exit $LASTEXITCODE
