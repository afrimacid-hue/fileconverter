# File Converter — Windows installer project

This package contains the **complete source and Windows installer build configuration**, not a precompiled `.exe`. A real Windows installer must be compiled on Windows; the GitHub Actions workflow does that automatically on a Windows runner.

## Easiest way: build with GitHub Actions (no Windows development setup)

1. Create a new GitHub repository and upload **the contents of this folder** (including the hidden `.github` folder) to its `main` branch.
2. In GitHub, open **Actions → Build Windows installer → Run workflow** (or push to `main` to trigger a build).
3. When the build finishes, open the run and download the `FileConverter-Windows-Installer` artifact.
4. Extract the downloaded artifact ZIP to get `FileConverter-Setup-1.0.0.exe`.
5. On Windows, double-click the setup EXE and follow the wizard. Windows SmartScreen may warn because this installer is **not code-signed**; only proceed if you trust the source.

## Build locally on Windows

1. Install Python 3.11+ from https://www.python.org/downloads/ and select the Python launcher option.
2. Install **Inno Setup 6** from https://jrsoftware.org/isinfo.php.
3. Open PowerShell in this folder and run `powershell -ExecutionPolicy Bypass -File .\build-installer.ps1`.
4. Your installer appears at `release\FileConverter-Setup-1.0.0.exe`.

## Installation behavior

- Bundles Python and conversion dependencies using PyInstaller; end users do not need Python.
- Installs to Program Files with an install wizard (administrator approval required).
- Adds a Start menu shortcut and optional desktop shortcut.
- Adds an entry to Windows Installed Apps with an Inno Setup uninstaller.
- All conversions happen locally; no upload or account required.
- Supported: PDF → JPG/PNG/WEBP/BMP/TIFF (each page separate); image → PDF; image → image.
- GIF/TIFF input uses the first frame; each selected image generates its own PDF.

## Note

Windows builds and installer installation have **not been executed in this Linux environment**. The project has been prepared for a Windows runner; if build errors occur, inspect the Actions log. The setup executable is unsigned.
