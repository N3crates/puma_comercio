CREATE DATABASE IF NOT EXISTS puma_comercio;
USE puma_comercio;

# Tabla de roles
CREATE TABLE IF NOT EXISTS roles(
    id_rol INT AUTO_INCREMENT,
    nombre VARCHAR(40) NOT NULL,
    PRIMARY KEY (id_rol),
    UNIQUE uni_nom(nombre)
);

# Tabla de puertos
CREATE TABLE IF NOT EXISTS puertos(
    id_puerto INT AUTO_INCREMENT,
    nombre VARCHAR(60) NOT NULL,
    PRIMARY KEY (id_puerto),
    UNIQUE uni_nom(nombre)
);

# Tabla de fracciones_arancelarias
CREATE TABLE IF NOT EXISTS fracciones_arancelarias(
    id_fraccion INT AUTO_INCREMENT,
    clave VARCHAR(20) NOT NULL,
    codigo VARCHAR(20) NOT NULL,
    descripcion TEXT,
    tasa_igi DECIMAL(5, 4) NOT NULL,
    PRIMARY KEY (id_fraccion),
    CONSTRAINT chk_tasa_igi CHECK (tasa_igi >= 0 AND tasa_igi <= 1),
    UNIQUE uni_clave(clave)
);

# Tabla de parametros
CREATE TABLE IF NOT EXISTS parametros(
    clave VARCHAR(40),
    valor_num DECIMAL(12, 4) NULL,
    valor_fecha DATE NULL,
    descripcion VARCHAR(100) NOT NULL,
    PRIMARY KEY (clave),
    CONSTRAINT chk_parametro_valor CHECK (valor_num IS NOT NULL OR valor_fecha IS NOT NULL)
);

# Tabla de usuarios
CREATE TABLE IF NOT EXISTS usuarios(
    id_usuario INT AUTO_INCREMENT,
    nombre VARCHAR(80) NOT NULL,
    usuario VARCHAR(30) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    id_rol INT NOT NULL,
    PRIMARY KEY (id_usuario),
    UNIQUE uni_usuario (usuario),
    CONSTRAINT fk_usuarios_rol
        FOREIGN KEY (id_rol)
        REFERENCES roles (id_rol)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

# Tabla de productos
CREATE TABLE IF NOT EXISTS productos(
    sku VARCHAR(30),
    descripcion TEXT NOT NULL,
    categoria VARCHAR(30) NOT NULL,
    material TEXT NOT NULL,
    precio_origen DECIMAL(10, 2) NOT NULL,
    id_fraccion INT NOT NULL,
    PRIMARY KEY (sku),
    CONSTRAINT chk_precio_origen CHECK (precio_origen > 0),
    CONSTRAINT fk_productos_fraccion
        FOREIGN KEY (id_fraccion)
        REFERENCES fracciones_arancelarias (id_fraccion)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

# Tabla de embarques
CREATE TABLE IF NOT EXISTS embarques(
    id_embarque VARCHAR(10),
    contenedor VARCHAR(20) NOT NULL,
    origen VARCHAR(80) NOT NULL,
    id_puerto INT NOT NULL,
    naviera VARCHAR(60) NOT NULL,
    fecha_salida DATE NOT NULL,
    eta DATE NOT NULL,
    fecha_arribo DATE NULL,
    estatus ENUM('En origen', 'En transito', 'En puerto', 'Liberado', 'Entregado en CD') NOT NULL DEFAULT 'En origen',
    flete DECIMAL(12, 2) NOT NULL,
    honorarios DECIMAL(12, 2) NOT NULL,
    PRIMARY KEY (id_embarque),
    UNIQUE uni_contenedor (contenedor),
    CONSTRAINT chk_fechas CHECK (eta > fecha_salida),
    CONSTRAINT chk_flete CHECK (flete >= 0),
    CONSTRAINT chk_honorarios CHECK (honorarios >= 0),
    CONSTRAINT fk_embarques_puerto
        FOREIGN KEY (id_puerto)
        REFERENCES puertos (id_puerto)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

# Tabla de detalle de embarque
CREATE TABLE IF NOT EXISTS detalle_embarque(
    id_detalle INT AUTO_INCREMENT,
    id_embarque VARCHAR(10) NOT NULL,
    sku VARCHAR(30) NOT NULL,
    cantidad_pedida INT NOT NULL,
    cantidad_facturada INT NOT NULL,
    PRIMARY KEY (id_detalle),
    CONSTRAINT chk_cantidad_pedida CHECK (cantidad_pedida >= 0),
    CONSTRAINT chk_cantidad_facturada CHECK (cantidad_facturada >= 0),
    CONSTRAINT uq_embarque_sku UNIQUE (id_embarque, sku),
    CONSTRAINT fk_detalle_embarque
        FOREIGN KEY (id_embarque)
        REFERENCES embarques (id_embarque)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT fk_detalle_producto
        FOREIGN KEY (sku)
        REFERENCES productos (sku)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);