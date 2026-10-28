param([string]$Python = '')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
try {
    if (-not $Python) {
        # Python Install Manager may expose third-party runtimes only by their full tag.
        foreach ($tag in @('3.11', 'Astral/CPython3.11.17', '3.12', '3.13')) {
            $candidate = $null
            try { $candidate = & py "-V:$tag" -c 'import sys; print(sys.executable)' 2>$null } catch { }
            if ($LASTEXITCODE -eq 0 -and $candidate) { $Python = $candidate.Trim(); break }
        }
    }
    if (-not $Python) { throw 'Python 3.11–3.13 not found. Install Python 3.11 from python.org, or run setup.ps1 -Python C:\path\to\python.exe' }
    & $Python -c 'import sys; sys.exit(0 if (3,11) <= sys.version_info[:2] <= (3,13) else 1)'
    if ($LASTEXITCODE -ne 0) { throw 'Unsupported Python version.' }
    if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
        & $Python -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Could not create the virtual environment.' }
    }
    & .\.venv\Scripts\python.exe -m ensurepip --upgrade
    & .\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Check network access and the Python version.' }
    & .\.venv\Scripts\python.exe -c 'from PySide6.QtWidgets import QApplication; import numpy, pypdf, docx, pptx'
    if ($LASTEXITCODE -ne 0) { throw 'Dependency verification failed.' }
    Write-Host 'Setup complete. Run run.bat. Ollama and model weights are optional and installed separately.'
} catch {
    Write-Host $_ -ForegroundColor Red
    exit 1
}
