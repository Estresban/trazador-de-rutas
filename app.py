import sys
import requests
import math
import json
import subprocess, time
import os
import base64
from PyQt5.QtWidgets import (
    QCompleter, QSplitter, QProgressBar, QGraphicsDropShadowEffect, QDialog, QFormLayout, QDateEdit, QComboBox, QDialogButtonBox, QMessageBox, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget,
    QListWidgetItem, QFrame, QTabWidget, QLineEdit, QInputDialog, QCheckBox, QCompleter, QFileDialog
)

from PyQt5.QtGui import QFont, QPixmap, QIcon, QColor
from PyQt5.QtCore import Qt, QUrl, QTimer, QThread, pyqtSignal, QPropertyAnimation, QRect
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QThread, pyqtSignal
from datetime import datetime
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtGui import QTextDocument
from PyQt5.QtWidgets import QFileDialog, QMessageBox


AUTOCOMPLETE_FILE = "autocompletado.json"

def cargar_autocompletado():
    """Carga la lista de direcciones guardadas para autocompletado"""
    if os.path.exists(AUTOCOMPLETE_FILE):
        with open(AUTOCOMPLETE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def guardar_autocompletado(lista):
    """Guarda la lista de direcciones para autocompletado"""
    with open(AUTOCOMPLETE_FILE, "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=4)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlag(Qt.FramelessWindowHint) 
        self.setWindowTitle("Gestor de Rutas")
        self.setGeometry(200, 100, 1200, 700)
        self.setStyleSheet("background-color: #F3F4F8; border-radius: 10px;") 

        self.ruta_actual_item = None  # Guardará el QListWidgetItem de la ruta abierta

        self.rutas_file = "rutas_guardadas.json"
             
        self.layout = QVBoxLayout(self)
        
        # Variables para arrastrar
        self.dragPos = None

        # Barra superior
        self.top_bar = QWidget()
        self.top_bar.setFixedHeight(40)
        self.top_bar.setStyleSheet("background-color: #2C3E50;")
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(10, 0, 10, 0)

        # Título
        self.title_label = QLabel("Gestor de Rutas")
        self.title_label.setStyleSheet("color: white; font-size: 14pt;")
        top_layout.addWidget(self.title_label)
        top_layout.addStretch()

        # Botón oscuro/claro
        self.btn_toggle_theme = QPushButton("🌙")
        self.btn_toggle_theme.setFixedSize(30, 30)
        self.btn_toggle_theme.setStyleSheet("""
            QPushButton {
                background-color: #34495E;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5D6D7E;
            }
        """)
        self.btn_toggle_theme.setCheckable(True)
        self.btn_toggle_theme.clicked.connect(self.toggle_theme)
        top_layout.addWidget(self.btn_toggle_theme)

        # Botones minimizar, maximizar, cerrar
        self.btn_min = QPushButton("-")
        self.btn_min.setFixedSize(30, 30)
        self.btn_min.setStyleSheet("background-color: #34495E; color: white; border-radius: 5px;")
        self.btn_min.clicked.connect(self.showMinimized)
        top_layout.addWidget(self.btn_min)

        self.btn_max = QPushButton("⬜")
        self.btn_max.setFixedSize(30, 30)
        self.btn_max.setStyleSheet("background-color: #34495E; color: white; border-radius: 5px;")
        self.btn_max.clicked.connect(self.toggle_max_restore)
        top_layout.addWidget(self.btn_max)

        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(30, 30)
        self.btn_close.setStyleSheet("background-color: #E74C3C; color: white; border-radius: 5px;")
        self.btn_close.clicked.connect(self.close)
        top_layout.addWidget(self.btn_close)


        # ───────────────────────────────
        #  SISTEMA DE PESTAÑAS (TABS)
        # ───────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)  # Pestañas arriba
        self.tabs.setFont(QFont("Segoe UI", 11, QFont.Medium))

        # ───────────── Estilo moderno de pestañas ───────────── #
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: #F3F4F8;
                border-radius: 12px;
                padding: 5px;
            }

            QTabBar::tab {
                background: #E0E4FF;
                color: #333;
                padding: 12px 25px;
                font-size: 15px;
                border-radius: 12px;
                margin-right: 5px;
                min-width: 160px;   /* ancho mínimo para mostrar todo el texto */
                max-width: 250px;   /* opcional */
                
            }

            QTabBar::tab:selected {
                background: #5E79FF;
                color: white;
                font-weight: bold;
            }
        
            QTabBar::tab:hover {
                background: #748CFF;
                color: white;
            }

            QTabBar::tab:!selected {
                margin-top: 2px;
            }
        """)


        # ───────────── Crear pestañas ───────────── #
        self.tab_calcular = QWidget()
        self.build_tab_calcular()

        self.tab_guardadas = QWidget()
        self.build_tab_guardadas()

        # Añadir pestañas al QTabWidget
        self.tabs.addTab(self.tab_calcular, QIcon("calc.png"), "CALCULAR RUTAS")
        self.tabs.addTab(self.tab_guardadas, QIcon("saved.png"), "RUTAS GUARDADAS")

        # agregar barra + pestañas al layout principal
        self.layout.addWidget(self.top_bar)
        self.layout.addWidget(self.tabs)

        self.cargar_rutas_desde_archivo()


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.dragPos:
            self.move(self.pos() + event.globalPos() - self.dragPos)
            self.dragPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.dragPos = None

    # Función maximizar/restaurar
    def toggle_max_restore(self):
        if self.isMaximized():
            self.showNormal()
            self.btn_max.setText("⬜")
        else:
            self.showMaximized()
            self.btn_max.setText("❐")


    # ────────────── TAB CALCULAR ────────────── #
    def build_tab_calcular(self):
        layout = QVBoxLayout(self.tab_calcular)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        self.top_bar_container = QWidget()
        self.top_bar_layout = QVBoxLayout(self.top_bar_container)
        self.top_bar_layout.setContentsMargins(0, 0, 0, 0)

        self.build_top_bar()
        self.build_main_content()

        layout.addWidget(self.top_bar_container)

    # ────────────── TAB RUTAS GUARDADAS ────────────── #
    def build_tab_guardadas(self):
        layout = QVBoxLayout(self.tab_guardadas)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("RUTAS GUARDADAS")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))

        self.saved_routes_list = QListWidget()
        self.saved_routes_list.setStyleSheet("""
            QListWidget {
                background: white;
                border-radius: 10px;
                padding: 10px;
                font-size: 16px;
            }
            QListWidget::item {
                padding: 12px;
                margin: 4px;
                border-radius: 8px;
                background: #EEF0F8;
            }
        """)

        layout.addWidget(title)
        layout.addWidget(self.saved_routes_list)
        self.saved_routes_list.itemDoubleClicked.connect(self.cargar_ruta_guardada)
        
        # Aquí se añaden los widgets al layout de la pestaña
        layout.addWidget(title)
        layout.addWidget(self.saved_routes_list)

        # ─── Botón para eliminar ruta seleccionada ───
        self.btn_delete_route = QPushButton("❌ ELIMINAR RUTA SELECCIONADA")
        self.btn_delete_route.setFont(QFont("Segoe UI", 12))
        self.btn_delete_route.clicked.connect(self.eliminar_ruta)
        layout.addWidget(self.btn_delete_route)

    # ────────────── BARRA SUPERIOR ────────────── #
    def build_top_bar(self):
        top_bar = QHBoxLayout()
        top_bar.setSpacing(20)

        # Logo
        logo = QLabel()
        pixmap = QPixmap("logo.png")
        if not pixmap.isNull():
            pixmap = pixmap.scaled(55, 55, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo.setPixmap(pixmap)
        logo.setFixedSize(60, 60)
        top_bar.addWidget(logo)

        top_bar.addStretch()
        self.top_bar_layout.addLayout(top_bar)

    # ────────────── CONTENIDO PRINCIPAL ────────────── #
    def build_main_content(self):
        button_style = """ ... tu estilo ... """
        main_layout = QVBoxLayout()

        # Estilo para los botones
        button_style = """
            QPushButton {
                background-color: #5E79FF;
                color: white;
                border-radius: 10px;
                padding: 8px 12px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #748CFF;
            }
        """
        
        # Contenedor tipo splitter
        splitter = QSplitter(Qt.Horizontal)

        # PANEL IZQUIERDO
        self.left_panel = QFrame()
        self.left_panel.setStyleSheet("background: white; border-radius: 15px;")

        left_layout = QVBoxLayout(self.left_panel)
        title_left = QLabel("RUTA")
        title_left.setFont(QFont("Segoe UI", 18, QFont.Bold))

        # Campo Origen (en una sola línea)
        origen_layout = QHBoxLayout()
        label_origen = QLabel("Origen:")
        label_origen.setFont(QFont("Segoe UI", 14))

        self.input_origen = QLineEdit()
        self.input_origen.setPlaceholderText("Introduce el origen")
        self.input_origen.textChanged.connect(lambda text: self.input_origen.setText(text.upper()))

        origen_layout.addWidget(label_origen)
        origen_layout.addWidget(self.input_origen)
        
        left_layout.addLayout(origen_layout)

       # Layout para paradas intermedias
        self.paradas_layout = QVBoxLayout()
        left_layout.addLayout(self.paradas_layout)

       # Campo Destino (en una sola línea)
        destino_layout = QHBoxLayout()
        label_destino = QLabel("Destino:")
        label_destino.setFont(QFont("Segoe UI", 14))

        self.input_destino = QLineEdit()
        self.input_destino.setPlaceholderText("Introduce el destino")
        self.input_destino.textChanged.connect(lambda text: self.input_destino.setText(text.upper()))

        destino_layout.addWidget(label_destino)
        destino_layout.addWidget(self.input_destino)

        left_layout.addLayout(destino_layout)

        
        # Cargar lista de autocompletado
        self.autocomplete_list = cargar_autocompletado()

        # Asignar completer a origen
        self.completer_origen = QCompleter(self.autocomplete_list)
        self.completer_origen.setCaseSensitivity(Qt.CaseInsensitive)
        self.input_origen.setCompleter(self.completer_origen)

        # Asignar completer a destino
        self.completer_destino = QCompleter(self.autocomplete_list)
        self.completer_destino.setCaseSensitivity(Qt.CaseInsensitive)
        self.input_destino.setCompleter(self.completer_destino)

        self.input_origen.editingFinished.connect(
            lambda: self.actualizar_autocompletado(self.input_origen.text())
        )
        self.input_destino.editingFinished.connect(
            lambda: self.actualizar_autocompletado(self.input_destino.text())
        )

       # CREAR BOTONES

        self.chk_start_nearest = QCheckBox("Empezar por el servicio más cercano")
        self.chk_start_nearest.setFont(QFont("Segoe UI", 12))
        left_layout.addWidget(self.chk_start_nearest)

        self.chk_add_destino = QCheckBox("Añadir destino como último servicio")
        self.chk_add_destino.setFont(QFont("Segoe UI", 12))
        left_layout.addWidget(self.chk_add_destino)
        
        self.btn_add_stop = QPushButton("➕  AÑADIR PARADA")
        self.btn_add_stop.setStyleSheet(button_style)
        self.btn_add_stop.clicked.connect(self.agregar_parada)
        

        self.btn_calculate = QPushButton("⚙️  CALCULAR RUTA")
        self.btn_calculate.setStyleSheet(button_style)
        self.btn_calculate.clicked.connect(self.on_calculate_route)
        

        self.btn_save_route = QPushButton("💾 GUARDAR RUTA")
        self.btn_save_route.setStyleSheet(button_style)
        self.btn_save_route.clicked.connect(self.guardar_ruta)
        

        self.btn_export_ods = QPushButton("📄 CARTA DE PORTES")
        self.btn_export_ods.setStyleSheet(button_style)
        self.btn_export_ods.clicked.connect(self.exportar_ruta)
        
  
        self.btn_new_route = QPushButton("🧭  NUEVA RUTA")
        self.btn_new_route.setStyleSheet(button_style)
        self.btn_new_route.clicked.connect(self.nueva_ruta)  
        

        # Grupo 1 – Añadir parada
        frame_add_stop = QFrame()
        frame_add_stop.setStyleSheet("background-color: #E0E4FF; border-radius: 10px;")
        layout_add_stop = QVBoxLayout(frame_add_stop)
        layout_add_stop.addWidget(self.btn_add_stop)
        left_layout.addWidget(frame_add_stop)

        # Grupo 2 – Ruta: calcular, guardar, nueva
        frame_route = QFrame()
        frame_route.setStyleSheet("background-color: #E0E4FF; border-radius: 10px;")
        layout_route = QVBoxLayout(frame_route)
        layout_route.setSpacing(10)
        layout_route.addWidget(self.btn_calculate)
        layout_route.addWidget(self.btn_save_route)
        layout_route.addWidget(self.btn_new_route)
        left_layout.addWidget(frame_route)


        # Grupo 3 – Exportar / Modo oscuro
        frame_utils = QFrame()
        frame_utils.setStyleSheet("background-color: #E0E4FF; border-radius: 10px;")
        layout_utils = QVBoxLayout(frame_utils)
        layout_utils.setSpacing(10)
        layout_utils.addWidget(self.btn_export_ods)
        left_layout.addWidget(frame_utils)
    

        # PANEL CENTRAL
        self.center_panel = QFrame()
        self.center_panel.setStyleSheet("background: white; border-radius: 15px;")
        self.center_layout = QVBoxLayout(self.center_panel)

        # Añadir paneles al splitter
        splitter.addWidget(self.left_panel)
        splitter.addWidget(self.center_panel)

        # Tamaño inicial de los paneles (opcional)
        splitter.setSizes([350, 800])

        # Agregar splitter al layout
        main_layout.addWidget(splitter)
        
        # Texto informativo
        self.center_msg = QLabel("Aquí se mostrará la ruta calculada")
        self.center_msg.setAlignment(Qt.AlignCenter)
        self.center_msg.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.center_msg.setWordWrap(True)
        self.center_layout.addWidget(self.center_msg)

        # Barra de progreso (moderna con degradado)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0) 
        self.progress_bar.setFixedHeight(25)
        self.progress_bar.setTextVisible(False)  # opcional: ocultar texto
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #5E79FF;
                border-radius: 12px;
                background-color: #E0E4FF;
                height: 25px;
            }
            QProgressBar::chunk {
                border-radius: 12px;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5E79FF, stop:0.5 #748CFF, stop:1 #5E79FF
                );
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)       # suavidad de la sombra
        shadow.setXOffset(0)           # desplazamiento horizontal
        shadow.setYOffset(2)           # desplazamiento vertical
        shadow.setColor(QColor("#00000030"))  # color negro semi-transparente
        self.progress_bar.setGraphicsEffect(shadow)

        # Timer para animación fluida
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.animar_progress_bar)
        self.progress_timer.start(20)  # actualiza cada 20 ms
        self.progress_value = 0  # variable de animación
        
        self.progress_bar.hide()  # <-- ocultamos al inicio
        self.center_layout.addWidget(self.progress_bar)

        self.top_bar_layout.addLayout(main_layout)

    def animar_progress_bar(self):
        if not self.progress_bar.isVisible():
            return  # no animar si está oculta
    
        self.progress_value += 2  # velocidad de animación
        if self.progress_value > 100:
            self.progress_value = 0

        self.progress_bar.setValue(self.progress_value)


    def actualizar_autocompletado(self, texto):
        texto = texto.upper().strip()
        if texto and texto not in self.autocomplete_list:
            self.autocomplete_list.append(texto)
            guardar_autocompletado(self.autocomplete_list)
            # Actualizar completers
            self.completer_origen.model().setStringList(self.autocomplete_list)
            self.completer_destino.model().setStringList(self.autocomplete_list)
  
    def geocode_direccion(self, direccion):
        """Devuelve (lat, lon) de una dirección usando Nominatim"""
        import requests
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": direccion, "format": "json"}
        headers = {"User-Agent": "MiAppRutas/1.0 (tu_email@dominio.com)"}  # Cambia por tu email
        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
            else:
                print(f"No se encontró la ubicación: {direccion}")
                return None
        except Exception as e:
            print(f"Error geocodificando: {direccion}", e)
            return None


        # Función para calcular la ruta óptima con OSRM
    def calcular_ruta_osrm(self, origen_coords, destino_coords, paradas_coords):
        import requests
    
        puntos = [origen_coords] + paradas_coords + [destino_coords]
        coords = ";".join(f"{lon},{lat}" for lat, lon in puntos)

        url = (
            f"http://router.project-osrm.org/trip/v1/driving/{coords}"
            "?source=first&destination=last&roundtrip=false&overview=false"
        )

        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()

            if "trips" not in data or not data["trips"]:
                return None, None, None

            trip = data["trips"][0]
            distancia_km = trip["distance"] / 1000
            tiempo_min = trip["duration"] / 60
            
            # Obtener orden real de los puntos desde trip["waypoints"]
            orden_waypoints = [wp["waypoint_index"] for wp in data["waypoints"]]
            indices = [idx - 1 for idx in orden_waypoints if 0 < idx < len(puntos) - 1]

            return distancia_km, tiempo_min, indices

        except Exception as e:
            print("Error OSRM:", e)
            return None, None, None

    def on_calculate_route(self, desde_guardada=False):
        from PyQt5.QtWidgets import QMessageBox
    
        # Recoger origen, destino y paradas
        origen = self.input_origen.text().strip()
        destino = self.input_destino.text().strip()
        paradas = self.obtener_paradas()

        if not origen or not destino:
            QMessageBox.warning(self, "Error", "Debes introducir origen y destino")
            return

        # Mostrar barra de progreso con texto según contexto
        if desde_guardada:
            self.mostrar_cargando("CARGANDO RUTA")
        else:
            self.mostrar_cargando("CALCULANDO RUTA...")

        # Crear Worker
        self.worker = RutaWorker(origen, destino, paradas, self.chk_start_nearest.isChecked(), self)
        self.worker.resultado.connect(self.ruta_calculada)
        self.worker.error.connect(lambda msg: QMessageBox.warning(self, "Error", msg))
        self.worker.start()

    def ruta_calculada(self, texto_ruta):
        # Ocultar barra de progreso
        self.ocultar_cargando()

        # Mostrar ruta en el panel central
        self.center_msg.setText(texto_ruta)

        # Preguntar si abrir en Google Maps
        from PyQt5.QtWidgets import QMessageBox
        import webbrowser

        reply = QMessageBox.question(
            self,
            "Abrir Google Maps",
            "¿Quieres abrir la ruta en Google Maps?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            lineas = texto_ruta.split("\n")
            origen = lineas[0].replace("Origen:", "").strip()
            destino = lineas[-1].split(",")[0].replace("Destino:", "").strip()
            paradas = [l.split(":")[1].strip() for l in lineas[1:-1] if l.startswith("Parada")]

            url = f"https://www.google.com/maps/dir/{origen}/"
            if paradas:
                url += "/".join(paradas) + "/"
            url += destino
            webbrowser.open(url)


    def show_google_maps(self):
        # Limpiar panel central
        layout = self.center_panel.layout()
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Crear QWebEngineView
        self.map_view = QWebEngineView()
        self.map_view.setUrl(QUrl("https://www.google.com/maps"))

        layout.addWidget(self.map_view)

    def agregar_parada(self):
        # Layout horizontal para la parada y su botón
        fila_widget = QWidget()
        parada_layout = QHBoxLayout(fila_widget)

        # Cuadro de texto para la parada
        parada_input = QLineEdit()
        parada_input.setPlaceholderText("Parada intermedia")
        parada_input.setMinimumWidth(180)  # ancho opcional
        parada_layout.addWidget(parada_input)
        parada_input.textChanged.connect(lambda text: parada_input.setText(text.upper()))

        # Completer con desplegable
        completer_parada = QCompleter(self.autocomplete_list)
        completer_parada.setCaseSensitivity(Qt.CaseInsensitive)
        completer_parada.setCompletionMode(QCompleter.PopupCompletion)  # hace que aparezca como desplegable
        parada_input.setCompleter(completer_parada)

        # Guardar el texto en la lista de autocompletado al terminar de editar
        parada_input.editingFinished.connect(
        lambda: self.actualizar_autocompletado(parada_input.text())
    )

        # Botón de eliminar
        btn_eliminar = QPushButton("❌")
        btn_eliminar.setFixedSize(30, 30)
        btn_eliminar.setStyleSheet("""
            QPushButton {
                background-color: #FF5E5E;
                color: white;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #FF8282;
            }
        """)
        parada_layout.addWidget(btn_eliminar)

      
        # Función anidada para eliminar esta parada
        def eliminar():
            anim = QPropertyAnimation(fila_widget, b"geometry")
            rect = fila_widget.geometry()  # posición actual
            end_rect = QRect(rect.x(), rect.y() - 20, rect.width(), rect.height())  # sube 20px
            anim.setStartValue(rect)
            anim.setEndValue(end_rect)
            anim.setDuration(200)  # duración ms
            anim.finished.connect(lambda: fila_widget.setParent(None))  # eliminar widget al terminar anim
            anim.start()

        btn_eliminar.clicked.connect(eliminar)

        # Añadir el layout al layout principal de paradas
        self.paradas_layout.addWidget(fila_widget)


        # Animación de aparición de la fila completa
        def animar_aparicion():
            anim = QPropertyAnimation(fila_widget, b"geometry")
            rect = fila_widget.geometry()  # posición final
            start_rect = QRect(rect.x(), rect.y() - 20, rect.width(), rect.height())
            anim.setStartValue(start_rect)
            anim.setEndValue(rect)
            anim.setDuration(200)
            anim.start()

        QTimer.singleShot(0, animar_aparicion)

    def obtener_paradas(self):
        """
        Devuelve una lista de los textos de las paradas intermedias.
        """
        paradas = []
        for i in range(self.paradas_layout.count()):
            layout = self.paradas_layout.itemAt(i)
            if layout is not None:
                widget = layout.itemAt(0).widget()  # primer widget = QLineEdit
                if isinstance(widget, QLineEdit) and widget.text().strip() != "":
                    paradas.append(widget.text().strip())
        return paradas


    def distancia_euclidiana(self, coord1, coord2):
        """Devuelve una distancia aproximada entre dos coordenadas (lat, lon)"""
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        return math.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)

    def guardar_ruta(self):
        from PyQt5.QtWidgets import QInputDialog, QMessageBox

        texto_ruta = self.center_msg.text().strip()
        if not texto_ruta or "Aquí se mostrará la ruta calculada" in texto_ruta:
            QMessageBox.warning(self, "Error", "Primero calcula la ruta antes de guardarla")
            return

        if self.ruta_actual_item:  # Ruta existente: sobrescribir
            self.ruta_actual_item.setData(Qt.UserRole, texto_ruta)
            self.guardar_rutas_en_archivo()
            QMessageBox.information(self, "Ruta actualizada", "La ruta se ha actualizado correctamente")
        else:  # Ruta nueva: pedir nombre

            nombre_ruta, ok = QInputDialog.getText(self, "Guardar Ruta", "Nombre de la ruta:")
            if ok and nombre_ruta.strip():
                item = QListWidgetItem()
                item.setText(nombre_ruta.strip())           # lo que verá el usuario en la lista
                item.setData(Qt.UserRole, texto_ruta)       # guardamos el contenido real en UserRole
                self.saved_routes_list.addItem(item)
                self.guardar_rutas_en_archivo()
                QMessageBox.information(self, "Ruta guardada", "La ruta se ha guardado correctamente")
            else:
                QMessageBox.information(self, "Cancelado", "No se guardó la ruta")


        # ─── Función para guardar ruta en archivo ───
    def guardar_rutas_en_archivo(self):
        import json

        rutas = []
        for i in range(self.saved_routes_list.count()):
            item = self.saved_routes_list.item(i)
            rutas.append({
                "nombre": item.text(),
                "texto": item.data(Qt.UserRole)
            })

        with open(self.rutas_file, "w", encoding="utf-8") as f:
            json.dump(rutas, f, ensure_ascii=False, indent=4)


    # ─── Función para eliminar ruta seleccionada ───
    def eliminar_ruta(self):
        from PyQt5.QtWidgets import QMessageBox

        item_seleccionado = self.saved_routes_list.currentItem()
        if item_seleccionado is None:
            QMessageBox.warning(self, "Error", "Selecciona primero una ruta para eliminar")
            return

        # Confirmación antes de eliminar
        reply = QMessageBox.question(
            self,
            "Confirmar eliminación",
            "¿Deseas eliminar la ruta seleccionada?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.saved_routes_list.takeItem(self.saved_routes_list.row(item_seleccionado))
            self.guardar_rutas_en_archivo()
            
    def nueva_ruta(self):
        self.ruta_actual_item = None  # <-- es ruta nueva
        
        # Limpiar campos de texto
        self.input_origen.clear()
        self.input_destino.clear()
    
        # Limpiar paradas intermedias
        for i in reversed(range(self.paradas_layout.count())):
            layout = self.paradas_layout.itemAt(i)
            if layout:
                for j in reversed(range(layout.count())):
                    widget = layout.itemAt(j).widget()
                    if widget:
                        widget.setParent(None)
                self.paradas_layout.removeItem(layout)
    
        # Limpiar panel central de resultados
        self.center_msg.setText("Aquí se mostrará la ruta calculada")
    
        # Resetear checkbox de "empezar por el más cercano"
        self.chk_start_nearest.setChecked(False)

    from PyQt5.QtCore import QTimer

    def cargar_ruta_guardada(self, item):
        self.ruta_actual_item = item  # <-- registrar la ruta abierta
        
        # Recupera el texto real de la ruta
        texto_ruta = item.data(Qt.UserRole) or item.text()

        # Cambiar a la pestaña CALCULAR RUTAS
        self.tabs.setCurrentWidget(self.tab_calcular)

        # Limpiar campos de texto, pero NO resetees self.ruta_actual_item
        self.input_origen.clear()
        self.input_destino.clear()

        # Limpiar paradas intermedias
        for i in reversed(range(self.paradas_layout.count())):
            layout = self.paradas_layout.itemAt(i)
            if layout:
                for j in reversed(range(layout.count())):
                    widget = layout.itemAt(j).widget()
                    if widget:
                        widget.setParent(None)
                self.paradas_layout.removeItem(layout)

        lineas = texto_ruta.split("\n")

        if lineas and lineas[0].startswith("Origen:"):
            self.input_origen.setText(lineas[0].replace("Origen:", "").strip())

        # Paradas EXACTAS como estaban guardadas
        for linea in lineas[1:-2]:
            if linea.startswith("Parada"):
                parada = linea.split(":", 1)[1].strip()
                self.agregar_parada()
                layout = self.paradas_layout.itemAt(self.paradas_layout.count() - 1)
                if layout is not None:
                    widget = layout.itemAt(0).widget()
                    if widget:
                        widget.setText(parada)

        if len(lineas) >= 2 and lineas[-2].startswith("Destino:"):
            self.input_destino.setText(lineas[-2].replace("Destino:", "").strip())

        # Mostrar la ruta tal cual en el panel central
        self.center_msg.setText(texto_ruta)
        self.center_msg.setAlignment(Qt.AlignLeft)
        self.progress_bar.hide()  # ocultar barra de carga
        
    def cargar_rutas_desde_archivo(self):
        import json, os

        if not os.path.exists(self.rutas_file):
            return

        try:
            with open(self.rutas_file, "r", encoding="utf-8") as f:
               rutas = json.load(f)

            self.saved_routes_list.clear()
            for ruta in rutas:
                item = QListWidgetItem(ruta["nombre"])
                item.setData(Qt.UserRole, ruta["texto"])
                self.saved_routes_list.addItem(item)

        except Exception as e:
            print("Error al cargar rutas:", e)

    def toggle_theme(self):
        if self.btn_toggle_theme.isChecked():
            # Modo oscuro
            color_fondo_panel = "#3C3C3C"
            color_texto_panel = "#F0F0F0"
            color_fondo_ventana = "#2E2E2E"
            color_boton = "#5E79FF"
            color_boton_hover = "#748CFF"

            self.setStyleSheet(f"background-color: {color_fondo_ventana}; color: {color_texto_panel};")
        
            # Paneles
            self.left_panel.setStyleSheet(f"background-color: {color_fondo_panel}; border-radius: 15px; color: {color_texto_panel};")
            self.center_panel.setStyleSheet(f"background-color: {color_fondo_panel}; border-radius: 15px; color: {color_texto_panel};")

            # Lista de rutas
            self.saved_routes_list.setStyleSheet(f"""
                QListWidget {{
                    background-color: {color_fondo_panel};
                    color: {color_texto_panel};
                    border-radius: 10px;
                    padding: 10px;
                    font-size: 16px;
                }}
            """)

            # Botones
            for btn in [self.btn_add_stop, self.btn_calculate, self.btn_save_route, self.btn_new_route, self.btn_toggle_theme, self.btn_delete_route]:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {color_boton};
                        color: white;
                        border-radius: 10px;
                        padding: 8px 15px;
                    }}
                    QPushButton:hover {{
                        background-color: {color_boton_hover};
                    }}
                """)
        
            # Pestañas
            self.tabs.setStyleSheet(f"""
                QTabWidget::pane {{
                    background: {color_fondo_panel};
                    border-radius: 12px;
                    padding: 5px;
                }}
                QTabBar::tab {{
                    background: #555555;
                    color: {color_texto_panel};
                    padding: 12px 25px;
                    border-radius: 12px;
                    margin-right: 5px;
                }}
                QTabBar::tab:selected {{
                    background: {color_boton};
                    color: white;
                    font-weight: bold;
                }}
                QTabBar::tab:hover {{
                    background: {color_boton_hover};
                    color: white;
                }}
            """)

            self.btn_toggle_theme.setText("☀️")

        else:
            # Modo claro: mismo procedimiento, colores claros
            color_fondo_panel = "white"
            color_texto_panel = "#000"
            color_fondo_ventana = "#F3F4F8"
            color_boton = "#5E79FF"
            color_boton_hover = "#748CFF"

            self.setStyleSheet(f"background-color: {color_fondo_ventana}; color: {color_texto_panel};")
            self.left_panel.setStyleSheet(f"background-color: {color_fondo_panel}; border-radius: 15px; color: {color_texto_panel};")
            self.center_panel.setStyleSheet(f"background-color: {color_fondo_panel}; border-radius: 15px; color: {color_texto_panel};")
            self.saved_routes_list.setStyleSheet(f"""
                QListWidget {{
                    background-color: {color_fondo_panel};
                    color: {color_texto_panel};
                    border-radius: 10px;
                    padding: 10px;
                    font-size: 16px;
                }}
            """)

            for btn in [self.btn_add_stop, self.btn_calculate, self.btn_save_route, self.btn_new_route, self.btn_toggle_theme, self.btn_delete_route]:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {color_boton};
                        color: white;
                        border-radius: 10px;
                        padding: 8px 15px;
                    }}
                    QPushButton:hover {{
                        background-color: {color_boton_hover};
                    }}
                """)

            self.tabs.setStyleSheet(f"""
                QTabWidget::pane {{
                    background: {color_fondo_panel};
                    border-radius: 12px;
                    padding: 5px;
                }}
                QTabBar::tab {{
                    background: #E0E4FF;
                    color: #333;
                    padding: 12px 25px;
                    border-radius: 12px;
                    margin-right: 5px;
                }}
                QTabBar::tab:selected {{
                    background: {color_boton};
                    color: white;
                    font-weight: bold;
                }}
                QTabBar::tab:hover {{
                    background: {color_boton_hover};
                    color: white;
                }}
            """)

            self.btn_toggle_theme.setText("🌙")

    def mostrar_cargando(self, texto):
        """Muestra la barra de progreso con un texto"""
        self.center_msg.setText(texto)
        self.center_msg.setAlignment(Qt.AlignCenter)
        self.progress_bar.show()

    def ocultar_cargando(self):
        """Oculta la barra de progreso"""
        self.progress_bar.hide()


    def exportar_ruta(self):
        texto_ruta = self.center_msg.text().strip()
        if not texto_ruta or "Aquí se mostrará" in texto_ruta:
            QMessageBox.warning(self, "Error", "No hay ninguna ruta calculada")
            return

        # Abrir diálogo de datos adicionales
        dialog = CartaDePortesDialog(self)
        if dialog.exec_() != QDialog.Accepted:
            return  # si cancelan, no hacemos nada

        datos = dialog.get_data()
        fecha = datos["fecha"]
        cisterna = datos["cisterna"]

        # Elegir archivo destino
        salida, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar carta de portes",
            f"CARTA_DE_PORTES_{fecha}.pdf",
            "PDF Files (*.pdf)"
        )
        if not salida:
            return

        salida = os.path.normpath(salida)

        # Crear HTML con estilo y logo
        with open("logo.png", "rb") as f:
            logo_base64 = base64.b64encode(f.read()).decode("utf-8")
        html = f"""
       <html>
           <head>
           <style>
            body {{
                font-family: 'Segoe UI', sans-serif;
                font-size: 12pt;
                color: #333333;
                margin: 0;
                padding: 0;
            }}
            .header {{
                display: flex;
                align-items: flex-start;   /* alinea arriba */
                margin-bottom: 20px;
            }}
            .logo {{
                width: 160px;
            }}
            h2 {{
                color: #5E79FF;
                margin: 0;
                padding-top: 5px;
                text-align: left;
            }}
            .header-table {{
                width: 100%;
                margin-bottom: 20px;
            }}

            th, td {{
                border: 1px solid #999999;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #5E79FF;
                color: white;
            }}
            .section-title {{
                font-weight: bold;
                margin-top: 15px;
                color: #5E79FF;
            }}
        </style>
        </head>
        <body>
            <table class="header-table">
                <tr>
                    <td style="width: 160px;">
                        <img src="data:image/png;base64,{logo_base64}" class="logo">
                    </td>
                    <td>
                        <h2>CARTA DE PORTES</h2>
                    </td>
                </tr>
            </table>

        """
        for linea in texto_ruta.split("\n"):
            html += f"<tr><td>{linea}</td></tr>"

        html += "</table></body></html>"


        doc = QTextDocument()
        doc.setHtml(html)

        # Configurar impresora PDF
        printer = QPrinter()
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(salida)
        printer.setPageMargins(15, 15, 15, 15, QPrinter.Millimeter)

        # Imprimir
        doc.print_(printer)

        QMessageBox.information(
            self,
            "Carta de portes generada",
            f"PDF generado correctamente:\n{salida}"
        )


class RutaWorker(QThread):
    resultado = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, origen, destino, paradas, chk_start_nearest, main):
        super().__init__()
        self.origen = origen
        self.destino = destino
        self.paradas = paradas
        self.chk_start_nearest = chk_start_nearest
        self.main = main

    def run(self):
        try:
            # Geocodificación
            origen_coords = self.main.geocode_direccion(self.origen)
            destino_coords = self.main.geocode_direccion(self.destino)
            
            if not origen_coords or not destino_coords:
                self.error.emit("No se pudo geocodificar origen o destino")
                return

            paradas_coords = []
            for p in self.paradas:
                coords = self.main.geocode_direccion(p)
                if not coords:
                    self.error.emit(f"No se pudo geocodificar: {p}")
                    return
                paradas_coords.append(coords)

            # Parada más cercana
            parada_fija = None
            nombre_parada_fija = None
            
            if self.chk_start_nearest and paradas_coords:
                distancias = [self.main.distancia_euclidiana(origen_coords, pc) for pc in paradas_coords]
                idx_mas_cercana = distancias.index(min(distancias))
                parada_fija = paradas_coords[idx_mas_cercana]
                nombre_parada_fija = self.paradas[idx_mas_cercana]

                paradas_coords_restantes = paradas_coords[:idx_mas_cercana] + paradas_coords[idx_mas_cercana + 1:]
                paradas_restantes = self.paradas[:idx_mas_cercana] + self.paradas[idx_mas_cercana + 1:]
            else:
                paradas_coords_restantes = paradas_coords
                paradas_restantes = self.paradas

            # Calcular ruta OSRM
            distancia_km, tiempo_min, indices = self.main.calcular_ruta_osrm(
                origen_coords, destino_coords, paradas_coords_restantes
            )
            if distancia_km is None:
                self.error.emit("No se pudo calcular la ruta")
                return

            if indices:
                paradas_ordenadas = [paradas_restantes[i] for i in indices]
            else:
                paradas_ordenadas = paradas_restantes

            if parada_fija:
                paradas_optimas = [nombre_parada_fija] + paradas_ordenadas
            else:
                paradas_optimas = paradas_ordenadas

            ruta_texto = f"Origen: {self.origen}\n"
            for idx, p in enumerate(paradas_optimas, 1):
                ruta_texto += f"Parada {idx}: {p}\n"
            ruta_texto += (
                f"Destino: {self.destino}\n"
                f"Distancia total: {distancia_km:.2f} km, Tiempo estimado: {tiempo_min:.0f} min"
            )
            self.resultado.emit(ruta_texto)

        except Exception as e:
            self.error.emit(str(e))
            
class CartaDePortesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Datos adicionales para la Carta de Portes")
        self.setFixedSize(350, 200)

        layout = QFormLayout(self)

        # Fecha de recogida
        self.fecha_edit = QDateEdit()
        self.fecha_edit.setCalendarPopup(True)
        self.fecha_edit.setDate(datetime.now().date())
        layout.addRow("Fecha de recogida:", self.fecha_edit)

        # Cisterna
        self.cisterna_combo = QComboBox()
        self.cisterna_combo.addItems(["1", "2", "3"])
        layout.addRow("Cisterna:", self.cisterna_combo)

        # Botones Aceptar/Cancelar
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addRow(self.buttons)

    def get_data(self):
        """Devuelve un diccionario con los datos introducidos"""
        return {
            "fecha": self.fecha_edit.date().toString("yyyy-MM-dd"),
            "cisterna": self.cisterna_combo.currentText()
        }  

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
