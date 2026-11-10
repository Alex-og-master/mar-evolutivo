#!/usr/bin/env bash
# Instala el mar evolutivo como fondo de pantalla (Linux).
set -e
cd "$(dirname "$0")"
DEST="$HOME/.local/share/mar-evolutivo"
echo "🌊  Instalando el mar evolutivo…"

tiene_deps() {
python3 - <<'PY' 2>/dev/null
import gi
gi.require_version('Gtk','3.0')
try: gi.require_version('WebKit2','4.1')
except ValueError: gi.require_version('WebKit2','4.0')
from gi.repository import Gtk, WebKit2
PY
}

if ! tiene_deps; then
  echo "Falta GTK/WebKitGTK para Python (suele ser una sola instalación)."
  if command -v apt >/dev/null; then
    CMD="sudo apt install -y python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.1"
    ALT="sudo apt install -y python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.0"
  elif command -v dnf >/dev/null; then
    CMD="sudo dnf install -y python3-gobject gtk3 webkit2gtk4.1"; ALT=""
  elif command -v pacman >/dev/null; then
    CMD="sudo pacman -S --needed --noconfirm python-gobject gtk3 webkit2gtk-4.1"; ALT=""
  elif command -v zypper >/dev/null; then
    CMD="sudo zypper install -y python3-gobject typelib-1_0-Gtk-3_0 typelib-1_0-WebKit2-4_1"; ALT=""
  else
    echo "No reconozco tu gestor de paquetes. Instala python3-gi (PyGObject) y WebKit2GTK 4.1 y vuelve a ejecutar."; exit 1
  fi
  echo "Voy a ejecutar:  $CMD"
  read -r -p "¿Vale? [S/n] " r
  if [[ "$r" =~ ^[nN] ]]; then exit 1; fi
  $CMD || { [ -n "$ALT" ] && $ALT; }
  tiene_deps || { echo "Sigue sin encontrar WebKitGTK. Pégale este error a Claude."; exit 1; }
fi

mkdir -p "$DEST"
cp mar-evolutivo.html mar-fondo.py desinstalar.sh "$DEST/"
chmod +x "$DEST/mar-fondo.py" "$DEST/desinstalar.sh"

mkdir -p "$HOME/.config/autostart" "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/mar-evolutivo.desktop" <<D
[Desktop Entry]
Type=Application
Name=Mar evolutivo
Comment=Fondo de pantalla vivo con un submarino
Exec=python3 $DEST/mar-fondo.py
Icon=weather-showers-scattered
Categories=Utility;
D
cp "$HOME/.local/share/applications/mar-evolutivo.desktop" "$HOME/.config/autostart/mar-evolutivo.desktop"
echo "X-GNOME-Autostart-Delay=25" >> "$HOME/.config/autostart/mar-evolutivo.desktop"
cat > "$HOME/.local/share/applications/mar-evolutivo-ajustes.desktop" <<D
[Desktop Entry]
Type=Application
Name=Ajustes del mar evolutivo
Comment=Ciudad, tiempo, árbol de especies y diario
Exec=python3 $DEST/mar-fondo.py --ajustes
Icon=preferences-desktop-wallpaper
Categories=Utility;
D
cat > "$HOME/.local/share/applications/mar-evolutivo-parar.desktop" <<D
[Desktop Entry]
Type=Application
Name=Parar mar evolutivo
Exec=pkill -f mar-fondo.py
Icon=process-stop
Categories=Utility;
D

pkill -f mar-fondo.py 2>/dev/null || true
sleep 0.5
nohup python3 "$DEST/mar-fondo.py" >/dev/null 2>&1 &
echo "✅  Listo. El mar arranca solo cada vez que inicies sesión."
echo "    En el menú de aplicaciones: «Mar evolutivo», «Ajustes del mar evolutivo» y «Parar mar evolutivo»."
echo "    Para quitarlo del todo:  $DEST/desinstalar.sh"
