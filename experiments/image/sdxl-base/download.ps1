. "$PSScriptRoot/../../../scripts/common.ps1"
Require-Environment
Invoke-Checked $PythonExe @('experiments/image/sdxl-base/download.py')
