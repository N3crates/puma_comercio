# Servidor Flask

from functools import wraps
from flask import Flask, jsonify, redirect, render_template, request, session, url_for

import datos
import logica

app = Flask(__name__)

app.secret_key = "clave-secreta-simulacion-puma"

# Control de acceso
def rol_requerido(*roles_permetidos):
    def decorador(funcion):
        @wraps(funcion)
        def envoltura(*args, **kwargs):
            es_api = request.path.startswith("/api/")

            # Hay sesion iniciada
            if "usuario" not in session:
                if es_api:
                    return jsonify({"ok": False, "mensajes": ["Debes iniciar sesión."]}), 401
                return redirect(url_for("login"))

            # El rol tiene permiso
            rol = session["rol"]
            if rol != "Administrador" and rol not in roles_permetidos:
                mensaje = "Acceso no permitido para tu rol."
                if es_api:
                    return jsonify({"ok": False, "mensajes": [mensaje]}), 403
                return mensaje, 403

            # Todo bien: Se ejecuta la ruta original
            return funcion(*args, **kwargs)
        return envoltura
    return decorador

# Rurtas de paginas
@app.route("/")
def index():
    if "usuario" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login")
def login():
    if "usuario" in session:
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
@rol_requerido(*datos.ROLES)
def dashboard():
    return render_template("dashboard.html")

# Rutas de API
@app.route("/api/login", methods=["POST"])
def api_login():
    # Datos que envia el navegador con fetch
    datos_recibidos = request.get_json(silent=True) or {}
    usuario = datos_recibidos.get("usuario", "")
    password = datos_recibidos.get("password", "")

    persona = logica.verificar_credenciales(usuario, password)

    if persona is None:
        return jsonify({"ok": False, "mensajes": ["Usuario o contraseña incorrectos."]}), 401

    # Guardamos la sesion 
    session["usuario"] = persona["usuario"]
    session["nombre"] = persona["nombre"]
    session["rol"] = persona["rol"]

    return jsonify({"ok": True, "nombre": persona["nombre"],
                    "rol": persona["rol"],
                    "redirigir": url_for("dashboard"),
                    }), 200

# Rutas de pagina: registro y validación
@app.route("/registrar")
@rol_requerido("Ejecutivo de trafico")
def registrar():
    return render_template("registrar.html")

@app.route("/validacion")
@rol_requerido("Ejecutivo de trafico")
def validacion():
    return render_template("validacion.html")

# Rutas de API: Catalogo y embarques
@app.route("/api/catalogo")
@rol_requerido("Ejecutivo de trafico")
def api_catalogo():
    return jsonify({"ok": True, "catalogo": datos.CATALOGO}), 200

@app.route("/api/embarques", methods=["GET"])
@rol_requerido(*datos.ROLES)
def api_embarques():
    estatus = request.args.get("estatus", "").strip()
    buscar = request.args.get("buscar", "").strip().upper()

    resultado = []
    for e in datos.EMBARQUES:
        if estatus and e["estatus"] != estatus:
            continue
        if buscar and buscar not in e["contenedor"].upper():
            continue
        resultado.append(e)

    return jsonify({"ok": True, "embarques": resultado}), 200

@app.route("/api/embarques", methods = ["POST"])
@rol_requerido("Ejecutivo de trafico")
def api_registrar_embarque():
    recibido = request.get_json(silent=True) or {}
    embarque, errores = logica.registrar_embarque(recibido)

    if errores:
        # Si el problema es un contenedor repetido (409)
        codigo = 409 if "El contenedor ya existe." in errores else 400
        return jsonify({"ok": False, "mensajes": errores}), codigo

    return jsonify({
        "ok": True,
        "id": embarque["id"],
        "mensajes": ["Embarque " + embarque["id"] + " registrado correctamente."],
    }), 201

@app.route("/api/embarques/<id_embarque>/validacion")
@rol_requerido("Ejecutivo de trafico")
def api_validacion(id_embarque):
    resultado = logica.validar_embarque(id_embarque)

    if resultado is None:
        return jsonify({"ok": False, "mensajes": ["El embarque no existe."]}), 404
    
    return jsonify({"ok": True, "validacion": resultado}), 200

# Costeo
@app.route("/costeo")
@rol_requerido("Agente aduanal", "Gerencia / Finanzas")
def costeo():
    return render_template("costeo.html")

@app.route("/api/embarques/<id_embarque>/costeo")
@rol_requerido("Agente aduanal", "Gerencia / Finanzas")
def api_costeo(id_embarque):
    resultado = logica.calcular_costeo(id_embarque)

    if resultado is None:
        return jsonify({"ok": False, "mensajes": ["El embarque no existe."]}), 404

    return jsonify({"ok": True, "costeo": resultado}), 200

@app.route("/api/dashboard")
@rol_requerido(*datos.ROLES)
def api_dashboard():
    return jsonify({"ok": True, "resumen": logica.resumen_dashboard()}), 200

@app.route("/embarques")
@rol_requerido(*datos.ROLES)
def embarques():
    return render_template("embarques.html", estatus = datos.ESTATUS)

if __name__ == "__main__":
    app.run(debug=True)