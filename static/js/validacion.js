const selector = document.getElementById("selector-embarque")
const botonValidar = document.getElementById("boton-validar")
const zonaResultado = document.getElementById("resultado")
const tituloResultado = document.getElementById("titulo-resultado")
const cuerpoTabla = document.getElementById("cuerpo-tabla")


async function cargarEmbarques(){
    const respuesta = await enviarJSON("/api/embarques", "GET")

    if(!respuesta.datos.ok){
        mostrarMensaje("error", respuesta.datos.mensajes)
        return
    }

    respuesta.datos.embarques.forEach(function (e){
        const opcion = document.createElement("option")
        opcion.value = e.id
        opcion.textContent = e.id + " - " + e.contenedor
        selector.appendChild(opcion)
    })
}

async function validar() {
    const id = selector.value
    if(id === ""){
        mostrarMensaje("error", "Selecciona un embarque.")
        return
    }

    const respuesta = await enviarJSON("/api/embarques/" + id + "/validacion", "GET")
    if(!respuesta.datos.ok){
        zonaResultado.classList.add("oculto")
        mostrarMensaje("error", respuesta.datos.mensajes)
        return
    }

    const v = respuesta.datos.validacion

    // Tabla
    cuerpoTabla.innerHTML = ""
    v.filas.forEach(function(fila){
        const tr = document.createElement("tr")
        const valores = [fila.sku, fila.pedido, fila.factura, fila.diferencia, fila.estado]

        valores.forEach(function(valor, indice){
            const td = document.createElement("td")
            td.textContent = valor
            if(indice === 4){
                td.className = "estado estado-" + fila.estado.toLowerCase()
            }
            tr.appendChild(td)
        })
        cuerpoTabla.appendChild(tr)
    })
    tituloResultado.textContent = v.id + " (contenedor " + v.contenedor + ")"
    zonaResultado.classList.remove("oculto")

    // Mensaje general
    if(v.validado){
        mostrarMensaje("exito", "Validacion completa: todos los SKUs coinciden.")
    }else{
        mostrarMensaje("advertencia", "Validacion completa con " + v.discrepancias + " discrepancia (s).")
    }
}

botonValidar.addEventListener("click", validar)
cargarEmbarques()