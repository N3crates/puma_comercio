function mostrarMensaje(tipo, texto){
    const zona = document.getElementById("mensajes")

    if(!zona) return

    const lista = Array.isArray(texto) ? texto : [texto]

    zona.innerHTML = ""
    
    const caja = document.createElement("div")

    caja.className = "mensaje mensaje-" + tipo

    lista.forEach(function(linea){
        const p = document.createElement("p")
        p.textContent = linea
        caja.appendChild(p)
    })
    zona.appendChild(caja)
}

async function enviarJSON(url, metodo, cuerpo) {
    const opciones = { method: metodo, headers: {} }

    if (cuerpo !== undefined) {
        opciones.headers["Content-Type"] = "application/json" 
        opciones.body = JSON.stringify(cuerpo)                   
    }

    try {
        const respuesta = await fetch(url, opciones)
        const datos = await respuesta.json()
        return { estado: respuesta.status, datos: datos }
    } catch (error) {
        return { estado: 0, datos: { ok: false, mensajes: ["No se pudo comunicar con el servidor."] } }
    }
}