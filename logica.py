# Reglas y calculos

from datetime import datetime
from werkzeug.security import check_password_hash

import traceback
import datos

# Verificar usuario y contraseña
def verificar_credenciales(usuario, password):
    usuario = (usuario or "").strip().lower()
    password = password or ""

    if usuario == "":
        return None

    persona = datos.obtener_usuario(usuario)
    if persona is None:
        return None

    if check_password_hash(persona["password_hash"], password):
        return persona

    return None

def buscar_embarque(id_embarque):
    return datos.obtener_embarque(id_embarque)

def validar_embarque(id_embarque):
    embarque = buscar_embarque(id_embarque)
    if embarque is None:
        return None

    filas = []
    discrepancias = 0

    for item in embarque["skus"]:
        pedido = item["pedido"]
        factura = item["factura"]
        diferencia = factura - pedido

        if diferencia == 0:
            estado = "Coincide"
        elif diferencia < 0:
            estado = "Faltante"
        else:
            estado = "Excedente"

        if estado != "Coincide":
            discrepancias += 1

        filas.append({
            "sku": item["sku"],
            "pedido": pedido,
            "factura": factura,
            "diferencia": diferencia,
            "estado": estado,
        })

    return { "id": embarque["id"], "contenedor": embarque["contenedor"], "filas": filas,
            "discrepancias": discrepancias, "validado": discrepancias == 0,}

