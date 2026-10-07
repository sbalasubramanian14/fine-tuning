param([switch]$SmokeOnly)
. "$PSScriptRoot/common.ps1"

# Complete local workflow. Every stage stops on errors.
& "$PSScriptRoot/setup.ps1"
& "$PSScriptRoot/download-model.ps1"
Invoke-Checked $PythonExe @('scripts/validate_dataset.py')
& "$PSScriptRoot/generate.ps1"
& "$PSScriptRoot/train.ps1" -Smoke
if ($SmokeOnly) {
    Write-Host 'Baseline and smoke run completed. Run start.ps1 without -SmokeOnly for full training.'
    return
}
$FullRunName = "sora-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
& "$PSScriptRoot/train.ps1" -RunName $FullRunName
$AdapterPath = Join-Path $RepoRoot "outputs/$FullRunName/sora.safetensors"
& "$PSScriptRoot/generate.ps1" -Lora $AdapterPath
Write-Host "Training and evaluation completed. Adapter: $AdapterPath"
