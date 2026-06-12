# UI-10.4 Windows Installer Checklist

## Executable

- Path: `dist/RMEAgenteStudio/RMEAgenteStudio.exe`
- Application folder: `dist/RMEAgenteStudio/`
- Packaging mode: PyInstaller one-folder

## Required Files

- `_internal/` PyInstaller runtime folder
- `_internal/PySide6/` Qt runtime and plugins
- `_internal/assets/images/rme_agent_ai_banner.png`
- `_internal/recursos/favicon.ico`
- `_internal/config.json`
- `_internal/pyproject.toml`
- `_internal/requirements-lock.txt`

## Shortcut

- Target: `RMEAgenteStudio.exe`
- Working directory: installed application folder
- Icon: `recursos/favicon.ico` bundled in the package

## Runtime Folders

- Config folder: use bundled default `config.json`; future user-specific config may live under `%APPDATA%\RMEAgenteStudio`.
- Output folder: create outside the install directory when user workflows require generated outputs.
- Logs folder: create outside the install directory, preferably `%LOCALAPPDATA%\RMEAgenteStudio\logs`.

## Uninstall Strategy

- Remove the installed application folder.
- Remove shortcuts from Start Menu/Desktop.
- Preserve user output/config/log folders unless the uninstaller offers an explicit cleanup option.

## Checklist Status

Status: **PASS**
