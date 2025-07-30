-- Crear la base de datos si no existe, usando la variable pasada desde sqlcmd
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = N'$(DB_NAME)')
BEGIN
    CREATE DATABASE [$(DB_NAME)];
END
GO

-- Usar la base de datos recién creada o ya existente
USE [$(DB_NAME)];
GO

-- Tabla para almacenar información de los documentos procesados
CREATE TABLE documentos (
    id INT IDENTITY(1,1) PRIMARY KEY,
    nombre_archivo NVARCHAR(255) NOT NULL,
    fecha_documento DATE,
    fuente NVARCHAR(100),
    hash_documento VARCHAR(64) NOT NULL,
    fecha_creacion DATETIME2 DEFAULT GETUTCDATE(),
    CONSTRAINT UQ_documentos_hash UNIQUE (hash_documento)
);

-- Tabla para inventarios extraídos
CREATE TABLE inventarios (
    id INT IDENTITY(1,1) PRIMARY KEY,
    documento_id INT NOT NULL REFERENCES documentos(id),
    fuente NVARCHAR(100),
    tipo_inventario NVARCHAR(255) NOT NULL,
    valor FLOAT,
    fecha_dato DATE,
    CONSTRAINT UQ_inventarios UNIQUE (documento_id, tipo_inventario)
);

-- Tabla para noticias extraídas
CREATE TABLE noticias (
    id INT IDENTITY(1,1) PRIMARY KEY,
    documento_id INT NOT NULL REFERENCES documentos(id),
    fuente NVARCHAR(100),
    titulo NVARCHAR(512) NOT NULL,
    resumen NVARCHAR(MAX),
    sentimiento NVARCHAR(50),
    fecha_noticia DATE,
    categoria NVARCHAR(100),
    tags NVARCHAR(MAX), -- Almacenado como JSON string
    CONSTRAINT UQ_noticias UNIQUE (documento_id, titulo)
);

-- Tabla para precios extraídos
CREATE TABLE precios (
    id INT IDENTITY(1,1) PRIMARY KEY,
    documento_id INT NOT NULL REFERENCES documentos(id),
    fuente NVARCHAR(100),
    tipo_precio NVARCHAR(255) NOT NULL,
    valor FLOAT,
    fecha_precio DATE,
    moneda NVARCHAR(10),
    unidad NVARCHAR(50),
    CONSTRAINT UQ_precios UNIQUE (documento_id, tipo_precio)
);

-- Tabla para gráficos extraídos
CREATE TABLE graficos (
    id INT IDENTITY(1,1) PRIMARY KEY,
    documento_id INT NOT NULL REFERENCES documentos(id),
    fuente NVARCHAR(100),
    titulo NVARCHAR(512),
    pagina INT,
    contenido VARBINARY(MAX),
    descripcion_ia NVARCHAR(MAX),
    fecha_grafico DATE,
    CONSTRAINT UQ_graficos UNIQUE (documento_id, titulo, pagina)
);

-- Tabla de logs para el procesamiento de documentos
CREATE TABLE logs_procesamiento (
    id INT IDENTITY(1,1) PRIMARY KEY,
    documento_id INT NOT NULL REFERENCES documentos(id),
    etapa NVARCHAR(100),
    estado NVARCHAR(50),
    duracion_ms INT,
    detalles NVARCHAR(MAX),
    error_mensaje NVARCHAR(MAX),
    timestamp DATETIME2 DEFAULT GETUTCDATE()
);

-- Tabla de logs para tareas específicas dentro del procesamiento
CREATE TABLE logs_tareas (
    id INT IDENTITY(1,1) PRIMARY KEY,
    documento_id INT NOT NULL REFERENCES documentos(id),
    nombre_tarea NVARCHAR(100),
    timestamp_inicio DATETIME2,
    timestamp_fin DATETIME2,
    estado NVARCHAR(50),
    resultados_encontrados INT,
    error_mensaje NVARCHAR(MAX)
);
GO 