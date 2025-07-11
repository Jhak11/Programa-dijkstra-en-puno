# ui/ventana.py
import sys
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QComboBox, QListWidget, QPushButton, QLabel, 
                             QTextEdit, QSplitter, QProgressBar, QMessageBox,
                             QGroupBox, QGridLayout, QListWidgetItem)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QThread, pyqtSignal, QUrl, Qt
from PyQt5.QtGui import QFont, QPixmap, QIcon

# Imports del proyecto
from config import CIUDAD_DEFAULT
from grafo.osm_datos import (obtener_grafo_ciudad, obtener_hospitales, 
                            guardar_hospitales, cargar_hospitales, 
                            obtener_nodos_principales)
from grafo.grafo import procesar_rutas_hospitales
from grafo.utilidades import nodo_mas_cercano, coordenadas_nodo
from mapa import generar_mapa_html, generar_mapa_simple

class WorkerThread(QThread):
    """
    Hilo de trabajo para operaciones pesadas
    """
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def __init__(self, task, *args, **kwargs):
        super().__init__()
        self.task = task
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        try:
            if self.task == 'cargar_grafo':
                self.progress.emit("Descargando grafo de la ciudad...")
                ciudad = self.args[0]
                grafo = obtener_grafo_ciudad(ciudad)
                self.finished.emit(grafo)
                
            elif self.task == 'cargar_hospitales':
                self.progress.emit("Buscando hospitales...")
                ciudad = self.args[0]
                hospitales = obtener_hospitales()
                self.finished.emit(hospitales)
                
            elif self.task == 'calcular_rutas':
                self.progress.emit("Calculando rutas más cortas...")
                G, nodo_origen, hospitales = self.args
                resultado = procesar_rutas_hospitales(G, nodo_origen, hospitales)
                self.finished.emit(resultado)
                
        except Exception as e:
            self.error.emit(str(e))

