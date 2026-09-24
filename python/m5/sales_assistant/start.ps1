# Start the mock mail server, then launch langgraph dev.
# Run from PowerShell: .\start.ps1
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$LangGraphArgs
)

$ErrorActionPreference = "Stop"
$scriptDir = $PSScriptRoot

# Stop any process left listening on the mock mail server port.
$oldProcessIds = @(
    Get-NetTCPConnection -LocalPort 5002 -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
)

foreach ($processId in $oldProcessIds) {
    Write-Host "Port 5002 already in use (PID $processId) - stopping it ..."
    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
}

if ($oldProcessIds.Count -gt 0) {
    Start-Sleep -Seconds 1
}

$originalPythonUtf8 = $env:PYTHONUTF8
$env:PYTHONUTF8 = "1"
$mailProcess = $null

try {
    Write-Host "Starting mock mail server on http://127.0.0.1:5002 ..."
    $mailScript = Join-Path $scriptDir "mcp\mock_mail_server.py"
    $mailProcess = Start-Process `
        -FilePath "uv" `
        -ArgumentList "run", "python", "`"$mailScript`"" `
        -WorkingDirectory $scriptDir `
        -NoNewWindow `
        -PassThru

    $mailReady = $false
    for ($attempt = 1; $attempt -le 10; $attempt++) {
        $mailProcess.Refresh()
        if ($mailProcess.HasExited) {
            throw "The mock mail server exited before it became ready."
        }

        if (Test-NetConnection 127.0.0.1 -Port 5002 -InformationLevel Quiet -WarningAction SilentlyContinue) {
            $mailReady = $true
            break
        }

        Start-Sleep -Seconds 1
    }

    if (-not $mailReady) {
        throw "The mock mail server did not become ready within 10 seconds."
    }

    Write-Host "Mail server up (PID $($mailProcess.Id)). Starting langgraph dev ..."
    Set-Location $scriptDir
    & uv run langgraph dev @LangGraphArgs

    if ($LASTEXITCODE -ne 0) {
        throw "langgraph dev exited with code $LASTEXITCODE."
    }
}
finally {
    if ($null -ne $mailProcess) {
        $mailProcess.Refresh()
        if (-not $mailProcess.HasExited) {
            & taskkill.exe /PID $mailProcess.Id /T /F 2>$null | Out-Null
        }
    }

    if ($null -eq $originalPythonUtf8) {
        Remove-Item Env:PYTHONUTF8 -ErrorAction SilentlyContinue
    }
    else {
        $env:PYTHONUTF8 = $originalPythonUtf8
    }
}
