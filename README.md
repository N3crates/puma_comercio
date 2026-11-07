# PUMA | Sistema de Gestión de Comercio Internacional

Simulación de un sistema de información para la importación de mercancía de PUMA.
Proyecto de la materia Sistemas de Información, Universidad de Guanajuato,
Campus Irapuato-Salamanca.

## Arquitectura
- **Front-End:** HTML, CSS y JavaScript (carpetas `templates/` y `static/`).
- **Back-End:** Python 3.11 con Flask (`app.py` rutas, `logica.py` reglas).
- **Base de datos:** MySQL 8 (8 tablas). `datos.py` es la capa de acceso a datos.

Flujo: Usuario -> Front-End -> Back-End -> MySQL -> Back-End -> Front-End -> Usuario.

## Requisitos
- Python 3.10 o superior
- MySQL Server 8 y MySQL Workbench

## Cómo ejecutarlo
1. Crear y activar el entorno virtual:

        python -m venv venv
        .\venv\Scripts\Activate.ps1

2. Instalar dependencias:

        pip install -r requirements.txt

3. Crear la base de datos: abrir `base_datos/crear_tablas.sql` en MySQL Workbench y ejecutarlo.

4. Crear un usuario de MySQL con permisos limitados (en Workbench, como administrador),
   cambiando la contraseña:

        CREATE USER 'puma_app'@'localhost' IDENTIFIED BY 'TU_CONTRASEÑA';
        GRANT SELECT, INSERT, UPDATE, DELETE ON puma_comercio.* TO 'puma_app'@'localhost';
        FLUSH PRIVILEGES;

5. Configurar la conexión: copiar `config_bd.ejemplo.py` como `config_bd.py` y escribir
   la contraseña real. Este archivo no se sube a Git.

6. Cargar los datos iniciales (una sola vez):

        python base_datos\cargar_datos.py

7. Iniciar el servidor:

        python app.py

8. Abrir http://127.0.0.1:5000 en el navegador.

## Usuarios de prueba
| Usuario | Contraseña | Rol |
|---|---|---|
| laura | trafico123 | Ejecutivo de tráfico |
| carlos | aduana123 | Agente aduanal |
| andrea | finanzas123 | Gerencia / Finanzas |
| admin | admin123 | Administrador |

## Funciones
- Login con roles y control de acceso en el servidor.
- Registro de embarques con validación de datos, guardado en MySQL con transacción.
- Validación de embarque: cotejo pedido vs. factura (Coincide, Faltante, Excedente).
- Costeo de importación: IGI, DTA, IVA y costo aterrizado por pieza.
- Dashboard con alertas (demora en puerto, retraso en tránsito, discrepancias).
- Listado de embarques con filtro por estatus y búsqueda por contenedor.

## Base de datos
Tablas: `roles`, `usuarios`, `puertos`, `fracciones_arancelarias`, `productos`,
`embarques`, `detalle_embarque` y `parametros`. El script de creación está en
`base_datos/crear_tablas.sql`.

## Alcance y supuestos
- Fracciones arancelarias y tasas ilustrativas, no oficiales.
- Fecha de referencia fija (2026-10-02, tabla `parametros`) para resultados reproducibles.
- Los embarques registrados se conservan en MySQL al reiniciar el servidor.
- El rastreo se cubre parcialmente en el dashboard.

## Seguridad
- Las contraseñas de usuarios se guardan con hash.
- Las credenciales de MySQL están en `config_bd.py`, ignorado por Git.
- Las consultas usan parámetros para evitar inyección SQL.

## Trabajo futuro
- Gestión de usuarios (alta, edición y baja) por el administrador.
- Edición y eliminación de embarques.
- Pantalla de rastreo con línea de tiempo y mapa.
- Integración con aduanas y GPS.