const cuerpoAlertas = document.getElementById("cuerpo-alertas")

async function cargarDashboard() {
    const respuesta = await enviarJSON("/api/dashboard", "GET")

    if(!respuesta.datos.ok){
        mostrarMensaje("error", respuesta.datos.mensajes)
        return
    }

    const r = respuesta.datos.resumen
    document.getElementById("dato-total").textContent = r.total
    document.getElementById("dato-transito").textContent = r.en_transito
    document.getElementById("dato-puerto").textContent = r.en_puerto
    document.getElementById("dato-alertas").textContent = r.con_alertas

    cuerpoAlertas.innerHTML = ""
    if(r.alertas.length === 0){
        mostrarMensaje("exito", "No hay alertas activas.")
        return
    }

    r.alertas.forEach(function (a){
        const tr = document.createElement("tr")
        const valores = [a.id, a.contenedor, a.tipo, a.gravedad, a.detalle]
        valores.forEach(function(valor, indice){
            const td = document.createElement("td")
            td.textContent = valor
            if(indice === 3){
                td.className = "gravedad gravedad-" + a.gravedad.toLowerCase()
            }
            tr.appendChild(td)
        })
        cuerpoAlertas.appendChild(tr)
    })
}

cargarDashboard()