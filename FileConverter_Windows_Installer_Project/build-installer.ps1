$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Get-Command py -ErrorAction SilentlyContinue)) { throw 'Install Python 3.11 or newer from python.org first.' }
py -3 -m venv .venv
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt 'pyinstaller>=6,<7'
& $python -m PyInstaller --noconfirm --clean --windowed --onedir --name FileConverter --icon installer\FileConverter.ico app.py
$iscc = @(
  "$env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe",
  "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) { throw 'Inno Setup 6 not found. Install from https://jrsoftware.org/isinfo.php' }
& $iscc installer\FileConverter.iss
if ($LASTEXITCODE -ne 0) { throw 'Inno Setup compilation failed.' }
Write-Host 'Installer ready: release\FileConverter-Setup-1.0.0.exe'
