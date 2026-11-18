import mysql.connector

from config_bd import CONFIG_BD
from datetime import date

ESTATUS = ["En origen", "En transito", "En puerto", "Liberado", "Entregado en CD"]

# Conexion
def _conectar():
    return mysql.connector.connect(**CONFIG_BD)

def _consultar(sql, parametros=()):
    conexion = _conectar()
    cur = conexion.cursor(dictionary=True)
    try:
        cur.execute(sql, parametros)
        return cur.fetchall()
    finally:
        cur.close()
        conexion.close()

def _numero(valor):
    numero = float(valor)
    return int(numero) if numero.is_integer() else numero

# Catalogo y constantes
ROLES = [f["nombre"] for f in _consultar("SELECT nombre FROM roles ORDER BY id_rol")]

PUERTOS = [f["nombre"] for f in _consultar("SELECT nombre FROM puertos ORDER BY id_puerto")]

FRACCIONES = {}
for _f in _consultar("SELECT clave, codigo, descripcion, tasa_igi FROM fracciones_arancelarias"):
    FRACCIONES[_f["clave"]] = {
        "fraccion": _f["codigo"],
        "descripcion": _f["descripcion"],
        "igi": float(_f["tasa_igi"]),
    }

CATALOGO = []
for _p in _consultar(
        "SELECT p.sku, p.descripcion, p.categoria, p.material, p.precio_origen, f.clave "
        "FROM productos p JOIN fracciones_arancelarias f ON f.id_fraccion = p.id_fraccion "
        "ORDER BY p.sku"):
    CATALOGO.append({
        "sku": _p["sku"],
        "descripcion": _p["descripcion"],
        "categoria": _p["categoria"],
        "fraccion_clave": _p["clave"],
        "material": _p["material"],
        "precio_origen": float(_p["precio_origen"]),
    })

# Parametros de calculo
_PARAMETROS = {}
for _r in _consultar("SELECT clave, valor_num, valor_fecha FROM parametros"):
    _PARAMETROS[_r["clave"]] = _r

IVA = float(_PARAMETROS["iva"]["valor_num"])
DTA = float(_PARAMETROS["dta"]["valor_num"])
TIPO_CAMBIO = _numero(_PARAMETROS["tipo_cambio"]["valor_num"])
DIAS_LIBRES_PUERTO = _numero(_PARAMETROS["dias_libres_puerto"]["valor_num"])
COSTO_DEMORA_DIA = _numero(_PARAMETROS["costo_demora_dia"]["valor_num"])

# Usuarios
def obtener_usuario(usuario):
    sql = "SELECT u.nombre, u.usuario, u.password_hash, r.nombre AS rol, u.activo FROM usuarios u JOIN roles r ON r.id_rol = u.id_rol WHERE LOWER(u.usuario) = %s"
    filas = _consultar(sql, ((usuario or "").lower(),))
    if not filas:
        return None

    persona = filas[0]
    persona["activo"] = bool(persona["activo"])
    return persona

# Embarques 
_SQL_EMBARQUES = (
    "SELECT e.id_embarque, e.contenedor, e.origen, p.nombre AS puerto_destino, e.naviera, "
    "e.fecha_salida, e.eta, e.fecha_arribo, e.estatus, e.flete, e.honorarios "
    "FROM embarques e JOIN puertos p ON p.id_puerto = e.id_puerto "
)

def _armar_embarque(f, skus):
    return{
        "id": f["id_embarque"],
        "contenedor": f["contenedor"],
        "origen": f["origen"],
        "puerto_destino": f["puerto_destino"],
        "naviera": f["naviera"],
        "fecha_salida": f["fecha_salida"].isoformat(),
        "eta": f["eta"].isoformat(),
        "fecha_arribo": f["fecha_arribo"].isoformat() if f["fecha_arribo"] else None,
        "estatus": f["estatus"],
        "flete": float(f["flete"]),
        "honorarios": float(f["honorarios"]),
        "skus": skus,
    }

