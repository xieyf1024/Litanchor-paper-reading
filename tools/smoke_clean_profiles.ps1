[CmdletBinding()]
param(
    [string]$Python = "python",
    [string]$ReportPath,
    [switch]$InstallCoreDependencies
)

$ErrorActionPreference = "Stop"
$sourceRoot = Split-Path -Parent $PSScriptRoot
$temporaryBase = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
$sandboxRoot = Join-Path $temporaryBase ("LitAnchor-RC1-Smoke-" + [guid]::NewGuid().ToString("N"))
$sandboxRoot = [IO.Path]::GetFullPath($sandboxRoot)

if (-not $sandboxRoot.StartsWith($temporaryBase, [StringComparison]::OrdinalIgnoreCase) -or
    -not (Split-Path -Leaf $sandboxRoot).StartsWith("LitAnchor-RC1-Smoke-")) {
    throw "Refusing unsafe smoke root: $sandboxRoot"
}

if (-not $ReportPath) {
    $ReportPath = Join-Path $sourceRoot "docs\v1.0.0-rc1-clean-profile-smoke.json"
}
$ReportPath = [IO.Path]::GetFullPath($ReportPath)

function Invoke-LitAnchorAction {
    param(
        [string]$ReleaseRoot,
        [string]$Action,
        [hashtable]$Profile,
        [string]$Version,
        [switch]$SkipDependencies,
        [switch]$Confirm
    )
    $arguments = @(
        "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", (Join-Path $ReleaseRoot "install.ps1"),
        "-Action", $Action,
        "-Python", $Python,
        "-InstallRoot", $Profile.InstallRoot,
        "-SkillsRoot", $Profile.SkillsRoot,
        "-ConfigPath", $Profile.ConfigPath
    )
    if ($Version) { $arguments += @("-Version", $Version) }
    if ($SkipDependencies) { $arguments += "-SkipDependencies" }
    if ($Confirm) { $arguments += "-Confirm" }
    & powershell @arguments | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "LitAnchor $Action failed for $($Profile.Name)."
    }
}

function Write-Utf8NoBom {
    param([string]$Path, [string]$Content)
    [IO.File]::WriteAllText($Path, $Content, (New-Object Text.UTF8Encoding($false)))
}

function Set-SmokeVersion {
    param([string]$ReleaseRoot, [string]$Version)
    $manifestPath = Join-Path $ReleaseRoot "litanchor-install.json"
    $manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $oldVersion = [string]$manifest.version
    $manifest.version = $Version
    Write-Utf8NoBom -Path $manifestPath -Content (($manifest | ConvertTo-Json -Depth 20) + "`n")
    foreach ($relative in @(
        "skills\litanchor-paper-reading\scripts\autonomous_deep_reading.py",
        "skills\litanchor-paper-reading\scripts\litanchor_local.py",
        "skills\litanchor-paper-reading\scripts\litanchor_setup.py"
    )) {
        $path = Join-Path $ReleaseRoot $relative
        $content = Get-Content -LiteralPath $path -Raw -Encoding UTF8
        Write-Utf8NoBom -Path $path -Content ($content.Replace($oldVersion, $Version))
    }
}

function New-Profile {
    param([string]$Name, [string]$RelativeRoot, [string]$VaultName)
    $root = Join-Path $sandboxRoot $RelativeRoot
    $vault = Join-Path $root $VaultName
    New-Item -ItemType Directory -Force -Path (Join-Path $vault ".obsidian") | Out-Null
    return @{
        Name = $Name
        Root = $root
        InstallRoot = Join-Path $root "Local App Data\LitAnchor"
        SkillsRoot = Join-Path $root "Agent Home\skills"
        ConfigPath = Join-Path $root "Config\litanchor.json"
        VaultPath = $vault
        InboxPath = Join-Path $vault "LitAnchor\00_Inbox"
    }
}

