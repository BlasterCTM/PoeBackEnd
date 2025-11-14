-- ========================================
-- SCRIPT PARA CREAR USUARIO SUPERADMIN
-- ========================================
-- Base de datos: POE (Path Optimization Engine)
-- Usuario: admin@poe.cl
-- Contraseña: admin123
-- ========================================

-- 1. CREAR ROL SUPERADMIN (si no existe)
INSERT INTO rol (nombre_rol)
VALUES ('SuperAdmin')
ON CONFLICT DO NOTHING;

-- 2. CREAR EMPRESA PARA SUPERADMIN (si no existe)
INSERT INTO empresa (nombre_empresa, rut_empresa, direccion, ciudad, region, estado, email)
VALUES ('POE System', '99.999.999-9', 'Oficina Central', 'Santiago', 'Metropolitana', 'activo', 'admin@poe.cl')
ON CONFLICT (rut_empresa) DO NOTHING;

-- 3. CREAR USUARIO SUPERADMIN
-- Contraseña: admin123 (ya hasheada con bcrypt)
-- Hash generado con passlib bcrypt

INSERT INTO usuario (
    id_empresa,
    rol_id,
    nombre,
    correo,
    contraseña,
    estado
)
VALUES (
    (SELECT id_empresa FROM empresa WHERE rut_empresa = '99.999.999-9' LIMIT 1),  -- ID de empresa POE System
    (SELECT id_rol FROM rol WHERE nombre_rol = 'SuperAdmin' LIMIT 1),             -- ID del rol SuperAdmin
    'Administrador del Sistema',
    'admin@poe.cl',
    '$2b$12$C4SiONNwYEJvbTHNdeFrrOOiQ02Ac1.Q5NEshCwtp/HVKshnggk9G',  -- admin123
    'activo'
)
ON CONFLICT (id_empresa, correo) DO UPDATE SET
    contraseña = EXCLUDED.contraseña,
    estado = 'activo';

-- ========================================
-- VERIFICAR QUE SE CREÓ CORRECTAMENTE
-- ========================================
SELECT 
    u.id_usuario,
    u.nombre,
    u.correo,
    u.estado,
    r.nombre_rol as rol,
    e.nombre_empresa as empresa,
    e.rut_empresa
FROM usuario u
LEFT JOIN rol r ON u.rol_id = r.id_rol
LEFT JOIN empresa e ON u.id_empresa = e.id_empresa
WHERE u.correo = 'admin@poe.cl';

-- ========================================
-- CREDENCIALES DE ACCESO
-- ========================================
-- Email: admin@poe.cl
-- Contraseña: admin123
-- ========================================
