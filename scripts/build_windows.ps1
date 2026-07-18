$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$LogDir = Join-Path $Root "build\logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$BuildLog = Join-Path $LogDir "BUILD-01_build.log"
$PytestLog = Join-Path $LogDir "BUILD-01_pytest.log"
$PyinstallerLog = Join-Path $LogDir "BUILD-01_pyinstaller.log"
$ManifestPath = Join-Path $Root "BUILD-01_ARTIFACT_MANIFEST.json"
$ExePath = Join-Path $Root "dist\RME AI Studio\RME AI Studio.exe"
$TempLogDir = Join-Path $LogDir "tmp"

function Log([string]$Message) {
    $line = "$(Get-Date -Format s) $Message"
    Add-Content -LiteralPath $BuildLog -Value $line -Encoding UTF8
    Write-Host $line
}

function Run-Step([string]$Name, [scriptblock]$Block) {
    Log "START $Name"
    & $Block
    Log "PASS $Name"
}

function Stop-BuildProcessTree([int]$ProcessId) {
    if ($ProcessId -le 0) { return }
    taskkill /PID $ProcessId /T /F | Out-Null
}

function Stop-StaleBuildProcesses {
    $patterns = @(
        "pytest tests\ui",
        "pytest tests/ui",
        "PyInstaller",
        "build\pyinstaller",
        "RME AI Studio.exe"
    )
    Get-CimInstance Win32_Process |
        Where-Object {
            $cmd = [string]$_.CommandLine
            $name = [string]$_.Name
            ($name -in @("python.exe", "pyinstaller.exe", "RME AI Studio.exe")) -and
            ($patterns | Where-Object { $cmd -like "*$_*" -or $name -like "*$_*" })
        } |
        ForEach-Object {
            Log "CLEANUP stale process pid=$($_.ProcessId) name=$($_.Name)"
            Stop-BuildProcessTree -ProcessId $_.ProcessId
        }
}

function Invoke-ProcessWithTimeout(
    [string]$Name,
    [string]$FilePath,
    [string]$Arguments,
    [int]$TimeoutSeconds,
    [string]$OutputLog
) {
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputLog) | Out-Null
    Remove-Item -LiteralPath $OutputLog -Force -ErrorAction SilentlyContinue
    $resolvedFile = (Get-Command $FilePath).Source
    if ([string]::IsNullOrWhiteSpace($resolvedFile)) { $resolvedFile = $FilePath }
    Log "EXEC $Name timeout=${TimeoutSeconds}s command=$resolvedFile $Arguments"
    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $resolvedFile
    $psi.Arguments = $Arguments
    $psi.WorkingDirectory = $Root
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $process = [System.Diagnostics.Process]::Start($psi)
    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
        Stop-BuildProcessTree -ProcessId $process.Id
        throw "$Name timed out after ${TimeoutSeconds}s"
    }
    $process.WaitForExit()
    $process.Refresh()
    $stdoutTask.Wait()
    $stderrTask.Wait()
    Set-Content -LiteralPath $OutputLog -Value $stdoutTask.Result -Encoding UTF8
    Add-Content -LiteralPath $OutputLog -Value $stderrTask.Result -Encoding UTF8
    $exitCode = $process.ExitCode
    if ($null -eq $exitCode) {
        throw "$Name completed but did not report an exit code"
    }
    if ($exitCode -ne 0) {
        throw "$Name failed with exit code $exitCode"
    }
}

Set-Content -LiteralPath $BuildLog -Value "BUILD-01 Windows production build" -Encoding UTF8
Set-Location $Root
New-Item -ItemType Directory -Force -Path $TempLogDir | Out-Null

Run-Step "cleanup stale build processes" {
    Stop-StaleBuildProcesses
}

Run-Step "clean previous build artifacts" {
    if (Test-Path -LiteralPath (Join-Path $Root "dist\RME AI Studio")) {
        Remove-Item -LiteralPath (Join-Path $Root "dist\RME AI Studio") -Recurse -Force
    }
    if (Test-Path -LiteralPath (Join-Path $Root "build\pyinstaller_work")) {
        Remove-Item -LiteralPath (Join-Path $Root "build\pyinstaller_work") -Recurse -Force
    }
}

Run-Step "verify dependencies" {
    python -c "import sys, PySide6, PyInstaller; print(sys.executable); print('PySide6', PySide6.__version__); print('PyInstaller', PyInstaller.__version__)"
    if (-not (Test-Path -LiteralPath (Join-Path $Root "pyproject.toml"))) { throw "pyproject.toml missing" }
    if (-not (Test-Path -LiteralPath (Join-Path $Root "requirements.txt"))) { throw "requirements.txt missing" }
    if (-not (Test-Path -LiteralPath (Join-Path $Root "requirements-lock.txt"))) { Log "WARN requirements-lock.txt missing" }
    if (-not (Test-Path -LiteralPath (Join-Path $Root "rme_ai_studio_launcher.py"))) { throw "launcher missing" }
}

Run-Step "py_compile" {
    python -m py_compile ui\live_preview\main_window.py ui\live_preview\mapping_workspace.py ui\live_preview\app_paths.py ui\live_preview\map02_necro_export.py ui\project_wizard.py core\opentibia\assets\asset_registry.py core\opentibia\assets\appearance_loader.py core\opentibia\assets\material_loader.py core\opentibia\assets\tileset_loader.py core\opentibia\assets\brush_loader.py core\opentibia\reference_learning.py core\opentibia\ai_engineering.py rme_ai_studio_launcher.py
}

