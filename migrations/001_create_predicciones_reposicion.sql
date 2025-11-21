-- ================================================================
-- Migración: Crear tabla predicciones_reposicion
-- ================================================================
-- Descripción: Tabla para almacenar predicciones ML de reposiciones
-- Fecha: 2025-11-21
-- Autor: POE Backend Team
-- ================================================================

CREATE TABLE IF NOT EXISTS public.predicciones_reposicion (
    -- IDENTIFICACIÓN
    id_prediccion SERIAL PRIMARY KEY,
    id_empresa INTEGER NOT NULL,
    
    -- PERÍODO DE PREDICCIÓN
    mes INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12),
    anio INTEGER NOT NULL CHECK (anio >= 2024),
    semana_mes INTEGER CHECK (semana_mes BETWEEN 1 AND 5),
    
    -- METADATA DEL MODELO
    version_modelo VARCHAR(20) DEFAULT '1.0.0',
    fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    generado_por INTEGER,
    
    -- RESULTADOS DE LA PREDICCIÓN (JSON)
    resultados_prediccion JSONB NOT NULL,
    
    -- FEATURES USADOS (JSON)
    features_utilizados JSONB,
    
    -- ESTADO Y NOTAS
    estado VARCHAR(20) DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'aplicado', 'rechazado')),
    notas TEXT,
    
    -- AUDITORÍA
    fecha_actualizacion TIMESTAMP,
    
    -- FOREIGN KEYS
    CONSTRAINT fk_prediccion_empresa 
        FOREIGN KEY (id_empresa) 
        REFERENCES public.empresa(id_empresa) 
        ON DELETE CASCADE,
    
    CONSTRAINT fk_prediccion_usuario 
        FOREIGN KEY (generado_por) 
        REFERENCES public.usuario(id_usuario) 
        ON DELETE SET NULL,
    
    -- CONSTRAINT ÚNICO: Evitar duplicados para mismo mes/año/empresa
    CONSTRAINT uq_prediccion_empresa_periodo 
        UNIQUE (id_empresa, mes, anio, semana_mes)
);

-- ================================================================
-- ÍNDICES PARA OPTIMIZACIÓN DE QUERIES
-- ================================================================

-- Índice para queries por empresa (multi-tenant)
CREATE INDEX IF NOT EXISTS idx_prediccion_empresa 
    ON public.predicciones_reposicion(id_empresa);

-- Índice para búsquedas por período
CREATE INDEX IF NOT EXISTS idx_prediccion_periodo 
    ON public.predicciones_reposicion(anio, mes);

-- Índice para filtrado por estado
CREATE INDEX IF NOT EXISTS idx_prediccion_estado 
    ON public.predicciones_reposicion(estado);

-- Índice compuesto para queries frecuentes (empresa + fecha)
CREATE INDEX IF NOT EXISTS idx_prediccion_empresa_fecha 
    ON public.predicciones_reposicion(id_empresa, fecha_generacion DESC);

-- Índice GIN para búsquedas JSONB (opcional, si se requiere búsqueda dentro de JSON)
CREATE INDEX IF NOT EXISTS idx_prediccion_resultados_gin 
    ON public.predicciones_reposicion USING GIN (resultados_prediccion);

-- ================================================================
-- COMENTARIOS EN TABLA Y COLUMNAS
-- ================================================================

COMMENT ON TABLE public.predicciones_reposicion IS 
'Tabla para almacenar predicciones ML de reposiciones generadas por el modelo RandomForest';

COMMENT ON COLUMN public.predicciones_reposicion.id_prediccion IS 
'ID único de la predicción';

COMMENT ON COLUMN public.predicciones_reposicion.id_empresa IS 
'FK a empresa (multi-tenant)';

COMMENT ON COLUMN public.predicciones_reposicion.mes IS 
'Mes predicho (1-12)';

COMMENT ON COLUMN public.predicciones_reposicion.anio IS 
'Año predicho';

COMMENT ON COLUMN public.predicciones_reposicion.semana_mes IS 
'Semana del mes (1-5, opcional)';

COMMENT ON COLUMN public.predicciones_reposicion.version_modelo IS 
'Versión del pipeline ML usado (ej: 1.0.0)';

COMMENT ON COLUMN public.predicciones_reposicion.resultados_prediccion IS 
'JSONB con resultados: resumen, por_categoria, por_semana';

COMMENT ON COLUMN public.predicciones_reposicion.features_utilizados IS 
'JSONB con metadata de features y métricas del modelo';

COMMENT ON COLUMN public.predicciones_reposicion.estado IS 
'Estado de la predicción: pendiente, aplicado, rechazado';

-- ================================================================
-- VERIFICACIÓN
-- ================================================================

-- Verificar que la tabla se creó correctamente
SELECT 
    table_name, 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public' 
  AND table_name = 'predicciones_reposicion'
ORDER BY ordinal_position;

-- Verificar índices creados
SELECT 
    indexname, 
    indexdef
FROM pg_indexes
WHERE tablename = 'predicciones_reposicion'
ORDER BY indexname;

-- ================================================================
-- DATOS DE PRUEBA (OPCIONAL - COMENTAR EN PRODUCCIÓN)
-- ================================================================

-- INSERT INTO public.predicciones_reposicion 
-- (id_empresa, mes, anio, version_modelo, generado_por, resultados_prediccion, features_utilizados)
-- VALUES 
-- (
--     1, 
--     12, 
--     2025, 
--     '1.0.0',
--     1,
--     '{
--         "resumen": {
--             "total_reposiciones": 145,
--             "total_unidades": 3850,
--             "categorias_activas": ["Lacteos", "Panaderia"],
--             "promedio_diario": 124.2
--         },
--         "por_categoria": [
--             {
--                 "categoria": "Lacteos",
--                 "ubicacion_mueble": 118,
--                 "reposiciones": 25,
--                 "total_unidades": 780,
--                 "dias_predichos": [1, 3, 5, 8]
--             }
--         ],
--         "por_semana": []
--     }'::jsonb,
--     '{
--         "features": ["categoria_producto", "ubicacion_mueble", "hora"],
--         "accuracy_clasificador": 0.89,
--         "r2_regresor": 0.76
--     }'::jsonb
-- );

-- ================================================================
-- FIN DE MIGRACIÓN
-- ================================================================
