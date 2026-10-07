param([string]$PythonPath)
. "$PSScriptRoot/common.ps1"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Git is required.' }
New-Item -ItemType Directory -Force -Path '.tools', '.cache', 'vendor', 'models', 'outputs', 'logs' | Out-Null

if (-not (Test-Path -LiteralPath $PythonExe)) {
    if ($PythonPath) {
        Invoke-Checked $PythonPath @('-c', 'import sys; assert sys.version_info[:2] == (3, 11), "Python 3.11 required"')
        Invoke-Checked $PythonPath @('-m', 'venv', '.venv')
    } else {
        $UvExe = Join-Path $RepoRoot '.tools/uv/uv.exe'
        if (-not (Test-Path -LiteralPath $UvExe)) {
            Write-Host 'Downloading uv into this project (no system Python changes).'
            if (-not (Get-Command curl.exe -ErrorAction SilentlyContinue)) { throw 'curl.exe is required (included with current Windows versions).' }
            Invoke-Checked 'curl.exe' @('--fail', '--location', '--connect-timeout', '30', '--output', '.tools/uv.zip', 'https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip')
            Expand-Archive -LiteralPath '.tools/uv.zip' -DestinationPath '.tools/uv' -Force
        }
        Invoke-Checked $UvExe @('python', 'install', '3.11')
        Invoke-Checked $UvExe @('venv', '--seed', '--python', '3.11', '.venv')
    }
}
Invoke-Checked $PythonExe @('-c', 'import sys; assert sys.version_info[:2] == (3, 11), "Python 3.11 required"')

$TrainerDir = Join-Path $RepoRoot 'vendor/sd-scripts'
if (-not (Test-Path -LiteralPath $TrainerDir)) {
    Invoke-Checked 'git' @('clone', '--depth', '1', '--branch', 'v0.10.6', 'https://github.com/kohya-ss/sd-scripts.git', $TrainerDir)
}
$TrainerTag = & git -C $TrainerDir describe --tags --exact-match
if ($LASTEXITCODE -ne 0 -or $TrainerTag -ne 'v0.10.6') { throw 'Trainer must be sd-scripts v0.10.6.' }

Invoke-Checked $PythonExe @('-m', 'pip', 'install', '--upgrade', 'pip')
Invoke-Checked $PythonExe @('-m', 'pip', 'install', 'torch==2.6.0', 'torchvision==0.21.0', '--index-url', 'https://download.pytorch.org/whl/cu124')
Push-Location -LiteralPath $TrainerDir
try { Invoke-Checked $PythonExe @('-m', 'pip', 'install', '-r', 'requirements.txt') }
finally { Pop-Location }
Invoke-Checked $PythonExe @('-m', 'pip', 'install', 'peft==0.14.0', 'scipy==1.15.3')
Invoke-Checked $PythonExe @('-m', 'pip', 'check')
Invoke-Checked $PythonExe @('-c', 'import torch; assert torch.cuda.is_available(), "CUDA unavailable"; print(torch.cuda.get_device_name(0)); print("VRAM GiB:", round(torch.cuda.get_device_properties(0).total_memory / 2**30, 2))')
Invoke-Checked $PythonExe @('-m', 'pip', 'freeze', '--all')
Write-Host 'Environment ready. Next: scripts/download-model.ps1'
