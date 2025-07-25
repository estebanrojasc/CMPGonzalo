-- Tabla para registrar los documentos procesados
CREATE TABLE documentos (
    id SERIAL PRIMARY KEY,
    nombre_archivo VARCHAR(255) NOT NULL,
    fecha_documento DATE NOT NULL,
    fuente VARCHAR(50) NOT NULL,
    fecha_procesamiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    hash_documento VARCHAR(64) UNIQUE
);

-- Tabla para inventarios Mysteel
CREATE TABLE inventarios (
    id SERIAL PRIMARY KEY,
    documento_id INTEGER REFERENCES documentos(id),
    fuente VARCHAR(50) NOT NULL, -- Mysteel, u otras fuentes futuras
    fecha_dato DATE NOT NULL,
    tipo_inventario VARCHAR(50) NOT NULL, -- pellet, concentrate, lump, fines, etc.
    valor DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(documento_id, fuente, tipo_inventario, fecha_dato)
);

-- Tabla para noticias (ahora genérica para múltiples fuentes)
CREATE TABLE noticias (
    id SERIAL PRIMARY KEY,
    documento_id INTEGER REFERENCES documentos(id),
    fuente VARCHAR(50) NOT NULL, -- Mysteel, Reuters, Bloomberg, etc.
    titulo TEXT NOT NULL,
    resumen TEXT,
    sentimiento VARCHAR(20),
    fecha_noticia DATE NOT NULL,
    categoria VARCHAR(50), -- mercado, economía, política, etc.
    tags TEXT[], -- Para facilitar búsquedas por temas
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(documento_id, fuente, titulo, fecha_noticia) -- Evitar duplicados
);

-- Tabla para gráficos
CREATE TABLE graficos (
    id SERIAL PRIMARY KEY,
    documento_id INTEGER REFERENCES documentos(id),
    fuente VARCHAR(50) NOT NULL, -- Mysteel u otras fuentes
    titulo VARCHAR(255) NOT NULL,
    pagina INTEGER NOT NULL,
    altura_px INTEGER,
    contenido BYTEA NOT NULL,
    ruta_archivo VARCHAR(255),
    tipo_grafico VARCHAR(50), -- línea, barra, etc.
    categoria VARCHAR(50), -- inventario, precios, producción, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla para precios
CREATE TABLE precios (
    id SERIAL PRIMARY KEY,
    documento_id INTEGER REFERENCES documentos(id),
    fuente VARCHAR(50) NOT NULL, -- Platts, FastMarkets, Baltic, Mysteel
    tipo_precio VARCHAR(100) NOT NULL, -- precio_62_cfr_china, mb_iro_0009, etc.
    valor DECIMAL(10,2),
    fecha_precio DATE NOT NULL,
    moneda VARCHAR(10), -- USD, CNY, etc.
    unidad VARCHAR(20), -- ton, mt, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(documento_id, fuente, tipo_precio, fecha_precio)
);

-- Tabla para metadatos adicionales (flexible para cualquier tipo de dato)
CREATE TABLE metadatos (
    id SERIAL PRIMARY KEY,
    tabla_referencia VARCHAR(50) NOT NULL, -- 'noticias', 'precios', etc.
    registro_id INTEGER NOT NULL,
    clave VARCHAR(100) NOT NULL,
    valor TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tabla_referencia, registro_id, clave)
);


-- Tabla para logs de errores y eventos
CREATE TABLE logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    nivel VARCHAR(20) NOT NULL, -- ERROR, WARNING, INFO, DEBUG
    fuente VARCHAR(50) NOT NULL, -- Nombre del módulo o componente
    mensaje TEXT NOT NULL,
    detalles JSONB, -- Para almacenar detalles adicionales en formato JSON
    stack_trace TEXT,
    resuelto BOOLEAN DEFAULT FALSE,
    fecha_resolucion TIMESTAMP
);

-- Tabla para logs específicos de procesamiento de documentos
CREATE TABLE logs_procesamiento (
    id SERIAL PRIMARY KEY,
    documento_id INTEGER REFERENCES documentos(id),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    etapa VARCHAR(50) NOT NULL, -- clasificacion, extraccion_texto, procesamiento_graficos, etc.
    estado VARCHAR(20) NOT NULL, -- SUCCESS, ERROR, WARNING
    duracion_ms INTEGER, -- Duración del procesamiento en milisegundos
    detalles JSONB,
    error_mensaje TEXT,
    error_stack TEXT
);

-- Tabla para logs de tareas específicas
CREATE TABLE logs_tareas (
    id SERIAL PRIMARY KEY,
    documento_id INTEGER REFERENCES documentos(id),
    nombre_tarea VARCHAR(100) NOT NULL, -- get_mysteel_inventory, get_mysteel_news, etc.
    timestamp_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    timestamp_fin TIMESTAMP,
    estado VARCHAR(20) NOT NULL, -- SUCCESS, ERROR, WARNING, IN_PROGRESS
    resultados_encontrados INTEGER, -- Número de items procesados
    error_mensaje TEXT,
    detalles JSONB -- Detalles específicos de la tarea
);


-- Índices para mejorar el rendimiento
CREATE INDEX idx_documentos_fuente ON documentos(fuente);
CREATE INDEX idx_noticias_fecha ON noticias(fecha_noticia);
CREATE INDEX idx_noticias_fuente ON noticias(fuente);
CREATE INDEX idx_precios_fecha ON precios(fecha_precio);
CREATE INDEX idx_inventarios_fecha ON inventarios(fecha_dato);
CREATE INDEX idx_logs_timestamp ON logs(timestamp);
CREATE INDEX idx_logs_nivel ON logs(nivel);
CREATE INDEX idx_logs_procesamiento_documento ON logs_procesamiento(documento_id);
CREATE INDEX idx_logs_procesamiento_estado ON logs_procesamiento(estado);
CREATE INDEX idx_logs_tareas_documento ON logs_tareas(documento_id);
CREATE INDEX idx_logs_tareas_estado ON logs_tareas(estado);