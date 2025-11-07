-- =====================================================================
-- SCRIPT SIMPLIFICADO DE INSERT PARA COPIAR/PEGAR EN pgAdmin
-- Ejecutar línea por línea o por secciones
-- =====================================================================

-- =====================================================================
-- PASO 1: CREAR LA EMPRESA PRINCIPAL
-- =====================================================================

INSERT INTO empresa (nombre_empresa, rut_empresa, direccion, estado)
VALUES ('Empresa Principal', '1-1', 'Santiago, Chile', 'activo')
ON CONFLICT (rut_empresa) DO NOTHING;

-- Verificar que se creó
SELECT * FROM empresa WHERE rut_empresa = '1-1';

-- =====================================================================
-- PASO 2: ACTUALIZAR TODAS LAS TABLAS CON id_empresa = 1
-- (Asumiendo que el id_empresa de "Empresa Principal" es 1)
-- Si es diferente, reemplaza el 1 por el id correcto
-- =====================================================================

-- Actualizar usuarios
UPDATE usuario 
SET id_empresa = 1 
WHERE id_empresa IS NULL;

-- Verificar
SELECT id_usuario, nombre, correo, id_empresa FROM usuario LIMIT 5;

-- Actualizar supervisiones
UPDATE supervision 
SET id_empresa = 1 
WHERE id_empresa IS NULL;

-- Verificar
SELECT COUNT(*) as total_supervisiones, COUNT(id_empresa) as con_empresa FROM supervision;

-- Actualizar mapas
UPDATE mapa 
SET id_empresa = 1 
WHERE id_empresa IS NULL;

-- Verificar
SELECT id_mapa, nombre_mapa, id_empresa FROM mapa LIMIT 5;

-- Actualizar objetos del mapa
UPDATE objeto_mapa 
SET id_empresa = 1 
WHERE id_empresa IS NULL;

-- Actualizar muebles de reposición
UPDATE mueble_reposicion 
SET id_empresa = 1 
WHERE id_empresa IS NULL;

-- Actualizar productos
UPDATE producto 
SET id_empresa = 1 
WHERE id_empresa IS NULL;

-- Verificar productos
SELECT id_producto, nombre, codigo_unico, id_empresa FROM producto LIMIT 5;

-- Actualizar puntos de reposición
UPDATE punto_reposicion 
SET id_empresa = 1 
WHERE id_empresa IS NULL;

-- Actualizar tareas
UPDATE tarea 
SET id_empresa = 1 
WHERE id_empresa IS NULL;

-- Verificar tareas
SELECT id_tarea, titulo, id_empresa FROM tarea LIMIT 5;

-- Actualizar rutas optimizadas
UPDATE ruta_optimizada 
SET id_empresa = 1 
WHERE id_empresa IS NULL;

-- Verificar rutas
SELECT id_ruta, fecha_creacion, id_empresa FROM ruta_optimizada LIMIT 5;

-- =====================================================================
-- PASO 3: CREAR PLANES DE SUSCRIPCIÓN
-- =====================================================================

INSERT INTO plan_suscripcion (nombre_plan, descripcion, precio_mensual, limite_usuarios, limite_rutas_mes, soporte_ia, estado)
VALUES 
    ('Plan Básico', 'Ideal para pequeñas empresas', 9990.00, 5, 100, false, 'activo'),
    ('Plan Profesional', 'Para empresas en crecimiento', 29990.00, 20, 500, true, 'activo'),
    ('Plan Enterprise', 'Sin límites', 99990.00, NULL, NULL, true, 'activo')
ON CONFLICT (nombre_plan) DO NOTHING;

-- Verificar planes
SELECT * FROM plan_suscripcion;

-- =====================================================================
-- PASO 4: ASIGNAR PLAN ENTERPRISE A LA EMPRESA
-- =====================================================================

INSERT INTO empresa_suscripcion (id_empresa, id_plan, fecha_inicio, fecha_fin, estado_pago)
VALUES (
    1,  -- id_empresa
    (SELECT id_plan FROM plan_suscripcion WHERE nombre_plan = 'Plan Enterprise'),
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP + INTERVAL '1 year',
    'pagado'
)
ON CONFLICT (id_empresa) DO NOTHING;

-- Verificar suscripción
SELECT 
    e.nombre_empresa, 
    p.nombre_plan, 
    s.estado_pago,
    s.fecha_inicio,
    s.fecha_fin
FROM empresa_suscripcion s
JOIN empresa e ON s.id_empresa = e.id_empresa
JOIN plan_suscripcion p ON s.id_plan = p.id_plan;

-- =====================================================================
-- PASO 5: VERIFICACIÓN FINAL - RESUMEN COMPLETO
-- =====================================================================

SELECT 'USUARIOS' as tabla, COUNT(*) as total, COUNT(id_empresa) as con_empresa FROM usuario
UNION ALL
SELECT 'SUPERVISIONES', COUNT(*), COUNT(id_empresa) FROM supervision
UNION ALL
SELECT 'MAPAS', COUNT(*), COUNT(id_empresa) FROM mapa
UNION ALL
SELECT 'OBJETOS_MAPA', COUNT(*), COUNT(id_empresa) FROM objeto_mapa
UNION ALL
SELECT 'MUEBLES', COUNT(*), COUNT(id_empresa) FROM mueble_reposicion
UNION ALL
SELECT 'PRODUCTOS', COUNT(*), COUNT(id_empresa) FROM producto
UNION ALL
SELECT 'PUNTOS', COUNT(*), COUNT(id_empresa) FROM punto_reposicion
UNION ALL
SELECT 'TAREAS', COUNT(*), COUNT(id_empresa) FROM tarea
UNION ALL
SELECT 'RUTAS', COUNT(*), COUNT(id_empresa) FROM ruta_optimizada;

-- =====================================================================
-- ¡LISTO! Todos los registros ahora tienen id_empresa = 1
-- =====================================================================
