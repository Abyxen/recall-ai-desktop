$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
& .\.venv\Scripts\python.exe -m pytest -q
if ($LASTEXITCODE -ne 0) { throw 'Tests failed; build cancelled.' }
$originalBuildPath = $env:PATH
try {
    # Avoid accidentally bundling unrelated ICU/UCRT DLLs from helper tools on PATH.
    $env:PATH = "$PSScriptRoot\.venv\Scripts;$env:SystemRoot\System32;$env:SystemRoot;$env:SystemRoot\System32\Wbem"
    & .\.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm --windowed --onedir --name RecallAI --collect-data pytesseract --copy-metadata PySide6 --copy-metadata PySide6_Essentials --copy-metadata PySide6_Addons --copy-metadata numpy --copy-metadata pypdf --copy-metadata python-docx --copy-metadata python-pptx --copy-metadata Pillow --copy-metadata pytesseract --copy-metadata lxml launch.py
    if ($LASTEXITCODE -ne 0) { throw 'Packaging failed.' }
} finally {
    $env:PATH = $originalBuildPath
}
Copy-Item -LiteralPath README.md,LICENSE -Destination dist\RecallAI -Force
Copy-Item -LiteralPath docs -Destination dist\RecallAI -Recurse -Force
Write-Host 'Built dist\RecallAI\RecallAI.exe. Distribute the whole RecallAI folder, not just the exe.'
