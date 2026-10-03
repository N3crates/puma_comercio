# Reglas y calculos

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
        return None # Usuario existe pero contraseña incorrecta
    return None    # El usuario no existe