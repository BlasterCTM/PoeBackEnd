-- =====================================================================
-- SCRIPT RÁPIDO: Solo INSERT de empresa y UPDATE de datos existentes
-- Copiar y pegar en pgAdmin (Query Tool)
-- =====================================================================

-- Crear empresa
INSERT INTO empresa (nombre_empresa, rut_empresa, direccion, estado)
VALUES ('Empresa Principal', '1-1', 'Santiago, Chile', 'activo')
ON CONFLICT (rut_empresa) DO NOTHING;

-- Actualizar usuarios con id_empresa = 1
UPDATE usuario SET id_empresa = 1 WHERE id_empresa IS NULL;

-- Actualizar otras tablas
UPDATE supervision SET id_empresa = 1 WHERE id_empresa IS NULL;
UPDATE mapa SET id_empresa = 1 WHERE id_empresa IS NULL;
UPDATE objeto_mapa SET id_empresa = 1 WHERE id_empresa IS NULL;
UPDATE mueble_reposicion SET id_empresa = 1 WHERE id_empresa IS NULL;
UPDATE producto SET id_empresa = 1 WHERE id_empresa IS NULL;
UPDATE punto_reposicion SET id_empresa = 1 WHERE id_empresa IS NULL;
UPDATE tarea SET id_empresa = 1 WHERE id_empresa IS NULL;
UPDATE ruta_optimizada SET id_empresa = 1 WHERE id_empresa IS NULL;

-- Crear planes
INSERT INTO plan_suscripcion (nombre_plan, descripcion, precio_mensual, limite_usuarios, limite_rutas_mes, soporte_ia, estado)
VALUES 
    ('Plan Básico', 'Pequeñas empresas', 9990.00, 5, 100, false, 'activo'),
    ('Plan Profesional', 'Empresas en crecimiento', 29990.00, 20, 500, true, 'activo'),
    ('Plan Enterprise', 'Sin límites', 99990.00, NULL, NULL, true, 'activo')
ON CONFLICT (nombre_plan) DO NOTHING;

-- Asignar plan Enterprise a la empresa
INSERT INTO empresa_suscripcion (id_empresa, id_plan, fecha_inicio, fecha_fin, estado_pago)
VALUES (
    1,
    (SELECT id_plan FROM plan_suscripcion WHERE nombre_plan = 'Plan Enterprise'),
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP + INTERVAL '1 year',
    'pagado'
)
ON CONFLICT (id_empresa) DO NOTHING;

-- Verificar resultados
SELECT 'Empresa:' as tipo, nombre_empresa as nombre FROM empresa WHERE id_empresa = 1
UNION ALL
SELECT 'Usuarios:', COUNT(*)::text FROM usuario WHERE id_empresa = 1
UNION ALL
SELECT 'Productos:', COUNT(*)::text FROM producto WHERE id_empresa = 1;
