-- ============================================
-- MIGRACIÓN MULTI-TENANT PARA POE
-- Transforma la aplicación a arquitectura SaaS
-- ============================================

-- 1. CREAR TABLA EMPRESA (TENANTS)
CREATE TABLE IF NOT EXISTS empresa (
    id_empresa SERIAL PRIMARY KEY,
    nombre_empresa VARCHAR(200) NOT NULL,
    rut_empresa VARCHAR(20) UNIQUE NOT NULL,
    direccion VARCHAR(300),
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado VARCHAR(20) DEFAULT 'activa'
);

-- 2. CREAR TABLA PLAN_SUSCRIPCION
CREATE TABLE IF NOT EXISTS plan_suscripcion (
    id_plan SERIAL PRIMARY KEY,
    nombre_plan VARCHAR(100) UNIQUE NOT NULL,
    descripcion TEXT,
    precio_mensual NUMERIC(10, 2) NOT NULL,
    limite_usuarios INTEGER,
    limite_rutas_mes INTEGER,
    soporte_ia BOOLEAN DEFAULT FALSE,
    estado VARCHAR(20) DEFAULT 'activo'
);

-- 3. CREAR TABLA EMPRESA_SUSCRIPCION
CREATE TABLE IF NOT EXISTS empresa_suscripcion (
    id_suscripcion SERIAL PRIMARY KEY,
    id_empresa INTEGER UNIQUE NOT NULL REFERENCES empresa(id_empresa) ON DELETE CASCADE,
    id_plan INTEGER NOT NULL REFERENCES plan_suscripcion(id_plan),
    fecha_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_fin TIMESTAMP,
    estado_pago VARCHAR(20) DEFAULT 'pendiente',
    id_pago_externo VARCHAR(100)
);

-- 4. CREAR TABLAS DE CHAT
CREATE TABLE IF NOT EXISTS chat_conversacion (
    id_conversacion SERIAL PRIMARY KEY,
    id_empresa INTEGER NOT NULL REFERENCES empresa(id_empresa) ON DELETE CASCADE,
    id_supervisor INTEGER NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    id_reponedor INTEGER NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_chat_empresa_supervisor_reponedor UNIQUE (id_empresa, id_supervisor, id_reponedor)
);

CREATE TABLE IF NOT EXISTS chat_mensaje (
    id_mensaje SERIAL PRIMARY KEY,
    id_conversacion INTEGER NOT NULL REFERENCES chat_conversacion(id_conversacion) ON DELETE CASCADE,
    id_emisor INTEGER NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    contenido TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    leido BOOLEAN DEFAULT FALSE
);

-- 5. ELIMINAR TABLA OBSOLETA (usuario_punto reemplazado por id_usuario en punto_reposicion)
DROP TABLE IF EXISTS usuario_punto CASCADE;

-- 6. AGREGAR id_empresa A TABLAS EXISTENTES

-- Tabla usuario
ALTER TABLE usuario ADD COLUMN IF NOT EXISTS id_empresa INTEGER;
ALTER TABLE usuario ADD CONSTRAINT fk_usuario_empresa 
    FOREIGN KEY (id_empresa) REFERENCES empresa(id_empresa) ON DELETE CASCADE;

-- Remover constraint unique de correo (ahora será único por empresa)
ALTER TABLE usuario DROP CONSTRAINT IF EXISTS usuario_correo_key;
ALTER TABLE usuario DROP CONSTRAINT IF EXISTS uq_correo;

-- Tabla supervision
ALTER TABLE supervision ADD COLUMN IF NOT EXISTS id_empresa INTEGER;
ALTER TABLE supervision ADD CONSTRAINT fk_supervision_empresa 
    FOREIGN KEY (id_empresa) REFERENCES empresa(id_empresa) ON DELETE CASCADE;

-- Tabla mapa
ALTER TABLE mapa ADD COLUMN IF NOT EXISTS id_empresa INTEGER;
ALTER TABLE mapa ADD CONSTRAINT fk_mapa_empresa 
    FOREIGN KEY (id_empresa) REFERENCES empresa(id_empresa) ON DELETE CASCADE;

-- Tabla objeto_mapa
ALTER TABLE objeto_mapa ADD COLUMN IF NOT EXISTS id_empresa INTEGER;
ALTER TABLE objeto_mapa ADD CONSTRAINT fk_objeto_mapa_empresa 
    FOREIGN KEY (id_empresa) REFERENCES empresa(id_empresa) ON DELETE CASCADE;

-- Tabla mueble_reposicion
ALTER TABLE mueble_reposicion ADD COLUMN IF NOT EXISTS id_empresa INTEGER;
ALTER TABLE mueble_reposicion ADD CONSTRAINT fk_mueble_reposicion_empresa 
    FOREIGN KEY (id_empresa) REFERENCES empresa(id_empresa) ON DELETE CASCADE;

-- Tabla producto
ALTER TABLE producto ADD COLUMN IF NOT EXISTS id_empresa INTEGER;
ALTER TABLE producto ADD CONSTRAINT fk_producto_empresa 
    FOREIGN KEY (id_empresa) REFERENCES empresa(id_empresa) ON DELETE CASCADE;

-- Remover unique constraint global de codigo_unico
ALTER TABLE producto DROP CONSTRAINT IF EXISTS producto_codigo_unico_key;

