[CmdletBinding()]
param(
    [ValidateSet("Install", "Upgrade", "Repair", "Rollback", "Uninstall", "Status")]
    [string]$Action = "Install",
    [string]$Python = "python",
    [string]$InstallRoot,
    [string]$SkillsRoot,
    [string]$ConfigPath,
    [string]$Version,
    [switch]$IncludeMinerU,
    [switch]$Confirm,
    [switch]$RemoveConfig,
    [switch]$SkipDependencies
)

$ErrorActionPreference = "Stop"
$sourceRoot = $PSScriptRoot
$manager = Join-Path $sourceRoot "tools\litanchor_manager.py"

if (-not (Test-Path -LiteralPath $manager -PathType Leaf)) {
    throw "LitAnchor installation manager is missing: $manager"
}

try {
    & $Python --version | Out-Null
} catch {
    throw "Python 3.10 or newer was not found. Install supported 64-bit Python, then ask the Agent to resume LitAnchor installation."
}
if ($LASTEXITCODE -ne 0) {
    throw "Python 3.10 or newer was not found. Install supported 64-bit Python, then ask the Agent to resume LitAnchor installation."
}

$arguments = @($manager)
if ($InstallRoot) { $arguments += @("--install-root", $InstallRoot) }
if ($SkillsRoot) { $arguments += @("--skills-root", $SkillsRoot) }
if ($ConfigPath) { $arguments += @("--config-path", $ConfigPath) }
$arguments += $Action.ToLowerInvariant()
if ($IncludeMinerU) { $arguments += "--include-mineru" }
if ($Confirm) { $arguments += "--confirm" }
if ($RemoveConfig) { $arguments += "--remove-config" }
if ($Version) { $arguments += @("--version", $Version) }
if ($SkipDependencies) { $arguments += "--skip-dependencies" }

& $Python @arguments
exit $LASTEXITCODE
