const filtroEstatus = document.getElementById("filtro-estatus")
const filtroBuscar = document.getElementById("filtro-buscar")
const cuerpoTabla = document.getElementById("cuerpo-tabla")

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
        cuerpoTabla.appendChild(tr)
    })
}

document.getElementById("boton-buscar").addEventListener("click", cargarEmbarques)
filtroEstatus.addEventListener("change", cargarEmbarques)
document.getElementById("boton-limpiar").addEventListener("click", function () {
    filtroEstatus.value = ""
    filtroBuscar.value = ""
    cargarEmbarques()
})

cargarEmbarques()