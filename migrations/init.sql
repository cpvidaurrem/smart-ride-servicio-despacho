-- Crear los tipos ENUM primero
CREATE TYPE estadoconductor AS ENUM ('DISPONIBLE', 'OCUPADO', 'INACTIVO', 'DESCONECTADO');
CREATE TYPE estadoasignacion AS ENUM ('ASIGNADO', 'ACEPTADO', 'RECHAZADO', 'CANCELADO', 'COMPLETADO');
CREATE TYPE tipoalgoritmo AS ENUM ('ROUND_ROBIN', 'CERCANIA', 'CALIFICACION', 'MENOR_CARGA');

-- Tabla de conductores
CREATE TABLE IF NOT EXISTS conductores (
    id_conductor SERIAL PRIMARY KEY,
    id_usuario INTEGER NOT NULL UNIQUE,
    nombre_completo VARCHAR(200) NOT NULL,
    licencia VARCHAR(50) NOT NULL UNIQUE,
    modelo_auto VARCHAR(100) NOT NULL,
    placa_auto VARCHAR(20) NOT NULL UNIQUE,
    estado estadoconductor NOT NULL DEFAULT 'DESCONECTADO',
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

-- Tabla de asignaciones
CREATE TABLE IF NOT EXISTS asignaciones (
    id_asignacion SERIAL PRIMARY KEY,
    id_viaje INTEGER NOT NULL,
    id_conductor INTEGER NOT NULL,
    id_pasajero INTEGER NOT NULL,
    origen VARCHAR(200) NOT NULL,
    destino VARCHAR(200) NOT NULL,
    estado estadoasignacion NOT NULL DEFAULT 'ASIGNADO',
    algoritmo_usado tipoalgoritmo NOT NULL DEFAULT 'ROUND_ROBIN',
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

-- Trigger para actualizar ultima_actualizacion
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.ultima_actualizacion = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_conductor_timestamp
BEFORE UPDATE ON conductores
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

-- Datos de prueba (usando valores ENUM correctos)
INSERT INTO conductores (id_usuario, nombre_completo, licencia, modelo_auto, placa_auto, estado, calificacion_promedio, ubicacion_lat, ubicacion_lng)
VALUES 
    (101, 'Juan Carlos Pérez', 'LIC-12345', 'Toyota Corolla 2020', 'ABC-1234', 'DISPONIBLE', 4.8, -19.0469, -65.2592),
    (102, 'María González', 'LIC-54321', 'Honda Civic 2021', 'DEF-5678', 'DISPONIBLE', 4.9, -19.0500, -65.2600),
    (103, 'Pedro Mamani', 'LIC-67890', 'Chevrolet Cruze 2019', 'GHI-9012', 'DISPONIBLE', 4.7, -19.0430, -65.2580),
    (104, 'Ana Quispe', 'LIC-11111', 'Volkswagen Gol 2022', 'JKL-3456', 'OCUPADO', 5.0, -19.0490, -65.2610),
    (105, 'Roberto Silva', 'LIC-22222', 'Ford Fiesta 2020', 'MNO-7890', 'DISPONIBLE', 4.6, -19.0460, -65.2570)
ON CONFLICT (id_usuario) DO NOTHING;

-- Mensaje de confirmación
DO $$
BEGIN
    RAISE NOTICE '✅ Base de datos inicializada correctamente';
END $$;