-- Agregar columna nombre_entidad a log_auditoria
ALTER TABLE log_auditoria 
ADD COLUMN IF NOT EXISTS nombre_entidad VARCHAR(255);

COMMENT ON COLUMN log_auditoria.nombre_entidad IS 'Nombre descriptivo de la entidad afectada (para histórico)';
