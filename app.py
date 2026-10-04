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
                    return jsonify({"ok": False, "mensaje": [mensaje]}), 403
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
        return jsonify({"ok": False, "mensajes": ["Usuario o contraseña incorrectos"]}), 401

    # Guardamos la sesion 
    session["usuario"] = persona["usuario"]
    session["nombre"] = persona["nombre"]
    session["rol"] = persona["rol"]

    return jsonify({"ok": True, "nombre": persona["nombre"],
                    "rol": persona["rol"],
                    "redirigir": url_for("dashboard"),
                    }), 200

if __name__ == "__main__":
    app.run(debug=True)