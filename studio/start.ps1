param([int]$Port = 7860)
. "$PSScriptRoot/../scripts/common.ps1"
Require-Environment
Invoke-Checked $PythonExe @('studio/server.py', '--port', "$Port")
