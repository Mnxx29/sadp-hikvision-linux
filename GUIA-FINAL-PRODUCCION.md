# 📦 SADP GUI para Linux - Guía de Producción

## ¿Qué es esto?

Una herramienta gráfica nativa para **descubrir y acceder a cámaras Hikvision en redes locales**. Reemplaza el SADP Tool oficial de Windows con una solución 100% Linux.

## Requisitos

- **Ubuntu 20.04 LTS o superior** (probado en 24.04 LTS)
- **Conexión a la red donde están las cámaras Hikvision**

## Instalación (3 pasos)

### Paso 1: Descargar los archivos

Descarga estos **3 archivos ÚNICOS**:

1. `setup.sh` - Script de instalación
2. `gui_sadp.py` - Interfaz gráfica
3. `sadp-linux-amd64` - Binario del scanner (compilado en Go)

### Paso 2: Ejecutar el instalador

```bash
bash setup.sh
```

El script:
- ✅ Instala Go (si no está instalado)
- ✅ Clona y compila el binario SADP real
- ✅ Instala Python3 + PyQt6
- ✅ Configura permisos de red
- ✅ Crea el lanzador

### Paso 3: Usar la aplicación

```bash
sadp-gui
```

O ejecuta directamente:

```bash
python3 ~/.local/bin/sadp/gui_sadp.py
```

## Características

✅ **Descubre cámaras automáticamente** - Multicast SADP en la red local  
✅ **Tabla interactiva** - IP, MAC, modelo, firmware, serial  
✅ **Doble clic en IP** - Abre el navegador web de la cámara  
✅ **Exportar a CSV** - Para reportes y auditorías  
✅ **Sin dependencias externas** - Solo Python y PyQt6  

## Uso Rápido

1. Abre `sadp-gui`
2. Presiona "🔍 Escanear Dispositivos"
3. Espera 10-15 segundos
4. Doble clic en cualquier IP para acceder

## Solución de Problemas

**Las cámaras no aparecen:**
```bash
# Verificar que el binario funciona
~/.local/bin/sadp/sadp-linux-amd64 discover:sadp

# Si muestra 0 dispositivos, el problema es la red, no la aplicación
```

**Permiso denegado al escanear:**
```bash
sudo setcap cap_net_raw,cap_net_admin=eip ~/.local/bin/sadp/sadp-linux-amd64
```

**La GUI se lanza pero no escanea:**
```bash
# Ejecutar con sudo temporalmente
sudo python3 ~/.local/bin/sadp/gui_sadp.py
```

## Arquitectura

```
┌──────────────────┐
│   gui_sadp.py    │  ← Interfaz gráfica (PyQt6)
│  (Python)        │
└────────┬─────────┘
         │ invoca
         ▼
┌──────────────────────┐
│ sadp-linux-amd64     │  ← Binario compilado (Go)
│ (Protocolo SADP)     │  ← Implementa multicast 239.255.255.250:37020
└────────┬─────────────┘
         │ envía
         ▼
┌──────────────────────┐
│  Red Local           │
│  Cámaras Hikvision   │
└──────────────────────┘
```

## Credenciales Predeterminadas

- **Usuario**: `admin`
- **Contraseña**: `12345`

⚠️ Cambiar después de acceder

## Notas Importantes

- Funciona **solo en la red local** (no atraviesa routers/VPNs)
- Requiere **acceso multicast** en la interfaz de red
- Las cámaras deben estar configuradas con IP en el rango de la red
- Compatible con **todas las cámaras Hikvision** que usen SADP (estándar)

## Para Múltiples PCs

1. **Crea una carpeta compartida** con los 3 archivos
2. **En cada PC remoto**, ejecuta `bash setup.sh`
3. **Listo** - La herramienta estará instalada y funcionando

---

**Versión**: 1.0 Producción  
**Última actualización**: Mayo 2026  
**Soporte**: Para cámaras Hikvision en redes locales
