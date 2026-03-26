from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel, 
                             QLineEdit, QTextEdit, QPushButton, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QAbstractItemView, 
                             QComboBox, QMessageBox, QFileDialog, QFrame, QDialog, 
                             QTextBrowser, QFormLayout, QGroupBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QDoubleValidator
from datetime import datetime
# import openpyxl
from .workers import LoadMantenimientosWorker, LoadEquiposWorker

class MantenimientosTab(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.equipos_cache = []
        self.init_ui()
        self.load_equipos()
        self.load_mantenimientos()

    def load_equipos(self):
        self.worker_eq = LoadEquiposWorker(self.db)
        self.worker_eq.finished.connect(self.process_equipos_data)
        self.worker_eq.start()

    def process_equipos_data(self, rows):
        # Convert tuples to dict list expected by update_equipos_data
        # Schema: id, nombre, descripcion, lugar, planta, fecha_inst, otros, baja, fecha_baja, deleted
        # Indices: 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
        formatted_data = []
        for r in rows:
            formatted_data.append({
                "id": r[0],
                "nombre": r[1],
                "lugar": r[3],
                "planta": r[4],
                "f_inst": r[5],
                "baja": r[7],
                "fecha_baja": r[8]
            })
        self.update_equipos_data(formatted_data)

    def init_ui(self):
        layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Panel Izquierdo
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        lbl_title = QLabel("Registrar Mantenimiento")
        lbl_title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        left_layout.addWidget(lbl_title)

        left_layout.addWidget(QLabel("Seleccionar Motor/Equipo:"))
        self.combo_equipos = QComboBox()
        self.combo_equipos.currentIndexChanged.connect(self.on_equipo_combo_select)
        left_layout.addWidget(self.combo_equipos)

        # Info Box
        info_group = QFrame()
        info_group.setFrameShape(QFrame.Shape.StyledPanel)
        info_layout = QVBoxLayout(info_group)
        self.lbl_info_lugar = QLabel("Lugar: ---")
        self.lbl_info_planta = QLabel("Planta: ---")
        self.lbl_info_finst = QLabel("F. Inst: ---")
        self.lbl_info_estado = QLabel("Estado: Activo")
        for l in [self.lbl_info_lugar, self.lbl_info_planta, self.lbl_info_finst, self.lbl_info_estado]:
            l.setStyleSheet("font-weight: bold;")
            info_layout.addWidget(l)
        left_layout.addWidget(info_group)

        left_layout.addSpacing(10)
        
        self.txt_mant_fecha = self.create_input(left_layout, "Fecha Mantenimiento:")
        self.txt_mant_fecha.setText(datetime.now().strftime("%d-%m-%Y"))
        
        self.txt_mant_horom = self.create_input(left_layout, "Horómetro Actual:")
        self.txt_mant_horom.setValidator(QDoubleValidator(0.0, 999999.0, 2))
        self.txt_mant_tipo = self.create_input(left_layout, "Tipo Mantención:")
        self.txt_mant_obs = self.create_text_input(left_layout, "Observaciones:", height=60)
        self.txt_mant_prox = self.create_input(left_layout, "Próxima Mantención:")

        left_layout.addSpacing(15)

        self.btn_save = QPushButton("Guardar Mantenimiento")
        self.btn_save.clicked.connect(self.save_mantenimiento)
        left_layout.addWidget(self.btn_save)

        btn_del = QPushButton("Eliminar Seleccionado")
        btn_del.setStyleSheet("background-color: #dc3545; color: white;")
        btn_del.clicked.connect(self.delete_mantenimiento)
        left_layout.addWidget(btn_del)

        btn_clear = QPushButton("Limpiar Formulario")
        btn_clear.clicked.connect(self.clear_form_mant)
        left_layout.addWidget(btn_clear)

        left_widget.setLayout(left_layout)
        splitter.addWidget(left_widget)

        # Panel Derecho
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        header = QHBoxLayout()
        lbl_hist = QLabel("Historial de Mantenimientos")
        lbl_hist.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        header.addWidget(lbl_hist)
        header.addStretch()

        btn_export = QPushButton("Exportar Excel")
        btn_export.clicked.connect(self.export_to_excel)
        header.addWidget(btn_export)

        btn_reload = QPushButton("Recargar Historial")
        btn_reload.clicked.connect(self.load_mantenimientos)
        header.addWidget(btn_reload)
        right_layout.addLayout(header)

        self.table_mant = QTableWidget()
        self.table_mant.setColumnCount(6)
        self.table_mant.setHorizontalHeaderLabels(["ID", "Equipo", "Fecha", "Horómetro", "Tipo", "Próxima"])
        self.table_mant.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_mant.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_mant.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_mant.doubleClicked.connect(self.show_details)
        right_layout.addWidget(self.table_mant)

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

    def update_equipos_data(self, equipos_cache):
        self.equipos_cache = equipos_cache
        self.combo_equipos.blockSignals(True)
        self.combo_equipos.clear()
        self.combo_equipos.addItem("Seleccionar Equipo...", None)
        for eq in self.equipos_cache:
            self.combo_equipos.addItem(f"{eq['nombre']} (ID: {eq['id']})", eq['id'])
        self.combo_equipos.blockSignals(False)

    def on_equipo_combo_select(self, index):
        eq_id = self.combo_equipos.currentData()
        if eq_id is None: 
            self.lbl_info_lugar.setText("Lugar: ---")
            self.lbl_info_planta.setText("Planta: ---")
            self.lbl_info_finst.setText("F. Inst: ---")
            self.lbl_info_estado.setText("Estado: ---")
            self.lbl_info_estado.setStyleSheet("font-weight: bold;")
            self.btn_save.setEnabled(False)
            self.btn_save.setText("Guardar Mantenimiento")
            return

        equipo = next((e for e in self.equipos_cache if e["id"] == eq_id), None)
        if equipo:
            self.lbl_info_lugar.setText(f"Lugar: {equipo['lugar']}")
            self.lbl_info_planta.setText(f"Planta: {equipo['planta']}")
            self.lbl_info_finst.setText(f"F. Inst: {equipo['f_inst']}")
            
            if equipo.get("baja"):
                fecha_baja = equipo.get("fecha_baja", "")
                msg = f"Estado: BAJA ({fecha_baja})" if fecha_baja else "Estado: BAJA"
                self.lbl_info_estado.setText(msg)
                self.lbl_info_estado.setStyleSheet("font-weight: bold; color: #dc3545;") # Red
                self.btn_save.setEnabled(False)
                self.btn_save.setText("Equipo dado de baja")
            else:
                self.lbl_info_estado.setText("Estado: Activo")
                self.lbl_info_estado.setStyleSheet("font-weight: bold; color: #28a745;") # Green
                self.btn_save.setEnabled(True)
                self.btn_save.setText("Guardar Mantenimiento")
            
        self.filter_mantenimientos(eq_id)

    def load_mantenimientos(self):
        self.table_mant.setRowCount(0)
        self.worker_mant = LoadMantenimientosWorker(self.db)
        self.worker_mant.finished.connect(self.populate_mant)
        self.worker_mant.error.connect(self.on_worker_error)
        self.worker_mant.start()

    def filter_mantenimientos(self, eq_id):
        self.table_mant.setRowCount(0)
        self.worker_mant = LoadMantenimientosWorker(self.db, eq_id)
        self.worker_mant.finished.connect(self.populate_mant)
        self.worker_mant.error.connect(self.on_worker_error)
        self.worker_mant.start()

    def on_worker_error(self, err_msg):
        print(f"Error cargando mantenimientos: {err_msg}")
        QMessageBox.warning(self, "Error de Datos", f"No se pudieron cargar los mantenimientos:\n{err_msg}")

    def populate_mant(self, rows):
        self.table_mant.setRowCount(len(rows))
        for i, row in enumerate(rows):
            eq_id = row[1]
            eq_name = "Desconocido"
            eq_obj = next((e for e in self.equipos_cache if e["id"] == eq_id), None)
            if eq_obj: eq_name = eq_obj["nombre"]
            
            self.table_mant.setItem(i, 0, QTableWidgetItem(str(row[0])))
            self.table_mant.setItem(i, 1, QTableWidgetItem(eq_name))
            self.table_mant.setItem(i, 2, QTableWidgetItem(str(row[2])))
            self.table_mant.setItem(i, 3, QTableWidgetItem(str(row[3])))
            self.table_mant.setItem(i, 4, QTableWidgetItem(str(row[4])))
            self.table_mant.setItem(i, 5, QTableWidgetItem(str(row[6])))

    def save_mantenimiento(self):
        eq_id = self.combo_equipos.currentData()
        if not eq_id:
            QMessageBox.warning(self, "Error", "Seleccione un equipo")
            return
            
        horometro = 0.0
        try:
            if self.txt_mant_horom.text():
                horometro = float(self.txt_mant_horom.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "Horómetro debe ser número")
            return

        data = {
            'equipo_id': eq_id,
            'fecha_ingreso': self.txt_mant_fecha.text(),
            'horometro': horometro,
            'tipo_mantencion': self.txt_mant_tipo.text(),
            'observaciones': self.txt_mant_obs.toPlainText().strip(),
            'proxima_mantencion': self.txt_mant_prox.text()
        }
        
        if self.db and self.db.add_mantenimiento(data):
            QMessageBox.information(self, "Éxito", "Mantenimiento registrado")
            self.clear_form_mant(keep_equipo=True)
            self.filter_mantenimientos(eq_id)
        else:
            QMessageBox.critical(self, "Error", "Fallo al guardar")

    def delete_mantenimiento(self):
        rows = self.table_mant.selectionModel().selectedRows()
        if not rows:
            QMessageBox.warning(self, "Atención", "Seleccione un registro para eliminar.")
            return

        row_idx = rows[0].row()
        mant_id = int(self.table_mant.item(row_idx, 0).text())

        reply = QMessageBox.question(
            self, "Confirmar Eliminación", 
            "¿Está seguro de eliminar este registro?\n(Se guardará como eliminado en la BD)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.db and self.db.delete_mantenimiento(mant_id):
                QMessageBox.information(self, "Éxito", "Mantenimiento eliminado correctamente (Soft Delete).")
                eq_id = self.combo_equipos.currentData()
                if eq_id:
                    self.filter_mantenimientos(eq_id)
                else:
                    self.load_mantenimientos()
            else:
                QMessageBox.critical(self, "Error", "No se pudo eliminar el registro.")

    def export_to_excel(self):
        try:
            import openpyxl
            filename, _ = QFileDialog.getSaveFileName(self, "Guardar Historial", "Historial_Mantenimientos.xlsx", "Excel Files (*.xlsx)")
            if not filename:
                return

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Mantenimientos"

            # Headers
            headers = ["ID", "Equipo ID", "Fecha Ingreso", "Horómetro", "Tipo", "Observaciones", "Próxima Mant."]
            ws.append(headers)

            # Data
            equipo_id = self.combo_equipos.currentData()
            
            if equipo_id:
                 mantenimientos = self.db.get_mantenimientos_by_equipo(equipo_id)
            else:
                 mantenimientos = self.db.get_all_mantenimientos()

            for m in mantenimientos:
                row = [
                    m[0], # id
                    m[1], # equipo_id
                    m[2], # fecha_ingreso
                    m[3], # horometro
                    m[4], # tipo
                    m[5], # obs
                    m[6]  # prox
                ]
                ws.append(row)

            wb.save(filename)
            QMessageBox.information(self, "Éxito", "Historial exportado correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al exportar: {e}")

    def clear_form_mant(self, keep_equipo=False):
        if not keep_equipo:
            self.combo_equipos.setCurrentIndex(0)
        self.txt_mant_fecha.setText(datetime.now().strftime("%d-%m-%Y"))
        self.txt_mant_horom.clear()
        self.txt_mant_tipo.clear()
        self.txt_mant_obs.clear()
        self.txt_mant_prox.clear()
        self.table_mant.clearSelection()

    def show_details(self, index):
        row_idx = index.row()
        mant_id = self.table_mant.item(row_idx, 0).text()
        
        record = self.db.get_mantenimiento_by_id(mant_id)
        if not record:
            QMessageBox.warning(self, "Error", "No se encontró el registro.")
            return

        # record indices: 0=id, 1=eq_id, 2=fecha, 3=horom, 4=tipo, 5=obs, 6=prox, 7=deleted
        
        eq_name = "Desconocido"
        eq_lugar = "---"
        eq_obj = next((e for e in self.equipos_cache if e["id"] == record[1]), None)
        if eq_obj: 
            eq_name = eq_obj["nombre"]
            eq_lugar = f"{eq_obj.get('lugar', '')} - {eq_obj.get('planta', '')}"

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Detalle Mantenimiento #{record[0]}")
        dlg.setMinimumWidth(500)
        dlg.setMinimumHeight(600)
        
        main_layout = QVBoxLayout(dlg)
        main_layout.setSpacing(15)

        # Header Title
        title = QLabel("Ficha de Mantenimiento")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # Group 1: Equipo Info
        grp_equipo = QGroupBox("Información del Equipo")
        grp_equipo.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #7f8c8d; border-radius: 5px; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }")
        form_eq = QFormLayout()
        form_eq.addRow(QLabel("Equipo:"), QLabel(f"{eq_name}"))
        form_eq.addRow(QLabel("ID Equipo:"), QLabel(str(record[1])))
        form_eq.addRow(QLabel("Ubicación:"), QLabel(eq_lugar))
        grp_equipo.setLayout(form_eq)
        main_layout.addWidget(grp_equipo)

        # Group 2: Detalles Mantenimiento
        grp_mant = QGroupBox("Datos del Registro")
        grp_mant.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #7f8c8d; border-radius: 5px; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }")
        form_mant = QFormLayout()
        
        # Style values
        def style_val(text):
            l = QLabel(str(text))
            l.setStyleSheet("font-weight: normal;")
            return l

        form_mant.addRow("ID Registro:", style_val(record[0]))
        form_mant.addRow("Fecha:", style_val(record[2]))
        form_mant.addRow("Horómetro:", style_val(f"{record[3]} hrs"))
        form_mant.addRow("Tipo:", style_val(record[4]))
        form_mant.addRow("Próxima Mant.:", style_val(record[6]))
        grp_mant.setLayout(form_mant)
        main_layout.addWidget(grp_mant)

        # Group 3: Observaciones
        grp_obs = QGroupBox("Observaciones")
        grp_obs.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #7f8c8d; border-radius: 5px; margin-top: 10px; }")
        vbox_obs = QVBoxLayout()
        obs_browser = QTextBrowser()
        obs_browser.setPlainText(record[5] if record[5] else "Sin observaciones.")
        # Removed explicit background-color to respect system theme (dark/light)
        obs_browser.setStyleSheet("border: none; padding: 5px;")
        vbox_obs.addWidget(obs_browser)
        grp_obs.setLayout(vbox_obs)
        main_layout.addWidget(grp_obs)

        # Close Button
        btn_close = QPushButton("Cerrar")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setFixedSize(100, 35)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #3498db; 
                color: white; 
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        btn_close.clicked.connect(dlg.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)
        
        dlg.exec()
