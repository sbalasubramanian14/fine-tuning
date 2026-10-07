param([string]$Lora, [string]$Prompt, [int]$Seed = 42)
. "$PSScriptRoot/common.ps1"
Require-Environment
$GenerateArgs = @('scripts/generate.py', '--seed', "$Seed")
if ($Lora) { $GenerateArgs += @('--lora', $Lora) }
if ($Prompt) { $GenerateArgs += @('--prompt', $Prompt) }
Invoke-Checked $PythonExe $GenerateArgs
