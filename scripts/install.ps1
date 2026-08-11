$ErrorActionPreference = "Stop"

$SourceDir = [System.IO.Path]::GetFullPath((Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)))
$CommonRoot = if ($env:AGENT_SKILLS_ROOT) { $env:AGENT_SKILLS_ROOT } else { Join-Path $HOME ".agents\skills" }
$Target = [System.IO.Path]::GetFullPath((Join-Path $CommonRoot "feishu2ppt"))

New-Item -ItemType Directory -Force -Path $CommonRoot | Out-Null
if (-not $SourceDir.Equals($Target, [System.StringComparison]::OrdinalIgnoreCase)) {
    if (Test-Path $Target) {
        $Backup = "$Target.backup.$(Get-Date -Format yyyyMMddHHmmss)"
        Move-Item $Target $Backup
    }
    Copy-Item -Recurse -Force $SourceDir $Target
}

$Roots = @(
    $(if ($env:CODEX_SKILLS_ROOT) { $env:CODEX_SKILLS_ROOT } else { Join-Path $HOME ".codex\skills" }),
    $(if ($env:CLAUDE_SKILLS_ROOT) { $env:CLAUDE_SKILLS_ROOT } else { Join-Path $HOME ".claude\skills" })
)
if ($env:WORKBUDDY_SKILLS_ROOT) { $Roots += $env:WORKBUDDY_SKILLS_ROOT }

foreach ($Root in $Roots) {
    New-Item -ItemType Directory -Force -Path $Root | Out-Null
    $Link = [System.IO.Path]::GetFullPath((Join-Path $Root "feishu2ppt"))
    if ($Link.Equals($Target, [System.StringComparison]::OrdinalIgnoreCase)) {
        continue
    }

    $IsCurrent = $false
    if (Test-Path -LiteralPath $Link) {
        $Item = Get-Item -LiteralPath $Link -Force
        foreach ($ExistingTarget in @($Item.Target)) {
            if ($ExistingTarget) {
                $ResolvedTarget = [System.IO.Path]::GetFullPath(
                    $(if ([System.IO.Path]::IsPathRooted($ExistingTarget)) {
                        $ExistingTarget
                    } else {
                        Join-Path (Split-Path -Parent $Link) $ExistingTarget
                    })
                if ($ResolvedTarget.Equals($Target, [System.StringComparison]::OrdinalIgnoreCase)) {
                    $IsCurrent = $true
                }
            }
        }
        if (-not $IsCurrent) {
            $RuntimeBackup = "$Link.runtime-backup.$(Get-Date -Format yyyyMMddHHmmss)"
            Move-Item -LiteralPath $Link -Destination $RuntimeBackup
            Write-Output "Backed up stale runtime entry: $RuntimeBackup"
        }
    }
    if (-not $IsCurrent) {
        New-Item -ItemType Junction -Path $Link -Target $Target | Out-Null
    }
    $Installed = Get-Item -LiteralPath $Link -Force
    if (-not $Installed.Target) {
        throw "Runtime entry verification failed: $Link"
    }
}

Write-Output "Installed: $Target"
