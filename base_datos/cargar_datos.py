import os
import sys
import unicodedata
import mysql.connector

# importar config_bd.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_bd import CONFIG_BD
import datos_semilla as semilla

# Valores del ENUM de embarques
ESTATUS_BD = ["En origen", "En transito", "En puerto", "Liberado", "Entregado en CD"]

def sin_acentos(texto):
    normal = unicodedata.normalize("NFD", texto)
    return "".join(ch for ch in normal if unicodedata.category(ch) != "Mn")

def estatus_bd(texto):
    for valido in ESTATUS_BD:
        if sin_acentos(texto).lower() == valido.lower():
            return valido
    raise ValueError("Estatus no reconocido: " + texto)

def borrar_datos(cur):
    for tabla in ["detalle_embarque", "embarques", "productos", "usuarios", "fracciones_arancelarias", "puertos", "roles", "parametros"]:
        cur.execute("DELETE FROM " + tabla)

def cargar (cur):
    # roles
    for nombre in semilla.ROLES:
        cur.execute("INSERT INTO roles (nombre) VALUES (%s)", (nombre,))

    # puertos
    for nombre in semilla.PUERTOS:
        cur.execute("INSERT INTO puertos (nombre) VALUES (%s)", (nombre,))

    # fracciones arancelarias
    for clave, f in semilla.FRACCIONES.items():
        cur.execute("INSERT INTO fracciones_arancelarias (clave, codigo, descripcion, tasa_igi)" "VALUES (%s, %s, %s, %s)",
                    (clave, f["fraccion"], f["descripcion"], f["igi"]))

    # parametros de calculo
    parametros = [
        ("iva", semilla.IVA, None, "Tasa de IVA"),
        ("dta", semilla.DTA, None, "Derecho de tramite aduanero"),
        ("tipo_cambio", semilla.TIPO_CAMBIO, None, "MXN por cada USD"),
        ("dias_libres_puerto", semilla.DIAS_LIBRES_PUERTO, None, "Dias sin cobro de demora"),
        ("costo_demora_dia", semilla.COSTO_DEMORA_DIA, None, "USD por dia de demora"),
        ("fecha_referencia", None, semilla.FECHA_REFERENCIA, "Fecha de hoy de la simulacion"),
    ]
    for clave, num, fecha, descripcion in parametros:
        cur.execute(
            "INSERT INTO parametros (clave, valor_num, valor_fecha, descripcion)"
            "VALUES (%s, %s, %s, %s)", (clave, num, fecha, descripcion)
        )

    # usuarios (buscando el id del rol por su nombre)
    for u in semilla.USUARIOS:
        cur.execute("SELECT id_rol FROM roles WHERE nombre = %s", (u["rol"],))
        id_rol = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO usuarios (nombre, usuario, password_hash, id_rol)"
            "VALUES (%s, %s, %s, %s)",
            (u["nombre"], u["usuario"], u["password_hash"], id_rol)
        )

    # productos (buscando el id de la fraccion por su clave)
    for p in semilla.CATALOGO:
        cur.execute("SELECT id_fraccion FROM fracciones_arancelarias WHERE clave = %s",
                    (p["fraccion_clave"],))
        id_fraccion = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO productos (sku, descripcion, categoria, material, precio_origen, id_fraccion)" \
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (p["sku"], p["descripcion"], p["categoria"], p["material"], p["precio_origen"], id_fraccion)
        )

    # Embarques y su detalle
    for e in semilla.EMBARQUES:
        cur.execute("SELECT id_puerto FROM puertos WHERE nombre = %s", (e["puerto_destino"],))
        id_puerto = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO embarques (id_embarque, contenedor, origen, id_puerto, naviera, "
            "fecha_salida, eta, fecha_arribo, estatus, flete, honorarios)"
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (e["id"], e["contenedor"], e["origen"], id_puerto, e["naviera"],
             e["fecha_salida"], e["eta"], e["fecha_arribo"], estatus_bd(e["estatus"]),
             e["flete"], e["honorarios"])
        )
        for item in e["skus"]:
            cur.execute(
                "INSERT INTO detalle_embarque (id_embarque, sku, cantidad_pedida, cantidad_facturada)"
                "VALUES (%s, %s, %s, %s)",
                (e["id"], item["sku"], item["pedido"], item["factura"])
            )

def main():
    conexion = mysql.connector.connect(**CONFIG_BD)
    cur = conexion.cursor()
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "reiniciar":
            borrar_datos(cur)

        cur.execute("SELECT COUNT(*) FROM roles")
        if cur.fetchone()[0] > 0:
            print("Las tablas ya tienen datos. No se cargo nada.")
            print("Si quieres empezar de nuevo, ejecuta: python base_datos\\cargar_datos.py reiniciar")
            return

        cargar(cur)
        conexion.commit()
        print("Datos cargados correctamente.")
    except Exception as error:
        conexion.rollback()
        print("Error, no se guardo nada:", error)
    finally:
        cur.close()
        conexion.close()

if __name__ == "__main__":
    main()