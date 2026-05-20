# SADP GUI para Linux - Descubridor de Cámaras Hikvision

Aplicación gráfica nativa para Linux que descubre y lista cámaras IP Hikvision en la red local.

## 🚀 Instalación rápida

```bash
# Ejecuta SIN sudo (el instalador pedirá sudo cuando sea necesario)
bash setup-produccion.sh

# Después de la instalación abre la app desde el menú de Ubuntu o con:
sadp-gui
```

## 📋 Requisitos

- Ubuntu 20.04 LTS o superior
- Acceso a la red donde estén las cámaras Hikvision

## ✨ Características principales

- Descubrimiento automático de dispositivos (multicast SADP)
- Tabla interactiva con IP, MAC, modelo, firmware
- Doble clic para abrir la interfaz web de la cámara
- Exportar datos a CSV
- Configuración automática del firewall para permitir multicast

## 🖥️ Integración como aplicación

El instalador crea un lanzador de usuario en `~/.local/share/applications/sadp-gui.desktop` y un comando `sadp-gui`, por lo que la aplicación aparecerá en el menú de Ubuntu como cualquier otra app de usuario.

## 📚 Documentación

- [Instalación](docs/INSTALACION.md)
- [Cómo usar](docs/USO.md)
- [Solución de problemas](docs/TROUBLESHOOTING.md)

Por qué esas entradas están listadas: son enlaces a archivos dentro de la carpeta `docs/` que contienen guías ampliadas (instalación, uso y solución de problemas). Separar la documentación en páginas específicas ayuda a mantener el README conciso y ofrece instrucciones detalladas cuando las necesitas.

## 📄 Licencia

MIT License — ver [LICENSE](LICENSE)

## 👨‍💻 Autor

Mnxx29

---

**Nota**: Esta aplicación usa internamente [hikvision-tooling](https://github.com/cameronnewman/hikvision-tooling) para realizar el descubrimiento SADP.
