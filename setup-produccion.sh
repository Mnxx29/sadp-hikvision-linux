#!/bin/bash

# SADP GUI para Linux - Script de Instalación de Producción
# Con detección automática de interfaz de red
# Uso: bash setup-produccion.sh

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║    SADP GUI para Linux - Instalación de Producción        ║"
echo "║    Descubridor de Cámaras Hikvision                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Validar que NO se ejecuta con sudo
if [[ "$EUID" -eq 0 ]]; then
    echo "❌ ERROR: Este script NO debe ejecutarse con sudo"
    echo ""
    echo "   Ejecuta:"
    echo "   bash setup-produccion.sh"
    echo ""
    echo "   NO ejecutes:"
    echo "   sudo bash setup-produccion.sh"
    echo ""
    echo "   El script pedirá sudo automáticamente cuando sea necesario"
    exit 1
fi

# Guardar el directorio donde se ejecutó el script (donde están los archivos)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Verificar que es Ubuntu
if ! grep -q "Ubuntu" /etc/os-release 2>/dev/null; then
    echo "❌ Este script está diseñado para Ubuntu"
    exit 1
fi

INSTALL_DIR="$HOME/.local/bin/sadp"
mkdir -p "$INSTALL_DIR"

echo "📋 Sistema: $(grep PRETTY_NAME /etc/os-release | cut -d'"' -f2)"
echo "📁 Instalación en: $INSTALL_DIR"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FUNCIÓN: Detectar interfaz de red
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

