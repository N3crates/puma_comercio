const formulario = document.getElementById("form-embarque")
const contenedorFilas = document.getElementById("filas-skus")
const botonAgregar = document.getElementById("boton-agregar")
const botonLimpiar = document.getElementById("boton-limpiar")

let catalogo = []

async function cargarCatalogo() {
    const respuesta = await enviarJSON("/api/catalogo", "GET")

    if(!respuesta.datos.ok){
        mostrarMensaje("error", respuesta.datos.mensajes)
        return
    }

    catalogo = respuesta.datos.catalogo
    agregarFila()
}

function agregarFila(){
    const fila = document.createElement("div")
    fila.className = "fila-sku"

    const select = document.createElement("select")
    select.className = "sku-select"
    const vacia = document.createElement("option")
    vacia.value = ""
    vacia.textContent = "Selecciona SKU..."
    select.appendChild(vacia)

    catalogo.forEach(function (p){
        const opcion = document.createElement("option")
        opcion.value = p.sku
        opcion.textContent = p.sku + " - " + p.descripcion
        select.appendChild(opcion)
    })

    const pedido = document.createElement("input")
    pedido.type = "number"
    pedido.min = "0"
    pedido.placeholder = "Pedido"
    pedido.className = "sku-pedido"

    const factura = document.createElement("input")
    factura.type = "number"
    factura.min = "0"
    factura.placeholder = "Factura"
    factura.className = "sku-factura"

    const quitar = document.createElement("button")
    quitar.type = "button"
    quitar.className = "boton boton-claro"
    quitar.textContent = "Quitar"
    quitar.addEventListener("click", function() {
        fila.remove()
    })

    fila.appendChild(select)
    fila.appendChild(pedido)
    fila.appendChild(factura)
    fila.appendChild(quitar)
    contenedorFilas.appendChild(fila)
}

function limpiarFormulario() {
    formulario.reset()
    contenedorFilas.innerHTML = ""
    agregarFila()
}

function aEntero(texto){
    if(texto.trim() === "") return NaN
    return Number(texto)
}

async function registrar(evento) {
    evento.preventDefault()

    const skus = []
    contenedorFilas.querySelectorAll(".fila-sku").forEach(function(fila){
        skus.push({
            sku: fila.querySelector(".sku-select").value,
            pedido: aEntero(fila.querySelector(".sku-pedido").value),
            factura: aEntero(fila.querySelector(".sku-factura").value)
        })
    })
    const incompletas = skus.some(function(s){
        return s.sku === "" || !Number.isInteger(s.pedido) || !Number.isInteger(s.factura)
    })
    if(incompletas){
        mostrarMensaje("error", "Cada fila de SKU necesita un SKU y cantidades enteras de pedido y factura.")
        return
    }

    const embarque = {
        contenedor: document.getElementById("contenedor").value,
        origen: document.getElementById("origen").value,
        puerto_destino: document.getElementById("puerto").value,
        naviera: document.getElementById("naviera").value,
        fecha_salida: document.getElementById("fecha-salida").value,
        eta: document.getElementById("eta").value,
        flete: document.getElementById("flete").value,
        honorarios: document.getElementById("honorarios").value,
        skus: skus
    }

    const respuesta = await enviarJSON("/api/embarques", "POST", embarque)

    if(respuesta.datos.ok){
        mostrarMensaje("exito", respuesta.datos.mensajes)
        limpiarFormulario()
    }else{
        mostrarMensaje("error", respuesta.datos.mensajes)
    }
}

formulario.addEventListener("submit", registrar)
botonAgregar.addEventListener("click", agregarFila)
botonLimpiar.addEventListener("click", function() {
    limpiarFormulario()
    mostrarMensaje("advertencia", "Formulario limpiado.")
})

cargarCatalogo()