#!/usr/bin/env bash
pkill -f mar-fondo.py 2>/dev/null || true
rm -f "$HOME/.config/autostart/mar-evolutivo.desktop" "$HOME/.local/share/applications/mar-evolutivo.desktop" "$HOME/.local/share/applications/mar-evolutivo-parar.desktop" "$HOME/.local/share/applications/mar-evolutivo-ajustes.desktop"
read -r -p "¿Borrar también el mar guardado (especies, diario…)? [s/N] " r
if [[ "$r" =~ ^[sS] ]]; then rm -rf "$HOME/.local/share/mar-evolutivo"; else rm -f "$HOME/.local/share/mar-evolutivo/"*.py "$HOME/.local/share/mar-evolutivo/"*.html; fi
echo "Desinstalado."
