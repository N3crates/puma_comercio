const selector = document.getElementById("selector-embarque")
const zonaRecepcion = document.getElementById("zona-recepcion")
const tituloRecepcion = document.getElementById("titulo-recepcion")
const infoRecepcion = document.getElementById("titulo-recepcion")
const cuerpoRecepcion = document.getElementById("cuerpo-recepcion")
const formularioRecepcion = document.getElementById("formulario-recepcion")
const campoFecha = document.getElementById("recepcion-fecha")
const campoObservaciones = document.getElementById("recepcion-observaciones")

let embarqueActual = null

function classEstado(estado){
    const clases = {"Coincide": "coincide", "Faltante": "faltante", "Excedente": "excedente", "Con daños": "danos"}
    return "estado estado-" + (clases[estado] || "")
}

function fechaLocal(){
    const hoy = new Date()
    return hoy.getFullYear() + "-" + String(hoy.getMonth() + 1).padStart(2, "0") + "-" + String(hoy.getDate()).padStart(2, "0")
}

function aEntero(texto){
    if(texto === null || texto === undefined || String(texto).trim() === "") return NaN
    return Number(texto)
}

function agregarCelda(fila, valor){
    const td = document.createElement("td")
    td.textContent = valor
    fila.appendChild(td)
    return td
}

function crearInput(clase, valor){
    const input = document.createElement("input")
    input.type = "number"
    input.min = "0"
    input.className = clase
    input.value = valor
    return input
}

async function cargarLista(idInicial){
    const respuesta = await enviarJSON("/api/embarques", "GET")
    if(!respuesta.datos.ok){
        mostrarMensaje("error", respuesta.datos.mensajes)
        return
    }

    selector.innerHTML = ""
    respuesta.datos.embarques.forEach(function (e) {
        if (e.estatus !== "Liberado" && e.estatus !== "Entregado en CD") return
        const opcion = document.createElement("option")
        opcion.value = e.id
        opcion.textContent = e.id + " - " + e.contenedor + " (" + e.estatus + ")"
        selector.appendChild(opcion)
    })

    if(selector.options.length === 0){
        mostrarMensaje("advertencia", "No hay embarques liberados ni entregados por mostrar.")
        return
    }
    if(idInicial){
        selector.value = idInicial
        cargar()
    }
}

async function cargar(){
    const id = selector.value
    if(id === ""){
        mostrarMensaje("error", "Selecciona un embarque.")
        return
    }

    const respuesta = await enviarJSON("/api/recepcion/" + encodeURIComponent(id), "GET")
    if(!respuesta.datos.ok){
        zonaRecepcion.classList.add("oculto")
        mostrarMensaje("error", respuesta.datos.mensajes)
        return
    }

    const r = respuesta.datos.recepcion
    const puedeRegistrar = respuesta.datos.puede_registrar
    embarqueActual = r.id
    tituloRecepcion.textContent = r.id + " (contenedor " + r.contenedor + ")"
    if(r.registrada){
        infoRecepcion.textContent = "Recepción registrada el " + r.fecha + " por " + r.usuario + 
            (r.observaciones ? ". Observaciones: " + r.observaciones : ".")
    }else if(puedeRegistrar){
        infoRecepcion.textContent = "Captura lo que llegó fisicamente al centro de distribución."
    }else{
        infoRecepcion.textContent = "La recepción de este embarque aun no se ha registrado."
    }

    cuerpoRecepcion.innerHTML = ""
    r.filas.forEach(function (f){
        const tr = document.createElement("tr")
        agregarCelda(tr, f.sku)
        agregarCelda(tr, f.descripcion)
        agregarCelda(tr, f.factura)

        if(puedeRegistrar){
            const tdRecibida = document.createElement("td")
            const inputRecibida = crearInput("rec-recibida", f.factura)
            tdRecibida.appendChild(inputRecibida)
            tr.appendChild(tdRecibida)
            const tdDanada = document.createElement("td")
            const inputDanada = crearInput("rec-danada", 0)
            tdDanada.appendChild(inputDanada)
            tr.appendChild(tdDanada)
            agregarCelda(tr, "-")
            agregarCelda(tr, "-")
            tr.dataset.sku = f.sku
        }else{
            agregarCelda(tr, f.recibida === null ? "-" : f.recibida)
            agregarCelda(tr, f.danada === null ? "-" : f.danada)
            agregarCelda(tr, f.diferencia === null ? "-" : f.diferencia)
            const celda = agregarCelda(tr, f.estado === "" ? "-" : f.estado)
            if(f.estado !== "") celda.className = classEstado(f.estado)
        }
    cuerpoRecepcion.appendChild(tr)
    })
    if(puedeRegistrar){
        campoFecha.value = fechaLocal()
        campoObservaciones.value = ""
        formularioRecepcion.classList.remove("oculto")
    }else{
        formularioRecepcion.classList.add("oculto")
    }
    zonaRecepcion.classList.remove("oculto")
}

async function guardar() {
    if(embarqueActual === null) return

    const skus = []
    cuerpoRecepcion.querySelectorAll("tr").forEach(function(fila){
        const recibida = fila.querySelector(".rec-recibida")
        const danada = fila.querySelector(".rec-danada")
        if(!recibida || !danada) return
        skus.push({
            sku: fila.dataset.sku,
            recibida: aEntero(recibida.value),
            danada: danada.value.trim() === "" ? 0 : aEntero(danada.value)
        })
    })
    const incompletas = skus.some(function(s){
        return !Number.isInteger(s.recibida) || !Number.isInteger(s.danada)
    })
    if(incompletas){
        mostrarMensaje("error", "Cada SKU necesita una cantidad recibida y una cantidad dañada en numero entero.")
        return
    }

    const respuesta = await enviarJSON("/api/recepcion/" + encodeURIComponent(embarqueActual), "POST", {
        fecha: campoFecha.value,
        observaciones: campoObservaciones.value,
        skus: skus
    })
    if(!respuesta.datos.ok){
        mostrarMensaje("error", respuesta.datos.mensajes)
        return
    }

    const id = embarqueActual
    await cargarLista(id)
    mostrarMensaje("exito", respuesta.datos.mensajes)
}

document.getElementById("boton-cargar").addEventListener("click", cargar)
document.getElementById("boton-guardar-recepcion").addEventListener("click", guardar)

const idParametro = new URLSearchParams(window.location.search).get("embarque")
cargarLista(idParametro)