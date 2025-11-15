-- ============================================
-- MIGRACIÓN 002: MÓDULO BACKOFFICE Y AUDITORÍA
-- ============================================
-- Descripción: 
--   - Agrega sistema de auditoría completo (tabla log_auditoria)
--   - Agrega campo modulos_habilitados a plan_empresa
--   - Crea índices para optimizar consultas de auditoría
--   - Agrega trigger para updated_at en log_auditoria
-- 
-- Autor: Sistema POE
-- Fecha: 15 de noviembre de 2025
-- Versión: 002
-- ============================================

-- Limpiar transacciones abortadas previas
ROLLBACK;

BEGIN;

-- ============================================
-- 1. CREAR TABLA LOG_AUDITORIA
-- ============================================

CREATE TABLE IF NOT EXISTS log_auditoria (
    id_log SERIAL PRIMARY KEY,
    id_usuario INTEGER NOT NULL,
    nombre_usuario VARCHAR(255) NOT NULL,
    accion VARCHAR(100) NOT NULL,
    entidad VARCHAR(100) NOT NULL,
    id_entidad INTEGER,
    datos_anteriores JSONB,
    datos_nuevos JSONB,
    ip_origen VARCHAR(45),
    user_agent TEXT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Keys
    CONSTRAINT fk_log_usuario FOREIGN KEY (id_usuario) 
        REFERENCES usuario(id_usuario) ON DELETE RESTRICT
);

-- Comentarios de tabla
COMMENT ON TABLE log_auditoria IS 'Registro completo de auditoría para todas las acciones de SuperAdmin';
COMMENT ON COLUMN log_auditoria.id_log IS 'Identificador único del registro de auditoría';
COMMENT ON COLUMN log_auditoria.id_usuario IS 'ID del usuario que realizó la acción';
COMMENT ON COLUMN log_auditoria.nombre_usuario IS 'Nombre del usuario (desnormalizado para histórico)';
COMMENT ON COLUMN log_auditoria.accion IS 'Tipo de acción: CREATE, UPDATE, DELETE, SUSPEND, REACTIVATE, etc.';
COMMENT ON COLUMN log_auditoria.entidad IS 'Nombre de la entidad modificada: Empresa, PlanEmpresa, Usuario, etc.';
COMMENT ON COLUMN log_auditoria.id_entidad IS 'ID del registro específico modificado';
COMMENT ON COLUMN log_auditoria.datos_anteriores IS 'Estado previo del registro en formato JSON';
COMMENT ON COLUMN log_auditoria.datos_nuevos IS 'Estado posterior del registro en formato JSON';
COMMENT ON COLUMN log_auditoria.ip_origen IS 'Dirección IP desde donde se realizó la acción';
COMMENT ON COLUMN log_auditoria.user_agent IS 'User-Agent del navegador/cliente';
COMMENT ON COLUMN log_auditoria.fecha IS 'Timestamp de cuándo se realizó la acción';

-- ============================================
-- 2. ÍNDICES PARA LOG_AUDITORIA
-- ============================================

-- Índice por usuario (para ver todas las acciones de un SuperAdmin)
CREATE INDEX IF NOT EXISTS idx_log_auditoria_usuario 
    ON log_auditoria(id_usuario);

-- Índice por tipo de acción (para filtrar CREATE, UPDATE, DELETE, etc.)
CREATE INDEX IF NOT EXISTS idx_log_auditoria_accion 
    ON log_auditoria(accion);

-- Índice por entidad (para ver todos los cambios en Empresa, PlanEmpresa, etc.)
CREATE INDEX IF NOT EXISTS idx_log_auditoria_entidad 
    ON log_auditoria(entidad);

-- Índice por fecha (para consultas por rango de fechas)
CREATE INDEX IF NOT EXISTS idx_log_auditoria_fecha 
    ON log_auditoria(fecha DESC);

-- Índice compuesto para consultas específicas de entidad
CREATE INDEX IF NOT EXISTS idx_log_auditoria_entidad_id 
    ON log_auditoria(entidad, id_entidad);

-- Índice compuesto para consultas por usuario y fecha
CREATE INDEX IF NOT EXISTS idx_log_auditoria_usuario_fecha 
    ON log_auditoria(id_usuario, fecha DESC);

-- Índice GIN para búsquedas en JSONB (datos_nuevos y datos_anteriores)
CREATE INDEX IF NOT EXISTS idx_log_auditoria_datos_nuevos 
    ON log_auditoria USING GIN (datos_nuevos);

CREATE INDEX IF NOT EXISTS idx_log_auditoria_datos_anteriores 
    ON log_auditoria USING GIN (datos_anteriores);

-- ============================================
-- 3. MODIFICAR TABLA PLAN_EMPRESA
-- ============================================