$results = @()
try {
    New-Item -ItemType Directory -Force -Path $sandboxRoot | Out-Null
    $packageDir = Join-Path $sandboxRoot "package"
    & $Python (Join-Path $sourceRoot "tools\build_release.py") --output $packageDir | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Release package build failed." }
    $archive = Get-ChildItem -LiteralPath $packageDir -Filter "*-windows.zip" | Select-Object -First 1
    if (-not $archive) { throw "Release archive was not produced." }
    $expanded = Join-Path $sandboxRoot "expanded"
    Expand-Archive -LiteralPath $archive.FullName -DestinationPath $expanded
    $baseRelease = Get-ChildItem -LiteralPath $expanded -Directory | Select-Object -First 1
    if (-not $baseRelease) { throw "Release archive has no payload root." }

    $releaseA = Join-Path $sandboxRoot "release-a"
    $releaseB = Join-Path $sandboxRoot "release-b"
    Copy-Item -LiteralPath $baseRelease.FullName -Destination $releaseA -Recurse
    Copy-Item -LiteralPath $baseRelease.FullName -Destination $releaseB -Recurse
    $versionA = "0.6.0-beta.3-smoke"
    $versionB = "1.0.0-rc1-smoke"
    Set-SmokeVersion -ReleaseRoot $releaseA -Version $versionA
    Set-SmokeVersion -ReleaseRoot $releaseB -Version $versionB

    $profiles = @(
        (New-Profile -Name "english" -RelativeRoot "English Profile" -VaultName "ResearchVault"),
        (New-Profile -Name "chinese" -RelativeRoot "中文 用户" -VaultName "研究 仓库"),
        (New-Profile -Name "interrupted" -RelativeRoot "Recovery Profile" -VaultName "RecoveryVault")
    )

    foreach ($profile in $profiles) {
        $skipDependencies = -not ($InstallCoreDependencies -and $profile.Name -eq "english")
        Invoke-LitAnchorAction -ReleaseRoot $releaseA -Action Install -Profile $profile -SkipDependencies:$skipDependencies

        & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $releaseA "litanchor.ps1") `
            setup -InstallRoot $profile.InstallRoot -ConfigPath $profile.ConfigPath `
            -VaultPath $profile.VaultPath -Inbox "LitAnchor\00_Inbox" `
            -MinerUConsent never -CreateInbox | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Setup failed for $($profile.Name)." }

        $samplePdf = Join-Path $profile.Root "sample.pdf"
        [IO.File]::WriteAllBytes($samplePdf, [Text.Encoding]::ASCII.GetBytes("%PDF-1.4`n% LitAnchor run-plan smoke`n"))
        $sampleNote = Join-Path $profile.Root "sample.md"
        & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $releaseA "litanchor.ps1") `
            run-plan -InstallRoot $profile.InstallRoot -ConfigPath $profile.ConfigPath `
            -PdfPath $samplePdf -OutputNote $sampleNote -ReadingMode deep | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Direct-PDF run-plan failed for $($profile.Name)." }

        if ($profile.Name -eq "interrupted") {
            $active = Join-Path $profile.SkillsRoot "litanchor-paper-reading"
            $backup = Join-Path $profile.SkillsRoot ".litanchor-paper-reading.litanchor-previous"
            $staging = Join-Path $profile.SkillsRoot ".litanchor-paper-reading.litanchor-next"
            Copy-Item -LiteralPath $active -Destination $backup -Recurse
            New-Item -ItemType Directory -Force -Path $staging | Out-Null
            Set-Content -LiteralPath (Join-Path $staging "partial.txt") -Value "interrupted" -Encoding UTF8
            Invoke-LitAnchorAction -ReleaseRoot $releaseA -Action Repair -Profile $profile -SkipDependencies
            if ((Test-Path -LiteralPath $backup) -or (Test-Path -LiteralPath $staging)) {
                throw "Repair left interrupted activation artifacts behind."
            }
        }

        Invoke-LitAnchorAction -ReleaseRoot $releaseB -Action Upgrade -Profile $profile -SkipDependencies:$skipDependencies
        Invoke-LitAnchorAction -ReleaseRoot $releaseB -Action Rollback -Profile $profile -Version $versionA -SkipDependencies
        Invoke-LitAnchorAction -ReleaseRoot $releaseB -Action Uninstall -Profile $profile -Confirm

        if (Test-Path -LiteralPath (Join-Path $profile.SkillsRoot "litanchor-paper-reading")) {
            throw "Uninstall left the active Skill behind for $($profile.Name)."
        }
        if (-not (Test-Path -LiteralPath $profile.ConfigPath -PathType Leaf)) {
            throw "Uninstall removed the preserved config for $($profile.Name)."
        }
        if (-not (Test-Path -LiteralPath $profile.VaultPath -PathType Container)) {
            throw "Lifecycle actions removed the Vault for $($profile.Name)."
        }
        $results += [ordered]@{
            profile = $profile.Name
            path_kind = if ($profile.Name -eq "chinese") { "non_ascii_and_spaces" } else { "ascii_and_spaces" }
            install = "pass"
            setup = "pass"
            direct_pdf_run_plan = "pass"
            interrupted_repair = if ($profile.Name -eq "interrupted") { "pass" } else { "not_applicable" }
            upgrade = "pass"
            rollback = "pass"
            uninstall = "pass"
            config_preserved = $true
            vault_preserved = $true
            dependencies = if ($skipDependencies) { "skipped_lifecycle_only" } else { "installed_core" }
        }
    }

    $report = [ordered]@{
        schema_version = "1.0"
        generated_at = (Get-Date).ToUniversalTime().ToString("o")
        status = "pass"
        scope = "isolated application profiles in one Windows user context"
        limitation = "This validates lifecycle isolation and path behavior; it is not independent-user usability evidence."
        profiles = $results
    }
    Write-Utf8NoBom -Path $ReportPath -Content (($report | ConvertTo-Json -Depth 10) + "`n")
    Write-Output $ReportPath
}
finally {
    $resolvedSandbox = [IO.Path]::GetFullPath($sandboxRoot)
    if ($resolvedSandbox.StartsWith($temporaryBase, [StringComparison]::OrdinalIgnoreCase) -and
        (Split-Path -Leaf $resolvedSandbox).StartsWith("LitAnchor-RC1-Smoke-") -and
        (Test-Path -LiteralPath $resolvedSandbox)) {
        Remove-Item -LiteralPath $resolvedSandbox -Recurse -Force
    }
}
