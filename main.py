import sys
import logging
import ctypes
import os

# Importar DatabaseManager primero para inicializar mysql.connector antes que PyQt
# Esto evita conflictos de DLLs SSL/OpenSSL
try:
    from database import DatabaseManager
except Exception as e:
    print(f"Failed to import DatabaseManager: {e}")

try:
    from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QMenu, QHBoxLayout, QTabWidget
except Exception as e:
    print(f"Failed to import PyQt6: {e}")

from PyQt6.QtGui import QAction, QPixmap, QIcon
from PyQt6.QtCore import Qt
from ui.equipos_tab import EquiposTab
from ui.mantenimientos_tab import MantenimientosTab
from ui.theme_manager import ThemeManager

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Planta Villa Bicentenario Mantención 2026")
        self.resize(1000, 700)
        
        self.db = DatabaseManager()
        self.theme_manager = ThemeManager(self) # Instanciar ThemeManager
        
        # Establecer ícono de la aplicación y ventana
        try:
            # Intentar usar logo.ico primero (mejor para Windows), fallback a logo.png
            icon_path_ico = self.db.get_resource_path("logo.ico")
            icon_path_png = self.db.get_resource_path("logo.png")
            
            if os.path.exists(icon_path_ico):
                app_icon = QIcon(icon_path_ico)
            else:
                app_icon = QIcon(icon_path_png)
                
            self.setWindowIcon(app_icon)
            # Asegurar que la instancia de QApplication también tenga el ícono (para barra de tareas)
            QApplication.instance().setWindowIcon(app_icon)
        except Exception as e:
            logger.warning(f"No se pudo establecer el ícono: {e}")

        self.init_ui()
        self.create_menu() # Crear menú para temas
        
        # Aplicar tema inicial (Auto por defecto)
        self.theme_manager.apply_theme("Auto")
        
    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout(main_widget)
        
        self.tabs = QTabWidget()

        # Agregar logo en la esquina superior derecha
        try:
            logo_path = self.db.get_resource_path("logo.png")
            logo_label = QLabel()
            # Escalar imagen para que ajuste en la barra de pestañas (aprox 30px)
            pixmap = QPixmap(logo_path).scaledToHeight(30, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(pixmap)
            logo_label.setContentsMargins(0, 0, 10, 0) # Margen derecho
            self.tabs.setCornerWidget(logo_label, Qt.Corner.TopRightCorner)
        except Exception as e:
            logger.warning(f"No se pudo cargar el logo: {e}")
        
        # Instanciar Tabs
        self.tab_equipos = EquiposTab(self.db)
        self.tab_mantenimientos = MantenimientosTab(self.db)
        
        # Conectar señales
        self.tab_equipos.equipos_updated.connect(self.tab_mantenimientos.update_equipos_data)
        self.tab_equipos.equipo_deleted.connect(self.tab_mantenimientos.load_mantenimientos)
        
        self.tabs.addTab(self.tab_equipos, "Inventario de Equipos")
        self.tabs.addTab(self.tab_mantenimientos, "Registro de Mantenimientos")
        
        layout.addWidget(self.tabs)
        
        # Footer
        footer_layout = QHBoxLayout()
        self.lbl_status = QLabel("Hecho por Lucas Caro")
        self.lbl_status.setStyleSheet("color: gray; font-size: 10px;")
        
        self.lbl_db_status = QLabel("Base de Datos: ...")
        self.lbl_db_status.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        footer_layout.addWidget(self.lbl_status)
        footer_layout.addStretch()
        footer_layout.addWidget(self.lbl_db_status)
        
        layout.addLayout(footer_layout)
        
        # Verificar conexión
        try:
            if self.db.get_connection():
                self.lbl_db_status.setText("Base de Datos: Conectado")
                self.lbl_db_status.setStyleSheet("color: green; font-weight: bold;")
                logger.info("UI: DB connection verified successfully")
            else:
                self.lbl_db_status.setText("Base de Datos: Desconectado")
                self.lbl_db_status.setStyleSheet("color: red; font-weight: bold;")
                logger.warning("UI: DB connection returned false/none")
        except Exception as e:
            logger.error(f"Error checking DB connection in UI: {e}")
            self.lbl_db_status.setText("Base de Datos: Error")
            self.lbl_db_status.setStyleSheet("color: red; font-weight: bold;")
        
    def create_menu(self):
        menubar = self.menuBar()
        view_menu = menubar.addMenu("Ver")
        
        theme_menu = view_menu.addMenu("Tema")
        
        action_auto = QAction("Automático (Sistema)", self)
        action_auto.triggered.connect(lambda: self.change_theme("Auto"))
        theme_menu.addAction(action_auto)
        
        action_dark = QAction("Oscuro", self)
        action_dark.triggered.connect(lambda: self.change_theme("Dark"))
        theme_menu.addAction(action_dark)
        
        action_light = QAction("Claro", self)
        action_light.triggered.connect(lambda: self.change_theme("Light"))
        theme_menu.addAction(action_light)

    def change_theme(self, mode):
        self.theme_manager.apply_theme(mode)

if __name__ == "__main__":
    try:
        # Configurar AppUserModelID para que el icono se muestre correctamente en la barra de tareas de Windows
        myappid = 'mycompany.myproduct.subproduct.version' # ID arbitrario pero único
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"CRITICAL ERROR: {e}")
        input("Press Enter to exit...")
