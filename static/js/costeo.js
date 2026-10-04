const selector = document.getElementById("selector-embarque")
const botonCalcular = document.getElementById("boton-calcular")
const zonaResultado = document.getElementById("resultado")
const tituloResultado = document.getElementById("titulo-resultado")
const cuerpoTabla = document.getElementById("cuerpo-tabla")
const totalEmbarque = document.getElementById("total-embarque")

async function cargarEmbarques() {
    const respuesta = await enviarJSON("/api/embarques", "GET")

    if (!respuesta.datos.ok) {
        mostrarMensaje("error", respuesta.datos.mensajes)
        return
    }

    respuesta.datos.embarques.forEach(function (e) {
        const opcion = document.createElement("option")
        opcion.value = e.id
        opcion.textContent = e.id + " - " + e.contenedor
        selector.appendChild(opcion)
    })
}

async function calcular() {
    const id = selector.value
    if (id === "") {
        mostrarMensaje("error", "Selecciona un embarque.")
        return
    }

    const respuesta = await enviarJSON("/api/embarques/" + id + "/costeo", "GET")

    if (!respuesta.datos.ok) {
        zonaResultado.classList.add("oculto")
        mostrarMensaje("error", respuesta.datos.mensajes)
        return
    }

    const c = respuesta.datos.costeo

    cuerpoTabla.innerHTML = ""
    c.filas.forEach(function (f) {
        const tr = document.createElement("tr")
        const valores = [f.sku, f.cantidad, f.fraccion, f.valor_origen, f.flete,
                         f.honorarios, f.igi, f.dta, f.iva, f.aterrizado,
                         f.por_pieza_usd, f.por_pieza_mxn]
        valores.forEach(function (valor) {
            const td = document.createElement("td")
            td.textContent = valor
            tr.appendChild(td)
        })
        cuerpoTabla.appendChild(tr)
    })

    tituloResultado.textContent = c.id + " (contenedor " + c.contenedor + ")"
    totalEmbarque.textContent = "Costo aterrizado total: USD " + c.total_usd.toFixed(2) +
        "  |  MXN " + c.total_mxn.toFixed(2) + " (tipo de cambio " + c.tipo_cambio + ")"
    zonaResultado.classList.remove("oculto")

    if (c.discrepancias > 0) {
        mostrarMensaje("advertencia", "Este embarque tiene " + c.discrepancias +
            " discrepancia(s) entre pedido y factura. El costeo se calculó sobre lo facturado.")
    } else {
        mostrarMensaje("exito", "Costeo calculado correctamente.")
    }
}

botonCalcular.addEventListener("click", calcular)
cargarEmbarques()