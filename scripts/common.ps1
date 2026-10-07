$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $RepoRoot
$env:HF_HOME = Join-Path $RepoRoot '.cache/huggingface'
$env:UV_CACHE_DIR = Join-Path $RepoRoot '.cache/uv'
$env:UV_PYTHON_INSTALL_DIR = Join-Path $RepoRoot '.tools/python'
$env:PIP_CACHE_DIR = Join-Path $RepoRoot '.cache/pip'
$env:TORCH_HOME = Join-Path $RepoRoot '.cache/torch'
$env:TEMP = Join-Path $RepoRoot '.cache/tmp'
$env:TMP = $env:TEMP
New-Item -ItemType Directory -Force -Path $env:TEMP | Out-Null
$env:PYTHONUTF8 = '1'
$PythonExe = Join-Path $RepoRoot '.venv/Scripts/python.exe'

function Invoke-Checked {
    param([string]$Program, [string[]]$Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed (exit $LASTEXITCODE): $Program"
    }
}

function Require-Environment {
    if (-not (Test-Path -LiteralPath $PythonExe)) {
        throw 'Run scripts/setup.ps1 first.'
    }
}
