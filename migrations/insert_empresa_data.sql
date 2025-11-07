-- =====================================================================
-- SCRIPT DE INSERT DE EMPRESA Y ASIGNACIÓN DE id_empresa
-- Para ejecutar después de la migración multi-tenant
-- =====================================================================

BEGIN;

-- =====================================================================
-- 1. INSERTAR EMPRESA PRINCIPAL
-- =====================================================================

INSERT INTO public.empresa (nombre_empresa, rut_empresa, direccion, estado)
VALUES ('Empresa Principal (Datos Migrados)', '1-1', 'Dirección a actualizar', 'activo')
ON CONFLICT (rut_empresa) DO NOTHING;

-- Obtener el ID de la empresa recién creada (o existente)
-- Para PostgreSQL, usamos una variable temporal

DO $$
DECLARE
    empresa_default_id INTEGER;
BEGIN
    -- Obtener el id_empresa de la empresa por defecto
    SELECT id_empresa INTO empresa_default_id 
    FROM public.empresa 
    WHERE rut_empresa = '1-1';

    -- =====================================================================
    -- 2. ACTUALIZAR TODAS LAS TABLAS CON id_empresa
    -- =====================================================================

    -- Actualizar tabla usuario (si hay registros sin id_empresa)
    UPDATE public.usuario 
    SET id_empresa = empresa_default_id 
    WHERE id_empresa IS NULL;

    -- Actualizar tabla supervision
    UPDATE public.supervision 
    SET id_empresa = empresa_default_id 
    WHERE id_empresa IS NULL;

    -- Actualizar tabla mapa
    UPDATE public.mapa 
    SET id_empresa = empresa_default_id 
    WHERE id_empresa IS NULL;

    -- Actualizar tabla objeto_mapa
    UPDATE public.objeto_mapa 
    SET id_empresa = empresa_default_id 
    WHERE id_empresa IS NULL;

    -- Actualizar tabla mueble_reposicion
    UPDATE public.mueble_reposicion 
    SET id_empresa = empresa_default_id 
    WHERE id_empresa IS NULL;

    -- Actualizar tabla producto
    UPDATE public.producto 
    SET id_empresa = empresa_default_id 
    WHERE id_empresa IS NULL;

    -- Actualizar tabla punto_reposicion
    UPDATE public.punto_reposicion 
    SET id_empresa = empresa_default_id 
    WHERE id_empresa IS NULL;

    -- Actualizar tabla tarea
    UPDATE public.tarea 
    SET id_empresa = empresa_default_id 
    WHERE id_empresa IS NULL;

    -- Actualizar tabla ruta_optimizada
    UPDATE public.ruta_optimizada 
    SET id_empresa = empresa_default_id 
    WHERE id_empresa IS NULL;

    -- Mostrar mensaje de confirmación
    RAISE NOTICE 'Se actualizaron todas las tablas con id_empresa = %', empresa_default_id;

END $$;

-- =====================================================================
-- 3. INSERTAR PLANES DE SUSCRIPCIÓN (OPCIONAL)
-- =====================================================================

INSERT INTO public.plan_suscripcion (nombre_plan, descripcion, precio_mensual, limite_usuarios, limite_rutas_mes, soporte_ia, estado)
VALUES 
    ('Plan Básico', 'Ideal para pequeñas empresas con hasta 5 usuarios', 9990.00, 5, 100, FALSE, 'activo'),
    ('Plan Profesional', 'Para empresas en crecimiento con IA incluida', 29990.00, 20, 500, TRUE, 'activo'),
    ('Plan Enterprise', 'Solución completa sin límites para grandes empresas', 99990.00, NULL, NULL, TRUE, 'activo')
ON CONFLICT (nombre_plan) DO NOTHING;

-- =====================================================================
-- 4. ASIGNAR PLAN A LA EMPRESA PRINCIPAL
-- =====================================================================

INSERT INTO public.empresa_suscripcion (id_empresa, id_plan, fecha_inicio, fecha_fin, estado_pago)
SELECT 
    e.id_empresa,
    p.id_plan,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP + INTERVAL '1 year',
    'pagado'
FROM public.empresa e
CROSS JOIN public.plan_suscripcion p
WHERE e.rut_empresa = '1-1' 
  AND p.nombre_plan = 'Plan Enterprise'
ON CONFLICT (id_empresa) DO NOTHING;

-- =====================================================================
-- 5. VERIFICAR RESULTADOS
-- =====================================================================

-- Mostrar la empresa creada
SELECT 'EMPRESA CREADA:' as info, id_empresa, nombre_empresa, rut_empresa, estado 
FROM public.empresa 
WHERE rut_empresa = '1-1';

-- Contar registros actualizados por tabla
SELECT 'USUARIOS:' as tabla, COUNT(*) as total, COUNT(id_empresa) as con_empresa
FROM public.usuario
UNION ALL
SELECT 'SUPERVISIONES:', COUNT(*), COUNT(id_empresa)
FROM public.supervision
UNION ALL
SELECT 'MAPAS:', COUNT(*), COUNT(id_empresa)
FROM public.mapa
UNION ALL
SELECT 'OBJETOS_MAPA:', COUNT(*), COUNT(id_empresa)
FROM public.objeto_mapa
UNION ALL
SELECT 'MUEBLES:', COUNT(*), COUNT(id_empresa)
FROM public.mueble_reposicion
UNION ALL
SELECT 'PRODUCTOS:', COUNT(*), COUNT(id_empresa)
FROM public.producto
UNION ALL
SELECT 'PUNTOS:', COUNT(*), COUNT(id_empresa)
FROM public.punto_reposicion
UNION ALL
SELECT 'TAREAS:', COUNT(*), COUNT(id_empresa)
FROM public.tarea
UNION ALL
SELECT 'RUTAS:', COUNT(*), COUNT(id_empresa)
FROM public.ruta_optimizada;

-- Mostrar planes de suscripción
SELECT 'PLANES CREADOS:' as info, id_plan, nombre_plan, precio_mensual, limite_usuarios
FROM public.plan_suscripcion
ORDER BY precio_mensual;

-- Mostrar suscripción activa de la empresa
SELECT 'SUSCRIPCIÓN ACTIVA:' as info, 
       e.nombre_empresa, 
       p.nombre_plan, 
       s.estado_pago,
       s.fecha_inicio,
       s.fecha_fin
FROM public.empresa_suscripcion s
JOIN public.empresa e ON s.id_empresa = e.id_empresa
JOIN public.plan_suscripcion p ON s.id_plan = p.id_plan
WHERE e.rut_empresa = '1-1';

COMMIT;

-- =====================================================================
-- FIN DEL SCRIPT
-- =====================================================================
