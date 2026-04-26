param(
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)
$pythonExe = Join-Path $projectRoot ".venv\\Scripts\\python.exe"
$distDir = Join-Path $projectRoot "dist"
$buildDir = Join-Path $projectRoot "build"
$installerDir = Join-Path $distDir "installer"
$iconPng = Join-Path $projectRoot "imagenes\\logo_serisa.png"
$iconIco = Join-Path $projectRoot "imagenes\\logo_serisa.ico"
$nsisScript = Join-Path $scriptDir "installer.nsi"

function Get-FirstExistingPath {
    param(
        [string[]]$Candidates
    )

    foreach ($candidate in $Candidates) {
        if ($candidate -and (Test-Path $candidate)) {
            return $candidate
        }
    }

    return $null
}

if (-not (Test-Path $pythonExe)) {
    throw "No se ha encontrado Python en .venv\\Scripts\\python.exe"
}

Write-Host "Instalando dependencias de empaquetado..."
& $pythonExe -m pip install pyinstaller

Write-Host "Generando icono ICO..."
& $pythonExe -c "from pathlib import Path; from PIL import Image; src = Path(r'$iconPng'); dst = Path(r'$iconIco'); img = Image.open(src); img.save(dst, format='ICO', sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])"

Write-Host "Limpiando builds anteriores..."
if (Test-Path $distDir) {
    Remove-Item -LiteralPath $distDir -Recurse -Force
}
if (Test-Path $buildDir) {
    Remove-Item -LiteralPath $buildDir -Recurse -Force
}

Write-Host "Generando ejecutable..."
Push-Location $projectRoot
try {
    & $pythonExe -m PyInstaller `
        --noconfirm `
        --clean `
        --windowed `
        --name SERISA `
        --icon $iconIco `
        --add-data "imagenes;imagenes" `
        --add-data ".env;." `
        --collect-all tkcalendar `
        main.py
} finally {
    Pop-Location
}

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller ha fallado"
}

if ($SkipInstaller) {
    Write-Host "Build completado en dist\\SERISA"
    exit 0
}

$makensis = Get-FirstExistingPath @(
    (Get-Command makensis -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue),
    "C:\\Program Files (x86)\\NSIS\\makensis.exe",
    "C:\\Program Files\\NSIS\\makensis.exe",
    "C:\\Program Files (x86)\\NSIS\\Bin\\makensis.exe",
    "C:\\Program Files\\NSIS\\Bin\\makensis.exe"
)

New-Item -ItemType Directory -Path $installerDir -Force | Out-Null

if ($makensis) {
    Write-Host "Generando instalador con NSIS..."
    Push-Location $projectRoot
    try {
        & $makensis /V2 $nsisScript
    } finally {
        Pop-Location
    }

    if ($LASTEXITCODE -ne 0) {
        throw "La generacion del instalador con NSIS ha fallado"
    }
} else {
    throw "No se ha encontrado NSIS. Instala NSIS para generar el instalador."
}

Write-Host "Instalador generado en dist\\installer"
