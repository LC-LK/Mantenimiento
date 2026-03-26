from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel, 
                             QLineEdit, QTextEdit, QPushButton, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QAbstractItemView, 
                             QCheckBox, QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QDoubleValidator
from datetime import datetime
# import openpyxl
from .workers import LoadEquiposWorker

class EquiposTab(QWidget):
    equipos_updated = pyqtSignal(list)  # Signal to notify other tabs (sends list of dicts)
    equipo_deleted = pyqtSignal()       # Signal to notify when an equipo is deleted

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.equipos_cache = []
        self.equipos_full_data = {}
        self.eq_id_sel = None
        self.init_ui()
        self.load_equipos()

    def toggle_fecha_baja(self, checked):
        self.txt_eq_fecha_baja.setEnabled(checked)
        if checked and not self.txt_eq_fecha_baja.text():
            self.txt_eq_fecha_baja.setText(datetime.now().strftime("%d-%m-%Y"))
        elif not checked:
            self.txt_eq_fecha_baja.clear()

    def init_ui(self):
        layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Panel Izquierdo: Formulario
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        lbl_title = QLabel("Datos del Motor/Equipo")
        lbl_title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        left_layout.addWidget(lbl_title)

        # Form Fields
        self.txt_eq_nombre = self.create_input(left_layout, "Nombre Equipo:")
        self.txt_eq_desc = self.create_text_input(left_layout, "Descripción:", height=60)
        self.txt_eq_lugar = self.create_input(left_layout, "Lugar Instalación:")
        self.txt_eq_planta = self.create_input(left_layout, "Planta:")
        self.txt_eq_finst = self.create_input(left_layout, "Fecha Instalación:")
        self.txt_eq_otros = self.create_text_input(left_layout, "Otros Datos Técnicos:", height=60)
        
        self.chk_eq_baja = QCheckBox("Dar de Baja")
        self.chk_eq_baja.toggled.connect(self.toggle_fecha_baja)
        left_layout.addWidget(self.chk_eq_baja)
        
        self.txt_eq_fecha_baja = self.create_input(left_layout, "Fecha de Baja:")
        self.txt_eq_fecha_baja.setPlaceholderText("DD-MM-YYYY")
        self.txt_eq_fecha_baja.setEnabled(False)
        
        left_layout.addSpacing(15)

        # Botones
        self.btn_save = QPushButton("Guardar Equipo")
        self.btn_save.clicked.connect(self.save_equipo)
        left_layout.addWidget(self.btn_save)

        self.btn_update = QPushButton("Actualizar Seleccionado")
        self.btn_update.clicked.connect(self.update_equipo)
        self.btn_update.setEnabled(False)  # Inicialmente deshabilitado
        left_layout.addWidget(self.btn_update)

        self.btn_clear = QPushButton("Limpiar Formulario")
        self.btn_clear.clicked.connect(self.clear_form_equipo)
        left_layout.addWidget(self.btn_clear)

        left_widget.setLayout(left_layout)
        splitter.addWidget(left_widget)

        # Panel Derecho: Tabla
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        self.table_eq = QTableWidget()
        self.table_eq.setColumnCount(5)
        self.table_eq.setHorizontalHeaderLabels(["ID", "Nombre", "Lugar", "Planta", "Baja"])
        self.table_eq.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_eq.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_eq.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_eq.itemSelectionChanged.connect(self.on_equipo_select)
        right_layout.addWidget(self.table_eq)

        btn_panel = QHBoxLayout()
        btn_del = QPushButton("Eliminar Equipo")
        btn_del.setStyleSheet("background-color: #dc3545; color: white;")
        btn_del.clicked.connect(self.delete_equipo)
        btn_reload = QPushButton("Recargar Lista")
        btn_reload.clicked.connect(self.load_equipos)
        
        btn_export = QPushButton("Exportar Excel")
        btn_export.clicked.connect(self.export_to_excel)
        
        btn_panel.addStretch()
        btn_panel.addWidget(btn_export)
        btn_panel.addWidget(btn_reload)
        btn_panel.addWidget(btn_del)
        right_layout.addLayout(btn_panel)

        right_widget.setLayout(right_layout)
        splitter.addWidget(right_widget)
        
        splitter.setSizes([350, 750])

    def create_input(self, layout, label_text):
        layout.addWidget(QLabel(label_text))
        inp = QLineEdit()
        layout.addWidget(inp)
        return inp

    def create_text_input(self, layout, label_text, height=50):
        layout.addWidget(QLabel(label_text))
        inp = QTextEdit()
        inp.setFixedHeight(height)
        layout.addWidget(inp)
        return inp

    def load_equipos(self):
        self.table_eq.setRowCount(0)
        self.worker_eq = LoadEquiposWorker(self.db)
        self.worker_eq.finished.connect(self.populate_equipos)
        self.worker_eq.error.connect(self.on_worker_error)
        self.worker_eq.start()

    def on_worker_error(self, err_msg):
        print(f"Error cargando equipos: {err_msg}")
        QMessageBox.warning(self, "Error de Datos", f"No se pudieron cargar los equipos:\n{err_msg}")

    def populate_equipos(self, rows):
        self.equipos_cache = []
        self.equipos_full_data = {}
        self.table_eq.setRowCount(len(rows))
        
        for i, row in enumerate(rows):
            # row: 0=id, 1=nombre, 2=desc, 3=lugar, 4=planta, 5=f_inst, 6=otros, 7=baja, 8=fecha_baja
            self.equipos_full_data[str(row[0])] = row
            
            self.table_eq.setItem(i, 0, QTableWidgetItem(str(row[0])))
            self.table_eq.setItem(i, 1, QTableWidgetItem(str(row[1])))
            self.table_eq.setItem(i, 2, QTableWidgetItem(str(row[3])))
            self.table_eq.setItem(i, 3, QTableWidgetItem(str(row[4])))
            self.table_eq.setItem(i, 4, QTableWidgetItem("Sí" if row[7] else "No"))

            fecha_baja = row[8] if len(row) > 8 else ""
            
            self.equipos_cache.append({
                "id": row[0], "nombre": row[1], "lugar": row[3], 
                "planta": row[4], "f_inst": row[5],
                "baja": bool(row[7]), "fecha_baja": fecha_baja
            })
        
        self.equipos_updated.emit(self.equipos_cache)

    def on_equipo_select(self):
        rows = self.table_eq.selectionModel().selectedRows()
        if not rows: return
        
        row_idx = rows[0].row()
        eq_id = self.table_eq.item(row_idx, 0).text()
        self.eq_id_sel = int(eq_id)

        # Update button states for editing mode
        self.btn_save.setEnabled(False)
        self.btn_update.setEnabled(True)

        if str(eq_id) in self.equipos_full_data:
            data = self.equipos_full_data[str(eq_id)]
            self.txt_eq_nombre.setText(data[1])
            self.txt_eq_desc.setText(data[2] or "")
            self.txt_eq_lugar.setText(data[3])
            self.txt_eq_planta.setText(data[4])
            self.txt_eq_finst.setText(data[5])
            self.txt_eq_otros.setText(data[6] or "")
            
            is_baja = bool(data[7])
            self.chk_eq_baja.setChecked(is_baja)
            self.toggle_fecha_baja(is_baja)
            if len(data) > 8 and data[8]:
                self.txt_eq_fecha_baja.setText(data[8])
            elif is_baja:
                 # Fallback if baja but no date (shouldn't happen with new logic but possible for old data)
                 self.txt_eq_fecha_baja.setText(datetime.now().strftime("%d-%m-%Y"))

    def save_equipo(self):
        if not self.txt_eq_nombre.text():
            QMessageBox.warning(self, "Error", "Nombre obligatorio")
            return
        
        data = {
            'nombre': self.txt_eq_nombre.text(),
            'descripcion': self.txt_eq_desc.toPlainText().strip(),
            'lugar_instalacion': self.txt_eq_lugar.text(),
            'planta': self.txt_eq_planta.text(),
            'fecha_instalacion': self.txt_eq_finst.text(),
            'otros': self.txt_eq_otros.toPlainText().strip(),
            'baja': self.chk_eq_baja.isChecked(),
            'fecha_baja': self.txt_eq_fecha_baja.text() if self.chk_eq_baja.isChecked() else ""
        }
        
        if self.db and self.db.add_equipo(data):
            QMessageBox.information(self, "Éxito", "Equipo agregado")
            self.clear_form_equipo()
            self.load_equipos()
        else:
            QMessageBox.critical(self, "Error", "No se pudo guardar")

    def update_equipo(self):
        if not self.eq_id_sel: return
        data = {
            'nombre': self.txt_eq_nombre.text(),
            'descripcion': self.txt_eq_desc.toPlainText().strip(),
            'lugar_instalacion': self.txt_eq_lugar.text(),
            'planta': self.txt_eq_planta.text(),
            'fecha_instalacion': self.txt_eq_finst.text(),
            'otros': self.txt_eq_otros.toPlainText().strip(),
            'baja': self.chk_eq_baja.isChecked(),
            'fecha_baja': self.txt_eq_fecha_baja.text() if self.chk_eq_baja.isChecked() else ""
        }
        if self.db and self.db.update_equipo(self.eq_id_sel, data):
            QMessageBox.information(self, "Éxito", "Equipo actualizado")
            self.clear_form_equipo()
            self.load_equipos()
        else:
            QMessageBox.critical(self, "Error", "Fallo al actualizar")

    def delete_equipo(self):
        if not self.eq_id_sel: return
        reply = QMessageBox.question(self, "Confirmar", 
                                   "Se eliminará el equipo y SU HISTORIAL. ¿Seguro?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if self.db and self.db.delete_equipo(self.eq_id_sel):
                QMessageBox.information(self, "Éxito", "Equipo eliminado correctamente (Soft Delete).")
                self.clear_form_equipo()
                self.load_equipos()
                self.equipo_deleted.emit()
            else:
                QMessageBox.critical(self, "Error", "No se pudo eliminar el equipo.")

    def export_to_excel(self):
        try:
            import openpyxl
            filename, _ = QFileDialog.getSaveFileName(self, "Guardar Inventario", "Inventario_Equipos.xlsx", "Excel Files (*.xlsx)")
            if not filename:
                return

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Equipos"

            # Headers
            headers = ["ID", "Nombre", "Descripción", "Lugar Instalación", "Planta", "Fecha Inst.", "Otros", "Baja", "Fecha Baja"]
            ws.append(headers)

            # Data
            equipos = self.db.get_equipos()
            for eq in equipos:
                # eq is a tuple: 0=id, 1=nombre, 2=desc, 3=lugar, 4=planta, 5=f_inst, 6=otros, 7=baja, 8=fecha_baja
                row = [
                    eq[0],
                    eq[1],
                    eq[2],
                    eq[3],
                    eq[4],
                    eq[5],
                    eq[6],
                    "Sí" if eq[7] else "No",
                    eq[8] if len(eq) > 8 else ""
                ]
                ws.append(row)

            wb.save(filename)
            QMessageBox.information(self, "Éxito", "Inventario exportado correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al exportar: {e}")

    def clear_form_equipo(self):
        self.eq_id_sel = None
        self.txt_eq_nombre.clear()
        self.txt_eq_desc.clear()
        self.txt_eq_lugar.clear()
        self.txt_eq_planta.clear()
        self.txt_eq_finst.clear()
        self.txt_eq_otros.clear()
        self.chk_eq_baja.setChecked(False)
        self.txt_eq_fecha_baja.clear()
        self.table_eq.clearSelection()
        
        # Reset buttons to default state
        self.btn_save.setEnabled(True)
        self.btn_update.setEnabled(False)
