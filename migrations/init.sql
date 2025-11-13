-- Script de inicialización de base de datos
-- Servicio de Despacho - Smart Ride

-- Crear extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tabla de conductores
CREATE TABLE IF NOT EXISTS conductores (
    id_conductor SERIAL PRIMARY KEY,
    id_usuario INTEGER NOT NULL UNIQUE,
    nombre_completo VARCHAR(200) NOT NULL,
    licencia VARCHAR(50) NOT NULL UNIQUE,
    modelo_auto VARCHAR(100) NOT NULL,
    placa_auto VARCHAR(20) NOT NULL UNIQUE,
    estado VARCHAR(20) NOT NULL DEFAULT 'desconectado'
        CHECK (estado IN ('disponible', 'ocupado', 'inactivo', 'desconectado')),
    ubicacion_lat DOUBLE PRECISION,
    ubicacion_lng DOUBLE PRECISION,
    calificacion_promedio REAL DEFAULT 5.0,
    viajes_completados INTEGER DEFAULT 0,
    ultima_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices para conductores
CREATE INDEX IF NOT EXISTS idx_conductores_estado ON conductores(estado);
CREATE INDEX IF NOT EXISTS idx_conductores_usuario ON conductores(id_usuario);
CREATE INDEX IF NOT EXISTS idx_conductores_calificacion ON conductores(calificacion_promedio DESC);

-- Tabla de asignaciones
CREATE TABLE IF NOT EXISTS asignaciones (
    id_asignacion SERIAL PRIMARY KEY,
    id_viaje INTEGER NOT NULL,
    id_conductor INTEGER NOT NULL,
    id_pasajero INTEGER NOT NULL,
    origen VARCHAR(200) NOT NULL,
    destino VARCHAR(200) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'asignado'
        CHECK (estado IN ('asignado', 'aceptado', 'rechazado', 'cancelado', 'completado')),
    algoritmo_usado VARCHAR(30) NOT NULL DEFAULT 'round_robin'
        CHECK (algoritmo_usado IN ('round_robin', 'cercania', 'calificacion', 'menor_carga')),
    prioridad INTEGER DEFAULT 1,
    tiempo_asignacion_ms INTEGER,
    distancia_estimada_km REAL,
    motivo_rechazo TEXT,
    fecha_asignacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_conductor) REFERENCES conductores(id_conductor) ON DELETE CASCADE
);

-- Índices para asignaciones
CREATE INDEX IF NOT EXISTS idx_asignaciones_viaje ON asignaciones(id_viaje);
CREATE INDEX IF NOT EXISTS idx_asignaciones_conductor ON asignaciones(id_conductor);
CREATE INDEX IF NOT EXISTS idx_asignaciones_estado ON asignaciones(estado);
CREATE INDEX IF NOT EXISTS idx_asignaciones_fecha ON asignaciones(fecha_asignacion DESC);

-- Trigger para actualizar ultima_actualizacion en conductores
CREATE OR REPLACE FUNCTION update_conductor_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.ultima_actualizacion = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_conductor_timestamp
BEFORE UPDATE ON conductores
FOR EACH ROW
EXECUTE FUNCTION update_conductor_timestamp();

-- Trigger para actualizar fecha_actualizacion en asignaciones
CREATE OR REPLACE FUNCTION update_asignacion_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_asignacion_timestamp
BEFORE UPDATE ON asignaciones
FOR EACH ROW
EXECUTE FUNCTION update_asignacion_timestamp();

-- Insertar datos de prueba
INSERT INTO conductores (id_usuario, nombre_completo, licencia, modelo_auto, placa_auto, estado, calificacion_promedio, ubicacion_lat, ubicacion_lng)
VALUES 
    (101, 'Juan Carlos Pérez', 'LIC-12345', 'Toyota Corolla 2020', 'ABC-1234', 'disponible', 4.8, -19.0469, -65.2592),
    (102, 'María González', 'LIC-54321', 'Honda Civic 2021', 'DEF-5678', 'disponible', 4.9, -19.0500, -65.2600),
    (103, 'Pedro Mamani', 'LIC-67890', 'Chevrolet Cruze 2019', 'GHI-9012', 'disponible', 4.7, -19.0430, -65.2580),
    (104, 'Ana Quispe', 'LIC-11111', 'Volkswagen Gol 2022', 'JKL-3456', 'ocupado', 5.0, -19.0490, -65.2610),
    (105, 'Roberto Silva', 'LIC-22222', 'Ford Fiesta 2020', 'MNO-7890', 'disponible', 4.6, -19.0460, -65.2570)
ON CONFLICT (id_usuario) DO NOTHING;

-- Vista para conductores disponibles con toda su información
CREATE OR REPLACE VIEW v_conductores_disponibles AS
SELECT 
    id_conductor,
    nombre_completo,
    modelo_auto,
    placa_auto,
    calificacion_promedio,
    viajes_completados,
    ubicacion_lat,
    ubicacion_lng,
    ultima_actualizacion
FROM conductores
WHERE estado = 'disponible'
ORDER BY calificacion_promedio DESC, viajes_completados ASC;

-- Vista de estadísticas de asignaciones
CREATE OR REPLACE VIEW v_estadisticas_asignaciones AS
SELECT 
    COUNT(*) as total_asignaciones,
    COUNT(CASE WHEN estado = 'completado' THEN 1 END) as asignaciones_exitosas,
    COUNT(CASE WHEN estado = 'rechazado' THEN 1 END) as asignaciones_rechazadas,
    COUNT(CASE WHEN estado = 'cancelado' THEN 1 END) as asignaciones_canceladas,
    AVG(tiempo_asignacion_ms) as tiempo_promedio_ms,
    MODE() WITHIN GROUP (ORDER BY algoritmo_usado) as algoritmo_mas_usado
FROM asignaciones;

-- Comentarios en tablas
COMMENT ON TABLE conductores IS 'Conductores registrados en el sistema de despacho';
COMMENT ON TABLE asignaciones IS 'Historial de asignaciones de conductores a viajes';

-- Información de la base de datos
DO $$
BEGIN
    RAISE NOTICE '✅ Base de datos inicializada correctamente';
    RAISE NOTICE '📊 Tablas creadas: conductores, asignaciones';
    RAISE NOTICE '👥 Conductores de prueba insertados: 5';
END $$;