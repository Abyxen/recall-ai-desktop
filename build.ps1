$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
& .\.venv\Scripts\python.exe -m pytest -q
if ($LASTEXITCODE -ne 0) { throw 'Tests failed; build cancelled.' }
& .\.venv\Scripts\python.exe -m PyInstaller --noconfirm --windowed --onedir --name RecallAI --collect-data pytesseract launch.py
if ($LASTEXITCODE -ne 0) { throw 'Packaging failed.' }
Write-Host 'Built dist\RecallAI\RecallAI.exe. Distribute the whole RecallAI folder, not just the exe.'
