[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$taskName = "SecurityDaily-DailyPipeline"
$projectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$backendDirectory = Join-Path $projectRoot "backend"
$runnerPath = Join-Path $PSScriptRoot "run_daily_pipeline.ps1"

if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    throw "Scheduled Task '$taskName' already exists. No changes were made."
}

$powershellPath = Join-Path $PSHOME "powershell.exe"
$action = New-ScheduledTaskAction `
    -Execute $powershellPath `
    -Argument "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$runnerPath`"" `
    -WorkingDirectory $backendDirectory
$trigger = New-ScheduledTaskTrigger -Daily -At "08:30"
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2)
$principal = New-ScheduledTaskPrincipal `
    -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) `
    -LogonType Interactive `
    -RunLevel Limited

$task = New-ScheduledTask `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Run the Security Daily pipeline every day at 08:30 KST."

Register-ScheduledTask -TaskName $taskName -InputObject $task | Out-Null
Write-Output "TaskName=$taskName"
Write-Output "Schedule=Daily 08:30"
Write-Output "WorkingDirectory=$backendDirectory"
Write-Output "Runner=$runnerPath"
