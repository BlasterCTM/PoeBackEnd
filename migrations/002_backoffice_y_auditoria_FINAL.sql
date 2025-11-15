-- ============================================
-- MIGRACIÓN SIMPLE: BACKOFFICE Y AUDITORÍA
-- ============================================
-- INSTRUCCIONES: 
-- 1. Cierra y reabre tu conexión SQL
-- 2. Copia y pega TODO este archivo
-- 3. Ejecuta
-- ============================================

-- 1. CREAR TABLA LOG_AUDITORIA
DROP TABLE IF EXISTS log_auditoria CASCADE;

CREATE TABLE log_auditoria (
    id_log SERIAL PRIMARY KEY,
    id_usuario INTEGER NOT NULL REFERENCES usuario(id_usuario) ON DELETE RESTRICT,
    nombre_usuario VARCHAR(255) NOT NULL,
    accion VARCHAR(100) NOT NULL,
    entidad VARCHAR(100) NOT NULL,
    id_entidad INTEGER,
    datos_anteriores JSONB,
    datos_nuevos JSONB,
    ip_origen VARCHAR(45),
    user_agent TEXT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. ÍNDICES
CREATE INDEX idx_log_auditoria_usuario ON log_auditoria(id_usuario);
CREATE INDEX idx_log_auditoria_accion ON log_auditoria(accion);
CREATE INDEX idx_log_auditoria_entidad ON log_auditoria(entidad);
CREATE INDEX idx_log_auditoria_fecha ON log_auditoria(fecha DESC);
CREATE INDEX idx_log_auditoria_entidad_id ON log_auditoria(entidad, id_entidad);

-- 3. AGREGAR CAMPO A PLAN_EMPRESA
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'plan_empresa' AND column_name = 'modulos_habilitados'
    ) THEN
        ALTER TABLE plan_empresa 
        ADD COLUMN modulos_habilitados JSONB DEFAULT '{"optimizacion_rutas": true, "chat_supervisor": true, "reportes_avanzados": true, "dashboard_ejecutivo": true, "multilocal": true, "app_movil": false, "integraciones_api": false, "soporte_prioritario": false}';
    END IF;
END
$$;

-- ============================================
-- FIN DE MIGRACIÓN 002
-- ============================================
