import json
import mysql.connector
import os

class DatabaseManager:
    def __init__(self):
        self.config = self.load_config()
        self.init_db()

    def load_config(self):
        try:
            with open("config.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            return {
                "remote_config": {
                    "host": "host",
                    "port": port,
                    "user": "user",
                    "password": "password",
                    "database": "informes_db",
                    "ssl_cert": os.path.join(base_dir, "service.cert"),
                    "ssl_key": os.path.join(base_dir, "service.key"),
                }
            }

    def get_connection(self):
        remote_config = self.config.get("remote_config", {})
        connect_args = {
            "host": remote_config.get("host"),
            "port": int(remote_config.get("port", 3306)),
            "user": remote_config.get("user"),
            "password": remote_config.get("password"),
            "database": remote_config.get("database")
        }
        if remote_config.get("ssl_cert") and remote_config.get("ssl_key"):
            connect_args["ssl_cert"] = remote_config.get("ssl_cert")
            connect_args["ssl_key"] = remote_config.get("ssl_key")
        return mysql.connector.connect(**connect_args)

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS informes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre_equipo VARCHAR(255),
                descripcion TEXT,
                lugar_instalacion VARCHAR(255),
                planta VARCHAR(255),
                fecha_instalacion VARCHAR(20),
                horometro FLOAT,
                fecha_ingreso VARCHAR(20),
                mantencion VARCHAR(255),
                observaciones TEXT,
                proxima_mantencion VARCHAR(20),
                baja TINYINT(1) DEFAULT 0,
                otros TEXT
            )
        ''')
            
        conn.commit()
        conn.close()

    def add_report(self, data):
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
            conn.close()

    def update_report(self, id_reporte, data):
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
            conn.close()

    def delete_report(self, id_reporte):
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
            conn.close()

    def get_reports(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM informes ORDER BY id DESC')
        rows = cursor.fetchall()
        conn.close()
        return rows
