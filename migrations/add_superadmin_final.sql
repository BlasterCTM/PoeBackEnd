-- ============================================================
-- PASO 1: Crear el rol SuperAdmin (solo con nombre_rol)
-- ============================================================

INSERT INTO rol (nombre_rol)
VALUES ('SuperAdmin');

-- ============================================================
-- PASO 2: Actualizar el usuario admin@poe.com para que sea SuperAdmin
-- ============================================================

UPDATE usuario 
SET rol_id = (SELECT id_rol FROM rol WHERE nombre_rol = 'SuperAdmin')
WHERE correo = 'admin@poe.com';

-- ============================================================
-- PASO 3: Verificar los cambios
-- ============================================================

-- Ver todos los roles
SELECT * FROM rol ORDER BY id_rol;

-- Ver el usuario admin actualizado
SELECT u.id_usuario, u.nombre, u.correo, r.nombre_rol, u.id_empresa
FROM usuario u
JOIN rol r ON u.rol_id = r.id_rol
WHERE u.correo = 'admin@poe.com';