class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.G = None
        self.hospitales = []
        self.nodos_principales = []
        self.worker = None
        
        self.init_ui()
        self.cargar_datos_iniciales()
    
    def init_ui(self):
        """
        Inicializa la interfaz de usuario
        """
        self.setWindowTitle("Rutas a Hospitales - Algoritmo de Dijkstra")
        self.setGeometry(100, 100, 1400, 800)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        
        # Splitter para dividir la interfaz
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Panel de control (izquierda)
        self.create_control_panel(splitter)
        
        # Panel del mapa (derecha)
        self.create_map_panel(splitter)
        
        # Configurar proporciones del splitter
        splitter.setSizes([400, 1000])
        
        # Barra de estado
        self.statusBar().showMessage("Listo")
        
        # Aplicar estilos
        self.apply_styles()
    
    def create_control_panel(self, parent):
        """
        Crea el panel de control
        """
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)
        
        # Título
        title_label = QLabel("Control de Rutas")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        control_layout.addWidget(title_label)
        
        # Grupo de configuración
        config_group = QGroupBox("Configuración")
        config_layout = QGridLayout(config_group)
        
        # Selector de ciudad
        config_layout.addWidget(QLabel("Ciudad:"), 0, 0)
        self.ciudad_combo = QComboBox()
        self.ciudad_combo.addItems([CIUDAD_DEFAULT, "Arequipa, Peru", "Cusco, Peru", "Trujillo, Peru"])
        self.ciudad_combo.setEditable(True)
        config_layout.addWidget(self.ciudad_combo, 0, 1)
        
        # Botón para cargar datos
        self.btn_cargar_datos = QPushButton("Cargar Datos")
        self.btn_cargar_datos.clicked.connect(self.cargar_datos_ciudad)
        config_layout.addWidget(self.btn_cargar_datos, 1, 0, 1, 2)
        
        control_layout.addWidget(config_group)
        
        # Grupo de origen
        origen_group = QGroupBox("Punto de Origen")
        origen_layout = QVBoxLayout(origen_group)
        
        self.origen_combo = QComboBox()
        self.origen_combo.setEnabled(False)
        origen_layout.addWidget(self.origen_combo)
        
        control_layout.addWidget(origen_group)
        
        # Grupo de destinos
        destinos_group = QGroupBox("Hospitales Disponibles")
        destinos_layout = QVBoxLayout(destinos_group)
        
        self.hospitales_list = QListWidget()
        self.hospitales_list.setEnabled(False)
        destinos_layout.addWidget(self.hospitales_list)
        
        control_layout.addWidget(destinos_group)
        
        # Botón para calcular rutas
        self.btn_calcular = QPushButton("Calcular Rutas")
        self.btn_calcular.setEnabled(False)
        self.btn_calcular.clicked.connect(self.calcular_rutas)
        control_layout.addWidget(self.btn_calcular)
        
        # Grupo de resultados
        resultados_group = QGroupBox("Resultados")
        resultados_layout = QVBoxLayout(resultados_group)
        
        self.resultados_text = QTextEdit()
        self.resultados_text.setMaximumHeight(200)
        self.resultados_text.setReadOnly(True)
        resultados_layout.addWidget(self.resultados_text)
        
        control_layout.addWidget(resultados_group)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        control_layout.addWidget(self.progress_bar)
        
        # Label de estado
        self.status_label = QLabel("Cargar datos para comenzar")
        control_layout.addWidget(self.status_label)
        
        # Espacio flexible
        control_layout.addStretch()
        
        parent.addWidget(control_widget)
    
    def create_map_panel(self, parent):
        """
        Crea el panel del mapa
        """
        map_widget = QWidget()
        map_layout = QVBoxLayout(map_widget)
        
        # Título del mapa
        map_title = QLabel("Visualización de Rutas")
        map_title.setFont(QFont("Arial", 12, QFont.Bold))
        map_layout.addWidget(map_title)
        
        # Vista web para el mapa
        self.web_view = QWebEngineView()
        map_layout.addWidget(self.web_view)
        
        # Cargar mapa inicial
        self.cargar_mapa_inicial()
        
        parent.addWidget(map_widget)
    
    def apply_styles(self):
        """
        Aplica estilos a la interfaz
        """
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin: 5px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QComboBox, QListWidget, QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 4px;
            }
            QListWidget::item:selected {
                background-color: #4CAF50;
                color: white;
            }
        """)
    
    def cargar_mapa_inicial(self):
        """
        Carga un mapa inicial centrado en Lima
        """
        try:
            archivo_mapa = generar_mapa_simple(-15.8402, -70.0219)
            if archivo_mapa and os.path.exists(archivo_mapa):
                self.web_view.load(QUrl.fromLocalFile(os.path.abspath(archivo_mapa)))
        except Exception as e:
            print(f"Error cargando mapa inicial: {e}")
    
    def cargar_datos_iniciales(self):
        """
        Intenta cargar datos guardados previamente
        """
        try:
            hospitales = cargar_hospitales()
            if hospitales:
                self.hospitales = hospitales
                self.actualizar_lista_hospitales()
                self.status_label.setText("Hospitales cargados desde archivo")
        except Exception as e:
            print(f"Error cargando datos iniciales: {e}")
    
    def cargar_datos_ciudad(self):
        """
        Carga los datos de la ciudad seleccionada
        """
        ciudad = self.ciudad_combo.currentText().strip()
        if not ciudad:
            QMessageBox.warning(self, "Error", "Por favor selecciona una ciudad")
            return
        
        self.btn_cargar_datos.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Progreso indeterminado
        
        # Cargar grafo
        self.worker = WorkerThread('cargar_grafo', ciudad)
        self.worker.finished.connect(self.on_grafo_cargado)
        self.worker.error.connect(self.on_error)
        self.worker.progress.connect(self.on_progress)
        self.worker.start()
    
    def on_grafo_cargado(self, grafo):
        """
        Callback cuando el grafo ha sido cargado
        """
        if grafo:
            self.G = grafo
            self.status_label.setText("Grafo cargado exitosamente")
            
            # Obtener nodos principales
            self.nodos_principales = obtener_nodos_principales(self.G)
            self.actualizar_combo_origen()
            
            # Cargar hospitales
            ciudad = self.ciudad_combo.currentText().strip()
            self.worker = WorkerThread('cargar_hospitales', ciudad)
            self.worker.finished.connect(self.on_hospitales_cargados)
            self.worker.error.connect(self.on_error)
            self.worker.progress.connect(self.on_progress)
            self.worker.start()
        else:
            self.on_error("No se pudo cargar el grafo")
    
    def on_hospitales_cargados(self, hospitales):
        """
        Callback cuando los hospitales han sido cargados
        """
        if hospitales:
            self.hospitales = hospitales
            guardar_hospitales(hospitales)  # Guardar para uso futuro
            self.actualizar_lista_hospitales()
            self.status_label.setText(f"Cargados {len(hospitales)} hospitales")
            self.btn_calcular.setEnabled(True)
        else:
            self.on_error("No se encontraron hospitales")
        
        self.progress_bar.setVisible(False)
        self.btn_cargar_datos.setEnabled(True)
    
    def actualizar_combo_origen(self):
        """
        Actualiza el combo de puntos de origen
        """
        self.origen_combo.clear()
        for nodo_info in self.nodos_principales:
            self.origen_combo.addItem(nodo_info['nombre'], nodo_info['id'])
        self.origen_combo.setEnabled(True)
    
    def actualizar_lista_hospitales(self):
        """
        Actualiza la lista de hospitales
        """
        self.hospitales_list.clear()
        for hospital in self.hospitales:
            item = QListWidgetItem(hospital['nombre'])
            item.setData(Qt.UserRole, hospital)
            self.hospitales_list.addItem(item)
        self.hospitales_list.setEnabled(True)
    
    def calcular_rutas(self):
        """
        Calcula las rutas a los hospitales seleccionados
        """
        if not self.G:
            QMessageBox.warning(self, "Error", "Primero carga los datos del grafo")
            return
        
        if self.origen_combo.currentIndex() == -1:
            QMessageBox.warning(self, "Error", "Selecciona un punto de origen")
            return
        
        if not self.hospitales:
            QMessageBox.warning(self, "Error", "No hay hospitales disponibles")
            return
        
        # Obtener nodo de origen
        nodo_origen = self.origen_combo.currentData()
        
        # Obtener hospitales seleccionados (o todos si no hay selección)
        hospitales_seleccionados = []
        if self.hospitales_list.selectedItems():
            for item in self.hospitales_list.selectedItems():
                hospitales_seleccionados.append(item.data(Qt.UserRole))
        else:
            hospitales_seleccionados = self.hospitales
        
        # Calcular rutas
        self.btn_calcular.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        self.worker = WorkerThread('calcular_rutas', self.G, nodo_origen, hospitales_seleccionados)
        self.worker.finished.connect(self.on_rutas_calculadas)
        self.worker.error.connect(self.on_error)
        self.worker.progress.connect(self.on_progress)
        self.worker.start()
    
    def on_rutas_calculadas(self, resultado):
        """
        Callback cuando las rutas han sido calculadas
        """
        if resultado and resultado['rutas']:
            # Mostrar resultados
            self.mostrar_resultados(resultado)
            
            # Generar mapa
            nodo_origen = self.origen_combo.currentData()
            archivo_mapa = generar_mapa_html(self.G, nodo_origen, resultado)
            
            if archivo_mapa and os.path.exists(archivo_mapa):
                self.web_view.load(QUrl.fromLocalFile(os.path.abspath(archivo_mapa)))
                self.status_label.setText("Rutas calculadas y mapa generado")
            else:
                self.status_label.setText("Rutas calculadas pero error generando mapa")
        else:
            self.on_error("No se pudieron calcular las rutas")
        
        self.progress_bar.setVisible(False)
        self.btn_calcular.setEnabled(True)
    
    def mostrar_resultados(self, resultado):
        """
        Muestra los resultados en el panel de texto
        """
        texto_resultados = "=== RESULTADOS DE RUTAS ===\n\n"
        
        # Estadísticas generales
        if 'estadisticas' in resultado:
            stats = resultado['estadisticas']
            texto_resultados += f"Rutas calculadas: {stats['total_rutas']}\n"
            texto_resultados += f"Distancia mínima: {stats['distancia_minima']:.0f}m\n"
            texto_resultados += f"Distancia máxima: {stats['distancia_maxima']:.0f}m\n"
            texto_resultados += f"Distancia promedio: {stats['distancia_promedio']:.0f}m\n\n"
        
        # Detalles de cada ruta
        rutas_ordenadas = sorted(
            resultado['rutas'].items(),
            key=lambda x: x[1]['longitud']
        )
        
        for i, (nodo, ruta_info) in enumerate(rutas_ordenadas):
            hospital_info = resultado['hospitales_info'][nodo]
            es_mas_cercano = nodo == resultado['destino_mas_cercano']
            
            texto_resultados += f"{i+1}. {hospital_info['nombre']}\n"
            texto_resultados += f"   Distancia: {ruta_info['longitud_formateada']}\n"
            texto_resultados += f"   Tiempo: {ruta_info['tiempo_formateado']}\n"
            
            if es_mas_cercano:
                texto_resultados += "   ★ MÁS CERCANO ★\n"
            
            texto_resultados += "\n"
        
        self.resultados_text.setPlainText(texto_resultados)
    
    def on_progress(self, mensaje):
        """
        Actualiza el mensaje de progreso
        """
        self.status_label.setText(mensaje)
    
    def on_error(self, mensaje):
        """
        Maneja errores
        """
        self.progress_bar.setVisible(False)
        self.btn_cargar_datos.setEnabled(True)
        self.btn_calcular.setEnabled(True)
        self.status_label.setText(f"Error: {mensaje}")
        QMessageBox.critical(self, "Error", mensaje)
    
    def closeEvent(self, event):
        """
        Limpia recursos al cerrar la aplicación
        """
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        event.accept()