from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTabWidget, QLabel)
from PyQt6.QtGui import QIcon
from database import DatabaseManager
from .equipos_tab import EquiposTab
from .mantenimientos_tab import MantenimientosTab
import sys
import os

def resource_path(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    # Navigate up one level if we are in ui/ folder and resource is in root
    # But usually _MEIPASS handles the root.
    # If running from source:
    if not hasattr(sys, "_MEIPASS"):
        # We are in ui/ folder? No, __file__ is ui/main_window.py
        # We want root.
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    return os.path.join(base_path, relative_path)

class MainWindow(QMainWindow):
    def __init__(self, db_manager=None):
        super().__init__()
        self.setWindowTitle("Planta Villa Bicentenario Mantención 2026")
        self.setMinimumSize(1100, 750)
        
        # Database
        self.db = db_manager
        self.db_status = bool(self.db)
        
        self.init_ui()
        self.create_menu()

    def create_menu(self):
        menubar = self.menuBar()
        view_menu = menubar.addMenu("Ver")
        
        theme_menu = view_menu.addMenu("Tema")
        
        action_auto = theme_menu.addAction("Automático (Sistema)")
        action_auto.triggered.connect(lambda: self.change_theme(None))
        
        action_dark = theme_menu.addAction("Modo Oscuro")
        action_dark.triggered.connect(lambda: self.change_theme("dark"))
        
        action_light = theme_menu.addAction("Modo Claro")
        action_light.triggered.connect(lambda: self.change_theme("light"))

    def change_theme(self, theme_name):
        from PyQt6.QtWidgets import QApplication
        from .theme_manager import ThemeManager
        app = QApplication.instance()
        ThemeManager.apply_theme(app, theme_name)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Tabs
        self.tabs = QTabWidget()
        self.tab_equipos = EquiposTab(self.db)
        self.tab_mant = MantenimientosTab(self.db)
        
        # Connect signals
        self.tab_equipos.equipos_updated.connect(self.tab_mant.update_equipos_data)
        
        self.tabs.addTab(self.tab_equipos, "Inventario de Motores/Equipos")
        self.tabs.addTab(self.tab_mant, "Registro de Mantenimientos")
        
        main_layout.addWidget(self.tabs)

        # Footer Status
        footer_layout = QHBoxLayout()
        self.lbl_status = QLabel("Estado: " + ("Conectado" if self.db_status else "Sin conexión"))
        self.lbl_status.setStyleSheet(f"color: {'green' if self.db_status else 'red'}; font-weight: bold;")
        footer_layout.addWidget(self.lbl_status)
        footer_layout.addStretch()
        lbl_credits = QLabel("Hecho por Lucas Caro")
        lbl_credits.setStyleSheet("color: #7f8c8d; font-style: italic;")
        footer_layout.addWidget(lbl_credits)
        main_layout.addLayout(footer_layout)
