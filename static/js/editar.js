const formulario = document.getElementById("form-embarque")
const contenedorFilas = document.getElementById("filas-skus")
const botonAgregar = document.getElementById("boton-agregar")
const idEmbarque = document.getElementById("datos-pagina").dataset.id

let catalogo = []

function agregarFila(sku, pedido, factura){
    const fila = document.createElement("div")
    fila.className = "fila-sku"

    const select = document.createElement("select")
    select.className = "sku-select"
    
    const vacia = document.createElement("option")
    vacia.value = ""
    vacia.textContent = "Selecciona SKU..."
    select.appendChild(vacia)
    catalogo.forEach(function(p){
        const opcion = document.createElement("option")
        opcion.value = p.sku
        opcion.textContent = p.sku + " - " + p.descripcion
        select.appendChild(opcion)
    })
    select.value = sku || ""

    const inputPedido = document.createElement("input")
    inputPedido.type = "number"
    inputPedido.min = "0"
    inputPedido.placeholder = "Pedido"
    inputPedido.className = "sku-pedido"
    inputPedido.value = pedido === undefined ? "" : pedido

    const inputFactura = document.createElement("input")
    inputFactura.type = "number"
    inputFactura.min = "0"
    inputFactura.placeholder = "Factura"
    inputFactura.className = "sku-factura"
    inputFactura.value = factura === undefined ? "" : factura

    const quitar = document.createElement("button")
    quitar.type = "button"
    quitar.className = "boton boton-claro"
    quitar.textContent = "Quitar"
    quitar.addEventListener("click", function () {
        fila.remove()
    })

    fila.appendChild(select)
    fila.appendChild(inputPedido)
    fila.appendChild(inputFactura)
    fila.appendChild(quitar)
    contenedorFilas.appendChild(fila)
}

function aEntero(texto){
    if(texto.trim() === "") return NaN
    return Number(texto)
}

async function cargar(){
    const resCatalogo = await enviarJSON("/api/catalogo", "GET")
    if(!resCatalogo.datos.ok){
        mostrarMensaje("error", resCatalogo.datos.mensajes)
        return
    }
    catalogo = resCatalogo.datos.catalogo

    const resEmbarque = await enviarJSON("/api/embarques/" + encodeURIComponent(idEmbarque), "GET")
    if(!resEmbarque.datos.ok){
        formulario.classList.add("oculto")
        mostrarMensaje("error", resEmbarque.datos.mensajes)
        return
    }

    const e = resEmbarque.datos.embarque
    document.getElementById("contenedor").value = e.contenedor
    document.getElementById("origen").value = e.origen
    document.getElementById("puerto").value = e.puerto_destino
    document.getElementById("naviera").value = e.naviera
    document.getElementById("fecha-salida").value = e.fecha_salida
    document.getElementById("eta").value = e.eta
    document.getElementById("flete").value = e.flete
    document.getElementById("honorarios").value = e.honorarios

    contenedorFilas.innerHTML = ""
    e.skus.forEach(function (s){
        agregarFila(s.sku, s.pedido, s.factura)
    })
}

async function guardar(evento){
    evento.preventDefault()

    const skus = []
    contenedorFilas.querySelectorAll(".fila-sku").forEach(function (fila){
        skus.push({
            sku: fila.querySelector(".sku-select"). value,
            pedido: aEntero(fila.querySelector(".sku-pedido").value),
            factura: aEntero(fila.querySelector(".sku-factura").value)
        })
    })

    const incompletas = skus.some(function (s){
        return s.sku === "" || !Number.isInteger(s.pedido) || !Number.isInteger(s.factura)
    })
    if(incompletas){
        mostrarMensaje("error", "cada fila de SKU necesita un SKU y cantidades enteras de pedido y factura")
        return
    }

    const embarque = {
        origen: document.getElementById("origen").value,
        puerto_destino: document.getElementById("puerto").value,
        naviera: document.getElementById("naviera").value,
        fecha_salida: document.getElementById("fecha-salida").value,
        eta: document.getElementById("eta").value,
        flete: document.getElementById("flete").value,
        honorarios: document.getElementById("honorarios").value,
        skus: skus
    }

    const respuesta = await enviarJSON("/api/embarques/" + encodeURIComponent(idEmbarque), "PUT", embarque)
    if(respuesta.datos.ok){
        mostrarMensaje("exito", respuesta.datos.mensajes)
        setTimeout(function() {
            window.location.href = "/embarques"
        }, 200)
    }else{
        mostrarMensaje("error", respuesta.datos.mensajes)
    }
}

formulario.addEventListener("submit", guardar)
botonAgregar.addEventListener("click", function() {
    agregarFila
})

cargar()