def listar_embarques():
    detalle = {}
    sql_detalle = "SELECT id_embarque, sku, cantidad_pedida, cantidad_facturada FROM detalle_embarque ORDER BY id_detalle"
    for d in _consultar(sql_detalle):
        detalle.setdefault(d["id_embarque"], []).append({
            "sku": d["sku"],
            "pedido": d["cantidad_pedida"],
            "factura": d["cantidad_facturada"],
        })

    filas = _consultar(_SQL_EMBARQUES + "ORDER BY e.id_embarque")
    return [_armar_embarque(f, detalle.get(f["id_embarque"], [])) for f in filas]


def obtener_embarque(id_embarque):
    filas = _consultar(_SQL_EMBARQUES + "WHERE e.id_embarque = %s", (id_embarque,))
    if not filas:
        return None

    sql_detalle = "SELECT sku, cantidad_pedida, cantidad_facturada FROM detalle_embarque WHERE id_embarque = %s ORDER BY id_detalle"
    skus = [{"sku": d["sku"], "pedido": d["cantidad_pedida"], "factura": d["cantidad_facturada"]}
            for d in _consultar(sql_detalle, (id_embarque,))]
    return _armar_embarque(filas[0], skus)

def existe_contenedor(contenedor):
    filas = _consultar("SELECT 1 AS existe FROM embarques WHERE UPPER(contenedor) = %s",
                       (contenedor.strip().upper(),))
    return len(filas) > 0

def guardar_embarque(embarque, id_usuario=None):
    conexion = _conectar()
    cur = conexion.cursor()
    try:
        cur.execute("SELECT MAX(CAST(SUBSTRING(id_embarque, 5) AS UNSIGNED)) FROM embarques")
        mayor = cur.fetchone()[0] or 0
        nuevo_id = "EMB-" + str(mayor + 1).zfill(3)

        cur.execute("SELECT id_puerto FROM puertos WHERE nombre = %s", (embarque["puerto_destino"],))
        id_puerto = cur.fetchone()[0]

        sql_embarque = "INSERT INTO embarques (id_embarque, contenedor, origen, id_puerto, naviera, fecha_salida, eta, fecha_arribo, estatus, flete, honorarios) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cur.execute(sql_embarque, (nuevo_id, embarque["contenedor"], embarque["origen"], id_puerto, 
                                   embarque["naviera"], embarque["fecha_salida"], embarque["eta"],
                                   embarque["fecha_arribo"], embarque["estatus"],
                                   embarque["flete"], embarque["honorarios"]))

        sql_detalle = "INSERT INTO detalle_embarque (id_embarque, sku, cantidad_pedida, cantidad_facturada) VALUES (%s, %s, %s, %s)"
        for item in embarque["skus"]:
            cur.execute(sql_detalle, (nuevo_id, item["sku"], item["pedido"], item["factura"]))

        sql_historial = "INSERT INTO historial_estatus (id_embarque, estatus, fecha_cambio, id_usuario, comentario) VALUES (%s, %s, %s, %s, %s)"
        cur.execute(sql_historial, (nuevo_id, embarque["estatus"], embarque["fecha_salida"], id_usuario, "Embarque registrado"))

        conexion.commit()
        return nuevo_id
    except Exception:
        conexion.rollback()
        raise
    finally:
        cur.close()
        conexion.close()

def fecha_referencia():
    filas = _consultar("SELECT valor_fecha FROM parametros WHERE clave = 'fecha_simulacion'")
    if filas and filas[0]["valor_fecha"]:
        return filas[0]["valor_fecha"].isoformat()
    return date.today().isoformat()

def obtener_id_usuario(usuario):
    filas = _consultar("SELECT id_usuario FROM usuarios WHERE LOWER(usuario) = %s", ((usuario or "").lower(),))
    return filas[0]["id_usuario"] if filas else None

