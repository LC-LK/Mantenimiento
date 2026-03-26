import json
import mysql.connector
import mysql.connector.locales
import mysql.connector.errors
import os
import threading
import logging
# from dotenv import load_dotenv

# Configurar logger
logger = logging.getLogger(__name__)

# Monkey-patch para evitar error "No localization support" en ejecutables compilados
try:
    _original_get_client_error = mysql.connector.locales.get_client_error

    def _patched_get_client_error(error_code, language='eng'):
        try:
            return _original_get_client_error(error_code, language)
        except (ImportError, Exception):
            # Fallback seguro si falla la carga de locales
            return f"MySQL Error {error_code} (Mensaje original no disponible por falta de locales)"

    # Parchear en locales (origen)
    mysql.connector.locales.get_client_error = _patched_get_client_error
    
    # Parchear en errors (consumidor común que importa la función)
    if hasattr(mysql.connector.errors, 'get_client_error'):
        mysql.connector.errors.get_client_error = _patched_get_client_error
        
    logger.info("Parche de localización MySQL aplicado correctamente.")
except Exception as e:
    logger.warning(f"No se pudo aplicar parche de localización MySQL: {e}")

import sys

class DatabaseManager:
    def __init__(self):
        # load_dotenv()
        self.config = self.load_config()
        self.conn = None
        self.lock = threading.Lock()
        self.init_db()

    def get_resource_path(self, relative_path):
        """Obtiene la ruta absoluta del recurso, compatible con PyInstaller y desarrollo."""
        try:
            # PyInstaller crea una carpeta temporal y guarda la ruta en _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            # En modo desarrollo, usar la ruta del directorio actual
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        return os.path.join(base_path, relative_path)

    def load_config(self):
        # Credenciales hardcodeadas internamente
        internal_config = {
            "host": "host",
            "port": port,
            "user": "user",
            "password": "password",
            "database": "informes_db",
            "ssl_cert": self.get_resource_path("service.cert"),
            "ssl_key": self.get_resource_path("service.key"),
        }

        return {"remote_config": internal_config}

    def get_connection(self):
        if self.conn is not None and self.conn.is_connected():
            return self.conn
            
        remote_config = self.config.get("remote_config", {})
        connect_args = {
            "host": remote_config.get("host"),
            "port": remote_config.get("port"),
            "user": remote_config.get("user"),
            "password": remote_config.get("password"),
            "database": remote_config.get("database"),
            "connection_timeout": 10,
            "use_pure": True # Force pure Python implementation to avoid C-ext SSL conflicts with PyQt6
        }
        
        if remote_config.get("ssl_cert") and remote_config.get("ssl_key"):
            if os.path.exists(remote_config["ssl_cert"]) and os.path.exists(remote_config["ssl_key"]):
                connect_args["ssl_cert"] = remote_config.get("ssl_cert")
                connect_args["ssl_key"] = remote_config.get("ssl_key")
            else:
                logger.warning("Certificados SSL definidos pero no encontrados en disco.")

        try:
            self.conn = mysql.connector.connect(**connect_args)
            return self.conn
        except mysql.connector.Error as err:
            logger.error(f"Error de conexión MySQL: {err}")
            raise

    def init_db(self):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Tabla Equipos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS equipos (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(255),
                    descripcion TEXT,
                    lugar_instalacion VARCHAR(255),
                    planta VARCHAR(255),
                    fecha_instalacion VARCHAR(20),
                    otros TEXT,
                    baja TINYINT(1) DEFAULT 0,
                    fecha_baja VARCHAR(20),
                    deleted TINYINT(1) DEFAULT 0
                )
            ''')
            
            # Migración: Agregar columna 'deleted' a equipos si no existe
            try:
                cursor.execute("SELECT deleted FROM equipos LIMIT 1")
                cursor.fetchall()
            except Exception:
                try:
                    cursor.execute("ALTER TABLE equipos ADD COLUMN deleted TINYINT(1) DEFAULT 0")
                    conn.commit()
                    logger.info("Columna 'deleted' agregada a tabla 'equipos'")
                except Exception as e:
                    logger.error(f"Error agregando columna 'deleted' a equipos: {e}")

            # Migración: Agregar columna 'fecha_baja' (revisión de seguridad)
            try:
                cursor.execute("SELECT fecha_baja FROM equipos LIMIT 1")
                cursor.fetchall()
            except Exception:
                try:
                    cursor.execute("ALTER TABLE equipos ADD COLUMN fecha_baja VARCHAR(20)")
                    conn.commit()
                except Exception:
                    pass

            # Tabla Mantenimientos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mantenimientos (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    equipo_id INT,
                    fecha_ingreso VARCHAR(20),
                    horometro FLOAT,
                    tipo_mantencion VARCHAR(255),
                    observaciones TEXT,
                    proxima_mantencion VARCHAR(20),
                    deleted TINYINT(1) DEFAULT 0,
                    FOREIGN KEY (equipo_id) REFERENCES equipos(id) ON DELETE CASCADE
                )
            ''')

            # Migración: Agregar columna 'deleted' a mantenimientos si no existe
            try:
                cursor.execute("SELECT deleted FROM mantenimientos LIMIT 1")
                cursor.fetchall()
            except Exception:
                try:
                    cursor.execute("ALTER TABLE mantenimientos ADD COLUMN deleted TINYINT(1) DEFAULT 0")
                    conn.commit()
                    logger.info("Columna 'deleted' agregada a tabla 'mantenimientos'")
                except Exception as e:
                    logger.error(f"Error agregando columna 'deleted' a mantenimientos: {e}")
            
            conn.commit()
            cursor.close()
        except Exception as e:
            logger.critical(f"Error inicializando base de datos: {e}")
            raise

    def add_report(self, data):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            try:
                query = '''
                INSERT INTO informes (
                    nombre_equipo, descripcion, lugar_instalacion, planta, 
                    fecha_instalacion, horometro, fecha_ingreso, mantencion, 
                    observaciones, proxima_mantencion, baja, otros
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                '''
                values = (
                    data.get('nombre_equipo'),
                    data.get('descripcion'),
                    data.get('lugar_instalacion'),
                    data.get('planta'),
                    data.get('fecha_instalacion'),
                    data.get('horometro'),
                    data.get('fecha_ingreso'),
                    data.get('mantencion'),
                    data.get('observaciones'),
                    data.get('proxima_mantencion'),
                    1 if data.get('baja') else 0,
                    data.get('otros')
                )
                cursor.execute(query, values)
                conn.commit()
                return True
            except Exception as e:
                print(f"Error al guardar: {e}")
                return False
            finally:
                cursor.close()

    def update_report(self, id_reporte, data):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            try:
                query = '''
                UPDATE informes SET
                    nombre_equipo = %s,
                    descripcion = %s,
                    lugar_instalacion = %s,
                    planta = %s,
                    fecha_instalacion = %s,
                    horometro = %s,
                    mantencion = %s,
                    observaciones = %s,
                    proxima_mantencion = %s,
                    baja = %s,
                    otros = %s
                WHERE id = %s
                '''
                values = (
                    data.get('nombre_equipo'),
                    data.get('descripcion'),
                    data.get('lugar_instalacion'),
                    data.get('planta'),
                    data.get('fecha_instalacion'),
                    data.get('horometro'),
                    data.get('mantencion'),
                    data.get('observaciones'),
                    data.get('proxima_mantencion'),
                    1 if data.get('baja') else 0,
                    data.get('otros'),
                    id_reporte
                )
                cursor.execute(query, values)
                conn.commit()
                return True
            except Exception as e:
                print(f"Error al actualizar: {e}")
                return False
            finally:
                cursor.close()

    def delete_report(self, id_reporte):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute('DELETE FROM informes WHERE id = %s', (id_reporte,))
                conn.commit()
                return True
            except Exception as e:
                print(f"Error al eliminar: {e}")
                return False
            finally:
                cursor.close()

    def get_reports(self):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM informes ORDER BY id DESC')
            rows = cursor.fetchall()
            cursor.close()
            return rows

    def get_report_by_id(self, id_reporte):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM informes WHERE id = %s', (id_reporte,))
            row = cursor.fetchone()
            cursor.close()
            return row

    # --- MÉTODOS PARA EQUIPOS (INVENTARIO) ---
    def add_equipo(self, data):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            try:
                query = '''
                    INSERT INTO equipos (nombre, descripcion, lugar_instalacion, planta, fecha_instalacion, otros, baja, fecha_baja)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                '''
                values = (
                    data.get('nombre'),
                    data.get('descripcion'),
                    data.get('lugar_instalacion'),
                    data.get('planta'),
                    data.get('fecha_instalacion'),
                    data.get('otros'),
                    1 if data.get('baja') else 0,
                    data.get('fecha_baja')
                )
                cursor.execute(query, values)
                conn.commit()
                return True
            except Exception as e:
                print(f"Error al agregar equipo: {e}")
                return False
            finally:
                cursor.close()

    def update_equipo(self, id_equipo, data):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            try:
                query = '''
                    UPDATE equipos SET
                        nombre = %s,
                        descripcion = %s,
                        lugar_instalacion = %s,
                        planta = %s,
                        fecha_instalacion = %s,
                        otros = %s,
                        baja = %s,
                        fecha_baja = %s
                    WHERE id = %s
                '''
                values = (
                    data.get('nombre'),
                    data.get('descripcion'),
                    data.get('lugar_instalacion'),
                    data.get('planta'),
                    data.get('fecha_instalacion'),
                    data.get('otros'),
                    1 if data.get('baja') else 0,
                    data.get('fecha_baja'),
                    id_equipo
                )
                cursor.execute(query, values)
                conn.commit()
                return True
            except Exception as e:
                print(f"Error al actualizar equipo: {e}")
                return False
            finally:
                cursor.close()

    def delete_equipo(self, id_equipo):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            try:
                # Soft delete equipo
                cursor.execute('UPDATE equipos SET deleted = 1 WHERE id = %s', (id_equipo,))
                # También deberíamos hacer soft delete de sus mantenimientos para mantener consistencia visual
                # aunque la FK es CASCADE, si no borramos realmente, el CASCADE no se dispara.
                # Opcional: Marcar sus mantenimientos como borrados.
                cursor.execute('UPDATE mantenimientos SET deleted = 1 WHERE equipo_id = %s', (id_equipo,))
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"Error al eliminar equipo (soft delete): {e}")
                return False
            finally:
                cursor.close()

    def get_equipos(self):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM equipos WHERE deleted = 0 ORDER BY id DESC')
            rows = cursor.fetchall()
            cursor.close()
            return rows

    # --- MÉTODOS PARA MANTENIMIENTOS ---
    def add_mantenimiento(self, data):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            try:
                query = '''
                    INSERT INTO mantenimientos (equipo_id, fecha_ingreso, horometro, tipo_mantencion, observaciones, proxima_mantencion)
                    VALUES (%s, %s, %s, %s, %s, %s)
                '''
                values = (
                    data.get('equipo_id'),
                    data.get('fecha_ingreso'),
                    data.get('horometro'),
                    data.get('tipo_mantencion'),
                    data.get('observaciones'),
                    data.get('proxima_mantencion')
                )
                cursor.execute(query, values)
                conn.commit()
                return True
            except Exception as e:
                print(f"Error al agregar mantenimiento: {e}")
                return False
            finally:
                cursor.close()

    def get_mantenimientos_by_equipo(self, equipo_id):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM mantenimientos WHERE equipo_id = %s AND deleted = 0 ORDER BY id DESC', (equipo_id,))
            rows = cursor.fetchall()
            cursor.close()
            return rows

    def get_all_mantenimientos(self):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM mantenimientos WHERE deleted = 0 ORDER BY id DESC')
            rows = cursor.fetchall()
            cursor.close()
            return rows

    def get_mantenimiento_by_id(self, mant_id):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM mantenimientos WHERE id = %s', (mant_id,))
            row = cursor.fetchone()
            cursor.close()
            return row
            
    def delete_mantenimiento(self, id_mant):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            try:
                # Soft delete
                cursor.execute('UPDATE mantenimientos SET deleted = 1 WHERE id = %s', (id_mant,))
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"Error al eliminar mantenimiento (soft delete): {e}")
                return False
            finally:
                cursor.close()
