# Datos ficticios del sistema, guardados en memoria.

from werkzeug.security import generate_password_hash

# Constantes Generales (Valores ficticios)
IVA = 0.16                      # 16% sobre la base gravable
DTA = 0.008                     # 0.8% Sobre el valor en aduana
TIPO_CAMBIO = 18.00             # MXN por cada USD
FECHA_REFERENCIA = "2026-10-02" # Dia de la simulación
DIAS_LIBRES_PUERTO = 5          # Dias sin cobro de demora
COSTO_DEMORA_DIA = 150          # USD por cada dia de demora

# Catalogos basicos
ROLES = ["Ejecutivo de trafico", "Agente aduanal", "Gerencia / Finanzas", "Administrador"]
ESTATUS = ["En origen", "En transito", "En puerto", "liberado", "Entregado en CD"]
PUERTOS = ["Manzanillo", "Lazaro Cardenas"]

# Usuarios
USUARIOS = [
    {
        "nombre": "Laura Mendez",
        "usuario": "laura",
        "password_hash": generate_password_hash("trafico123"),
        "rol": "Ejecutivo de trafico",
    },
    {
       "nombre": "Carlos Ruiz",
       "usuario": "carlos",
       "password_hash": generate_password_hash("aduana123"),
       "rol": "Agente aduanal", 
    },
    {
        "nombre": "Andrea Solis",
        "usuario": "andrea",
        "password_hash": generate_password_hash("finanzas123"),
        "rol": "Gerencia / Finanzas",
    },
    {
        "nombre": "Administrador",
        "usuario": "admin",
        "password_hash": generate_password_hash("admin123"),
        "rol": "Administrador",        
    },
]

# Fracciones arancelarias
FRACCIONES = {
    "calzado":  {"fraccion": "6404.11.xx", "descripcion": "Calzado deportivo", "igi": 0.20},
    "sudadera": {"fraccion": "6110.20.xx", "descripcion": "Sudaderas de algodón", "igi": 0.25},
    "playera":  {"fraccion": "6109.10.xx", "descripcion": "Playeras de algodón", "igi": 0.20},
    "mochila":  {"fraccion": "4202.92.xx", "descripcion": "Mochilas y accesorios", "igi": 0.15},
}

# Catalogo de productos (SKUs)
CATALOGO = [
    {"sku": "PUM-TEN-001-42-NG", "descripcion": "Tenis Velocity Nitro, talla 42, negro",
     "categoria": "Calzado", "fraccion_clave": "calzado",
     "material": "Suela de goma sintética, malla textil", "precio_origen": 38.50},
    {"sku": "PUM-TEN-002-40-BL", "descripcion": "Tenis RS-X Efekt, talla 40, blanco",
     "categoria": "Calzado", "fraccion_clave": "calzado",
     "material": "Suela de goma sintética, piel sintética", "precio_origen": 52.00},
    {"sku": "PUM-TEN-003-43-AZ", "descripcion": "Tenis Deviate Nitro, talla 43, azul",
     "categoria": "Calzado", "fraccion_clave": "calzado",
     "material": "Suela de espuma, malla textil", "precio_origen": 85.00},
    {"sku": "PUM-TEN-004-39-RJ", "descripcion": "Tenis Carina Street, talla 39, rojo",
     "categoria": "Calzado", "fraccion_clave": "calzado",
     "material": "Suela de goma sintética, piel sintética", "precio_origen": 41.00},
    {"sku": "PUM-SUD-001-M-GR", "descripcion": "Sudadera Essentials, talla M, gris",
     "categoria": "Ropa", "fraccion_clave": "sudadera",
     "material": "Algodón 80%, poliéster 20%", "precio_origen": 18.50},
    {"sku": "PUM-SUD-002-L-NG", "descripcion": "Sudadera Hoodie, talla L, negro",
     "categoria": "Ropa", "fraccion_clave": "sudadera",
     "material": "Algodón 70%, poliéster 30%", "precio_origen": 22.00},
    {"sku": "PUM-PLA-001-M-BL", "descripcion": "Playera Logo, talla M, blanca",
     "categoria": "Ropa", "fraccion_clave": "playera",
     "material": "Algodón 100%", "precio_origen": 8.50},
    {"sku": "PUM-MOC-001-UN-NG", "descripcion": "Mochila Phase, talla única, negro",
     "categoria": "Accesorios", "fraccion_clave": "mochila",
     "material": "Poliéster reciclado", "precio_origen": 14.00},
]

