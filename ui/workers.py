from PyQt6.QtCore import QThread, pyqtSignal

class LoadEquiposWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager

    def run(self):
        if not self.db:
            return
        try:
            rows = self.db.get_equipos()
            self.finished.emit(rows)
        except Exception as e:
            self.error.emit(str(e))

class LoadMantenimientosWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, db_manager, eq_id=None):
        super().__init__()
        self.db = db_manager
        self.eq_id = eq_id

    def run(self):
        if not self.db:
            return
        try:
            if self.eq_id:
                rows = self.db.get_mantenimientos_by_equipo(self.eq_id)
            else:
                rows = self.db.get_all_mantenimientos()
            self.finished.emit(rows)
        except Exception as e:
            self.error.emit(str(e))
