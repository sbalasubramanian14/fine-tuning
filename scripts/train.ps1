param([switch]$Smoke, [string]$RunName)
. "$PSScriptRoot/common.ps1"
Require-Environment
if (-not $RunName) {
    $Prefix = if ($Smoke) { 'smoke' } else { 'sora' }
    $RunName = "$Prefix-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
}
if ($RunName -notmatch '^[a-zA-Z0-9_-]+$') { throw 'RunName must contain only letters, numbers, underscores or hyphens.' }
$RunDir = Join-Path $RepoRoot "outputs/$RunName"
if (Test-Path -LiteralPath $RunDir) { throw "Run already exists: $RunDir" }
Invoke-Checked $PythonExe @('scripts/validate_dataset.py')
Invoke-Checked $PythonExe @('scripts/check_environment.py')
New-Item -ItemType Directory -Path $RunDir | Out-Null
$Steps = if ($Smoke) { '10' } else { '400' }
Invoke-Checked $PythonExe @('scripts/prepare_run.py', '--output', $RunDir, '--steps', $Steps)
$Trainer = Join-Path $RepoRoot 'vendor/sd-scripts/train_network.py'
$TrainArgs = @('-m', 'accelerate.commands.launch', '--num_processes=1', '--num_machines=1', '--mixed_precision=fp16', '--num_cpu_threads_per_process=2', $Trainer,
    '--config_file', (Join-Path $RunDir 'train.toml'), '--dataset_config', (Join-Path $RunDir 'dataset.toml'),
    '--pretrained_model_name_or_path', (Join-Path $RepoRoot 'models/waifu-diffusion'),
    '--output_dir', $RunDir, '--output_name', 'sora', '--max_train_steps', $Steps)
Invoke-Checked $PythonExe $TrainArgs
Write-Host "Finished: $RunDir/sora.safetensors"