-- Tabla punto_reposicion
ALTER TABLE punto_reposicion ADD COLUMN IF NOT EXISTS id_empresa INTEGER;
ALTER TABLE punto_reposicion ADD CONSTRAINT fk_punto_reposicion_empresa 
    FOREIGN KEY (id_empresa) REFERENCES empresa(id_empresa) ON DELETE CASCADE;

-- Tabla tarea
ALTER TABLE tarea ADD COLUMN IF NOT EXISTS id_empresa INTEGER;
ALTER TABLE tarea ADD CONSTRAINT fk_tarea_empresa 
    FOREIGN KEY (id_empresa) REFERENCES empresa(id_empresa) ON DELETE CASCADE;

-- Tabla ruta_optimizada
ALTER TABLE ruta_optimizada ADD COLUMN IF NOT EXISTS id_empresa INTEGER;
ALTER TABLE ruta_optimizada ADD CONSTRAINT fk_ruta_optimizada_empresa 
    FOREIGN KEY (id_empresa) REFERENCES empresa(id_empresa) ON DELETE CASCADE;

-- 7. CREAR EMPRESA POR DEFECTO PARA DATOS EXISTENTES
INSERT INTO empresa (nombre_empresa, rut_empresa, direccion, estado)
VALUES ('Empresa Principal (Datos Migrados)', '1-1', 'Dirección a actualizar', 'activa')
ON CONFLICT (rut_empresa) DO NOTHING;

-- 8. MIGRAR DATOS EXISTENTES A EMPRESA POR DEFECTO
-- Obtener el id de la empresa por defecto
DO $$
DECLARE
    empresa_default_id INTEGER;
BEGIN
    SELECT id_empresa INTO empresa_default_id FROM empresa WHERE rut_empresa = '1-1';
    
    -- Actualizar tablas con datos existentes
    UPDATE usuario SET id_empresa = empresa_default_id WHERE id_empresa IS NULL;
    UPDATE supervision SET id_empresa = empresa_default_id WHERE id_empresa IS NULL;
    UPDATE mapa SET id_empresa = empresa_default_id WHERE id_empresa IS NULL;
    UPDATE objeto_mapa SET id_empresa = empresa_default_id WHERE id_empresa IS NULL;
    UPDATE mueble_reposicion SET id_empresa = empresa_default_id WHERE id_empresa IS NULL;
    UPDATE producto SET id_empresa = empresa_default_id WHERE id_empresa IS NULL;
    UPDATE punto_reposicion SET id_empresa = empresa_default_id WHERE id_empresa IS NULL;
    UPDATE tarea SET id_empresa = empresa_default_id WHERE id_empresa IS NULL;
    UPDATE ruta_optimizada SET id_empresa = empresa_default_id WHERE id_empresa IS NULL;
END $$;

-- 9. HACER id_empresa NOT NULL DESPUÉS DE MIGRAR DATOS
ALTER TABLE usuario ALTER COLUMN id_empresa SET NOT NULL;
ALTER TABLE supervision ALTER COLUMN id_empresa SET NOT NULL;
ALTER TABLE mapa ALTER COLUMN id_empresa SET NOT NULL;
ALTER TABLE objeto_mapa ALTER COLUMN id_empresa SET NOT NULL;
ALTER TABLE mueble_reposicion ALTER COLUMN id_empresa SET NOT NULL;
ALTER TABLE producto ALTER COLUMN id_empresa SET NOT NULL;
ALTER TABLE punto_reposicion ALTER COLUMN id_empresa SET NOT NULL;
ALTER TABLE tarea ALTER COLUMN id_empresa SET NOT NULL;
ALTER TABLE ruta_optimizada ALTER COLUMN id_empresa SET NOT NULL;

-- 10. CREAR CONSTRAINTS ÚNICOS MULTI-TENANT

-- Correo único por empresa
ALTER TABLE usuario ADD CONSTRAINT uq_correo_empresa UNIQUE (id_empresa, correo);

-- Codigo único por empresa (productos)
ALTER TABLE producto ADD CONSTRAINT uq_codigo_empresa UNIQUE (id_empresa, codigo_unico);

-- Supervisor-reponedor único por empresa
ALTER TABLE supervision ADD CONSTRAINT uq_supervision_empresa 
    UNIQUE (id_empresa, supervisor_id, reponedor_id);

-- 11. INSERTAR PLANES DE SUSCRIPCIÓN DE EJEMPLO
INSERT INTO plan_suscripcion (nombre_plan, descripcion, precio_mensual, limite_usuarios, limite_rutas_mes, soporte_ia, estado)
VALUES 
    ('Plan Básico', 'Ideal para pequeñas empresas', 9990.00, 5, 100, FALSE, 'activo'),
    ('Plan Profesional', 'Para empresas en crecimiento', 29990.00, 20, 500, TRUE, 'activo'),
    ('Plan Enterprise', 'Solución completa sin límites', 99990.00, NULL, NULL, TRUE, 'activo')
ON CONFLICT (nombre_plan) DO NOTHING;

-- 12. ASIGNAR PLAN A EMPRESA POR DEFECTO
INSERT INTO empresa_suscripcion (id_empresa, id_plan, estado_pago)
SELECT 
    e.id_empresa,
    p.id_plan,
    'activo'
FROM empresa e
CROSS JOIN plan_suscripcion p
WHERE e.rut_empresa = '1-1' AND p.nombre_plan = 'Plan Enterprise'
ON CONFLICT (id_empresa) DO NOTHING;

-- ============================================
-- FIN DE LA MIGRACIÓN
-- ============================================
