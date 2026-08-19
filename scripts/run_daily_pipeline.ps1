[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$projectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$backendDirectory = Join-Path $projectRoot "backend"
$environmentFile = Join-Path $projectRoot ".env"
$logDirectory = Join-Path $projectRoot "logs"
$uvPath = Join-Path $env:USERPROFILE ".local\bin\uv.exe"

if (-not (Test-Path -LiteralPath $backendDirectory -PathType Container)) {
    throw "Backend directory was not found."
}
if (-not (Test-Path -LiteralPath $environmentFile -PathType Leaf)) {
    throw "Project .env file was not found."
}
if (-not (Test-Path -LiteralPath $uvPath -PathType Leaf)) {
    $uvCommand = Get-Command uv.exe -ErrorAction SilentlyContinue
    if ($null -eq $uvCommand) {
        throw "uv.exe was not found."
    }
    $uvPath = $uvCommand.Source
}

New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
$retentionLimit = (Get-Date).AddDays(-30)
Get-ChildItem -LiteralPath $logDirectory -Filter "daily-pipeline-*.log" -File |
    Where-Object { $_.LastWriteTime -lt $retentionLimit } |
    Remove-Item -Force

$logFile = Join-Path $logDirectory ("daily-pipeline-{0}.log" -f (Get-Date -Format "yyyy-MM-dd"))
$startedAt = Get-Date
"[{0}] scheduler_script_started" -f $startedAt.ToString("o") |
    Add-Content -LiteralPath $logFile -Encoding utf8

Set-Location -LiteralPath $backendDirectory
$ErrorActionPreference = "Continue"
& $uvPath run python -m security_daily.jobs.daily 2>&1 |
    ForEach-Object {
        $line = $_.ToString()
        Write-Output $line
        $line | Add-Content -LiteralPath $logFile -Encoding utf8
    }
$exitCode = $LASTEXITCODE
$ErrorActionPreference = "Stop"

$finishedAt = Get-Date
"[{0}] scheduler_script_finished exit_code={1}" -f $finishedAt.ToString("o"), $exitCode |
    Add-Content -LiteralPath $logFile -Encoding utf8

exit $exitCode
