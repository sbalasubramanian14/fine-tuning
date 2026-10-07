. "$PSScriptRoot/common.ps1"
Require-Environment
Invoke-Checked $PythonExe @('scripts/download_model.py')
