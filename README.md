# PUMA | Sistema de Gestión de Comercio Internacional

Simulación de un sistema de información para la importación de mercancía de PUMA.
Proyecto de la materia Sistemas de Información, Universidad de Guanajuato,
Campus Irapuato-Salamanca.

## Arquitectura
- **Front-End:** HTML, CSS y JavaScript (carpetas `templates/` y `static/`).
- **Back-End:** Python 3.11 con Flask (`app.py` rutas, `logica.py` reglas, `datos.py` datos).
- Los datos son ficticios y viven en memoria (sin base de datos).

Flujo: Usuario -> Front-End -> Back-End -> Front-End -> Usuario.

## Cómo ejecutarlo
1. Crear y activar el entorno virtual:

        python -m venv venv
        .\venv\Scripts\Activate.ps1

2. Instalar dependencias:

        pip install -r requirements.txt

3. Iniciar el servidor:

        python app.py

4. Abrir http://127.0.0.1:5000 en el navegador.

## Usuarios de prueba
| Usuario | Contraseña | Rol |
|---|---|---|
| laura | trafico123 | Ejecutivo de tráfico |
| carlos | aduana123 | Agente aduanal |
| andrea | finanzas123 | Gerencia / Finanzas |
| admin | admin123 | Administrador |

## Funciones
- Login con roles y control de acceso en el servidor.
- Registro de embarques con validación de datos.
- Validación de embarque: cotejo pedido vs. factura (Coincide, Faltante, Excedente).
- Costeo de importación: IGI, DTA, IVA y costo aterrizado por pieza.
- Dashboard con alertas (demora en puerto, retraso en tránsito, discrepancias).
- Listado de embarques con filtro por estatus y búsqueda por contenedor.

## Alcance y supuestos
- Fracciones arancelarias y tasas ilustrativas, no oficiales.
- Fecha de referencia fija (2026-10-02) para resultados reproducibles.
- Los embarques registrados se pierden al reiniciar el servidor.
- El rastreo se cubre parcialmente en el dashboard (días en puerto y alertas de demora).

## Trabajo futuro
- Base de datos real.
- Gestión de usuarios (alta, edición y baja) por el administrador.
- Pantalla de rastreo con línea de tiempo y mapa.
- Integración con aduanas y GPS.