# Enbarques de prueba
# ------------------------------------------------------------------------------
# "pedido" = lo que swe ordeno a la fabrica
# "factura" = lo que la fabrica declaro que envio
# Fechas en formato AAAA-MM-DD. "fecha_arribo" es None si aun no llega al puerto.
# -------------------------------------------------------------------------------
EMBARQUES = [
    # EMB-001: todo coincide, ya liberado -> validacion exitosa
    {
        "id": "EMB-001", "contenedor": "MSKU7345129", "origen": "Ho Chi Minh Vietnam", 
        "puerto_destino": "Manzanillo", "naviera": "maerks", "fecha_salida": "2026-08-20",
        "eta": "2026-09-27", "fecha_arribo": "2026-09-27", "estatus": "liberado", 
        "flete": 4200.00, "honorarios": 650.00,
        "skus": [
            {"sku": "PUM-TEN-001-42-NG", "pedido": 200, "factura": 200},
            {"sku": "PUM-SUD-001-M-GR", "pedido": 150, "factura": 150},
            {"sku": "PUM-PLA-001-M-BL", "pedido": 300, "factura": 300},
        ],
    },

    # EMB-002: un SKU no viene en la factura (factura = 0) -> faltante
    {
        "id": "EMB-002", "contenedor": "TGHU4821067", "origen": "Shangai, China",
        "puerto_destino": "Lazaro Cardenas", "naviera": "MSC", "fecha_salida": "2026-09-10",
        "eta": "2026-10-10", "fecha_arribo": None, "estatus": "En transito",
        "flete": 3800.00, "honorarios": 600.00,
        "skus": [
            {"sku": "PUM-TEN-002-40-BL", "pedido": 120, "factura": 120},
            {"sku": "PUM-SUD-002-L-NG", "pedido": 100, "factura": 100},
            {"sku": "PUM-MOC-001-UN-NG", "pedido": 80, "factura": 0},
        ],
    },

    # EMB-003: Cantidad facturada distinta -> excedente
    {
        "id": "EMB-003", "contenedor": "CMAU6109354", "origen": "yakarta, indonesa",
        "puerto_destino": "Manzanillo", "naviera": "Hapag-Lloyd", "fecha_salida": "2026-10-05",
        "eta": "2026-11-10", "fecha_arribo": None, "estatus": "En origen", "flete": 3500.00,
        "honorarios": 580.00,
        "skus": [
            {"sku": "PUM-TEN-003-43-AZ", "pedido": 90, "factura": 90},
            {"sku": "PUM-PLA-001-M-BL", "pedido": 400, "factura": 420},
        ],
    },

    # EMB-004: en puerto con muchos dias -> alerta de demora
    {
        "id": "EMB-004", "contenedor": "HLXU3392841", "origen": "Ningbo, china",
        "puerto_destino": "Lazaro Cardenas", "naviera": "COSCO", "fecha_salida": "2026-08-25",
        "eta": "2026-09-22", "fecha_arribo": "2026-09-22", "estatus": "En puerto",
        "flete": 5100.00, "honorarios": 720.00,
        "skus": [
            {"sku": "PUM-TEN-001-42-NG", "pedido": 250, "factura": 250},
            {"sku": "PUM-TEN-004-39-RJ", "pedido": 180, "factura": 180},
            {"sku": "PUM-SUD-001-M-GR", "pedido": 120, "factura": 120},
        ],
    },

    # EMB-005: en transito y a tiempo -> rastreo normal
    {
        "id": "EMB-005", "contenedor": "OOLU8204713", "origen": "ho chi minh, vietnam",
        "puerto_destino": "Manzanillo", "naviera": "maersk", "fecha_salida": "2026-09-15",
        "eta": "2026-10-20", "fecha_arribo": None, "estatus": "En transito", "flete": 4000.00,
        "honorarios": 630.00,
        "skus": [
            {"sku": "PUM-SUD-002-L-NG", "pedido": 200, "factura": 200},
            {"sku": "PUM-PLA-001-M-BL", "pedido": 500, "factura": 500},
            {"sku": "PUM-MOC-001-UN-NG", "pedido": 150, "factura": 150},
        ],
    },
]