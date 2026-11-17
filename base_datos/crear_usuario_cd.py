import os
import sys
import mysql.connector

from werkzeug.security import generate_password_hash
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_bd import CONFIG_BD


NOMBRE = "Marco Torres"
USUARIO = "marco"
PASSWORD = "recepcion123"
ROL = "Personal de CD"

def main():
    conexion = mysql.connector.connect(**CONFIG_BD)
    cur = conexion.cursor()
    try:
        cur.execute("SELECT id_rol FROM roles WHERE nombre = %s", (ROL,))
        fila = cur.fetchone()
        if fila is None:
            print("No existe el rol. Primero ejecuta base_datos en Workbench.")
            return

        cur.execute("SELECT 1 FROM usuarios WHERE usuario = %s", (USUARIO,))
        if cur.fetchone() is not None:
            print("El usuario ya existe. No se hizo nada.")
            return

        cur.execute("INSERT INTO usuarios (nombre, usuario, password_hash, id_rol) VALUE (%s, %s, %s, %s)",
                    (NOMBRE, USUARIO, generate_password_hash(PASSWORD), fila[0]))
        conexion.commit()
        print("Usuario creado.")
    except Exception as error:
        conexion.rollback()
        print("Error, no se guardo nada:", error)
    finally:
        cur.close()
        conexion.close()

if __name__ == "__main__":
    main()

