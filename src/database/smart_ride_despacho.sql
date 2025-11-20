-- ================================================
-- TABLA: disponibilidad_conductores
-- ================================================
CREATE TABLE disponibilidad_conductores (
    id_conductor INTEGER PRIMARY KEY,         -- ← FK lógica → conductores.id_conductor (INT)
    estado_actual VARCHAR(20) NOT NULL DEFAULT 'desconectado'
        CHECK (estado_actual IN ('disponible', 'ocupado', 'desconectado', 'pausa')),
    zona_cobertura VARCHAR(100),
    ultima_actualizacion TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_disp_conductor ON disponibilidad_conductores(id_conductor);
CREATE INDEX idx_disp_estado ON disponibilidad_conductores(estado_actual);
CREATE INDEX idx_disp_actualizacion ON disponibilidad_conductores(ultima_actualizacion);

-- ================================================
-- TABLA: asignaciones
-- ================================================
CREATE TABLE asignaciones (
    id_asignacion SERIAL PRIMARY KEY,        
    id_viaje BIGINT NOT NULL,                 -- ← FK lógica → viajes.id_viaje (BIGINT)
    id_conductor INTEGER NOT NULL,            -- ← FK lógica → conductores.id_conductor (INT)
    metodo_asignacion VARCHAR(20) NOT NULL DEFAULT 'automatico'
        CHECK (metodo_asignacion IN ('automatico', 'manual')),
    prioridad SMALLINT DEFAULT 0,
    estado_asignacion VARCHAR(20) NOT NULL DEFAULT 'pendiente'
        CHECK (estado_asignacion IN ('pendiente', 'asignado', 'confirmado', 'rechazado')),
    fecha_asignacion TIMESTAMP NOT NULL DEFAULT NOW(),
    fecha_confirmacion TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_asignaciones_viaje ON asignaciones(id_viaje);
CREATE INDEX idx_asignaciones_conductor ON asignaciones(id_conductor);
CREATE INDEX idx_asignaciones_estado ON asignaciones(estado_asignacion);