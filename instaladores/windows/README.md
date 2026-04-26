# Instalador de Windows

Esta carpeta agrupa los archivos necesarios para generar el ejecutable y el instalador de Windows:

- `build_windows.ps1`: script principal de empaquetado.
- `installer.nsi`: script de NSIS para crear el instalador.
- `SERISA.spec`: especificación alternativa de PyInstaller.

## Requisitos

- Entorno virtual creado en `.venv`
- Dependencias del proyecto instaladas
- NSIS instalado y accesible con `makensis`

## Generar el instalador

Desde la raíz del proyecto:

```powershell
powershell -ExecutionPolicy Bypass -File .\instaladores\windows\build_windows.ps1
```

El instalador resultante se genera en `dist\installer\SERISA-Setup.exe`.

## Generar solo el ejecutable

```powershell
powershell -ExecutionPolicy Bypass -File .\instaladores\windows\build_windows.ps1 -SkipInstaller
```
