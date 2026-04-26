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
package_root="$build_dir/linux-package"
app_dir="$package_root/opt/serisa"
icon_png="$project_root/imagenes/logo_serisa.png"

if [[ ! -x "$python_bin" ]]; then
  echo "No se ha encontrado Python en .venv/bin/python3 ni .venv/bin/python" >&2
  exit 1
fi

echo "Instalando dependencias de empaquetado..."
"$python_bin" -m pip install pyinstaller

echo "Limpiando builds anteriores..."
rm -rf "$dist_dir" "$build_dir"

echo "Generando ejecutable Linux..."
(
  cd "$project_root"
  "$python_bin" -m PyInstaller \
    --noconfirm \
    --clean \
    --windowed \
    --name SERISA \
    --icon "$icon_png" \
    --add-data "imagenes:imagenes" \
    --add-data ".env:." \
    --collect-all tkcalendar \
    main.py
)

if [[ "$skip_installer" -eq 1 ]]; then
  echo "Build completado en dist/SERISA"
  exit 0
fi

echo "Preparando paquete Linux..."
mkdir -p "$app_dir" \
  "$package_root/usr/bin" \
  "$package_root/usr/share/applications" \
  "$package_root/usr/share/icons/hicolor/256x256/apps" \
  "$package_root/DEBIAN" \
  "$installer_dir"

cp -R "$dist_dir/SERISA/." "$app_dir/"
cp "$icon_png" "$package_root/usr/share/icons/hicolor/256x256/apps/serisa.png"

cat > "$package_root/usr/bin/serisa" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
exec /opt/serisa/SERISA "$@"
EOF
chmod +x "$package_root/usr/bin/serisa"

cat > "$package_root/usr/share/applications/serisa.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=SERISA
Comment=Aplicacion SERISA
Exec=/usr/bin/serisa
Icon=serisa
Terminal=false
Categories=Utility;
EOF

cat > "$package_root/DEBIAN/control" <<'EOF'
Package: serisa
Version: 1.0.0
Section: utils
Priority: optional
Architecture: amd64
Maintainer: SERISA
Description: Aplicacion SERISA
EOF

tar -C "$package_root/opt" -czf "$installer_dir/SERISA-linux.tar.gz" serisa

if command -v dpkg-deb >/dev/null 2>&1; then
  dpkg-deb --build "$package_root" "$installer_dir/SERISA-linux.deb"
  echo "Paquetes generados en dist/installer: SERISA-linux.tar.gz y SERISA-linux.deb"
else
  echo "Paquete generado en dist/installer: SERISA-linux.tar.gz"
  echo "No se ha generado .deb porque dpkg-deb no esta disponible."
fi
