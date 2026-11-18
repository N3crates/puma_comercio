const formAlta = document.getElementById("form-alta")
const altaNombre = document.getElementById("alta-nombre")
const altaUsuario = document.getElementById("alta-usuario")
const altaPassword = document.getElementById("alta-password")
const altaRol = document.getElementById("alta-rol")
const panelEditar = document.getElementById("panel-editar")
const tituloEditar = document.getElementById("titulo-editar")
const editarNombre = document.getElementById("editar-nombre")
const editarRol = document.getElementById("editar-rol")
const panelPassword = document.getElementById("panel-password")
const tituloPassword = document.getElementById("titulo-password")
const passwordNueva = document.getElementById("password-nueva")
const cuerpoUsuarios = document.getElementById("cuerpo-usuarios")

let usuarioEditando = null
let usuarioPassword = null

function crearBoton(texto, clase, accion){
    const boton = document.createElement("button")
    boton.type = "button"
    boton.className = "boton " + clase + " boton-chico"
    boton.textContent = texto
    boton.addEventListener("click", accion)
    return boton
}

function llenarRoles(select, roles){
    select.innerHTML = ""
    roles.forEach(function (rol){
        const opcion = document.createElement("option")
        opcion.value = rol
        opcion.textContent = rol
        select.appendChild(opcion)
    })
}

async function cargarUsuarios(){
    const respuesta = await enviarJSON("/api/usuarios", "GET")
    if(!respuesta.datos.ok){
        mostrarMensaje("error", respuesta.datos.mensajes)
        return
    }

    const roles = respuesta.datos.roles
    const actual = respuesta.datos.roles
    llenarRoles(altaRol, roles)
    llenarRoles(editarRol, roles)
    cuerpoUsuarios.innerHTML = ""
    respuesta.datos.usuarios.forEach(function (u){
        const tr = document.createElement("tr")
        if(!u.activo) tr.className = "fila-inactiva"

        const valores = [u.nombre, u.usuario, u.rol]
        valores.forEach(function(valor){
            const td = document.createElement("td")
            td.textContent = valor
            tr.appendChild(td)
        })

        const tdEstado = document.createElement("td")
        tdEstado.textContent = u.activo ? "Activo" : "Inactivo"
        tdEstado.className = u.activo ? "usuario-activo" : "usuario-inactivo"
        tr.appendChild(tdEstado)

        const acciones = document.createElement("td")
        acciones.appendChild(crearBoton("Editar", "boton-claro", function () {
            abrirEditar(u)
        }))
        acciones.appendChild(crearBoton("Contraseña", "boton-claro", function (){
            abrirPassword(u)
        }))

        if(u.usuario !== actual){
            const texto = u.activo ? "Desactivar" : "Reactivar"
            acciones.appendChild(crearBoton(texto, "boton-claro", function (){
                cambiarEstado(u, !u.activo)
            }))
        }
        tr.appendChild(acciones)
        cuerpoUsuarios.appendChild(tr)
    })
}

async function crearUsuario(evento){
    evento.preventDefault()
    const respuesta = await enviarJSON("/api/usuarios", "POST", {
        nombre: altaNombre.value,
        usuario: altaUsuario.value,
        password: altaPassword.value,
        rol: altaRol.value
    })

    if(!respuesta.datos.ok){
        mostrarMensaje("error", respuesta.datos.mensajes)
        return
    }
    
    formAlta.reset()
    await cargarUsuarios()
    mostrarMensaje("exito", respuesta.datos.mensajes)
}

function abrirEditar(u){
    panelPassword.classList.add("oculto")
    usuarioEditando = u.usuario
    tituloEditar.textContent = "Editar a " + u.usuario
    editarNombre.value = u.nombre
    editarRol.value = u.rol
    panelEditar.classList.remove("oculto")
    panelEditar.scrollIntoView({ behavior: "smooth" })
}

function cerrarEditar(){
    usuarioEditando = null
    panelEditar.classList.add("oculto")
}

async function guardarEditar(){
    if(usuarioEditando === null) return

    const respuesta = await enviarJSON("/api/usuarios/" + encodeURIComponent(usuarioEditando), "PUT", {
        nombre: editarNombre.value,
        rol: editarRol.value
    })

    if(!respuesta.datos.ok){
        mostrarMensaje("error", respuesta.datos.mensajes)
        return
    }

    cerrarEditar()
    await cargarUsuarios()
    mostrarMensaje("exito", respuesta.datos.mensajes)
}

function abrirPassword(u){
    panelEditar.classList.add("oculto")
    usuarioPassword = u.usuario
    tituloPassword.textContent = "Nueva contraseña para " + u.usuario
    passwordNueva.value = ""
    panelPassword.classList.remove("oculto")
    panelPassword.scrollIntoView({ behavior: "smooth" })
}

function cerrarPassword() {
    usuarioPassword = null
    passwordNueva.value = ""
    panelPassword.classList.add("oculto")
}

async function guardarPassword(){
    if(usuarioPassword === null) return

    const respuesta = await enviarJSON("/api/usuarios/" + encodeURIComponent(usuarioPassword) + "/password", "POST", {
        password: passwordNueva.value
    })

    if(!respuesta.datos.ok){
        mostrarMensaje("error", respuesta.datos.mensajes)
        return
    }

    cerrarPassword()
    mostrarMensaje("exito", respuesta.datos.mensajes)
}

async function cambiarEstado(u, activo){
    const accion = activo ? "reactivar" : "desactivar"
    if(!window.confirm("¿Seguro que quieres " + accion + " al usuario " + u.usuario + "?")) return

    const respuesta = await enviarJSON("/api/usuarios/" + encodeURIComponent(u.usuario) + "/estado", "POST", {
        activo: activo
    })

    if(!respuesta.datos.ok){
        mostrarMensaje("error", respuesta.datos.mensajes)
        return
    }

    await cargarUsuarios()
    mostrarMensaje("exito", respuesta.datos.mensajes)
}

formAlta.addEventListener("submit", crearUsuario)
document.getElementById("boton-limpiar-alta").addEventListener("clcik", function(){
    formAlta.reset()
    mostrarMensaje("advertencia", "Formulario limpiado.")
})
document.getElementById("boton-guardar-editar").addEventListener("click", guardarEditar)
document.getElementById("boton-cancelar-editar").addEventListener("click", cerrarEditar)
document.getElementById("boton-guardar-password").addEventListener("click", guardarPassword)
document.getElementById("boton-cancelar-password").addEventListener("click", cerrarPassword)

cargarUsuarios()