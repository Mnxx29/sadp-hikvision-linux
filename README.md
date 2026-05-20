# SADP GUI para Linux - Descubridor de Cámaras Hikvision

Herramienta gráfica nativa de Linux para descubrir y acceder a cámaras IP Hikvision en redes locales.

## 🚀 Instalación Rápida

```bash
# ⚠️  IMPORTANTE: Ejecuta SIN sudo (el script pedirá sudo cuando sea necesario)
bash setup-produccion.sh

# Una vez completada la instalación:
sadp-gui
``` 

- Se crea un lanzador de escritorio para que la aplicación aparezca en el menú de Ubuntu.


**⚠️ NOTA IMPORTANTE:** 
- ✅ Ejecuta: `bash setup-produccion.sh` (SIN sudo)
- ❌ NO ejecutes: `sudo bash setup-produccion.sh`

Si ejecutas con `sudo`, se instalará en el home de root y no funcionará para otros usuarios.

## 📋 Requisitos

- Ubuntu 20.04 LTS o superior
- Conexión a red con cámaras Hikvision

## ✨ Características

- ✅ Descubrimiento automático de dispositivos (multicast SADP)
- ✅ Tabla interactiva con IP, MAC, modelo, firmware
- ✅ Doble clic para abrir en navegador
- ✅ Exportar datos a CSV
- ✅ Firewall automáticamente configurado
- ✅ Sin intervención manual del usuario

## 📚 Documentación

- [Instalación](docs/INSTALACION.md)
- [Cómo usar](docs/USO.md)
- [Solución de problemas](docs/TROUBLESHOOTING.md)

## 📄 Licencia

MIT License - Ver [LICENSE](LICENSE)

## 👨‍💻 Autor

Mnxx29

---

**Nota**: Este proyecto es una interfaz gráfica para [hikvision-tooling](https://github.com/cameronnewman/hikvision-tooling)
