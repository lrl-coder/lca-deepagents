# Start the mock mail server, the chat UI, then launch langgraph dev.
# Run from PowerShell: .\start.ps1

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptDir = $PSScriptRoot
$mailProcess = $null
$uiProcess = $null
$deepAgentsUiProcess = $null

function Get-NativeCommandPath {
    param([Parameter(Mandatory)][string] $Name)

    $command = Get-Command "$Name.cmd" -CommandType Application -ErrorAction SilentlyContinue
    if (-not $command) {
        $command = Get-Command $Name -CommandType Application -ErrorAction Stop
    }
    return $command.Source
}

function Get-PackageManagerCommand {
    param([Parameter(Mandatory)][string] $Name)

    $command = Get-Command "$Name.cmd" -CommandType Application -ErrorAction SilentlyContinue
    if (-not $command) {
        $command = Get-Command $Name -CommandType Application -ErrorAction SilentlyContinue
    }
    if ($command) {
        return [pscustomobject]@{
            FilePath = $command.Source
            PrefixArguments = @()
        }
    }

    # Current Node.js releases can run project-pinned pnpm/yarn through Corepack.
    return [pscustomobject]@{
        FilePath = Get-NativeCommandPath 'corepack'
        PrefixArguments = @($Name)
    }
}

function Stop-ProcessTree {
    param([System.Diagnostics.Process] $Process)

    if (-not $Process -or $Process.HasExited) {
        return
    }

    # taskkill /T also stops children created by pnpm/yarn (for example next dev).
    & taskkill.exe /PID $Process.Id /T /F 2>$null | Out-Null
}

function Stop-ListenersOnPort {
    param([Parameter(Mandatory)][int] $Port)

    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    $processIds = @($connections | Select-Object -ExpandProperty OwningProcess -Unique)
    foreach ($processId in $processIds) {
        if ($processId -le 4) {
            Write-Warning "Port $Port is owned by system process $processId and cannot be stopped."
            continue
        }

        Write-Host "Port $Port already in use (PID $processId) - stopping it ..."
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
    }
}

function Test-TcpPort {
    param(
        [Parameter(Mandatory)][string] $HostName,
        [Parameter(Mandatory)][int] $Port,
        [int] $TimeoutMilliseconds = 1000
    )

    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $asyncResult = $client.BeginConnect($HostName, $Port, $null, $null)
        if (-not $asyncResult.AsyncWaitHandle.WaitOne($TimeoutMilliseconds)) {
            return $false
        }
        $client.EndConnect($asyncResult)
        return $true
    }
    catch {
        return $false
    }
    finally {
        $client.Dispose()
    }
}

$uv = Get-NativeCommandPath 'uv'
$pnpm = Get-PackageManagerCommand 'pnpm'
$previousPythonUtf8 = [Environment]::GetEnvironmentVariable('PYTHONUTF8', 'Process')
$hadPythonUtf8 = Test-Path Env:PYTHONUTF8

foreach ($port in 5002, 3000, 3001) {
    Stop-ListenersOnPort -Port $port
}

