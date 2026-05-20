# Solución de problemas

Guía de verificación y corrección de problemas comunes.

## 1) No se encuentran dispositivos

- Comprueba que estás en la misma red que las cámaras.
- Revisa el estado del firewall:

```bash
sudo ufw status verbose
```

- Permitir el puerto SADP si es necesario:

```bash
sudo ufw allow 37810/udp
```

- Verifica que el binario exista y sea ejecutable:

```bash
ls -l ~/.local/bin/sadp/sadp-linux-amd64
```

- Ejecuta el binario manualmente para observar la salida:

```bash
~/.local/bin/sadp/sadp-linux-amd64 discover:sadp
```

Si el binario imprime dispositivos en la terminal pero la GUI no los muestra, abre la GUI desde la terminal para inspeccionar errores visibles.

## 2) Errores de permisos (capabilities)

- Verifica las capabilities asignadas:

```bash
getcap ~/.local/bin/sadp/sadp-linux-amd64
```

- Si no aparece `cap_net_raw=ep`, asigna la capability:

```bash
sudo apt install -y libcap2-bin
sudo setcap cap_net_raw=ep ~/.local/bin/sadp/sadp-linux-amd64
```

Después reinicia la aplicación.

## 3) Fallo al compilar el binario (Go)

- Instala Go y vuelve a ejecutar el instalador:

```bash
sudo apt update
sudo apt install -y golang-go
bash setup-produccion.sh
```

- Alternativa: copiar un binario precompilado `sadp-linux-amd64` a `~/.local/bin/sadp/` y asegurarte de marcarlo ejecutable.

## 4) Problemas de red avanzados

- Si la red bloquea multicast, el descubrimiento no funcionará. Consulta con el administrador de red.
- Puedes comprobar tráfico UDP multicast con `tcpdump` (requiere privilegios y tcpdump instalado):

```bash
sudo apt install -y tcpdump
sudo tcpdump -n -i any udp port 37810
```

## 5) Otros

- Si abriste el instalador con `sudo`, desinstala y vuelve a ejecutar sin `sudo`.
- Para borrar la instalación:

```bash
rm -rf ~/.local/bin/sadp
rm -f ~/.local/bin/sadp-gui
rm -f ~/.local/share/applications/sadp-gui.desktop
```

Si necesitas ayuda adicional, indícame el mensaje de error concreto y te guío en el siguiente paso.
