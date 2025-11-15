-- Corregir restricción CHECK para permitir estado 'suspendido'
ALTER TABLE empresa DROP CONSTRAINT IF EXISTS empresa_estado_check;
ALTER TABLE empresa ADD CONSTRAINT empresa_estado_check CHECK (estado IN ('activo', 'inactivo', 'suspendido', 'prueba'));
