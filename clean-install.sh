#!/bin/bash

# SADP GUI para Linux - Script de Limpieza Completa
# Elimina todos los archivos instalados para poder hacer una instalación limpia
# Uso: bash clean-install.sh

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║    SADP GUI para Linux - Limpieza Completa                ║"
echo "║    Se eliminarán todos los archivos instalados             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Confirmación
echo -e "${YELLOW}⚠️  ADVERTENCIA: Esto eliminará:${NC}"
echo "  • Directorio de instalación: ~/.local/bin/sadp"
echo "  • Lanzador de aplicación: ~/.local/share/applications/sadp-gui.desktop"
echo "  • Acceso directo del menú: ~/.local/share/applications/sadp-gui.desktop"
echo ""
read -p "¿Estás seguro de que quieres continuar? (s/n): " -r
echo ""

if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "❌ Operación cancelada"
    exit 0
fi

INSTALL_DIR="$HOME/.local/bin/sadp"
DESKTOP_FILE="$HOME/.local/share/applications/sadp-gui.desktop"
CACHE_DIR="$HOME/.cache/sadp"

# Función para eliminar archivo/directorio
remove_if_exists() {
    local path="$1"
    local description="$2"
    
    if [[ -e "$path" ]]; then
        rm -rf "$path"
        echo -e "${GREEN}✓${NC} Eliminado: $description"
    fi
}

echo "🗑️  Eliminando archivos instalados..."
echo ""

# Eliminar directorio de instalación
remove_if_exists "$INSTALL_DIR" "Directorio de instalación (~/.local/bin/sadp)"

# Eliminar lanzador de aplicación
remove_if_exists "$DESKTOP_FILE" "Desktop launcher (~/.local/share/applications/sadp-gui.desktop)"

# Eliminar caché si existe
remove_if_exists "$CACHE_DIR" "Caché de la aplicación (~/.cache/sadp)"

# Limpiar comandos instalados
if command -v sadp-gui &> /dev/null; then
    # Buscar y eliminar los symlinks o copias del comando
    cmd_path=$(command -v sadp-gui)
    if [[ -L "$cmd_path" ]] || [[ "$cmd_path" == "$HOME/.local/bin/sadp-gui" ]]; then
        remove_if_exists "$cmd_path" "Comando sadp-gui"
    fi
fi

echo ""
echo -e "${GREEN}✅ Limpieza completada exitosamente${NC}"
echo ""
echo "Ahora puedes ejecutar nuevamente:"
echo "  bash setup-produccion.sh"
echo ""
echo "para instalar una versión limpia."
