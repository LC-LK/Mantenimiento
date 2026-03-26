import sys
import winreg
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt

class ThemeManager:
    def __init__(self, parent=None):
        self.parent = parent
        self.app = QApplication.instance()

    def get_system_theme(self):
        """Detecta si Windows está en modo oscuro o claro."""
        try:
            registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return "Light" if value == 1 else "Dark"
        except Exception:
            return "Light"  # Fallback a claro si falla

    def apply_theme(self, mode="Auto"):
        """Aplica el tema seleccionado: 'Auto', 'Dark', o 'Light'"""
        target_theme = mode
        
        if mode == "Auto":
            target_theme = self.get_system_theme()
            print(f"Tema detectado del sistema: {target_theme}")

        if target_theme == "Dark":
            self.apply_dark_theme()
        else:
            self.apply_light_theme()

    def apply_dark_theme(self):
        self.app.setStyle("Fusion")
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        self.app.setPalette(palette)
        
        # Stylesheet adicional para controles específicos
        self.app.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #353535;
                color: white;
            }
            QTabWidget::pane {
                border: 1px solid #6c6c6c;
                background-color: #353535;
            }
            QTabBar::tab {
                background-color: #353535;
                color: white;
                border: 1px solid #6c6c6c;
                padding: 5px;
            }
            QTabBar::tab:selected {
                background-color: #505050;
            }
            QToolTip { 
                color: #ffffff; 
                background-color: #2a82da; 
                border: 1px solid white; 
            }
            QHeaderView::section {
                background-color: #353535;
                color: white;
                border: 1px solid #6c6c6c;
            }
            QTableWidget {
                gridline-color: #6c6c6c;
                background-color: #252525;
                color: white;
            }
            QTableWidget::item {
                color: white;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #191919;
                color: white;
                border: 1px solid #6c6c6c;
                padding: 4px;
            }
            QComboBox::item:selected {
                background-color: #2a82da;
            }
            QComboBox QAbstractItemView {
                background-color: #191919;
                color: white;
                selection-background-color: #2a82da;
            }
            QMenuBar {
                background-color: #353535;
                color: white;
            }
            QMenuBar::item {
                background-color: transparent;
                color: white;
            }
            QMenuBar::item:selected {
                background-color: #505050;
            }
            QMenu {
                background-color: #353535;
                color: white;
                border: 1px solid #6c6c6c;
            }
            QMenu::item {
                background-color: transparent;
                color: white;
            }
            QMenu::item:selected {
                background-color: #2a82da;
            }
            QPushButton {
                background-color: #353535;
                color: white;
                border: 1px solid #6c6c6c;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #454545;
            }
            QPushButton:pressed {
                background-color: #252525;
            }
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #808080;
            }
            QLabel {
                color: white;
            }
        """)

    def apply_light_theme(self):
        self.app.setStyle("Fusion")
        # Resetear paleta a la default del sistema (Fusion standard)
        self.app.setPalette(self.app.style().standardPalette())
        
        # Stylesheet ligera para unificar tamaños y espaciados, pero colores standard
        self.app.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #f0f0f0;
                color: black;
            }
            QTabWidget::pane {
                border: 1px solid #d0d0d0;
                background-color: #f0f0f0;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                color: black;
                border: 1px solid #c0c0c0;
                padding: 5px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                color: black;
                border: 1px solid #d0d0d0;
            }
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: white;
                color: black;
            }
            QTableWidget::item {
                color: black;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: white;
                color: black;
                border: 1px solid #c0c0c0;
                padding: 4px;
                selection-background-color: #2a82da;
                selection-color: white;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
                selection-background-color: #2a82da;
                selection-color: white;
            }
            QMenuBar {
                background-color: #f0f0f0;
                color: black;
            }
            QMenuBar::item {
                background-color: transparent;
                color: black;
            }
            QMenuBar::item:selected {
                background-color: #e0e0e0;
            }
            QMenu {
                background-color: #f0f0f0;
                color: black;
                border: 1px solid #c0c0c0;
            }
            QMenu::item {
                background-color: transparent;
                color: black;
            }
            QMenu::item:selected {
                background-color: #2a82da;
                color: white;
            }
            QPushButton {
                background-color: #f0f0f0;
                color: black;
                border: 1px solid #c0c0c0;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
            QPushButton:disabled {
                background-color: #f5f5f5;
                color: #a0a0a0;
            }
            QLabel {
                color: black;
            }
        """)