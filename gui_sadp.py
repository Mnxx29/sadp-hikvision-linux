import sys
import subprocess
import csv
import io
import webbrowser
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QMessageBox, QLabel, QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings
from PyQt6.QtGui import QFont


class SortableItem(QTableWidgetItem):
    """QTableWidgetItem que soporta clave de ordenación personalizada."""
    def __init__(self, text: str, sort_key=None):
        super().__init__(text)
        self.sort_key = sort_key if sort_key is not None else text

    def __lt__(self, other):
        try:
            # Comparar por la clave de ordenación si existe
            return self.sort_key < other.sort_key
        except Exception:
            return super().__lt__(other)

class ScanThread(QThread):
    """Thread para ejecutar el escaneo sin congelar la interfaz"""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    devices = pyqtSignal(list)
    
    def run(self):
        try:
            import os
            
            # Obtener la ruta del directorio donde está este script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Rutas posibles del binario (en orden de preferencia)
            posibles_rutas = [
                os.path.join(script_dir, "sadp-linux-amd64"),
                os.path.join(script_dir, "sadp-linux-amd64-real"),
                "./sadp-linux-amd64",
                "./sadp-linux-amd64-real",
            ]
            
            binario_path = None
            for ruta in posibles_rutas:
                if os.path.exists(ruta):
                    binario_path = ruta
                    break
            
            if not binario_path:
                self.error.emit(f"No se encontró el binario SADP.\nBuscó en:\n- {script_dir}/sadp-linux-amd64\n- {script_dir}/sadp-linux-amd64-real\n\nAsegúrate de que el archivo esté en el mismo directorio que gui_sadp.py")
                self.finished.emit()
                return
            
            # Intentar ejecutar el binario
            resultado = subprocess.run(
                ["python3", binario_path, "discover:sadp"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False
            )
            
            # Si falla con python3, intentar ejecutarlo directamente
            if resultado.returncode != 0 and not binario_path.endswith("-real"):
                resultado = subprocess.run(
                    [binario_path, "discover:sadp"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False
                )
            
            if resultado.returncode != 0:
                self.error.emit(f"Error al ejecutar sadp:\n{resultado.stderr}")
                self.finished.emit()
                return
            
            # Parsear la salida
            dispositivos = []
            lineas = resultado.stdout.strip().split('\n')
            
            # Buscar la línea donde comienzan los datos (después de los ===)
            inicio_datos = False
            for linea in lineas:
                if '-----' in linea or '=====' in linea:
                    inicio_datos = True
                    continue
                
                if inicio_datos and linea.strip() and not linea.startswith('#'):
                    # Parsear cada línea de dispositivo
                    # Formato: #   IP   MAC   Tipo   Estado   Puerto   Serial   Version
                    partes = linea.split()
                    
                    if len(partes) >= 8:
                        try:
                            numero = partes[0]
                            ip = partes[1]
                            mac = partes[2]
                            tipo = partes[3]
                            estado = partes[4]
                            puerto = partes[5]
                            serial = partes[6]
                            version = ' '.join(partes[7:])
                            
                            dispositivos.append({
                                'ip': ip,
                                'mac': mac,
                                'tipo': tipo,
                                'estado': estado,
                                'puerto': puerto,
                                'serial': serial,
                                'version': version
                            })
                        except:
                            pass
            
            self.devices.emit(dispositivos)
            self.finished.emit()
            
        except subprocess.TimeoutExpired:
            self.error.emit("Timeout: el escaneo tardó demasiado tiempo")
            self.finished.emit()
        except FileNotFoundError:
            self.error.emit("No se encontró el binario 'sadp-linux-amd64' en el directorio actual")
            self.finished.emit()
        except Exception as e:
            self.error.emit(f"Error inesperado: {str(e)}")
            self.finished.emit()


class SADPGui(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SADP Tool para Linux")
        self.setGeometry(100, 100, 1000, 600)
        self.scan_thread = None
        self.settings = QSettings("sadp", "sadp-gui")
        
        # Widget principal y Layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)
        
        # Título
        titulo = QLabel("Escáner de Dispositivos Hikvision SADP")
        titulo_font = QFont()
        titulo_font.setPointSize(14)
        titulo_font.setBold(True)
        titulo.setFont(titulo_font)
        self.layout.addWidget(titulo)
        
        # Barra de herramientas superior (Botones)
        self.top_layout = QHBoxLayout()
        self.btn_scan = QPushButton("🔍 Escanear Dispositivos")
        self.btn_scan.setMinimumHeight(40)
        self.btn_scan.clicked.connect(self.ejecutar_escaneo)
        self.top_layout.addWidget(self.btn_scan)
        
        self.btn_export = QPushButton("📥 Exportar a CSV")
        self.btn_export.setMinimumHeight(40)
        self.btn_export.clicked.connect(self.exportar_csv)
        self.btn_export.setEnabled(False)
        self.top_layout.addWidget(self.btn_export)
        
        self.top_layout.addStretch()
        self.layout.addLayout(self.top_layout)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(0)  # Modo indeterminado
        self.progress_bar.setVisible(False)
        self.layout.addWidget(self.progress_bar)
        
        # Etiqueta de estado
        self.status_label = QLabel("Presiona 'Escanear Dispositivos' para comenzar")
        self.layout.addWidget(self.status_label)
        
        # Tabla de dispositivos
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels([
            "Dirección IP", 
            "Dirección MAC", 
            "Tipo de Dispositivo", 
            "Estado", 
            "Puerto", 
            "Número de Serie",
            "Versión"
        ])
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionsClickable(True)
        header.setSortIndicatorShown(True)
        self.tabla.setSelectionBehavior(self.tabla.SelectionBehavior.SelectRows)
        self.tabla.cellDoubleClicked.connect(self.celda_clickeada)
        # Restaurar estado del encabezado (orden/posición/tamaños) si existe
        try:
            state = self.settings.value("headerState")
            if state is not None:
                header.restoreState(state)
        except Exception:
            pass

        # Restaurar columna/orden de ordenación
        try:
            sort_col = self.settings.value("sortColumn")
            sort_order = self.settings.value("sortOrder")
            if sort_col is not None:
                sort_col = int(sort_col)
                sort_order = int(sort_order) if sort_order is not None else int(Qt.SortOrder.AscendingOrder)
                self.tabla.sortItems(sort_col, Qt.SortOrder(sort_order))
        except Exception:
            pass

        # Conectar señales para persistir cambios del encabezado y orden
        header.sectionMoved.connect(self.save_header_state)
        header.sectionResized.connect(self.save_header_state)
        header.sortIndicatorChanged.connect(self.save_sort_indicator)
        # Habilitar ordenación; la deshabilitaremos temporalmente al rellenar
        self.tabla.setSortingEnabled(True)
        self.layout.addWidget(self.tabla)
        
        # Almacenar dispositivos para exportar
        self.dispositivos = []

    def ejecutar_escaneo(self):
        """Inicia el escaneo en un thread aparte"""
        if self.scan_thread and self.scan_thread.isRunning():
            QMessageBox.warning(self, "Escaneo en curso", "Ya hay un escaneo en progreso")
            return
        
        self.tabla.setRowCount(0)
        self.dispositivos = []
        self.btn_scan.setEnabled(False)
        self.btn_export.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Escaneando dispositivos... por favor espera")
        
        self.scan_thread = ScanThread()
        self.scan_thread.devices.connect(self.mostrar_dispositivos)
        self.scan_thread.error.connect(self.mostrar_error)
        self.scan_thread.finished.connect(self.escaneo_finalizado)
        self.scan_thread.start()

    def mostrar_dispositivos(self, dispositivos):
        """Muestra los dispositivos en la tabla"""
        self.dispositivos = dispositivos
        
        if not dispositivos:
            self.status_label.setText("⚠️  No se encontraron dispositivos Hikvision en la red")
            return
        
        # Desactivar ordenación mientras se insertan filas para evitar reordenados intermedios
        self.tabla.setSortingEnabled(False)
        for idx, disp in enumerate(dispositivos):
            row_position = self.tabla.rowCount()
            self.tabla.insertRow(row_position)
            # IP: convertir a tupla de enteros para ordenar correctamente
            ip_text = disp.get('ip', '')
            try:
                ip_key = tuple(int(x) for x in ip_text.split('.') if x != '')
            except Exception:
                ip_key = ip_text
            self.tabla.setItem(row_position, 0, SortableItem(ip_text, sort_key=ip_key))

            # MAC: normalizar para ordenar
            mac_text = disp.get('mac', '')
            mac_key = mac_text.replace(':', '').replace('-', '').lower()
            self.tabla.setItem(row_position, 1, SortableItem(mac_text, sort_key=mac_key))

            # Tipo y Estado: ordenar por texto
            tipo_text = disp.get('tipo', '')
            self.tabla.setItem(row_position, 2, SortableItem(tipo_text, sort_key=tipo_text))

            estado_text = disp.get('estado', '')
            self.tabla.setItem(row_position, 3, SortableItem(estado_text, sort_key=estado_text))

            # Puerto: ordenar numéricamente si es posible
            puerto_text = disp.get('puerto', '')
            try:
                puerto_key = int(puerto_text)
            except Exception:
                puerto_key = puerto_text
            self.tabla.setItem(row_position, 4, SortableItem(puerto_text, sort_key=puerto_key))

            # Serial y Versión: texto
            serial_text = disp.get('serial', '')
            self.tabla.setItem(row_position, 5, SortableItem(serial_text, sort_key=serial_text))

            version_text = disp.get('version', '')
            self.tabla.setItem(row_position, 6, SortableItem(version_text, sort_key=version_text))
        
        # Volver a activar ordenación después de insertar todas las filas
        self.tabla.setSortingEnabled(True)
        self.status_label.setText(f"✅ Se encontraron {len(dispositivos)} dispositivo(s)")

    def save_header_state(self, *args):
        try:
            header = self.tabla.horizontalHeader()
            state = header.saveState()
            self.settings.setValue("headerState", state)
        except Exception:
            pass

    def save_sort_indicator(self, index: int, order: Qt.SortOrder):
        try:
            self.settings.setValue("sortColumn", int(index))
            # store as int
            self.settings.setValue("sortOrder", int(order))
        except Exception:
            pass

    def closeEvent(self, event):
        # Guardar estado al cerrar
        try:
            self.save_header_state()
        except Exception:
            pass
        super().closeEvent(event)

    def mostrar_error(self, mensaje):
        """Muestra un error"""
        QMessageBox.critical(self, "Error", f"Error en el escaneo:\n\n{mensaje}")
        self.status_label.setText("❌ Error durante el escaneo")

    def escaneo_finalizado(self):
        """Llamado cuando el escaneo termina"""
        self.btn_scan.setEnabled(True)
        if self.dispositivos:
            self.btn_export.setEnabled(True)
        self.progress_bar.setVisible(False)

    def celda_clickeada(self, row, column):
        """Maneja el doble clic en las celdas"""
        if column == 0:  # Columna de IP
            item_ip = self.tabla.item(row, column)
            if item_ip:
                ip = item_ip.text()
                url = f"http://{ip}"
                
                respuesta = QMessageBox.question(
                    self,
                    "Abrir en navegador",
                    f"¿Deseas abrir la interfaz web de {ip}?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if respuesta == QMessageBox.StandardButton.Yes:
                    webbrowser.open(url)
                    self.status_label.setText(f"Abriendo {url} en el navegador...")

    def exportar_csv(self):
        """Exporta los dispositivos a un archivo CSV"""
        if not self.dispositivos:
            QMessageBox.warning(self, "No hay datos", "No hay dispositivos para exportar")
            return
        
        try:
            filename = "dispositivos_hikvision.csv"
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['ip', 'mac', 'tipo', 'estado', 'puerto', 'serial', 'version'])
                writer.writeheader()
                writer.writerows(self.dispositivos)
            
            QMessageBox.information(self, "Éxito", f"Datos exportados a '{filename}'")
            self.status_label.setText(f"Exportado: {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al exportar: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = SADPGui()
    ventana.show()
    sys.exit(app.exec())
