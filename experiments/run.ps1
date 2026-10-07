param(
    [string]$Profile = 'experiments/image/dreamshaper8/profile.json',
    [ValidateSet('all','download','baseline','smoke','train','evaluate','generate','verify','preserve')]
    [string]$Action = 'all',
    [string]$RunName,
    [string]$Lora,
    [string]$Prompt
)
. "$PSScriptRoot/../scripts/common.ps1"
Require-Environment
$Arguments = @('experiments/run.py', '--profile', $Profile, '--action', $Action)
if ($RunName) { $Arguments += @('--run-name', $RunName) }
if ($Lora) { $Arguments += @('--lora', $Lora) }
if ($Prompt) { $Arguments += @('--prompt', $Prompt) }
Invoke-Checked $PythonExe $Arguments
