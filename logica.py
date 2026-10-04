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
            # check_password_hash compara la contraseña escrita contra el hash guardado
            if check_password_hash(u["password_hash"], password):
                return u
            return None   # el usuario existe pero la contraseña no coincide

    return None           # el usuario no existe