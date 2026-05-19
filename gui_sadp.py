import sys
import subprocess
import csv
import io
import webbrowser
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QMessageBox, QLabel, QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

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
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.setSelectionBehavior(self.tabla.SelectionBehavior.SelectRows)
        self.tabla.cellDoubleClicked.connect(self.celda_clickeada)
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
        
        for idx, disp in enumerate(dispositivos):
            row_position = self.tabla.rowCount()
            self.tabla.insertRow(row_position)
            
            self.tabla.setItem(row_position, 0, QTableWidgetItem(disp['ip']))
            self.tabla.setItem(row_position, 1, QTableWidgetItem(disp['mac']))
            self.tabla.setItem(row_position, 2, QTableWidgetItem(disp['tipo']))
            self.tabla.setItem(row_position, 3, QTableWidgetItem(disp['estado']))
            self.tabla.setItem(row_position, 4, QTableWidgetItem(disp['puerto']))
            self.tabla.setItem(row_position, 5, QTableWidgetItem(disp['serial']))
            self.tabla.setItem(row_position, 6, QTableWidgetItem(disp['version']))
        
        self.status_label.setText(f"✅ Se encontraron {len(dispositivos)} dispositivo(s)")

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
