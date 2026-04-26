# Instalador de macOS

Esta carpeta contiene el script para empaquetar la aplicacion en macOS.

- `build_macos.sh`: genera `SERISA.app` con PyInstaller.
- Siempre genera `dist/installer/SERISA-macOS.zip`.
- Si `hdiutil` esta disponible, tambien genera `dist/installer/SERISA-macOS.dmg`.

## Requisitos

- macOS
- Entorno virtual creado en `.venv`
- Dependencias del proyecto instaladas
- Tcl/Tk disponible en el sistema
- Opcional: `sips` e `iconutil` para generar icono `.icns`

## Generar instaladores

Desde la raiz del proyecto:

```bash
chmod +x ./instaladores/macos/build_macos.sh
./instaladores/macos/build_macos.sh
```

Salida esperada:

- `dist/installer/SERISA-macOS.zip`
- `dist/installer/SERISA-macOS.dmg` si `hdiutil` esta disponible

## Generar solo la app

```bash
./instaladores/macos/build_macos.sh --skip-installer
```

La app quedara en `dist/SERISA.app`.
