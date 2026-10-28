@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Python environment missing. Run setup.bat first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -c "import PySide6, numpy, pypdf, docx, pptx" >nul 2>&1
if errorlevel 1 (
  echo Dependencies are missing. Run setup.bat to repair this environment.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m recall %*
if errorlevel 1 (
  echo Recall AI could not start. Copy the error above and consult docs\TROUBLESHOOTING.md.
  pause
  exit /b 1
)
