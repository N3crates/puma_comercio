const filtroEstatus = document.getElementById("filtro-estatus")
const filtroBuscar = document.getElementById("filtro-buscar")
const cuerpoTabla = document.getElementById("cuerpo-tabla")
const panelEstatus = document.getElementById("panel-estatus")
const tituloEstatus = document.getElementById("titulo-estatus")
const campoFecha = document.getElementById("estatus-fecha")
const campoComentario = document.getElementById("estatus-comentario")
const panelHistorial = document.getElementById("panel-historial")
const tituloHistorial = document.getElementById("titulo-historial")
const cuerpoHistorial = document.getElementById("cuerpo-historial")

let embarqueSeleccionado = null
let estatusNuevo = null

function crearBoton(texto, clase, accion){
    const boton = document.createElement("button")
    boton.type = "button"
    boton.className = "boton " + clase + " boton-chico"
    boton.textContent = texto
    boton.addEventListener("click", accion)
    return boton
}

async function cargarEmbarques() {
    const url = "/api/embarques?estatus=" + encodeURIComponent(filtroEstatus.value) +
                "&buscar=" + encodeURIComponent(filtroBuscar.value)
    const respuesta = await enviarJSON(url, "GET")

    if (!respuesta.datos.ok) {
        mostrarMensaje("error", respuesta.datos.mensajes)
        return
    }

    cuerpoTabla.innerHTML = ""
    const lista = respuesta.datos.embarques

    if (lista.length === 0) {
        mostrarMensaje("advertencia", "No se encontraron embarques con ese filtro.")
        return
    }

    mostrarMensaje("exito", lista.length + " embarque(s) encontrado(s).")
    lista.forEach(function (e) {
        const tr = document.createElement("tr")
        const valores = [e.id, e.contenedor, e.origen, e.puerto_destino, e.estatus, e.eta]
        valores.forEach(function (valor) {
            const td = document.createElement("td")
            td.textContent = valor
            tr.appendChild(td)
        })

        const acciones = document.createElement("td")
        acciones.appendChild(crearBoton("Historial", "boton-claro", function(){
            mostrarHistorial(e.id)
        }))
        if (e.puede_cambiar && e.siguiente){
            acciones.appendChild(crearBoton("Pasar a " + e.siguiente, "boton-principal", function(){
                abrirPanelEstatus(e)
            }))
        }
        tr.appendChild(acciones)
        cuerpoTabla.appendChild(tr)
    })
}

function abrirPanelEstatus(e){
    const hoy = new Date()
    embarqueSeleccionado = e.id
    estatusNuevo = e.siguiente
    tituloEstatus.textContent = e.id + ": " + e.estatus + " -> " + e.siguiente 
    campoFecha.value = hoy.getFullYear() + "-" + String(hoy.getMonth() + 1).padStart(2, "0") + "-" + String(hoy.getDate()).padStart(2, "0")
    campoComentario.value = ""
    panelEstatus.classList.remove("oculto")
    panelEstatus.scrollIntoView({ behavior: "smooth"})
}

function cerrarPanelEstatus(){
    embarqueSeleccionado = null
    estatusNuevo = null
    panelEstatus.classList.add("oculto")
}

async function confirmarEstatus() {
    if(embarqueSeleccionado === null) return

    const respuesta = await enviarJSON("/api/embarques/" + embarqueSeleccionado + "/estatus", "POST", {
        estatus: estatusNuevo,
        fecha: campoFecha.value,
        comentario: campoComentario.value
    })

    if(!respuesta.datos.ok){
        mostrarMensaje("error", respuesta.datos.mensajes)
        return
    }

    const id = embarqueSeleccionado
    cerrarPanelEstatus()
    await cargarEmbarques()
    mostrarMensaje("exito", respuesta.datos.mensajes)
    mostrarHistorial(id)
}

async function mostrarHistorial(id){
    const respuesta = await enviarJSON("/api/embarques/" + id + "/historial", "GET")

    if(!respuesta.datos.ok){
        mostrarMensaje("error", respuesta.datos.mensajes)
        return
    }

    cuerpoHistorial.innerHTML = ""
    respuesta.datos.historial.forEach(function(h){
        const tr = document.createElement("tr")
        const valores = [h.fecha, h.estatus, h.usuario, h.comentario]
        valores.forEach(function(valor){
            const td = document.createElement("td")
            td.textContent = valor
            tr.appendChild(td)
        })
        cuerpoHistorial.appendChild(tr)
    })

    tituloHistorial.textContent = "Historial de " + id
    panelHistorial.classList.remove("oculto")
}

function cerrarHistorial(){
    panelHistorial.classList.add("oculto")
    cuerpoHistorial.innerHTML = ""
}

document.getElementById("boton-buscar").addEventListener("click", cargarEmbarques)
filtroEstatus.addEventListener("change", cargarEmbarques)
document.getElementById("boton-limpiar").addEventListener("click", function () {
    filtroEstatus.value = ""
    filtroBuscar.value = ""
    cargarEmbarques()
})
document.getElementById("boton-confirmar-estatus").addEventListener("click", confirmarEstatus)
document.getElementById("boton-cancelar-estatus").addEventListener("click", cerrarPanelEstatus)
document.getElementById("boton-cerrar-historial").addEventListener("click", cerrarHistorial)

cargarEmbarques()