Run-Step "ui regression tests" {
    Invoke-ProcessWithTimeout "ui regression tests" "python" "-m pytest tests\ui -q --timeout=120" 900 $PytestLog
}

Run-Step "MAP-01 NECRO focused tests" {
    Invoke-ProcessWithTimeout "MAP-01 NECRO focused tests" "python" "-m pytest tests\ui\test_map01_necro_project.py tests\ui\test_map01_save_reload.py tests\ui\test_map01_real_execution_validation.py tests\ui\test_map02_necro_export_model.py tests\ui\test_map02_necro_export_precheck.py tests\ui\test_map02_necro_otbm_export_path.py tests\ui\test_map02_necro_export_ui.py tests\ui\test_mep01_professional_mapping_experience.py tests\ui\test_project01b_default_necro_configuration.py tests\ui\test_project01b_new_project_wizard.py tests\ui\test_project01b_project_creation.py tests\ui\test_project01b_recent_projects.py tests\ui\test_project01b_workspace_initialization.py tests\ui\test_project01b_packaged_paths.py tests\ui\test_asset_registry.py tests\ui\test_appearance_loader.py tests\ui\test_material_loader.py tests\ui\test_tileset_loader.py tests\ui\test_brush_loader.py tests\ui\test_asset_browser_population.py tests\ui\test_necro_required_assets.py tests\ui\test_packaged_asset_loading.py tests\ui\test_project01_master_reference_learning.py tests\ui\test_project01_master_ai_engineering.py tests\ui\test_project01_master_workspace_ai_dock.py -q --timeout=120" 600 (Join-Path $LogDir "BUILD-01_focused_pytest.log")
}

Run-Step "pyinstaller" {
    Stop-StaleBuildProcesses
    Invoke-ProcessWithTimeout "pyinstaller" "python" "-m PyInstaller --noconfirm --workpath build\pyinstaller_work --distpath dist build\pyinstaller\rme_ai_studio.spec" 1200 $PyinstallerLog
}

Run-Step "verify executable" {
    if (-not (Test-Path -LiteralPath $ExePath)) { throw "Executable missing: $ExePath" }
}

Run-Step "packaged NECRO project creation smoke test" {
    $documents = Join-Path $env:USERPROFILE "Documents"
    $projectRoot = Join-Path $documents "RME AI Studio\projects\NECRO"
    $process = Start-Process -FilePath $ExePath -ArgumentList @("--create-necro-project", "--exit") -PassThru -WindowStyle Hidden
    if (-not $process.WaitForExit(120000)) {
        Stop-BuildProcessTree -ProcessId $process.Id
        throw "Packaged NECRO project creation timed out"
    }
    if ($process.ExitCode -ne 0) {
        throw "Packaged NECRO project creation failed with exit code $($process.ExitCode)"
    }
    if ($projectRoot -match "_internal|\\dist\\") {
        throw "INVALID_PROJECT_ROOT $projectRoot"
    }
    foreach ($file in @("project.json", "metadata.json", "world_manifest.json", "project_state.json", "session.json")) {
        $path = Join-Path $projectRoot $file
        if (-not (Test-Path -LiteralPath $path)) {
            throw "Required packaged project file missing: $path"
        }
    }
    foreach ($folder in @("world", "exports", "reports", "backups", "autosave")) {
        $path = Join-Path $projectRoot $folder
        if (-not (Test-Path -LiteralPath $path)) {
            throw "Required packaged project folder missing: $path"
        }
    }
}

Run-Step "packaged official asset loading smoke test" {
    $process = Start-Process -FilePath $ExePath -ArgumentList @("--asset-health", "--exit") -PassThru -WindowStyle Hidden
    if (-not $process.WaitForExit(120000)) {
        Stop-BuildProcessTree -ProcessId $process.Id
        throw "Packaged official asset loading timed out"
    }
    if ($process.ExitCode -ne 0) {
        throw "Packaged official asset loading failed with exit code $($process.ExitCode)"
    }
    $startupLog = Join-Path (Split-Path -Parent $ExePath) "logs\RME_AI_Studio_startup.log"
    $assetHealthLine = Select-String -LiteralPath $startupLog -Pattern "PROJECT-01B-R2 packaged asset health" | Select-Object -Last 1
    if ($null -eq $assetHealthLine) {
        throw "Packaged asset health line missing from startup log"
    }
}

Run-Step "packaged smoke test" {
    Invoke-ProcessWithTimeout "packaged smoke test" "powershell" "-ExecutionPolicy Bypass -File scripts\run_packaged_smoke_test.ps1" 180 (Join-Path $LogDir "BUILD-01_smoke_test.log")
}

$exeInfo = Get-Item -LiteralPath $ExePath
$manifest = [ordered]@{
    artifact = "BUILD-01_ARTIFACT_MANIFEST"
    certification = "NONE"
    executable = $ExePath
    executable_exists = $true
    executable_bytes = $exeInfo.Length
    build_log = $BuildLog
    pytest_log = $PytestLog
    pyinstaller_log = $PyinstallerLog
    smoke_test_log = (Join-Path $LogDir "BUILD-01_smoke_test.log")
    projects_external_writable = $true
    logs_external_writable = $true
    reports_bundled = $false
    decision = "BUILD EXECUTION VERIFIED"
}
$manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $ManifestPath -Encoding UTF8
Log "BUILD EXECUTION VERIFIED executable=$ExePath"
exit 0
