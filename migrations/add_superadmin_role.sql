-- ============================================================
-- Migración: Agregar rol SuperAdmin para Multi-Tenant
-- Fecha: 2025-11-07
-- Descripción: Crea el rol SuperAdmin que puede gestionar todas las empresas
-- ============================================================

BEGIN;

-- Verificar si ya existe el rol SuperAdmin
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM rol WHERE nombre_rol = 'SuperAdmin') THEN
        -- Insertar el nuevo rol SuperAdmin
        INSERT INTO rol (nombre_rol, descripcion, permisos)
        VALUES (
            'SuperAdmin',
            'Super administrador del sistema con acceso global a todas las empresas',
            'all'
        );
        
        RAISE NOTICE 'Rol SuperAdmin creado exitosamente';
    ELSE
        RAISE NOTICE 'Rol SuperAdmin ya existe';
    END IF;
END $$;

-- Verificación: Mostrar todos los roles
SELECT id_rol, nombre_rol, descripcion 
FROM rol 
ORDER BY id_rol;

COMMIT;

-- ============================================================
-- NOTA: Después de ejecutar este script, puedes actualizar
-- el usuario admin@poe.com para que tenga el rol SuperAdmin:
-- 
-- UPDATE usuario 
-- SET rol_id = (SELECT id_rol FROM rol WHERE nombre_rol = 'SuperAdmin')
-- WHERE correo = 'admin@poe.com';
-- ============================================================
