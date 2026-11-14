const buscarContenedor = document.getElementById("buscar-contenedor")
const buscarSku = document.getElementById("buscar-sku")
const zonaResultados = document.getElementById("zona-resultados")
const cuerpoResultados = document.getElementById("cuerpo-resultados")
const zonaFicha = document.getElementById("zona-ficha")
const tituloFicha = document.getElementById("titulo-ficha")
const datosFicha = document.getElementById("datos-ficha")
const textoEta = document.getElementById("texto-eta")
const lineaTiempo = document.getElementById("linea-tiempo")
const cuerpoAlertasFicha = document.getElementById("cuerpo-alertas-ficha")
const cuerpoProductos = document.getElementById("cuerpo-productos")

function agregarCelda(fila, vlaor){
    const td = document.createElement("td")
    td.textContent = vlaor
    fila.appendChild(td)
    return td
}

function agregarDato(etiqueta, valor){
    const caja = document.createElement("div")
    caja.className = "dato-ficha"
    
    const pequeno = document.createElement("small")
    pequeno.textContent = etiqueta

    const fuerte = document.createElement("strong")
    fuerte.textContent = valor

    caja.appendChild(pequeno)
    caja.appendChild(fuerte)
    datosFicha.appendChild(caja)
}

async function buscar(){
    const url = "/api/rastreo?contenedor=" + encodeURIComponent(buscarContenedor.value) + "&sku=" + encodeURIComponent(buscarSku.value)
    const respuesta = await enviarJSON(url, "GET")

    if(!respuesta.datos.ok){
        zonaResultados.classList.add("oculto")
        zonaFicha.classList.add("oculto")
        mostrarMensaje("error", respuesta.datos.mensajes)
        return
    }

    const lista = respuesta.datos.resultados
    cuerpoResultados.innerHTML = ""
    zonaFicha.classList.add("oculto")

    if(lista.length === 0){
        zonaResultados.classList.add("oculto")
        mostrarMensaje("advertencia", "No se encontraron embarques con esa busqueda.")
        return
    }

    mostrarMensaje("exito", lista.length + " embarque(s) encontrado(s).")
    lista.forEach(function (r){
        const tr = document.createElement("tr")
        agregarCelda(tr, r.id)
        agregarCelda(tr, r.contenedor)
        agregarCelda(tr, r.puerto_destino)
        agregarCelda(tr, r.estatus)
        agregarCelda(tr, r.eta)
        agregarCelda(tr, r.cantidad === null ? "-" : r.cantidad)

        const acciones = document.createElement("td")
        const boton = document.createElement("button")
        boton.type = "button"
        boton.className = "boton boton-principal boton-chico"
        boton.textContent = "Ver ficha"
        boton.addEventListener("click", function() {
            mostrarFicha(r.contenedor)
        })
        acciones.appendChild(boton)
        tr.appendChild(acciones)
        cuerpoResultados.appendChild(tr)
    })
    zonaResultados.classList.remove("oculto")
}

async function mostrarFicha(contenedor){
    const respuesta = await enviarJSON("/api/rastreo/" + encodeURIComponent(contenedor), "GET")

    if(!respuesta.datos.ok){
        zonaFicha.classList.add("oculto")
        mostrarMensaje("error", respuesta.datos.mensajes)
        return
    }

    const f = respuesta.datos.ficha
    tituloFicha.textContent = f.id + " (contenedor " + f.contenedor + ")"

    datosFicha.innerHTML = ""
    agregarDato("Estatus", f.estatus)
    agregarDato("Naviera", f.naviera)
    agregarDato("Origen", f.origen)
    agregarDato("Puerto de destino", f.puerto_destino)
    agregarDato("Fecha de salida", f.fecha_salida)
    agregarDato("ETA", f.eta)
    agregarDato("Fecha de arribo", f.arribo || "Aun no llega")
    agregarDato("Dias de arribo", f.dias_transito)
    agregarDato("Dias en puerto", f.dias_puerto)
    agregarDato("Dias de demora", f.dias_demora)
    agregarDato("Costo de demora", "USD" + f.costo_demora)
    textoEta.textContent = f.texto_eta

    // Linea de tiempo
    lineaTiempo.innerHTML = ""
    f.linea_tiempo.forEach(function(p){
        const li = document.createElement("li")
        li.className = "paso paso-" + p.estado

        const nombre = document.createElement("strong")
        nombre.textContent = p.estatus
        li.appendChild(nombre)

        if(p.fecha){
            const fecha = document.createElement("div")
            fecha.textContent = p.fecha
            li.appendChild(fecha)
        }
        if(p.usuario){
            const usuario = document.createElement("small")
            usuario.textContent = p.usuario
            li.appendChild(usuario)
        }
        lineaTiempo.appendChild(li)
    })

    // Alertas
    cuerpoAlertasFicha.innerHTML = ""
    if(f.alertas.length === 0){
        const tr = document.createElement("tr")
        const td = agregarCelda(tr, "Sin alertas activas.")
        td.colSpan = 3
        cuerpoAlertasFicha.appendChild(tr)
    }else{
        f.alertas.forEach(function (a){
            const tr = document.createElement("tr")
            agregarCelda(tr, a.tipo)
            const celda = agregarCelda(tr, a.gravedad)
            celda.className = "gravedad gravedad-" + a.gravedad.toLowerCase()
            agregarCelda(tr, a.detalle)
            cuerpoAlertasFicha.appendChild(tr)
        })
    }

    // Productos
    cuerpoProductos.innerHTML = ""
    f.productos.forEach(function (p){
        const tr = document.createElement("tr")
        agregarCelda(tr, p.sku)
        agregarCelda(tr, p.descripcion)
        agregarCelda(tr, p.cantidad)
        cuerpoProductos.appendChild(tr)
    })

    zonaFicha.classList.remove("oculto")
    zonaFicha.scrollIntoView({ behavior: "smooth" })
}

document.getElementById("boton-buscar").addEventListener("click", buscar)
document.getElementById("boton-limpiar").addEventListener("click", function (){
    buscarContenedor.value = ""
    buscarSku.value = ""
    zonaResultados.classList.add("oculto")
    zonaFicha.classList.add("oculto")
})

document.getElementById("boton-cerrar-ficha").addEventListener("click", function(){
    zonaFicha.classList.add("oculto")
})

const contenedorInicial = new URLSearchParams(window.location.search).get("contenedor")
if(contenedorInicial){
    buscarContenedor.value = contenedorInicial
    mostrarFicha(contenedorInicial)
}