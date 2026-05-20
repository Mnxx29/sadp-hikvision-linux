# Cómo usar SADP GUI

Guía rápida para usar la interfaz gráfica.

## Iniciar la aplicación

- Lanza la app desde el menú de Ubuntu buscando "SADP GUI" o ejecuta `sadp-gui` en un terminal.

## Interfaz principal

- **🔍 Escanear Dispositivos**: inicia el descubrimiento SADP en la red local. Durante el escaneo la aplicación muestra una barra de progreso.
- **📥 Exportar a CSV**: guarda los dispositivos detectados en `dispositivos_hikvision.csv` en el directorio actual de trabajo (normalmente el directorio desde donde se lanzó `sadp-gui` o `~/.local/bin/sadp` si se usa el lanzador).
- **Tabla de dispositivos**: muestra las columnas: Dirección IP, MAC, Tipo, Estado, Puerto, Número de Serie, Versión.

### Doble clic en la IP

- Al hacer doble clic sobre una fila en la columna de IP se pregunta si deseas abrir la interfaz web de la cámara (`http://<IP>`). Aceptando, se abrirá el navegador predeterminado.

## Consejos de uso

- Si no aparecen dispositivos, intenta ejecutar el escaneo de nuevo y espera unos segundos; el descubrimiento multicast puede tardar dependiendo de la red.
- Si la app se instala con el lanzador, abre con el menú para tener el directorio de trabajo correcto (el lanzador cambia al directorio de instalación antes de ejecutar la GUI).
- Para exportar, usa el botón "Exportar a CSV"; el archivo resultante tiene las columnas `ip, mac, tipo, estado, puerto, serial, version`.

## Comportamiento del binario SADP

La interfaz usa internamente el binario `sadp-linux-amd64` (instalado en `~/.local/bin/sadp/`) para realizar el descubrimiento. Si necesitas depurar, puedes ejecutar el binario directamente:

```bash
~/.local/bin/sadp/sadp-linux-amd64 discover:sadp
```

Esto imprime los dispositivos detectados en stdout.