def _fecha_valida(texto):
    try:
        datetime.strptime(texto, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False

def _numero_no_negativo(valor):
    try:
        numero = float(valor)
    except (ValueError, TypeError):
        return None
    return numero if numero >= 0 else None

def validar_datos_embarque(nuevo):
    errores = []

    # Campos de texto obligatorios
    campos = [("contenedor", "El contenedor"), ("origen", "El origen"),
              ("puerto_destino", "El puerto de destino"), ("naviera", "La naviera")]

    for clave, nombre in campos:
        if not str(nuevo.get(clave, "")).strip():
            errores.append(nombre + " es obligatorio.")

    # Contenedor repetido (sin distinguir mayusculas)
    contenedor = str(nuevo.get("contenedor", "")).strip().upper()
    if contenedor and datos.existe_contenedor(contenedor):
        errores.append("El contenedor ya existe.")

    # Puerto valido
    if nuevo.get("puerto_destino") and nuevo["puerto_destino"] not in datos.PUERTOS:
        errores.append("El puerto de destino no es valido.")

    # Fechas
    salida = nuevo.get("fecha_salida")
    eta = nuevo.get("eta")
    if not _fecha_valida(salida):
        errores.append("La fecha de salida no es valida.")
    if not _fecha_valida(eta):
        errores.append("La fecha de ETA no es valida.")
    if _fecha_valida(salida) and _fecha_valida(eta) and eta <= salida:
        errores.append("El ETA debe ser posterior a la fecha de salida.")

    # flete y honorarios
    if _numero_no_negativo(nuevo.get("flete")) is None:
        errores.append("El flete debe de ser un numero mayor o igaul a 0.")
    if _numero_no_negativo(nuevo.get("honorarios")) is None:
        errores.append("Los honorarios deben de ser un numero mayor o igual a 0.")

    # SKUs
    skus = nuevo.get("skus")
    if not isinstance(skus, list) or len(skus) == 0:
        errores.append("Debes agregar al menos un SKU.")
    else:
        catalogo = [p["sku"] for p in datos.CATALOGO]
        vistos = []
        for item in skus:
            sku = item.get("sku")
            if sku not in catalogo:
                errores.append("El SKU " + str(sku) + " no existe en el catalogo.")
            elif sku in vistos:
                errores.append("El sku " + sku + " esta repetido.")
            vistos.append(sku)

            for campo in ("pedido", "factura"):
                valor = item.get(campo)
                if not isinstance(valor, int) or isinstance(valor, bool) or valor < 0:
                    errores.append("Cantidad de " + campo + " invalida en " + str(sku) + ".")

    return errores

def registrar_embarque(nuevo, usuario=None):
    errores = validar_datos_embarque(nuevo)
    if errores:
        return None, errores

    embarque = {
        "contenedor": nuevo["contenedor"].strip().upper(),
        "origen": nuevo["origen"].strip(),
        "puerto_destino": nuevo["puerto_destino"],
        "naviera": nuevo["naviera"].strip(),
        "fecha_salida": nuevo["fecha_salida"],
        "eta": nuevo["eta"],
        "fecha_arribo": None,
        "estatus": datos.ESTATUS[0],
        "flete": float(nuevo["flete"]),
        "honorarios": float(nuevo["honorarios"]),
        "skus": [{"sku": i["sku"], "pedido": i["pedido"], "factura": i["factura"]}
                 for i in nuevo["skus"]],
    }
    try:
        id_usuario = datos.obtener_id_usuario(usuario) if usuario else None
        embarque["id"] = datos.guardar_embarque(embarque, id_usuario)
    except Exception:
        return None, ["No se pudo guardar el embarque en la base de datos."]
    return embarque, []
    
# Costeo
def _producto(sku):
    for p in datos.CATALOGO:
        if p["sku"] == sku:
            return p
    return None

def calcular_costeo(id_embarque):
    embarque = buscar_embarque(id_embarque)
    if embarque is None:
        return None

    items = []
    for item in embarque["skus"]:
        if item["factura"] > 0:
            producto = _producto(item["sku"])
            valor_origen = producto["precio_origen"] * item["factura"]
            items.append((item, producto, valor_origen))

    total_origen = sum(i[2] for i in items)
    filas = []
    total_aterrizado = 0.0

    for item, producto, valor_origen in items:
        proporcion = valor_origen / total_origen if total_origen > 0 else 0
        flete = embarque["flete"] * proporcion
        honorarios = embarque["honorarios"] * proporcion
        valor_aduana = valor_origen + flete

        fraccion = datos.FRACCIONES[producto["fraccion_clave"]]
        igi = valor_aduana * fraccion["igi"]
        dta = valor_aduana * datos.DTA
        iva = (valor_aduana + igi + dta) * datos.IVA

        aterrizado = valor_origen + flete + honorarios + igi + dta
        por_pieza = aterrizado / item["factura"]
        total_aterrizado += aterrizado

        filas.append({
            "sku": item["sku"],
            "cantidad": item["factura"],
            "fraccion": fraccion["fraccion"],
            "tasa_igi": fraccion["igi"],
            "valor_origen": round(valor_origen, 2),
            "flete": round(flete, 2),
            "honorarios": round(honorarios, 2),
            "igi": round(igi, 2),
            "dta": round(dta, 2),
            "iva": round(iva, 2),
            "aterrizado": round(aterrizado, 2),
            "por_pieza_usd": round(por_pieza, 2),
            "por_pieza_mxn": round(por_pieza * datos.TIPO_CAMBIO, 2),
        })

    validacion = validar_embarque(id_embarque)
    return{
        "id": embarque["id"],
        "contenedor": embarque["contenedor"],
        "filas": filas,
        "total_usd": round(total_aterrizado, 2),
        "total_mxn": round(total_aterrizado * datos.TIPO_CAMBIO, 2),
        "tipo_cambio": datos.TIPO_CAMBIO,
        "discrepancias": validacion["discrepancias"],
    }

# Alertas y dashboard
def _dias_entre(fecha_inicio, fecha_fin):
    inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
    return (fin - inicio).days

def calcular_alertas(embarque):
    alertas = []
    hoy = datos.fecha_referencia()

    en_transito = datos.ESTATUS[1]
    en_puerto = datos.ESTATUS[2]

    if embarque["estatus"] == en_puerto and embarque["fecha_arribo"]:
        dias = _dias_entre(embarque["fecha_arribo"], hoy)
        dias_demora = max(0, dias - datos.DIAS_LIBRES_PUERTO)
        if dias_demora > 0:
            costo = dias_demora * datos.COSTO_DEMORA_DIA
            alertas.append({
                "tipo": "Demora en puerto",
                "gravedad": "Alta",
                "detalle": str(dias) + " días en puerto, " + str(dias_demora) +
                           " con cobro (USD " + str(costo) + ")",
            })
        elif dias >= 3:
            alertas.append({
                "tipo": "Riesgo de demora",
                "gravedad": "Media",
                "detalle": str(dias) + " días en puerto, cerca del límite de " +
                           str(datos.DIAS_LIBRES_PUERTO),
            })

    if embarque["estatus"] == en_transito and embarque["eta"] < hoy:
        retraso = _dias_entre(embarque["eta"], hoy)
        alertas.append({
            "tipo": "Retraso en tránsito",
            "gravedad": "Media",
            "detalle": "El ETA ya pasó hace " + str(retraso) + " día(s)",
        })

    validacion = validar_embarque(embarque["id"])
    if validacion["discrepancias"] > 0:
        alertas.append({
            "tipo": "Discrepancia en documentos",
            "gravedad": "Media",
            "detalle": str(validacion["discrepancias"]) + " SKU(s) no coinciden con la factura",
        })
    return alertas

def resumen_dashboard():
    embarques = datos.listar_embarques()
    listar_alertas = []
    con_alertas = 0

    for e in embarques:
        alertas = calcular_alertas(e)
        if alertas:
            con_alertas += 1
        for a in alertas:
            listar_alertas.append({
                "id": e["id"],
                "contenedor": e["contenedor"],
                "tipo": a["tipo"],
                "gravedad": a["gravedad"],
                "detalle": a["detalle"],
            })

    return {
        "total": len(embarques),
        "en_transito": sum(1 for e in embarques if e["estatus"] == datos.ESTATUS[1]),
        "en_puerto": sum(1 for e in embarques if e["estatus"] == datos.ESTATUS[2]),
        "con_alertas": con_alertas, "alertas": listar_alertas,
    }

PERMISOS_ESTATUS = {
    "Ejecutivo de trafico": ["En transito", "En puerto", "Entregado en CD"],
    "Agente aduanal": ["Liberado"],
}

def siguiente_estatus(estatus):
    lista = datos.ESTATUS
    if estatus not in lista:
        return None

    posicion = lista.index(estatus)
    if posicion + 1 >= len(lista):
        return None
    return lista[posicion + 1]

def rol_puede_asignar(rol, estatus):
    if rol == "Administrador":
        return True
    return estatus in PERMISOS_ESTATUS.get(rol, [])

def cambiar_estatus(id_embarque, nuevo, fecha, comentario, rol, usuario):
    embarque = buscar_embarque(id_embarque)
    if embarque is None:
        return None, ["El embarque no existe."], 404

    nuevo = (nuevo or "").strip()
    comentario = (comentario or "").strip()

    siguiente = siguiente_estatus(embarque["estatus"])
    if siguiente is None:
        return None, ["El embarque ya esta en el ultimo estatus."], 400
    if nuevo != siguiente:
        return None, ["Solo se puede avanzar al siguiente estatus: " + siguiente + "."], 400
    if not rol_puede_asignar(rol, nuevo):
        return None, ["Tu rol no puede asignar el estatus " + nuevo + "."], 403

    errores = []
    if not _fecha_valida(fecha):
        errores.append("La fecha no es valida.")
    else:
        historial = datos.listar_historial(id_embarque)
        minima = historial[-1]["fecha"] if historial else embarque["fecha_salida"]
        if fecha < minima:
            errores.append("La fecha no puede ser anterior a " + minima + ".")
        if fecha > datos.fecha_referencia():
            errores.append("La fecha no puede ser futura.")
    if len(comentario) > 200:
        errores.append("El comentario no puede pasar de 200 caracteres.")
    if errores:
        return None, errores, 400

    try:
        id_usuario = datos.obtener_id_usuario(usuario)
        datos.cambiar_estatus(id_embarque, nuevo, fecha, id_usuario, comentario)
    except Exception:
        traceback.print_exc()
        return None, ["No se pudo guardar el cambio en la base de datos."], 500

    return {"id": id_embarque, "estatus": nuevo}, [], 200

# Rastreo
def _fecha_estatus(historial, estatus):
    fecha = None
    for h in historial:
        if h["estatus"] == estatus:
            fecha = h["fecha"]
    return fecha

def calcular_ficha_rastreo(embarque):
    hoy = datos.fecha_referencia()
    historial = datos.listar_historial(embarque["id"])
    lista = datos.ESTATUS
    posicion = lista.index(embarque["estatus"])

    # Dias en transito
    dias_transito = 0
    if posicion > 0:
        fin = embarque["fecha_arribo"] or hoy
        dias_transito = max(0, _dias_entre(embarque["fecha_salida"], fin))

    # Dias en puerto
    dias_puerto = 0
    if embarque["fecha_arribo"]:
        fin = hoy
        if posicion >= 3:
            fin = _fecha_estatus(historial, lista[3]) or hoy
        dias_puerto = max(0, _dias_entre(embarque["fecha_arribo"], fin))

    dias_demora = max(0, dias_puerto - datos.DIAS_LIBRES_PUERTO)
    costo_demora = dias_demora * datos.COSTO_DEMORA_DIA

    # ETA
    if posicion < 2:
        dias_eta = _dias_entre(hoy, embarque["eta"])
        if dias_eta >= 0:
            texto_eta = "Faltan " + str(dias_eta) + " dia(s) para el ETA."
        else:
            texto_eta = "Retraso de " + str(-dias_eta) + " dia(s) respecto al ETA."
    else:
        texto_eta = "El contenedor ya llego a puerto."

    # Linea de tiempo
    linea = []
    for i, nombre in enumerate(lista):
        registro = None
        for h in historial:
            if h["estatus"] == nombre:
                registro = h
        if i < posicion:
            estado = "completado"
        elif i == posicion:
            estado = "actual"
        else:
            estado = "pendiente"
            registro = None
        linea.append({
            "estatus": nombre,
            "estado": estado,
            "fecha": registro["fecha"] if registro else "",
            "usuario": registro["usuario"] if registro else "",
            "comentario": registro["comentario"] if registro else "",
        })

    # Producto del embarque 
    productos = []
    for item in embarque["skus"]:
        p = _producto(item["sku"])
        productos.append({
            "sku": item["sku"],
            "descripcion": p["descripcion"] if p else "",
            "cantidad": item["factura"],
        })

    return {
        "id": embarque["id"],
        "contenedor": embarque["contenedor"],
        "origen": embarque["origen"],
        "puerto_destino": embarque["puerto_destino"],
        "naviera": embarque["naviera"],
        "estatus": embarque["estatus"],
        "fecha_salida": embarque["fecha_salida"],
        "eta": embarque["eta"],
        "fecha_arribo": embarque["fecha_arribo"],
        "dias_transito": dias_transito,
        "dias_puerto": dias_puerto,
        "dias_demora": dias_demora,
        "costo_demora": costo_demora,
        "texto_eta": texto_eta,
        "alertas": calcular_alertas(embarque),
        "linea_tiempo": linea,
        "productos": productos,
    }

def buscar_rastreo(contenedor, sku):
    contenedor = (contenedor or "").strip().upper()
    sku = (sku or "").strip()
    if not contenedor and not sku:
        return None, ["Escribe un contenedor o elige un SKU."]

    cantidades = {}
    if sku:
        for r in datos.listar_embarques_sku(sku):
            cantidades[r["id"]] = r["factura"]

    resultado = []
    for e in datos.listar_embarques():
        if sku and e["id"] not in cantidades:
            continue
        if contenedor and contenedor not in e["contenedor"].upper():
            continue
        resultado.append({
            "id": e["id"],
            "contenedor": e["contenedor"],
            "puerto_destino": e["puerto_destino"],
            "estatus": e["estatus"],
            "eta": e["eta"],
            "cantidad": cantidades.get[e["id"]] if sku else sum(i["factura"] for i in e["skus"]),
        })
    return resultado, []

def ficha_rastreo(contenedor):
    id_embarque = datos.obtener_id_contenedor(contenedor)
    if id_embarque is None:
        return None
    return calcular_ficha_rastreo(buscar_embarque(id_embarque))