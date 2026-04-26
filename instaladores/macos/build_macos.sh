#!/usr/bin/env bash
set -euo pipefail

skip_installer=0
if [[ "${1:-}" == "--skip-installer" ]]; then
  skip_installer=1
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd "$script_dir/../.." && pwd)"
python_bin="$project_root/.venv/bin/python3"
if [[ ! -x "$python_bin" ]]; then
  python_bin="$project_root/.venv/bin/python"
fi

dist_dir="$project_root/dist"
build_dir="$project_root/build"
installer_dir="$dist_dir/installer"
icon_png="$project_root/imagenes/logo_serisa.png"
iconset_dir="$build_dir/SERISA.iconset"
icon_icns="$build_dir/SERISA.icns"
pyinstaller_icon_args=()

if [[ ! -x "$python_bin" ]]; then
  echo "No se ha encontrado Python en .venv/bin/python3 ni .venv/bin/python" >&2
  exit 1
fi

echo "Instalando dependencias de empaquetado..."
"$python_bin" -m pip install pyinstaller

echo "Limpiando builds anteriores..."
rm -rf "$dist_dir" "$build_dir"
mkdir -p "$installer_dir"

if command -v sips >/dev/null 2>&1 && command -v iconutil >/dev/null 2>&1; then
  echo "Generando icono ICNS..."
  mkdir -p "$iconset_dir"
  sips -z 16 16 "$icon_png" --out "$iconset_dir/icon_16x16.png" >/dev/null
  sips -z 32 32 "$icon_png" --out "$iconset_dir/icon_16x16@2x.png" >/dev/null
  sips -z 32 32 "$icon_png" --out "$iconset_dir/icon_32x32.png" >/dev/null
  sips -z 64 64 "$icon_png" --out "$iconset_dir/icon_32x32@2x.png" >/dev/null
  sips -z 128 128 "$icon_png" --out "$iconset_dir/icon_128x128.png" >/dev/null
  sips -z 256 256 "$icon_png" --out "$iconset_dir/icon_128x128@2x.png" >/dev/null
  sips -z 256 256 "$icon_png" --out "$iconset_dir/icon_256x256.png" >/dev/null
  sips -z 512 512 "$icon_png" --out "$iconset_dir/icon_256x256@2x.png" >/dev/null
  sips -z 512 512 "$icon_png" --out "$iconset_dir/icon_512x512.png" >/dev/null
  cp "$icon_png" "$iconset_dir/icon_512x512@2x.png"
  iconutil -c icns "$iconset_dir" -o "$icon_icns"
  pyinstaller_icon_args=(--icon "$icon_icns")
else
  echo "No se ha generado icono ICNS porque faltan sips/iconutil. Se continuara sin icono especifico."
fi

echo "Generando app de macOS..."
(
  cd "$project_root"
  "$python_bin" -m PyInstaller \
    --noconfirm \
    --clean \
    --windowed \
    --name SERISA \
    "${pyinstaller_icon_args[@]}" \
    --add-data "imagenes:imagenes" \
    --add-data ".env:." \
    --collect-all tkcalendar \
    main.py
)

if [[ "$skip_installer" -eq 1 ]]; then
  echo "Build completado en dist/SERISA.app"
  exit 0
fi

echo "Generando ZIP..."
ditto -c -k --sequesterRsrc --keepParent "$dist_dir/SERISA.app" "$installer_dir/SERISA-macOS.zip"

if command -v hdiutil >/dev/null 2>&1; then
  echo "Generando DMG..."
  dmg_root="$build_dir/dmg-root"
  rm -rf "$dmg_root"
  mkdir -p "$dmg_root"
  cp -R "$dist_dir/SERISA.app" "$dmg_root/"
  hdiutil create -volname "SERISA" -srcfolder "$dmg_root" -ov -format UDZO "$installer_dir/SERISA-macOS.dmg" >/dev/null
  echo "Paquetes generados en dist/installer: SERISA-macOS.zip y SERISA-macOS.dmg"
else
  echo "Paquete generado en dist/installer: SERISA-macOS.zip"
  echo "No se ha generado .dmg porque hdiutil no esta disponible."
fi