def listar_historial(id_embarque):
    sql = "SELECT h.estatus, h.fecha_cambio, u.nombre AS usuario, h.comentario FROM historial_estatus h LEFT JOIN usuarios u ON u.id_usuario = h.id_usuario WHERE h.id_embarque = %s ORDER BY h.fecha_cambio, h.id_historial"
    resultado = []
    for f in _consultar(sql, (id_embarque,)):
        resultado.append({
            "estatus": f["estatus"],
            "fecha": f["fecha_cambio"].isoformat(),
            "usuario": f["usuario"] or "Sistema",
            "comentario": f["comentario"] or "",
        })
    return resultado

def cambiar_estatus(id_embarque, nuevo_estatus, fecha, id_usuario, comentario):
    conexion = _conectar()
    cur = conexion.cursor()
    try:
        if nuevo_estatus == ESTATUS[2]:
            cur.execute("UPDATE embarques SET estatus = %s, fecha_arribo = %s WHERE id_embarque = %s", (nuevo_estatus, fecha, id_embarque))
        else:
            cur.execute("UPDATE embarques SET estatus = %s WHERE id_embarque = %s", (nuevo_estatus, id_embarque))

        cur.execute("INSERT INTO historial_estatus (id_embarque, estatus, fecha_cambio, id_usuario, comentario) VALUES (%s, %s, %s, %s, %s)", (id_embarque, nuevo_estatus, fecha, id_usuario, comentario or None))
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        cur.close()
        conexion.close()

# Rastreo
def obtener_id_contenedor(contenedor):
    filas = _consultar("SELECT id_embarque FROM embarques WHERE UPPER(contenedor) = %s", ((contenedor or "").strip().upper(),))
    return filas[0]["id_embarque"] if filas else None

def listar_embarques_sku(sku):
    sql = "SELECT id_embarque, cantidad_pedida, cantidad_facturada FROM detalle_embarque WHERE sku = %s ORDER BY id_embarque"
    return [{"id": f["id_embarque"], "pedido": f["cantidad_pedida"], "factura": f["cantidad_facturada"]}
            for f in _consultar(sql, (sku,))]

# Edicion y eliminacion de embarques
def actualizar_embarque(id_embarque, cambios):
    conexion = _conectar()
    cur = conexion.cursor()
    try:
        cur.execute("SELECT id_puerto FROM puertos WHERE nombre = %s", (cambios["puerto_destino"],))
        id_puerto = cur.fetchone()[0]
        sql = "UPDATE embarques SET origen = %s, id_puerto = %s, naviera = %s, fecha_salida = %s, eta = %s, flete = %s, honorarios = %s WHERE id_embarque = %s"
        cur.execute(sql, (cambios["origen"], id_puerto, cambios["naviera"], cambios["fecha_salida"],
                          cambios["eta"], cambios["flete"], cambios["honorarios"], id_embarque))

        cur.execute("DELETE FROM detalle_embarque WHERE id_embarque = %s", (id_embarque,))
        sql_detalle = "INSERT INTO detalle_embarque (id_embarque, sku, cantidad_pedida, cantidad_facturada) VALUES (%s, %s, %s, %s)"
        for item in cambios["skus"]:
            cur.execute(sql_detalle, (id_embarque, item["sku"], item["pedido"], item["factura"]))
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        cur.close()
        conexion.close()

def eliminar_embarque(id_embarque):
    conexion = _conectar()
    cur = conexion.cursor()
    try:
        cur.execute("DELETE FROM embarques WHERE id_embarque = %s", (id_embarque,))
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        cur.close()
        conexion.close()

# Recepcion en el centro de distribucion
def obtener_recepcion(id_embarque):
    sql = "SELECT r.id_recepcion, r.fecha_recepcion, r.observaciones, u.nombre AS usuario FROM recepciones r LEFT JOIN usuarios u ON u.id_usuario = r.id_usuario WHERE r.id_embarque = %s"
    filas = _consultar(sql, (id_embarque,))
    if not filas:
        return None

    r = filas[0]
    detalle = {}
    sql_detalle = "SELECT sku, cantidad_recibida, cantidad_danada FROM recepcion_detalle WHERE id_recepcion = %s"
    for d in _consultar(sql_detalle, (r["id_recepcion"],)):
        detalle[d["sku"]] = {"recibida": d["cantidad_recibida"], "danada": d["cantidad_danada"]}

    return{
        "fecha": r["fecha_recepcion"].isoformat(),
        "observaciones": r["observaciones"] or "",
        "usuario": r["usuario"] or "Sistema",
        "filas": detalle,
    }

