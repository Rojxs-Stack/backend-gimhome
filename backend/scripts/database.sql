CREATE DATABASE IF NOT EXISTS nutriescan;

USE nutriescan;


CREATE TABLE IF NOT EXISTS usuario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    apellido VARCHAR(50) NULL,
    sexo ENUM('Masculino', 'Femenino') NULL,
    fecha_nacimiento DATE NULL,
    num_telefono VARCHAR(50) NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    google_id VARCHAR(255) NULL UNIQUE,
    nombre VARCHAR(100) NULL,
    foto_url VARCHAR(500) NULL,
    password_hash VARCHAR(255) NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT 1
);



CREATE TABLE IF NOT EXISTS datoscorporales(
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT UNIQUE NOT NULL,
    altura DECIMAL(5,2),
    peso DECIMAL(5,2),
    FOREIGN KEY (usuario_id) REFERENCES usuario(id)
);



CREATE TABLE IF NOT EXISTS saludcorporal(
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    enfermedad_corporal VARCHAR(100),
    fecha_padecimiento DATETIME NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuario(id)
);





CREATE TABLE IF NOT EXISTS saludalimenticia(
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    enfermedad_alimenticia VARCHAR(100),
    FOREIGN KEY (usuario_id) REFERENCES usuario(id)
);


-- hacer bien esta parte por que tengo que sacar personalizar
-- para que en caso de que ponga el sus macros seleccione ninguno
-- y ya esta
CREATE TABLE IF NOT EXISTS objetivo(
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT UNIQUE NOT NULL ,
    objetivo_peso ENUM('ninguno','bajar','subir', 'mantener') DEFAULT 'ninguno',
    FOREIGN KEY (usuario_id) REFERENCES usuario(id)
);




CREATE TABLE IF NOT EXISTS metanutricional(
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT UNIQUE NOT NULL,
    calorias DECIMAL(7,2),
    proteinas DECIMAL(6,2),
    grasas DECIMAL(6,2),
    carbohidratos DECIMAL(6,2),
    azucares DECIMAL(6,2),
    FOREIGN KEY (usuario_id) REFERENCES usuario(id)

);


-- Para controlar los escaneos diarios por usuario
CREATE TABLE cuota_diaria (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    fecha DATE NOT NULL,
    escaneos_realizados INT DEFAULT 0,
    INDEX idx_user_fecha (user_id, fecha),
    UNIQUE KEY unique_user_fecha (user_id, fecha)
);



CREATE TABLE IF NOT EXISTS historialconsumidopordia(
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    nombre VARCHAR(255) NULL,
    fecha_consumido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    calorias DECIMAL(7,2),
    proteinas DECIMAL(6,2),
    grasas DECIMAL(6,2),
    carbohidratos DECIMAL(6,2),
    azucares DECIMAL(6,2),
    FOREIGN KEY (usuario_id) REFERENCES usuario(id)
);
















