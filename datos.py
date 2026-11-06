import mysql.connector

from config_bd import CONFIG_BD

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
FECHA_REFERENCIA = _PARAMETROS["fecha_referencia"]["valor_fecha"].isoformat()

# Usuarios
def obtener_usuario(usuario):
    filas = _consultar(
        "SELECT u.nombre, u.usuario, u.password_hash, r.nombre AS rol FROM usuarios u JOIN roles r ON r.id_rol = u.id_rol WHERE LOWER(u.usuario) = %s", (usuario.lower(),)
    )
    return filas[0] if filas else None

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

def guardar_embarque(embarque):
    conexion = _conectar()
    cur = conexion.cursor()
    try:
        cur.execute("SELECT MAX(CAST(SUBSTRING(id_embarque, 5) AS UNISIGNED)) FROM embarques")
        mayor = cur.fetchone()[0] or 0
        nuevo_id = "EMB-" + str(mayor + 1).zfill(3)

        cur.execute("SELECT id_puerto FROM puertos WHERE nombre = %s", (embarque["puerto_destino"],))
        id_puerto = cur.fetchone()[0]

        cur.execute(
            "INSERT INTO embarques (id_embarques, contenedor, origen, id_puerto, naviera, " \
            "fecha_salida, eta, fecha_arribo, estatus, flete, honorarios) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (nuevo_id, embarque["contenedor"], embarque["origen"], id_puerto, embarque["naviera"], 
             embarque["fecha_salida"], embarque["eta"], embarque["fecha_arribo"],
             embarque["estatus"], embarque["flete"], embarque["honorarios"])
        )
        for item in embarque["skus"]:
            cur.execute(
                "INSERT INTO detalle_embarque (id_embarque, sku, cantidad_pedida, cantidad_facturada) "
                "VALUES (%s, %s, %s, %s)",
                (nuevo_id, item["sku"], item["pedido"], item["factura"])
            )
        conexion.commit()
        return nuevo_id
    except Exception:
        conexion.rollback()
        raise
    finally:
        cur.close()
        conexion.close()
