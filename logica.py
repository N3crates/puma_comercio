# Reglas y calculos

from datetime import datetime
from werkzeug.security import check_password_hash

import datos

# Verificar usuario y contraseña
def verificar_credenciales(usuario, password):
    # Limpiar lo que se escribio
    usuario = (usuario or ""). strip().lower()
    password = password or ""

    for u in datos.USUARIOS:
        if u["usuario"].lower() == usuario:
            if check_password_hash(u["password_hash"], password):
                return u
            return None
    return None

def buscar_embarque(id_embarque):
    for e in datos.EMBARQUES:
        if e["id"] == id_embarque:
            return e
    return None

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
    if contenedor:
        for e in datos.EMBARQUES:
            if e["contenedor"].upper() == contenedor:
                errores.append("El contenedor ya existe.")
                break

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

def registrar_embarque(nuevo):
    errores = validar_datos_embarque(nuevo)
    if errores:
        return None, errores

    numero = len(datos.EMBARQUES) + 1
    embarque = {
        "id": "EMB-" + str(numero).zfill(3),
        "contenedor": nuevo["contenedor"].strip().upper(),
        "origen": nuevo["origen"].strip(),
        "puerto_destino": nuevo["puerto_destino"],
        "naviera": nuevo["naviera"].strip(),
        "fecha_salida": nuevo["fecha_salida"],
        "eta": nuevo["eta"],
        "fecha_arribo": None,
        "estatus": "En origen",
        "flete": float(nuevo["flete"]),
        "honorarios": float(nuevo["honorarios"]),
        "skus": [{"sku": i["sku"], "pedido": i["pedido"], "factura": i["factura"]}
                 for i in nuevo["skus"]]
    }
    datos.EMBARQUES.append(embarque)
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
    hoy = datos.FECHA_REFERENCIA

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
    lista_alertas = []
    con_alertas = 0

    for e in datos.EMBARQUES:
        alertas = calcular_alertas(e)
        if alertas:
            con_alertas += 1
        for a in alertas:
            lista_alertas.append({
                "id": e["id"],
                "contenedor": e["contenedor"],
                "tipo": a["tipo"],
                "gravedad": a["gravedad"],
                "detalle": a["detalle"],
            })
    return{
        "total": len(datos.EMBARQUES),
        "en_transito": sum(1 for e in datos.EMBARQUES if e["estatus"] == datos.ESTATUS[1]),
        "en_puerto": sum(1 for e in datos.EMBARQUES if e["estatus"] == datos.ESTATUS[2]),
        "con_alertas": con_alertas,
        "alertas": lista_alertas,
    }