def guardar_recepcion(id_embarque, fecha, id_usuario, observaciones, filas):
    conexion = _conectar()
    cur = conexion.cursor()
    try:
        sql_rec = "INSERT INTO recepciones (id_embarque, fecha_recepcion, id_usuario, observaciones) VALUES (%s, %s, %s, %s)"
        cur.execute(sql_rec, (id_embarque, fecha, id_usuario, observaciones or None))
        id_recepcion = cur.lastrowid
        sql_det = "INSERT INTO recepcion_detalle (id_recepcion, sku, cantidad_recibida, cantidad_danada) VALUES (%s, %s, %s, %s)"
        for f in filas:
            cur.execute(sql_det, (id_recepcion, f["sku"], f["recibida"], f["danada"]))

        cur.execute("UPDATE embarques SET estatus = %s WHERE id_embarque = %s", (ESTATUS[4], id_embarque))
        sql_hist = "INSERT INTO historial_estatus (id_embarque, estatus, fecha_cambio, id_usuario, comentario) VALUES (%s, %s, %s, %s, %s)"
        cur.execute(sql_hist, (id_embarque, ESTATUS[4], fecha, id_usuario, "Recepcion registrada en el CD"))
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        cur.close()
        conexion.close()

# Gestion de usuarios
def listar_usuarios():
    sql = "SELECT u.id_usuario, u.nombre, u.usuario, r.nombre AS rol, u.activo FROM usuarios u JOIN roles r ON r.id_rol = u.id_rol ORDER BY u.id_usuario"
    return [{"nombre": f["nombre"], "usuario": f["usuario"], "rol": f["rol"], "activo": bool(f["activo"])}
            for f in _consultar(sql)]

def contar_administradores_activos():
    sql = "SELECT COUNT(*) AS n FROM usuarios u JOIN roles r ON r.id_rol = u.id_rol WHERE r.nombre = %s AND u.activo = 1"
    return _consultar(sql, ("Administrador",))[0]["n"]

def _id_rol(cur, nombre_rol):
    cur.execute("SELECT id_rol FROM roles WHERE nombre = %s", (nombre_rol,))
    return cur.fetchone()[0]

def crear_usuario(nombre, usuario, password_hash, rol):
    conexion = _conectar()
    cur = conexion.cursor()
    try:
        sql = "INSERT INTO usuarios (nombre, usuario, password_hash, id_rol, activo) VALUES (%s, %s, %s, %s, 1)"
        cur.execute(sql, (nombre, usuario, password_hash, _id_rol(cur, rol)))
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        cur.close()
        conexion.close()

def actualizar_usuario(usuario, nombre, rol):
    conexion = _conectar()
    cur = conexion.cursor()
    try:
        sql = "UPDATE usuarios SET nombre = %s, id_rol = %s WHERE LOWER(usuario) = %s"
        cur.execute(sql, (nombre, _id_rol(cur, rol), usuario.lower()))
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        cur.close()
        conexion.close()

def actualizar_password(usuario, password_hash):
    conexion = _conectar()
    cur = conexion.cursor()
    try:
        cur.execute("UPDATE usuarios SET password_hash = %s WHERE LOWER(usuario) = %s", (password_hash, usuario.lower()))
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        cur.close()
        conexion.close()

def cambiar_estado_usuario(usuario, activo):
    conexion = _conectar()
    cur = conexion.cursor()
    try:
        cur.execute("UPDATE usuarios SET activo = %s WHERE LOWER(usuario) = %s", (1 if activo else 0, usuario.lower()))
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        cur.close()
        conexion.close()