detect_network_interface() {
    echo "🔍 Detectando interfaz de red activa..."
    
    # Método 1: Usar ip route para obtener la interfaz por defecto
    DEFAULT_IFACE=$(ip route | grep '^default' | awk '{print $5}' | head -1)
    
    if [[ -n "$DEFAULT_IFACE" ]]; then
        # Obtener la IP de esa interfaz
        IFACE_IP=$(ip addr show "$DEFAULT_IFACE" | grep "inet " | awk '{print $2}' | cut -d'/' -f1)
        
        if [[ -n "$IFACE_IP" ]]; then
            echo "✅ Interfaz detectada: $DEFAULT_IFACE"
            echo "   IP: $IFACE_IP"
            echo ""
            return 0
        fi
    fi
    
    # Método 2: Si falla, buscar cualquier interfaz con IP (no loopback)
    echo "⚠️  No se detectó interfaz por defecto, buscando alternativas..."
    
    DEFAULT_IFACE=$(ip link show | grep "UP" | grep -v "lo:" | awk '{print $2}' | sed 's/:$//' | head -1)
    
    if [[ -n "$DEFAULT_IFACE" ]]; then
        IFACE_IP=$(ip addr show "$DEFAULT_IFACE" | grep "inet " | awk '{print $2}' | cut -d'/' -f1)
        
        if [[ -n "$IFACE_IP" ]]; then
            echo "✅ Interfaz alternativa detectada: $DEFAULT_IFACE"
            echo "   IP: $IFACE_IP"
            echo ""
            return 0
        fi
    fi
    
    echo "❌ No se pudo detectar ninguna interfaz de red activa"
    return 1
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FUNCIÓN: Configurar firewall para SADP multicast
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

configure_ufw() {
    echo "🔐 Configurando firewall para SADP multicast..."
    
    # Verificar si UFW está instalado
    if ! command -v ufw &> /dev/null; then
        echo "   ⚠️  UFW no instalado, usando iptables directamente"
        configure_iptables
        return 0
    fi
    
    # Intentar configurar con UFW (método moderno)
    local ufw_ok=true
    
    # Permitir puerto SADP específico (UDP 37810)
    sudo ufw allow 37810/udp 2>/dev/null && \
        echo "   ✓ Puerto SADP UDP 37810 permitido" || {
        echo "   ⚠️  No se pudo permitir puerto 37810 en UFW"
        ufw_ok=false
    }
    
    # Permitir multicast en entrada
    sudo ufw allow in proto udp to 224.0.0.0/4 2>/dev/null && \
        echo "   ✓ Multicast entrada permitido" || echo "   ⚠️  Multicast entrada (intento fallido)"
    
    # Permitir multicast en salida
    sudo ufw allow out proto udp to 224.0.0.0/4 2>/dev/null && \
        echo "   ✓ Multicast salida permitido" || echo "   ⚠️  Multicast salida (intento fallido)"
    
    # Habilitar UFW si no está habilitado
    if ! sudo ufw status | grep -q "Status: active"; then
        sudo ufw --force enable 2>/dev/null && echo "   ✓ Firewall habilitado" || echo "   ⚠️  Error habilitando firewall"
    else
        echo "   ✓ Firewall ya está activo"
    fi
    
    # Si UFW falla, usar iptables como fallback
    if [[ "$ufw_ok" == false ]]; then
        echo ""
        echo "   📋 Configurando reglas iptables adicionales..."
        configure_iptables
    fi
    
    echo ""
}

configure_iptables() {
    echo "   🔧 Configurando iptables para SADP..."
    
    # Permitir todo el tráfico multicast
    sudo iptables -A INPUT -d 224.0.0.0/4 -j ACCEPT 2>/dev/null && echo "   ✓ Entrada multicast aceptada" || true
    sudo iptables -A OUTPUT -d 224.0.0.0/4 -j ACCEPT 2>/dev/null && echo "   ✓ Salida multicast aceptada" || true
    
    # Permitir específicamente puerto SADP
    sudo iptables -A INPUT -p udp --dport 37810 -j ACCEPT 2>/dev/null && echo "   ✓ Puerto entrada 37810 aceptado" || true
    sudo iptables -A OUTPUT -p udp --dport 37810 -j ACCEPT 2>/dev/null && echo "   ✓ Puerto salida 37810 aceptado" || true
    
    # Persistir las reglas (ip6tables también)
    if command -v iptables-save &> /dev/null; then
        sudo iptables-save | sudo tee /etc/iptables/rules.v4 >/dev/null 2>&1 || true
    fi
    
    if command -v ip6tables-save &> /dev/null; then
        sudo ip6tables-save | sudo tee /etc/iptables/rules.v6 >/dev/null 2>&1 || true
    fi
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Paso 1: Instalación de dependencias
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Paso 1: Instalando dependencias..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

sudo apt update >/dev/null 2>&1 || true
echo "📦 Instalando: python3, python3-pyqt6, golang-go, git, ufw..."

sudo apt install -y python3 python3-pyqt6 golang-go git ufw >/dev/null 2>&1

echo "✅ Dependencias instaladas"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Paso 2: Detectar interfaz de red
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Paso 2: Detectando configuración de red..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if ! detect_network_interface; then
    echo "❌ No se pudo detectar la interfaz de red"
    exit 1
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Paso 3: Compilar binario SADP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Paso 3: Compilando binario SADP..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

TEMP_BUILD="/tmp/sadp-build-$$"
mkdir -p "$TEMP_BUILD"

echo "📥 Clonando repositorio hikvision-tooling..."
cd "$TEMP_BUILD"
git clone --depth 1 https://github.com/cameronnewman/hikvision-tooling.git >/dev/null 2>&1

cd hikvision-tooling
echo "🔨 Compilando con Go (esto puede tardar 30-60 segundos)..."

CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-s -w" -o sadp-linux-amd64 ./cmd/sadp 2>&1 | grep -v "^$" || true

if [[ -f "sadp-linux-amd64" ]]; then
    echo "✅ Binario compilado exitosamente"
    cp sadp-linux-amd64 "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/sadp-linux-amd64"
else
    echo "❌ Error compilando el binario"
    exit 1
fi

echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Paso 4: Copiar GUI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Paso 4: Instalando interfaz gráfica..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Buscar gui_sadp.py en el directorio original del script
if [[ -f "$SCRIPT_DIR/gui_sadp.py" ]]; then
    cp "$SCRIPT_DIR/gui_sadp.py" "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/gui_sadp.py"
    echo "✅ GUI instalada"
else
    echo "❌ No se pudo encontrar gui_sadp.py en $SCRIPT_DIR"
    echo "   Asegúrate de que el archivo gui_sadp.py está en el mismo directorio que el script de instalación"
    exit 1
fi

echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Paso 5: Crear lanzador
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Paso 5: Creando lanzador..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

LAUNCHER="$HOME/.local/bin/sadp-gui"
cat > "$LAUNCHER" << 'LAUNCHER_EOF'
#!/bin/bash
cd "$HOME/.local/bin/sadp"
python3 gui_sadp.py
LAUNCHER_EOF

chmod +x "$LAUNCHER"
echo "✅ Lanzador creado: sadp-gui"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Paso 6: Configurar permisos de red
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Paso 6: Configurando firewall para multicast..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

configure_ufw

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Paso 7: Configurar permisos de red para el binario
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Paso 7: Configurando permisos de red para el binario..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "   Configurando capabilities del binario para multicast..."
if command -v setcap &> /dev/null; then
    # Dar capacidades necesarias para raw sockets y multicast
    sudo setcap cap_net_raw=ep "$INSTALL_DIR/sadp-linux-amd64" 2>/dev/null && \
        echo "   ✅ Permisos cap_net_raw configurados" || \
        echo "   ⚠️  Error configurando cap_net_raw"
    
    # Verificar que se asignaron correctamente
    if sudo getcap "$INSTALL_DIR/sadp-linux-amd64" 2>/dev/null | grep -q "cap_net_raw"; then
        echo "   ✅ Capabilities verificadas correctamente"
    fi
else
    echo "   ⚠️  setcap no encontrado, se intentará sin capabilities"
fi

echo ""

# Limpiar archivos temporales
rm -rf "$TEMP_BUILD"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RESUMEN FINAL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "╔════════════════════════════════════════════════════════════╗"
echo "║            ✅ INSTALACIÓN COMPLETADA                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "🚀 Para abrir la aplicación, ejecuta:"
echo ""
echo "   sadp-gui"
echo ""
echo "   O:"
echo ""
echo "   python3 ~/.local/bin/sadp/gui_sadp.py"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Configuración aplicada:"
echo "   • Interfaz de red: $DEFAULT_IFACE"
echo "   • IP local: $IFACE_IP"
echo "   • Firewall: Configurado para multicast"
echo "   • Directorio instalación: $INSTALL_DIR"
echo ""
echo "📞 Credenciales predeterminada: admin / 12345"
echo ""
echo "✨ ¡Listo para usar en cualquier PC!"
echo ""