-- Agregar campo modulos_habilitados
ALTER TABLE plan_empresa 
ADD COLUMN IF NOT EXISTS modulos_habilitados JSONB DEFAULT '{
    "optimizacion_rutas": true,
    "chat_supervisor": true,
    "reportes_avanzados": true,
    "dashboard_ejecutivo": true,
    "multilocal": true,
    "app_movil": false,
    "integraciones_api": false,
    "soporte_prioritario": false
}'::jsonb;

COMMENT ON COLUMN plan_empresa.modulos_habilitados IS 'Módulos específicos habilitados/deshabilitados por el SuperAdmin para esta empresa';

-- ============================================
-- 4. FUNCIÓN PARA UPDATED_AT AUTOMÁTICO
-- ============================================

-- Crear función si no existe
CREATE OR REPLACE FUNCTION actualizar_fecha_modificacion()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 5. TRIGGERS
-- ============================================

-- No agregamos trigger a log_auditoria porque fecha es immutable (solo INSERT)
-- El log no se debe modificar después de creado

-- ============================================
-- 6. PERMISOS Y SEGURIDAD
-- ============================================

-- Crear rol específico para auditoría si no existe
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'poe_auditor') THEN
        CREATE ROLE poe_auditor;
    END IF;
END
$$;

-- Permisos de solo lectura para auditor
GRANT SELECT ON log_auditoria TO poe_auditor;

-- ============================================
-- 7. DATOS INICIALES
-- ============================================

-- Insertar log inicial de creación del sistema de auditoría
-- Solo si existe al menos un usuario SuperAdmin
DO $$
DECLARE
    admin_id INTEGER;
BEGIN
    -- Buscar primer usuario SuperAdmin (rol_id = 1 generalmente es Admin/SuperAdmin)
    SELECT id_usuario INTO admin_id 
    FROM usuario 
    WHERE rol_id = 1 
    LIMIT 1;
    
    IF admin_id IS NOT NULL THEN
        INSERT INTO log_auditoria (
            id_usuario,
            nombre_usuario,
            accion,
            entidad,
            id_entidad,
            datos_nuevos,
            ip_origen,
            user_agent
        ) VALUES (
            admin_id,
            'Sistema',
            'CREATE_SYSTEM',
            'log_auditoria',
            NULL,
            '{"descripcion": "Sistema de auditoría inicializado", "version": "002", "modulo": "Backoffice/SuperAdmin"}'::jsonb,
            '127.0.0.1',
            'PostgreSQL Migration Script'
        );
    ELSE
        RAISE NOTICE 'No se encontró usuario SuperAdmin. Log inicial no creado.';
    END IF;
END
$$;

-- ============================================
-- 8. VALIDACIONES
-- ============================================

-- Verificar que la tabla se creó correctamente
DO $$
DECLARE
    tabla_existe BOOLEAN;
    columna_existe BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'log_auditoria'
    ) INTO tabla_existe;
    
    IF NOT tabla_existe THEN
        RAISE EXCEPTION 'Error: Tabla log_auditoria no fue creada';
    END IF;
    
    SELECT EXISTS (
        SELECT FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'plan_empresa'
        AND column_name = 'modulos_habilitados'
    ) INTO columna_existe;
    
    IF NOT columna_existe THEN
        RAISE EXCEPTION 'Error: Columna modulos_habilitados no fue agregada a plan_empresa';
    END IF;
    
    RAISE NOTICE 'Migración 002 completada exitosamente';
    RAISE NOTICE '  ✓ Tabla log_auditoria creada';
    RAISE NOTICE '  ✓ 8 índices creados en log_auditoria';
    RAISE NOTICE '  ✓ Campo modulos_habilitados agregado a plan_empresa';
    RAISE NOTICE '  ✓ Permisos configurados';
    RAISE NOTICE '  ✓ Log inicial insertado';
END
$$;

-- ============================================
-- 9. ROLLBACK SCRIPT (PARA REFERENCIA)
-- ============================================

-- ROLLBACK:
-- DROP INDEX IF EXISTS idx_log_auditoria_datos_anteriores;
-- DROP INDEX IF EXISTS idx_log_auditoria_datos_nuevos;
-- DROP INDEX IF EXISTS idx_log_auditoria_usuario_fecha;
-- DROP INDEX IF EXISTS idx_log_auditoria_entidad_id;
-- DROP INDEX IF EXISTS idx_log_auditoria_fecha;
-- DROP INDEX IF EXISTS idx_log_auditoria_entidad;
-- DROP INDEX IF EXISTS idx_log_auditoria_accion;
-- DROP INDEX IF EXISTS idx_log_auditoria_usuario;
-- DROP TABLE IF EXISTS log_auditoria CASCADE;
-- ALTER TABLE plan_empresa DROP COLUMN IF EXISTS modulos_habilitados;
-- DROP ROLE IF EXISTS poe_auditor;

COMMIT;

-- ============================================
-- FIN DE MIGRACIÓN 002
-- ============================================
