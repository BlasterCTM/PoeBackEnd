-- =====================================================================
-- MIGRACIÓN: Agregar columnas de contacto a tabla empresa
-- Fecha: 7 de noviembre de 2025
-- Descripción: Agrega campos de contacto necesarios para registro B2B
-- =====================================================================

BEGIN;

-- Agregar columnas de contacto a la tabla empresa
ALTER TABLE empresa 
ADD COLUMN IF NOT EXISTS ciudad VARCHAR(100),
ADD COLUMN IF NOT EXISTS region VARCHAR(100),
ADD COLUMN IF NOT EXISTS telefono VARCHAR(20),
ADD COLUMN IF NOT EXISTS email VARCHAR(255);

-- Crear índice para búsquedas por email
CREATE INDEX IF NOT EXISTS idx_empresa_email ON empresa(email);

-- Crear índice para búsquedas por ciudad
CREATE INDEX IF NOT EXISTS idx_empresa_ciudad ON empresa(ciudad);

-- Hacer el campo rut_empresa NOT NULL si aún no lo es
ALTER TABLE empresa 
ALTER COLUMN rut_empresa SET NOT NULL;

-- Verificar las columnas agregadas
SELECT 
    'Columnas agregadas exitosamente' as mensaje,
    COUNT(*) as total_empresas
FROM empresa;

-- Mostrar estructura de la tabla
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'empresa'
ORDER BY ordinal_position;

COMMIT;

-- =====================================================================
-- NOTAS:
-- 1. Las columnas ciudad, region, telefono y email son opcionales (nullable)
-- 2. El campo rut_empresa ahora es obligatorio (NOT NULL)
-- 3. Se crearon índices para mejorar el rendimiento de búsquedas
-- =====================================================================
