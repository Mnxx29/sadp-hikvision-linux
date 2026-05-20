# Instalación

Esta página describe la instalación de la aplicación SADP GUI en sistemas Ubuntu.

## Requisitos

- Ubuntu 20.04 LTS o superior
- Conexión a la red local donde estén las cámaras Hikvision
- Acceso a internet para descargar dependencias y clonar repositorios
- `python3` y `python3-pyqt6` para la interfaz gráfica (el instalador puede instalarlos)
- Opcionalmente `git` y `golang-go` si quieres compilar el binario localmente

## Instalación rápida (usuario)

1. Clona o descarga este repositorio y sitúate en su carpeta:

```bash
cd /ruta/al/repositorio
bash setup-produccion.sh
```

> Nota: ejecuta el script sin `sudo`. El instalador pedirá permisos elevador cuando sean necesarios. Ejecutar el script como `sudo` instalaría los archivos en el home de `root` y no funcionaría correctamente para tu usuario.

2. Finalizada la instalación:

- El binario SADP y la GUI se instalan en `~/.local/bin/sadp/`.
- Se crea un lanzador de usuario `~/.local/bin/sadp-gui` y un archivo de escritorio en `~/.local/share/applications/sadp-gui.desktop`.

3. Abrir la aplicación

- Desde el menú de Ubuntu busca "SADP GUI" o ejecuta:

```bash
sadp-gui
```

## Notas sobre capacidades y firewall

- El instalador intenta configurar `setcap cap_net_raw=ep` sobre el binario (`sadp-linux-amd64`) para permitir el acceso a sockets raw necesarios para el descubrimiento multicast.
- También configura `ufw` (o `iptables` como fallback) para permitir tráfico multicast/puerto UDP 37810.

Si tu sistema no tiene `setcap`, el descubrimiento puede requerir ejecutar el binario con privilegios (no recomendado). Mejor instalar `libcap2-bin` y volver a ejecutar el instalador.

## Desinstalación rápida

```bash
rm -rf ~/.local/bin/sadp
rm -f ~/.local/bin/sadp-gui
rm -f ~/.local/share/applications/sadp-gui.desktop
```

## Problemas al compilar

- Si la compilación en Go falla, instala `golang-go` o revisa que la versión de Go sea compatible. También puedes usar un binario precompilado en lugar de compilar localmente.