try {
    # This environment's python-dotenv uses the Windows default encoding when
    # reading ../../.env. Force UTF-8 so non-ASCII comments do not fail on GBK.
    $env:PYTHONUTF8 = '1'

    Write-Host 'Starting mock mail server on http://127.0.0.1:5002 ...'
    $mockMailServer = Join-Path $scriptDir 'mcp\mock_mail_server.py'
    $mailProcess = Start-Process -FilePath $uv `
        -ArgumentList @('run', 'python', "`"$mockMailServer`"") `
        -WorkingDirectory $scriptDir -NoNewWindow -PassThru

    $agentChatUiDir = [IO.Path]::GetFullPath((Join-Path $scriptDir '..\..\..\agent-chat-ui'))
    if (-not (Test-Path -LiteralPath $agentChatUiDir -PathType Container)) {
        throw "agent-chat-ui directory not found: $agentChatUiDir"
    }

    if (-not (Test-Path -LiteralPath (Join-Path $agentChatUiDir 'node_modules') -PathType Container)) {
        Write-Host 'Installing agent-chat-ui dependencies (pnpm install) ...'
        Push-Location $agentChatUiDir
        try {
            $pnpmInstallArguments = @($pnpm.PrefixArguments) + @('install')
            & ($pnpm.FilePath) @pnpmInstallArguments
            if ($LASTEXITCODE -ne 0) {
                throw "pnpm install failed with exit code $LASTEXITCODE."
            }
        }
        finally {
            Pop-Location
        }
    }

    $envFile = if ($env:ENV_FILE) {
        $env:ENV_FILE
    }
    else {
        Join-Path $agentChatUiDir '..\python\.env'
    }
    if (-not [IO.Path]::IsPathRooted($envFile)) {
        $envFile = [IO.Path]::GetFullPath((Join-Path $agentChatUiDir $envFile))
    }

    $node = Get-NativeCommandPath 'node'
    $readKeyScript = "const parsed = require('dotenv').config({path: process.argv[1], override: true, quiet: true}).parsed || {}; process.stdout.write(parsed.LANGSMITH_API_KEY || '')"
    Push-Location $agentChatUiDir
    try {
        $correctKey = (& $node -e $readKeyScript $envFile | Out-String).Trim()
        if ($LASTEXITCODE -ne 0) {
            throw "Could not read LANGSMITH_API_KEY from $envFile."
        }
    }
    finally {
        Pop-Location
    }
    if (-not $correctKey) {
        throw "Could not read LANGSMITH_API_KEY from $envFile - check that the file exists and has the key set."
    }

    Write-Host 'Starting agent-chat-ui on http://localhost:3000 ...'
    $previousLangSmithKey = [Environment]::GetEnvironmentVariable('LANGSMITH_API_KEY', 'Process')
    $hadLangSmithKey = Test-Path Env:LANGSMITH_API_KEY
    try {
        $env:LANGSMITH_API_KEY = $correctKey
        $uiArguments = @($pnpm.PrefixArguments) + @('run', 'dev')
        $uiProcess = Start-Process -FilePath $pnpm.FilePath -ArgumentList $uiArguments `
            -WorkingDirectory $agentChatUiDir -NoNewWindow -PassThru
    }
    finally {
        if ($hadLangSmithKey) {
            $env:LANGSMITH_API_KEY = $previousLangSmithKey
        }
        else {
            Remove-Item Env:LANGSMITH_API_KEY -ErrorAction SilentlyContinue
        }
    }

    # Optional side-by-side UI. It is not required by the lesson.
    $deepAgentsUiDir = Join-Path ([Environment]::GetFolderPath('UserProfile')) 'Documents\Github\deep-agents-ui'
    if (Test-Path -LiteralPath $deepAgentsUiDir -PathType Container) {
        $yarn = Get-PackageManagerCommand 'yarn'
        if (-not (Test-Path -LiteralPath (Join-Path $deepAgentsUiDir 'node_modules') -PathType Container)) {
            Write-Host 'Installing deep-agents-ui dependencies (yarn install) ...'
            Push-Location $deepAgentsUiDir
            try {
                $yarnInstallArguments = @($yarn.PrefixArguments) + @('install')
                & ($yarn.FilePath) @yarnInstallArguments
                if ($LASTEXITCODE -ne 0) {
                    throw "yarn install failed with exit code $LASTEXITCODE."
                }
            }
            finally {
                Pop-Location
            }
        }

        Write-Host 'Starting deep-agents-ui on http://localhost:3001 ...'
        $deepAgentsUiArguments = @($yarn.PrefixArguments) + @('dev', '--port', '3001')
        $deepAgentsUiProcess = Start-Process -FilePath $yarn.FilePath -ArgumentList $deepAgentsUiArguments `
            -WorkingDirectory $deepAgentsUiDir -NoNewWindow -PassThru
    }

    # Wait until the mock mail server accepts connections (up to 10 seconds).
    foreach ($attempt in 1..10) {
        if (Test-TcpPort -HostName '127.0.0.1' -Port 5002) {
            break
        }
        Start-Sleep -Seconds 1
    }

    Write-Host "Mail server up (PID $($mailProcess.Id)), chat UI starting (PID $($uiProcess.Id)). Starting langgraph dev ..."
    Push-Location $scriptDir
    try {
        & $uv run langgraph dev --n-jobs-per-worker 10
        if ($LASTEXITCODE -ne 0) {
            throw "langgraph dev exited with code $LASTEXITCODE."
        }
    }
    finally {
        Pop-Location
    }

}
finally {
    Stop-ProcessTree -Process $deepAgentsUiProcess
    Stop-ProcessTree -Process $uiProcess
    Stop-ProcessTree -Process $mailProcess

    Write-Host 'Stopping any running sandboxes ...'
    $stopSandboxes = Join-Path $scriptDir 'stop_sandboxes.py'
    Push-Location $scriptDir
    try {
        & $uv run python $stopSandboxes
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "stop_sandboxes.py exited with code $LASTEXITCODE."
        }
    }
    catch {
        Write-Warning "Could not stop sandboxes: $($_.Exception.Message)"
    }
    finally {
        Pop-Location
    }

    if ($hadPythonUtf8) {
        $env:PYTHONUTF8 = $previousPythonUtf8
    }
    else {
        Remove-Item Env:PYTHONUTF8 -ErrorAction SilentlyContinue
    }
}
