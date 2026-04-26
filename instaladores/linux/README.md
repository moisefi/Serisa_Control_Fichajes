# Instalador de Linux

Esta carpeta contiene el script para empaquetar la aplicacion en Linux.

- `build_linux.sh`: genera el ejecutable con PyInstaller.
- Si el sistema tiene `dpkg-deb`, tambien genera un paquete `.deb`.
- Si no, al menos genera `dist/installer/SERISA-linux.tar.gz`.

## Requisitos

- Linux
- Entorno virtual creado en `.venv`
- Dependencias del proyecto instaladas
- `python3-tk` instalado en el sistema
- Opcional: `dpkg-deb` para crear el `.deb`

## Generar instaladores

Desde la raiz del proyecto:

```bash
chmod +x ./instaladores/linux/build_linux.sh
./instaladores/linux/build_linux.sh
```

Salida esperada:

- `dist/installer/SERISA-linux.tar.gz`
- `dist/installer/SERISA-linux.deb` si `dpkg-deb` esta disponible

## Generar solo el ejecutable

```bash
./instaladores/linux/build_linux.sh --skip-installer
```

El ejecutable quedara en `dist/SERISA`.
